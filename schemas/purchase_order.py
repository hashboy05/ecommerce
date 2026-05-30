from marshmallow import Schema, fields


class PurchaseOrderSchema(Schema):
    """
    A restock order to a supplier.

    ``supplier_id`` and ``item_id`` are provided on input; ``status``,
    ``user_id`` and ``created_at`` are set by the server. The nested ``supplier``
    and ``item`` are included in responses for convenience.
    """
    id = fields.Int(dump_only=True)
    supplier_id = fields.Int(required=True, load_only=True)
    item_id = fields.Int(required=True, load_only=True)
    quantity = fields.Int(required=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)
    supplier = fields.Nested(lambda: __import__('schemas.supplier', fromlist=['PlainSupplierSchema']).PlainSupplierSchema(), dump_only=True)
    item = fields.Nested(lambda: __import__('schemas.item', fromlist=['PlainItemSchema']).PlainItemSchema(), dump_only=True)
