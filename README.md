# E-Commerce REST API

A service-oriented backend for managing **stores, items, tags, and users**, built
with Flask. It exposes a RESTful, JSON API with JWT authentication, Marshmallow
validation, and an auto-generated OpenAPI (Swagger) UI. A small HTML dashboard is
served at `/` for interacting with the API in the browser.

---

## Tech stack

| Concern | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | Flask + Flask-Smorest (REST routing + OpenAPI) |
| ORM | Flask-SQLAlchemy (SQLAlchemy 2.x) |
| Database | SQLite (file-based, zero-config) |
| Validation / serialization | Marshmallow |
| Authentication | Flask-JWT-Extended (JWT) |
| Password hashing | Werkzeug (`pbkdf2:sha256`) |
| Production server | gunicorn |
| Containerization | Docker / Docker Compose |

---

## Project structure

```
ecommerce/
├── app.py              # Application factory: config, extensions, blueprint registration
├── wsgi.py             # Production entry point (gunicorn imports this)
├── db.py               # Shared SQLAlchemy instance
├── models/
│   └── models.py       # StoreModel, ItemModel, TagModel, UserModel + relationships
├── schemas/            # Marshmallow schemas (validation + serialization)
│   ├── store.py
│   ├── item.py
│   ├── tag.py
│   └── user.py
├── resources/          # Flask-Smorest Blueprints (the API endpoints)
│   ├── store.py
│   ├── item.py
│   ├── tag.py
│   └── user.py         # register / login / profile
├── templates/
│   └── index.html      # Browser dashboard (vanilla JS, calls the API)
├── requirements.txt    # Pinned dependencies
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

---

## Architecture overview

```
   Browser / curl / Postman
            │  JSON over HTTP
            ▼
   ┌─────────────────────────┐
   │   Flask app (app.py)     │
   │  ┌───────────────────┐   │
   │  │ Smorest Blueprints │   │  ← API layer (routes, HTTP methods, status codes)
   │  │ store/item/tag/user│   │
   │  └─────────┬─────────┘   │
   │            │              │
   │  ┌─────────▼─────────┐   │
   │  │ Marshmallow schemas│   │  ← validation + serialization
   │  └─────────┬─────────┘   │
   │            │              │
   │  ┌─────────▼─────────┐   │
   │  │ SQLAlchemy models  │   │  ← data-access layer
   │  └─────────┬─────────┘   │
   └────────────┼─────────────┘
                ▼
        SQLite (ecommerce.db)
```

JWT authentication guards every **write** operation (`POST`/`PATCH`/`DELETE`);
read operations (`GET`) are public.

---

## Running locally (development)

Requires Python 3.12+.

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # Windows PowerShell
# source .venv/bin/activate             # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
flask --app app.py run --debug
```

Open **http://127.0.0.1:5000** for the dashboard, or
**http://127.0.0.1:5000/swagger-ui** for the interactive API docs.

---

## Running with Docker

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### Option A — Docker directly

```bash
docker build -t ecommerce-api .
docker run -p 5000:5000 ecommerce-api
```

### Option B — Docker Compose (recommended)

```bash
docker compose up --build
```

Either way the API is available at **http://localhost:5000**.

To set a real secret key:

```bash
docker run -p 5000:5000 -e JWT_SECRET_KEY="a-long-random-string" ecommerce-api
```

---

## Database initialization

No manual step is needed. On startup `create_app()` calls
`db.create_all()`, which creates the SQLite file and all tables
(`stores`, `items`, `tags`, `items_tags`, `users`) if they don't exist.

- **Local runs:** the file lives at `instance/ecommerce.db`.
- **Compose runs:** the file is stored in the named volume `ecommerce-data`,
  so data survives container restarts.

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | `dev-only-change-me-in-production` | Signs JWT tokens — **set a strong value in production** |
| `DATABASE_URL` | `sqlite:///ecommerce.db` | SQLAlchemy connection string (e.g. point at PostgreSQL) |

---

## API reference

🔒 = requires `Authorization: Bearer <token>` header.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Create an account `{username, password}` → `201` |
| POST | `/login` | Get a JWT `{username, password}` → `{access_token}` |
| GET 🔒 | `/user/me` | Current user's profile |

### Stores
| Method | Endpoint | Description |
|---|---|---|
| GET | `/store` | List all stores |
| POST 🔒 | `/store` | Create a store `{name, description}` |
| GET | `/store/<id>` | Get one store |
| PATCH 🔒 | `/store/<id>` | Update a store |
| DELETE 🔒 | `/store/<id>` | Delete a store (cascades to its items) |

### Items
| Method | Endpoint | Description |
|---|---|---|
| GET | `/item` | List all items |
| POST 🔒 | `/item` | Create an item `{name, price, description, store_id}` |
| GET | `/item/<id>` | Get one item |
| PATCH 🔒 | `/item/<id>` | Update an item |
| DELETE 🔒 | `/item/<id>` | Delete an item |
| GET | `/store/<id>/item` | List items in a store |

### Tags
| Method | Endpoint | Description |
|---|---|---|
| GET | `/store/<id>/tag` | List tags in a store |
| POST 🔒 | `/store/<id>/tag` | Create a tag in a store `{name}` |
| GET | `/store/<id>/tag/<tag_id>` | Get one tag |
| DELETE 🔒 | `/store/<id>/tag/<tag_id>` | Delete a tag (only if unlinked) |
| POST 🔒 | `/item/<id>/tag/<tag_id>` | Link a tag to an item |
| DELETE 🔒 | `/item/<id>/tag/<tag_id>` | Unlink a tag from an item |

---

## Authentication walkthrough (curl)

```bash
# 1. Register
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

# 2. Log in → returns {"access_token": "..."}
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

# 3. Creating a store WITHOUT a token fails with 401
curl -X POST http://localhost:5000/store \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme"}'

# 4. With the token it succeeds with 201
curl -X POST http://localhost:5000/store \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <PASTE_TOKEN_HERE>" \
  -d '{"name": "Acme"}'
```

In the Swagger UI you can click **Authorize** and paste the token to try
protected endpoints interactively.

---

## Data model

- **Store** `1 ──< ` **Item** — one-to-many (a store has many items; deleting a
  store cascades to its items).
- **Item** `>──< ` **Tag** — many-to-many via the `items_tags` junction table.
- **Tag** is scoped to a store, so the same tag name can exist in different stores.
- **User** — independent authentication entity (unique username, hashed password).

---

## Design notes

- **Application factory** (`create_app`) keeps the app configurable and testable.
- **Blueprints** split the API into independent, modular resource files.
- **Schemas** separate validation/serialization from business logic.
- **SQLite** is used for a zero-config prototype; swap to PostgreSQL by setting
  `DATABASE_URL` — no code changes required.
- **gunicorn** serves the app in the container instead of the Flask dev server,
  reflecting a production-ready deployment.
