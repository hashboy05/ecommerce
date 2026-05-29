import os
from flask import Flask, render_template
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from db import db

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
# Using a factory function (instead of a module-level app instance) keeps the
# application configurable and testable: each call creates a fresh app so
# tests can set different DATABASE_URL values without side effects.
# ---------------------------------------------------------------------------


def create_app(db_url: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Parameters
    ----------
    db_url : str, optional
        SQLAlchemy database URL.  Defaults to the DATABASE_URL environment
        variable, falling back to a local SQLite file (``ecommerce.db``).
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Core configuration
    # ------------------------------------------------------------------
    app.config["PROPAGATE_EXCEPTIONS"] = True

    # Flask-Smorest (OpenAPI) settings
    app.config["API_TITLE"] = "E-Commerce REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )
    # Advertise the JWT bearer scheme globally so the Swagger UI renders an
    # "Authorize" button and attaches the token to requests. (Read endpoints
    # are still public — that is enforced in code by the absence of
    # @jwt_required; the global marking here is just for the interactive docs.)
    app.config["API_SPEC_OPTIONS"] = {
        "security": [{"BearerAuth": []}],
    }

    # Database – prefer explicit argument, then env var, then SQLite default
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        db_url
        or os.getenv("DATABASE_URL", "sqlite:///ecommerce.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------------------------------------------------------
    # JWT configuration
    # ------------------------------------------------------------------
    # The secret signs every token; it MUST come from the environment in
    # production. The dev default only exists so the prototype runs locally.
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", "dev-only-change-me-in-production"
    )
    # Tokens stay valid for 12 hours — convenient for the demo UI.
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600 * 12

    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    db.init_app(app)

    api = Api(app)

    # Register the bearer-token security scheme referenced by API_SPEC_OPTIONS
    # above, so Swagger UI knows to send "Authorization: Bearer <token>".
    api.spec.components.security_scheme(
        "BearerAuth",
        {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    )

    # JWTManager wires token creation/verification into the app and lets us
    # customise the JSON returned when authentication fails so that every
    # error response in the API consistently uses a "message" field.
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"message": "The token has expired.", "error": "token_expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            "message": "Signature verification failed.",
            "error": "invalid_token",
        }, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            "message": "Request does not contain an access token.",
            "error": "authorization_required",
        }, 401

    # ------------------------------------------------------------------
    # Create tables on first run
    # ------------------------------------------------------------------
    # In production you would use Flask-Migrate (Alembic) instead of
    # create_all(), but for the prototype this keeps the setup simple.
    with app.app_context():
        # Import models so SQLAlchemy is aware of them before create_all().
        from models.models import (  # noqa: F401
            StoreModel,
            ItemModel,
            TagModel,
            UserModel,
            SupplierModel,
            CategoryModel,
            StockMovementModel,
        )
        db.create_all()

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    # Blueprints are imported here (inside the factory) to avoid circular
    # imports: blueprints import db and models, which are already set up.
    #
    # Additional blueprints (users, auth) follow the same pattern and
    # will be registered here by other team members.
    from resources.store import blp as store_blueprint
    from resources.item import blp as item_blueprint
    from resources.tag import blp as tag_blueprint
    from resources.user import blp as user_blueprint
    from resources.supplier import blp as supplier_blueprint
    from resources.category import blp as category_blueprint
    from resources.stock_movement import blp as stock_blueprint

    api.register_blueprint(store_blueprint)
    api.register_blueprint(item_blueprint)
    api.register_blueprint(tag_blueprint)
    api.register_blueprint(user_blueprint)
    api.register_blueprint(supplier_blueprint)
    api.register_blueprint(category_blueprint)
    api.register_blueprint(stock_blueprint)

    # ------------------------------------------------------------------
    # Frontend – serve the HTML dashboard at the root URL
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
