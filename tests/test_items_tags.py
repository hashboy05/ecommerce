"""Tests for item CRUD, the store association, and tag many-to-many linking."""


def _create_store(client, auth_headers, name="Store 1"):
    return client.post("/store", json={"name": name}, headers=auth_headers).get_json()["id"]


def test_create_item_without_token_is_401(client, auth_headers):
    store_id = _create_store(client, auth_headers)
    resp = client.post(
        "/item", json={"name": "Laptop", "price": 999.99, "store_id": store_id}
    )
    assert resp.status_code == 401


def test_create_item_returns_store_association(client, auth_headers):
    store_id = _create_store(client, auth_headers)
    resp = client.post(
        "/item",
        json={"name": "Laptop", "price": 999.99, "store_id": store_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    item = resp.get_json()
    assert item["name"] == "Laptop"
    # Retrieving an item includes its nested store (one-to-many association).
    assert item["store"]["id"] == store_id


def test_create_item_for_missing_store_is_404(client, auth_headers):
    resp = client.post(
        "/item",
        json={"name": "Ghost", "price": 1.0, "store_id": 9999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_listing_items_is_public(client, auth_headers):
    store_id = _create_store(client, auth_headers)
    client.post(
        "/item",
        json={"name": "Laptop", "price": 10.0, "store_id": store_id},
        headers=auth_headers,
    )
    resp = client.get("/item")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_tag_create_link_and_unlink(client, auth_headers):
    store_id = _create_store(client, auth_headers)
    item_id = client.post(
        "/item",
        json={"name": "Laptop", "price": 10.0, "store_id": store_id},
        headers=auth_headers,
    ).get_json()["id"]

    # Create a tag scoped to the store
    tag = client.post(
        f"/store/{store_id}/tag", json={"name": "Electronics"}, headers=auth_headers
    )
    assert tag.status_code == 201
    tag_id = tag.get_json()["id"]

    # Link the tag to the item (many-to-many)
    link = client.post(f"/item/{item_id}/tag/{tag_id}", headers=auth_headers)
    assert link.status_code == 201

    # The store's tag list now contains the tag
    tags = client.get(f"/store/{store_id}/tag").get_json()
    assert len(tags) == 1
    assert tags[0]["name"] == "Electronics"

    # Unlink the tag from the item
    unlink = client.delete(f"/item/{item_id}/tag/{tag_id}", headers=auth_headers)
    assert unlink.status_code == 200
