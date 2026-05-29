from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required

from db import db
from models.models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, PlainTagSchema, TagAndItemSchema

blp = Blueprint("tags", __name__, description="Operations on tags")


@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):

    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        """List all tags scoped to a store."""
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @jwt_required()
    @blp.arguments(PlainTagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        """Create a new tag scoped to a store."""
        if TagModel.query.filter(
            TagModel.store_id == store_id,
            TagModel.name == tag_data["name"]
        ).first():
            abort(400, message="A tag with that name already exists in this store.")
        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the tag.")
        return tag


@blp.route("/store/<int:store_id>/tag/<int:tag_id>")
class TagInStore(MethodView):

    @blp.response(200, TagSchema)
    def get(self, store_id, tag_id):
        """Get a specific tag within a store."""
        tag = TagModel.query.filter_by(id=tag_id, store_id=store_id).first_or_404()
        return tag

    @jwt_required()
    @blp.response(204)
    def delete(self, store_id, tag_id):
        """Delete a tag from a store (only if not linked to any items)."""
        tag = TagModel.query.filter_by(id=tag_id, store_id=store_id).first_or_404()
        if tag.items:
            abort(400, message="Cannot delete a tag that is still linked to items.")
        try:
            db.session.delete(tag)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while deleting the tag.")


@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):

    @jwt_required()
    @blp.response(201, TagAndItemSchema)
    def post(self, item_id, tag_id):
        """Assign a tag to an item."""
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        if item.store_id != tag.store_id:
            abort(400, message="Tag and item must belong to the same store.")
        if tag in item.tags:
            abort(400, message="This tag is already linked to the item.")
        item.tags.append(tag)
        try:
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while linking the tag.")
        return {"message": "Tag linked to item.", "item": item, "tag": tag}

    @jwt_required()
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        """Remove a tag from an item."""
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        if tag not in item.tags:
            abort(404, message="This tag is not linked to the item.")
        item.tags.remove(tag)
        try:
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while removing the tag.")
        return {"message": "Tag removed from item.", "item": item, "tag": tag}
