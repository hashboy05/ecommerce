from marshmallow import Schema, fields


class PlainItemSchema(Schema):
    """Fields returned/accepted without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    description = fields.Str(load_default=None)
    # Current quantity on hand, derived from the stock-movement ledger. Defined
    # here (not just on ItemSchema) so nested item lists also show stock.
    stock = fields.Int(dump_only=True)


class ItemSchema(PlainItemSchema):
    """Full item response — nested store, supplier, category, tags, and derived stock."""
    store_id = fields.Int(required=True, load_only=True)
    supplier_id = fields.Int(load_default=None, load_only=True)
    category_id = fields.Int(load_default=None, load_only=True)
    store = fields.Nested(lambda: __import__('schemas.store', fromlist=['PlainStoreSchema']).PlainStoreSchema(), dump_only=True)
    supplier = fields.Nested(lambda: __import__('schemas.supplier', fromlist=['PlainSupplierSchema']).PlainSupplierSchema(), dump_only=True)
    category = fields.Nested(lambda: __import__('schemas.category', fromlist=['PlainCategorySchema']).PlainCategorySchema(), dump_only=True)
    tags = fields.List(fields.Nested(lambda: __import__('schemas.tag', fromlist=['PlainTagSchema']).PlainTagSchema()), dump_only=True)


class ItemUpdateSchema(Schema):
    """All fields optional — used for PATCH requests."""
    name = fields.Str()
    price = fields.Float()
    description = fields.Str()
    # allow_none so the client can clear an item's supplier/category (send null).
    supplier_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
