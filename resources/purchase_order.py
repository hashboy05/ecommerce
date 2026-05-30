from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import db
from models.models import (
    PurchaseOrderModel,
    SupplierModel,
    ItemModel,
    StockMovementModel,
)
from schemas import PurchaseOrderSchema

blp = Blueprint("purchase_orders", __name__, description="Restock orders to suppliers")


@blp.route("/purchase-order")
class PurchaseOrderList(MethodView):

    @blp.response(200, PurchaseOrderSchema(many=True))
    def get(self):
        """List all purchase orders (newest first)."""
        return PurchaseOrderModel.query.order_by(
            PurchaseOrderModel.created_at.desc()
        ).all()

    @jwt_required()
    @blp.arguments(PurchaseOrderSchema)
    @blp.response(201, PurchaseOrderSchema)
    def post(self, po_data):
        """Place a purchase order with a supplier (starts as 'pending')."""
        if po_data["quantity"] <= 0:
            abort(400, message="Quantity must be a positive number.")
        SupplierModel.query.get_or_404(po_data["supplier_id"])
        ItemModel.query.get_or_404(po_data["item_id"])

        order = PurchaseOrderModel(
            supplier_id=po_data["supplier_id"],
            item_id=po_data["item_id"],
            quantity=po_data["quantity"],
            user_id=int(get_jwt_identity()),
        )
        try:
            db.session.add(order)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the purchase order.")
        return order


@blp.route("/purchase-order/<int:order_id>")
class PurchaseOrder(MethodView):

    @blp.response(200, PurchaseOrderSchema)
    def get(self, order_id):
        """Get a purchase order by ID."""
        return PurchaseOrderModel.query.get_or_404(order_id)

    @jwt_required()
    @blp.response(204)
    def delete(self, order_id):
        """Delete a purchase order."""
        order = PurchaseOrderModel.query.get_or_404(order_id)
        try:
            db.session.delete(order)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the purchase order.")


@blp.route("/purchase-order/<int:order_id>/receive")
class PurchaseOrderReceive(MethodView):

    @jwt_required()
    @blp.response(200, PurchaseOrderSchema)
    def post(self, order_id):
        """Mark an order as received — records a stock movement for the item."""
        order = PurchaseOrderModel.query.get_or_404(order_id)
        if order.status == "received":
            abort(400, message="This purchase order has already been received.")

        # Receiving stock = a positive movement on the item, by the current user.
        movement = StockMovementModel(
            item_id=order.item_id,
            user_id=int(get_jwt_identity()),
            change=order.quantity,
            reason=f"Purchase order #{order.id} received",
        )
        order.status = "received"
        try:
            db.session.add(movement)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while receiving the order.")
        return order
