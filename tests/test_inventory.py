"""Tests for the inventory models: Supplier, Category, and StockMovement."""


def _store(client, headers, name="Warehouse 1"):
    return client.post("/store", json={"name": name}, headers=headers).get_json()["id"]


def test_supplier_crud(client, auth_headers):
    # Creating requires a token
    assert client.post("/supplier", json={"name": "Acme Supplies"}).status_code == 401

    created = client.post(
        "/supplier",
        json={"name": "Acme Supplies", "contact_email": "sales@acme.com"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    supplier_id = created.get_json()["id"]

    assert client.get("/supplier").status_code == 200
    assert client.get(f"/supplier/{supplier_id}").status_code == 200

    patched = client.patch(
        f"/supplier/{supplier_id}", json={"phone": "+1-555-0100"}, headers=auth_headers
    )
    assert patched.status_code == 200
    assert patched.get_json()["phone"] == "+1-555-0100"

    assert client.delete(f"/supplier/{supplier_id}", headers=auth_headers).status_code == 204


def test_category_crud(client, auth_headers):
    assert client.post("/category", json={"name": "Laptops"}).status_code == 401
    created = client.post("/category", json={"name": "Laptops"}, headers=auth_headers)
    assert created.status_code == 201
    assert client.get("/category").status_code == 200


def test_item_links_supplier_and_category(client, auth_headers):
    store_id = _store(client, auth_headers)
    supplier_id = client.post(
        "/supplier", json={"name": "Acme"}, headers=auth_headers
    ).get_json()["id"]
    category_id = client.post(
        "/category", json={"name": "Laptops"}, headers=auth_headers
    ).get_json()["id"]

    resp = client.post(
        "/item",
        json={
            "name": "ThinkPad",
            "price": 1200.0,
            "store_id": store_id,
            "supplier_id": supplier_id,
            "category_id": category_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["supplier"]["id"] == supplier_id
    assert data["category"]["id"] == category_id
    assert data["stock"] == 0  # no movements recorded yet


def test_item_with_unknown_supplier_is_404(client, auth_headers):
    store_id = _store(client, auth_headers)
    resp = client.post(
        "/item",
        json={"name": "Ghost", "price": 1.0, "store_id": store_id, "supplier_id": 9999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_stock_movements_drive_derived_stock(client, auth_headers):
    store_id = _store(client, auth_headers)
    item_id = client.post(
        "/item", json={"name": "ThinkPad", "price": 1200.0, "store_id": store_id},
        headers=auth_headers,
    ).get_json()["id"]

    # Recording a movement requires a token
    assert client.post(f"/item/{item_id}/movement", json={"change": 5}).status_code == 401

    # Receive 10, then ship 3
    assert client.post(
        f"/item/{item_id}/movement", json={"change": 10, "reason": "delivery"},
        headers=auth_headers,
    ).status_code == 201
    assert client.post(
        f"/item/{item_id}/movement", json={"change": -3, "reason": "shipment"},
        headers=auth_headers,
    ).status_code == 201

    # History shows both entries
    history = client.get(f"/item/{item_id}/movement")
    assert history.status_code == 200
    assert len(history.get_json()) == 2

    # Derived stock = 10 - 3 = 7
    item = client.get(f"/item/{item_id}").get_json()
    assert item["stock"] == 7


def test_zero_change_movement_is_rejected(client, auth_headers):
    store_id = _store(client, auth_headers)
    item_id = client.post(
        "/item", json={"name": "Mouse", "price": 9.99, "store_id": store_id},
        headers=auth_headers,
    ).get_json()["id"]
    resp = client.post(
        f"/item/{item_id}/movement", json={"change": 0}, headers=auth_headers
    )
    assert resp.status_code == 400
