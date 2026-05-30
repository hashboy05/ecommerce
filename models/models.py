from datetime import datetime, timezone

from db import db

# ---------------------------------------------------------------------------
# Junction table for the Item ↔ Tag many-to-many relationship.
# SQLAlchemy manages this as a plain Table (no model class needed because
# the table carries no extra columns beyond the two foreign keys).
# ---------------------------------------------------------------------------
items_tags = db.Table(
    "items_tags",
    db.Column(
        "item_id",
        db.Integer,
        db.ForeignKey("items.id"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id"),
        primary_key=True,
    ),
)


class StoreModel(db.Model):
    """
    Represents a store that owns Items and scopes Tags.

    Relationships
    -------------
    items : one-to-many (a Store has many Items)
    tags  : one-to-many (Tags belong to a Store, used to categorise its Items)
    """

    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # lazy="dynamic" defers loading so we can apply filters before executing.
    items = db.relationship("ItemModel", back_populates="store", lazy="dynamic", cascade="all, delete")
    tags = db.relationship("TagModel", back_populates="store", lazy="dynamic")


class ItemModel(db.Model):
    """
    Represents a product (SKU) held in exactly one Store (warehouse).

    Relationships
    -------------
    store     : many-to-one (each Item belongs to one Store)
    supplier  : many-to-one (the vendor that provides this Item)
    category  : many-to-one (the Item's primary classification)
    tags      : many-to-many via the items_tags junction table
    movements : one-to-many (stock in/out ledger; current stock is derived)
    """

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    description = db.Column(db.String(255))

    # Foreign key linking back to the owning store (warehouse).
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    # Optional links to the vendor that supplies this item and its category.
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    store = db.relationship("StoreModel", back_populates="items")
    tags = db.relationship("TagModel", secondary=items_tags, back_populates="items")
    supplier = db.relationship("SupplierModel", back_populates="items")
    category = db.relationship("CategoryModel", back_populates="items")
    # Stock ledger: every change in quantity is recorded as a StockMovement,
    # so the current quantity on hand is always derivable from the movements.
    movements = db.relationship(
        "StockMovementModel",
        back_populates="item",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def stock(self):
        """Current quantity on hand = sum of all recorded stock movements."""
        return sum(m.change for m in self.movements)


class TagModel(db.Model):
    """
    A label scoped to a Store that can be applied to many Items.

    Relationships
    -------------
    store : many-to-one (a Tag belongs to one Store)
    items : many-to-many via items_tags junction table
    """

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

    # Tags are scoped to a store so that "Sale" in Store A ≠ "Sale" in Store B.
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)

    store = db.relationship("StoreModel", back_populates="tags")
    items = db.relationship("ItemModel", secondary=items_tags, back_populates="tags")


class UserModel(db.Model):
    """
    Represents an account that can authenticate against the API.

    Only the password *hash* is ever stored — the plaintext password is
    discarded immediately after hashing in the registration endpoint.
    The username is unique so it can be used as a login identifier.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Holds a Werkzeug pbkdf2/scrypt hash, never the raw password.
    password = db.Column(db.String(256), nullable=False)


class SupplierModel(db.Model):
    """
    A vendor that supplies products to the company.

    Relationships
    -------------
    items : one-to-many (a Supplier provides many Items)
    """

    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    contact_email = db.Column(db.String(120))
    phone = db.Column(db.String(40))

    items = db.relationship("ItemModel", back_populates="supplier", lazy="dynamic")


class CategoryModel(db.Model):
    """
    A primary classification for products (e.g. "Laptops", "Office").

    Unlike Tags (flexible, many-to-many labels), each Item has at most one
    Category, giving a clean one-to-many hierarchy.

    Relationships
    -------------
    items : one-to-many (a Category groups many Items)
    """

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    items = db.relationship("ItemModel", back_populates="category", lazy="dynamic")


class StockMovementModel(db.Model):
    """
    A single entry in an Item's stock ledger.

    A positive ``change`` means stock came in (e.g. a delivery); a negative
    ``change`` means stock went out (e.g. a shipment or correction). Summing
    an Item's movements yields its current quantity on hand.

    Relationships
    -------------
    item : many-to-one (the Item whose stock changed)
    user : many-to-one (the staff member who recorded the movement)
    """

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    item = db.relationship("ItemModel", back_populates="movements")
    user = db.relationship("UserModel")


class PurchaseOrderModel(db.Model):
    """
    A restock order placed with a Supplier for a quantity of one Item.

    Workflow: created as ``pending``; when marked ``received`` the system records
    a positive StockMovement for the item, so ordering and stock stay in sync.

    Relationships
    -------------
    supplier : many-to-one (who the order is placed with)
    item     : many-to-one (what is being ordered)
    user     : many-to-one (the staff member who placed the order)
    """

    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    supplier = db.relationship("SupplierModel")
    item = db.relationship("ItemModel")
    user = db.relationship("UserModel")
