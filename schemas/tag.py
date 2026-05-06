from marshmallow import Schema, fields


class PlainTagSchema(Schema):
    """Fields returned/accepted without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


class TagSchema(PlainTagSchema):
    """Full tag response — includes nested store and items."""
    store_id = fields.Int(dump_only=True)
    store = fields.Nested(lambda: __import__('schemas.store', fromlist=['PlainStoreSchema']).PlainStoreSchema(), dump_only=True)
    items = fields.List(fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema()), dump_only=True)


class TagAndItemSchema(Schema):
    """Used for responses when a tag is linked/unlinked from an item."""
    message = fields.Str()
    item = fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema())
    tag = fields.Nested(PlainTagSchema)
