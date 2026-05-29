from marshmallow import Schema, fields


class StockMovementSchema(Schema):
    """
    A single stock-ledger entry.

    ``change`` is positive for stock coming in (a delivery) and negative for
    stock going out (a shipment or correction). ``item_id`` and ``user_id`` are
    set by the server (the item from the URL, the user from the JWT).
    """
    id = fields.Int(dump_only=True)
    change = fields.Int(required=True)
    reason = fields.Str(load_default=None)
    created_at = fields.DateTime(dump_only=True)
    item_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
