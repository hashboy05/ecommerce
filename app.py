import os
from flask import Flask, render_template
from flask_smorest import Api
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

    # Database – prefer explicit argument, then env var, then SQLite default
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        db_url
        or os.getenv("DATABASE_URL", "sqlite:///ecommerce.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    db.init_app(app)

    api = Api(app)

    # ------------------------------------------------------------------
    # Create tables on first run
    # ------------------------------------------------------------------
    # In production you would use Flask-Migrate (Alembic) instead of
    # create_all(), but for the prototype this keeps the setup simple.
    with app.app_context():
        # Import models so SQLAlchemy is aware of them before create_all().
        from models.models import StoreModel, ItemModel, TagModel  # noqa: F401
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

    api.register_blueprint(store_blueprint)
    api.register_blueprint(item_blueprint)
    api.register_blueprint(tag_blueprint)

    # ------------------------------------------------------------------
    # Frontend – serve the HTML dashboard at the root URL
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
