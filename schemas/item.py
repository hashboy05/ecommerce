from marshmallow import Schema, fields


class PlainItemSchema(Schema):
    """Fields returned/accepted without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    description = fields.Str(load_default=None)


class ItemSchema(PlainItemSchema):
    """Full item response — includes nested store and tags."""
    store_id = fields.Int(required=True, load_only=True)
    store = fields.Nested(lambda: __import__('schemas.store', fromlist=['PlainStoreSchema']).PlainStoreSchema(), dump_only=True)
    tags = fields.List(fields.Nested(lambda: __import__('schemas.tag', fromlist=['PlainTagSchema']).PlainTagSchema()), dump_only=True)


class ItemUpdateSchema(Schema):
    """All fields optional — used for PATCH requests."""
    name = fields.Str()
    price = fields.Float()
    description = fields.Str()
