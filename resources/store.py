from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import jwt_required

from db import db
from models.models import StoreModel
from schemas import StoreSchema, StoreUpdateSchema

blp = Blueprint("stores", __name__, description="Operations on stores")


@blp.route("/store")
class StoreList(MethodView):

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        """List all stores."""
        return StoreModel.query.all()

    @jwt_required()
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        """Create a new store."""
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the store.")
        return store


@blp.route("/store/<int:store_id>")
class Store(MethodView):

    @blp.response(200, StoreSchema)
    def get(self, store_id):
        """Get a store by ID."""
        return StoreModel.query.get_or_404(store_id)

    @jwt_required()
    @blp.arguments(StoreUpdateSchema)
    @blp.response(200, StoreSchema)
    def patch(self, store_data, store_id):
        """Partially update a store."""
        store = StoreModel.query.get_or_404(store_id)
        for key, value in store_data.items():
            setattr(store, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while updating the store.")
        return store

    @jwt_required()
    @blp.response(204)
    def delete(self, store_id):
        """Delete a store (cascades to its items)."""
        store = StoreModel.query.get_or_404(store_id)
        try:
            db.session.delete(store)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the store.")
