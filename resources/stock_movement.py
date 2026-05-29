from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import db
from models.models import StockMovementModel, ItemModel
from schemas import StockMovementSchema

blp = Blueprint("stock", __name__, description="Stock movement ledger")


@blp.route("/item/<int:item_id>/movement")
class ItemMovements(MethodView):

    @blp.response(200, StockMovementSchema(many=True))
    def get(self, item_id):
        """List an item's stock movement history (newest first)."""
        item = ItemModel.query.get_or_404(item_id)
        return item.movements.order_by(StockMovementModel.created_at.desc()).all()

    @jwt_required()
    @blp.arguments(StockMovementSchema)
    @blp.response(201, StockMovementSchema)
    def post(self, movement_data, item_id):
        """Record a stock movement (+in / -out) for an item."""
        ItemModel.query.get_or_404(item_id)
        if movement_data["change"] == 0:
            abort(400, message="Stock change cannot be zero.")

        movement = StockMovementModel(
            item_id=item_id,
            user_id=int(get_jwt_identity()),  # the staff member recording it
            change=movement_data["change"],
            reason=movement_data.get("reason"),
        )
        try:
            db.session.add(movement)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while recording the movement.")
        return movement
