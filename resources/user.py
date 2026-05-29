from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models.models import UserModel
from schemas import UserSchema

blp = Blueprint("users", __name__, description="Registration and authentication")


@blp.route("/register")
class UserRegister(MethodView):

    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
        """Create a new user account (username must be unique)."""
        if UserModel.query.filter_by(username=user_data["username"]).first():
            abort(409, message="A user with that username already exists.")

        user = UserModel(
            username=user_data["username"],
            # Hash immediately; the plaintext password is never persisted.
            password=generate_password_hash(user_data["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the user.")
        return user


@blp.route("/login")
class UserLogin(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        """Verify credentials and return a JWT access token."""
        user = UserModel.query.filter_by(username=user_data["username"]).first()

        # check_password_hash compares the stored hash against the candidate
        # password in constant time. Same generic error for unknown user and
        # wrong password so we don't leak which usernames exist.
        if user and check_password_hash(user.password, user_data["password"]):
            # PyJWT requires the "sub" claim to be a string, so the user id is
            # cast to str here and back to int wherever the identity is read.
            access_token = create_access_token(identity=str(user.id))
            return {"access_token": access_token}

        abort(401, message="Invalid username or password.")


@blp.route("/user/me")
class UserProfile(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self):
        """Return the profile of the currently authenticated user."""
        user_id = int(get_jwt_identity())
        return UserModel.query.get_or_404(user_id)
