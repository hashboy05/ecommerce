from marshmallow import Schema, fields


class PlainStoreSchema(Schema):
    """Fields returned/accepted without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(load_default=None)


class StoreSchema(PlainStoreSchema):
    """Full store response — includes nested items and tags."""
    items = fields.List(fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema()), dump_only=True)
    tags = fields.List(fields.Nested(lambda: __import__('schemas.tag', fromlist=['PlainTagSchema']).PlainTagSchema()), dump_only=True)


class StoreUpdateSchema(Schema):
    """All fields optional — used for PATCH requests."""
    name = fields.Str()
    description = fields.Str()
