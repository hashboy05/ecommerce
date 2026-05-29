from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import jwt_required

from db import db
from models.models import CategoryModel
from schemas import CategorySchema, CategoryUpdateSchema

blp = Blueprint("categories", __name__, description="Operations on categories")


@blp.route("/category")
class CategoryList(MethodView):

    @blp.response(200, CategorySchema(many=True))
    def get(self):
        """List all categories."""
        return CategoryModel.query.all()

    @jwt_required()
    @blp.arguments(CategorySchema)
    @blp.response(201, CategorySchema)
    def post(self, category_data):
        """Create a new category."""
        category = CategoryModel(**category_data)
        try:
            db.session.add(category)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A category with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the category.")
        return category


@blp.route("/category/<int:category_id>")
class Category(MethodView):

    @blp.response(200, CategorySchema)
    def get(self, category_id):
        """Get a category by ID."""
        return CategoryModel.query.get_or_404(category_id)

    @jwt_required()
    @blp.arguments(CategoryUpdateSchema)
    @blp.response(200, CategorySchema)
    def patch(self, category_data, category_id):
        """Update a category."""
        category = CategoryModel.query.get_or_404(category_id)
        for key, value in category_data.items():
            setattr(category, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            abort(400, message="A category with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while updating the category.")
        return category

    @jwt_required()
    @blp.response(204)
    def delete(self, category_id):
        """Delete a category (its items are simply unlinked, not deleted)."""
        category = CategoryModel.query.get_or_404(category_id)
        for item in category.items:
            item.category_id = None
        try:
            db.session.delete(category)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the category.")
