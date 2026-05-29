from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required

from db import db
from models.models import ItemModel, StoreModel, SupplierModel, CategoryModel
from schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("items", __name__, description="Operations on items")


@blp.route("/item")
class ItemList(MethodView):

    @blp.response(200, ItemSchema(many=True))
    def get(self):
        """List all items."""
        return ItemModel.query.all()

    @jwt_required()
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        """Create a new item inside an existing store."""
        StoreModel.query.get_or_404(item_data["store_id"])
        if item_data.get("supplier_id") is not None:
            SupplierModel.query.get_or_404(item_data["supplier_id"])
        if item_data.get("category_id") is not None:
            CategoryModel.query.get_or_404(item_data["category_id"])
        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the item.")
        return item


@blp.route("/item/<int:item_id>")
class Item(MethodView):

    @blp.response(200, ItemSchema)
    def get(self, item_id):
        """Get an item by ID."""
        return ItemModel.query.get_or_404(item_id)

    @jwt_required()
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def patch(self, item_data, item_id):
        """Partially update an item."""
        item = ItemModel.query.get_or_404(item_id)
        if item_data.get("supplier_id") is not None:
            SupplierModel.query.get_or_404(item_data["supplier_id"])
        if item_data.get("category_id") is not None:
            CategoryModel.query.get_or_404(item_data["category_id"])
        for key, value in item_data.items():
            setattr(item, key, value)
        try:
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while updating the item.")
        return item

    @jwt_required()
    @blp.response(204)
    def delete(self, item_id):
        """Delete an item."""
        item = ItemModel.query.get_or_404(item_id)
        try:
            db.session.delete(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the item.")


@blp.route("/store/<int:store_id>/item")
class ItemsByStore(MethodView):

    @blp.response(200, ItemSchema(many=True))
    def get(self, store_id):
        """List all items belonging to a specific store."""
        store = StoreModel.query.get_or_404(store_id)
        return store.items.all()
