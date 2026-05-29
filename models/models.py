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
    Represents a product belonging to exactly one Store.

    Relationships
    -------------
    store : many-to-one (each Item belongs to one Store)
    tags  : many-to-many via items_tags junction table
    """

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    description = db.Column(db.String(255))

    # Foreign key linking back to the owning store.
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)

    store = db.relationship("StoreModel", back_populates="items")
    tags = db.relationship("TagModel", secondary=items_tags, back_populates="items")


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
