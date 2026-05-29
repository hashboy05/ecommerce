"""Tests for store CRUD and JWT protection of write operations."""


def test_listing_stores_is_public(client):
    resp = client.get("/store")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_store_without_token_is_401(client):
    resp = client.post("/store", json={"name": "Acme"})
    assert resp.status_code == 401


def test_create_store_with_token_is_201(client, auth_headers):
    resp = client.post(
        "/store", json={"name": "Acme", "description": "My shop"}, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Acme"
    assert "id" in data


def test_create_store_missing_name_is_validation_error(client, auth_headers):
    # "name" is required by StoreSchema → Marshmallow rejects the request.
    resp = client.post("/store", json={"description": "no name"}, headers=auth_headers)
    assert resp.status_code in (400, 422)


def test_get_patch_delete_store_lifecycle(client, auth_headers):
    store_id = client.post(
        "/store", json={"name": "Acme"}, headers=auth_headers
    ).get_json()["id"]

    # GET is public
    assert client.get(f"/store/{store_id}").status_code == 200

    # PATCH requires a token
    patched = client.patch(
        f"/store/{store_id}", json={"name": "Acme Renamed"}, headers=auth_headers
    )
    assert patched.status_code == 200
    assert patched.get_json()["name"] == "Acme Renamed"

    # DELETE requires a token
    assert client.delete(f"/store/{store_id}", headers=auth_headers).status_code == 204

    # The store is gone afterwards
    assert client.get(f"/store/{store_id}").status_code == 404


def test_delete_store_without_token_is_401(client, auth_headers):
    store_id = client.post(
        "/store", json={"name": "Acme"}, headers=auth_headers
    ).get_json()["id"]
    assert client.delete(f"/store/{store_id}").status_code == 401
