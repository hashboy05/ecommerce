# ---------------------------------------------------------------------------
# E-Commerce REST API — container image
# ---------------------------------------------------------------------------
# A small, reproducible image that installs the pinned dependencies and serves
# the Flask app with gunicorn (a production WSGI server) on port 5000.
#
#   docker build -t ecommerce-api .
#   docker run -p 5000:5000 ecommerce-api
# ---------------------------------------------------------------------------

# python:3.12-slim is small and has prebuilt wheels for every pinned package.
FROM python:3.12-slim

# - PYTHONDONTWRITEBYTECODE: don't litter the image with .pyc files
# - PYTHONUNBUFFERED: stream logs straight to the container output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies in their own layer so Docker caches them and only
# reinstalls when requirements.txt changes (fast rebuilds after code edits).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source code.
COPY . .

# The Flask app listens on 5000.
EXPOSE 5000

# Serve with gunicorn. "wsgi:app" is the app instance defined in wsgi.py.
# create_app() builds the tables on startup, so the API is ready at once.
# Hosts like Render inject the listening port via $PORT; default to 5000 locally.
# (sh -c is used so ${PORT} is expanded at runtime.)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 wsgi:app"]
