from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import jwt_required

from db import db
from models.models import SupplierModel
from schemas import SupplierSchema, SupplierUpdateSchema

blp = Blueprint("suppliers", __name__, description="Operations on suppliers")


@blp.route("/supplier")
class SupplierList(MethodView):

    @blp.response(200, SupplierSchema(many=True))
    def get(self):
        """List all suppliers."""
        return SupplierModel.query.all()

    @jwt_required()
    @blp.arguments(SupplierSchema)
    @blp.response(201, SupplierSchema)
    def post(self, supplier_data):
        """Create a new supplier."""
        supplier = SupplierModel(**supplier_data)
        try:
            db.session.add(supplier)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A supplier with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the supplier.")
        return supplier


@blp.route("/supplier/<int:supplier_id>")
class Supplier(MethodView):

    @blp.response(200, SupplierSchema)
    def get(self, supplier_id):
        """Get a supplier by ID."""
        return SupplierModel.query.get_or_404(supplier_id)

    @jwt_required()
    @blp.arguments(SupplierUpdateSchema)
    @blp.response(200, SupplierSchema)
    def patch(self, supplier_data, supplier_id):
        """Update a supplier."""
        supplier = SupplierModel.query.get_or_404(supplier_id)
        for key, value in supplier_data.items():
            setattr(supplier, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            abort(400, message="A supplier with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while updating the supplier.")
        return supplier

    @jwt_required()
    @blp.response(204)
    def delete(self, supplier_id):
        """Delete a supplier (its items are simply unlinked, not deleted)."""
        supplier = SupplierModel.query.get_or_404(supplier_id)
        for item in supplier.items:
            item.supplier_id = None
        try:
            db.session.delete(supplier)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the supplier.")
