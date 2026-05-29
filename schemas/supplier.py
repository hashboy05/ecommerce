from marshmallow import Schema, fields


class PlainSupplierSchema(Schema):
    """Supplier fields without nested relationships."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    contact_email = fields.Str(load_default=None)
    phone = fields.Str(load_default=None)


class SupplierSchema(PlainSupplierSchema):
    """Full supplier response — includes the items it supplies."""
    items = fields.List(
        fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema()),
        dump_only=True,
    )


class SupplierUpdateSchema(Schema):
    """All fields optional — used for PATCH requests."""
    name = fields.Str()
    contact_email = fields.Str()
    phone = fields.Str()
