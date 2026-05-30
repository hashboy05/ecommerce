"""Tests for purchase orders and the receive -> stock-movement workflow."""


def _supplier_and_item(client, headers):
    sid = client.post("/store", json={"name": "WH"}, headers=headers).get_json()["id"]
    sup = client.post("/supplier", json={"name": "Acme"}, headers=headers).get_json()["id"]
    item = client.post(
        "/item",
        json={"name": "Laptop", "price": 10.0, "store_id": sid, "supplier_id": sup},
        headers=headers,
    ).get_json()["id"]
    return sup, item


def test_create_po_requires_token(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    resp = client.post("/purchase-order", json={"supplier_id": sup, "item_id": item, "quantity": 5})
    assert resp.status_code == 401


def test_create_po_starts_pending(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    resp = client.post(
        "/purchase-order",
        json={"supplier_id": sup, "item_id": item, "quantity": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "pending"
    assert data["quantity"] == 5
    assert data["supplier"]["id"] == sup
    assert data["item"]["id"] == item


def test_po_non_positive_quantity_rejected(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    resp = client.post(
        "/purchase-order",
        json={"supplier_id": sup, "item_id": item, "quantity": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_po_unknown_supplier_is_404(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    resp = client.post(
        "/purchase-order",
        json={"supplier_id": 9999, "item_id": item, "quantity": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_receiving_po_increases_stock(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    assert client.get(f"/item/{item}").get_json()["stock"] == 0

    po = client.post(
        "/purchase-order",
        json={"supplier_id": sup, "item_id": item, "quantity": 8},
        headers=auth_headers,
    ).get_json()["id"]

    received = client.post(f"/purchase-order/{po}/receive", headers=auth_headers)
    assert received.status_code == 200
    assert received.get_json()["status"] == "received"

    # Stock went up by the ordered quantity, via an auto-created movement.
    assert client.get(f"/item/{item}").get_json()["stock"] == 8
    moves = client.get(f"/item/{item}/movement").get_json()
    assert len(moves) == 1 and moves[0]["change"] == 8


def test_double_receive_is_rejected(client, auth_headers):
    sup, item = _supplier_and_item(client, auth_headers)
    po = client.post(
        "/purchase-order",
        json={"supplier_id": sup, "item_id": item, "quantity": 3},
        headers=auth_headers,
    ).get_json()["id"]
    assert client.post(f"/purchase-order/{po}/receive", headers=auth_headers).status_code == 200
    assert client.post(f"/purchase-order/{po}/receive", headers=auth_headers).status_code == 400


def test_clearing_item_category_and_supplier(client, auth_headers):
    sid = client.post("/store", json={"name": "WH"}, headers=auth_headers).get_json()["id"]
    sup = client.post("/supplier", json={"name": "Acme"}, headers=auth_headers).get_json()["id"]
    cat = client.post("/category", json={"name": "Laptops"}, headers=auth_headers).get_json()["id"]
    iid = client.post(
        "/item",
        json={"name": "L", "price": 1.0, "store_id": sid, "supplier_id": sup, "category_id": cat},
        headers=auth_headers,
    ).get_json()["id"]

    # Sending null clears the optional links.
    resp = client.patch(
        f"/item/{iid}", json={"supplier_id": None, "category_id": None}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.get_json()["supplier"] is None
    assert resp.get_json()["category"] is None
