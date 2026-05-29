from marshmallow import Schema, fields


class PlainCategorySchema(Schema):
    """Category fields without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(load_default=None)


class CategorySchema(PlainCategorySchema):
    """Full category response — includes the items in the category."""
    items = fields.List(
        fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema()),
        dump_only=True,
    )


class CategoryUpdateSchema(Schema):
    """All fields optional — used for PATCH requests."""
    name = fields.Str()
    description = fields.Str()
