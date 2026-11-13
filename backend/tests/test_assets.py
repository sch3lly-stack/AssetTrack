from fastapi import status
from app.models.category import AssetCategory
from app.models.department import Department
from app.models.vendor import Vendor


def test_create_asset_success(client, manager_token, db_session):
    cat = db_session.query(AssetCategory).first()
    dept = db_session.query(Department).first()
    vend = db_session.query(Vendor).first()

    payload = {
        "asset_tag": "AST-2026-0001",
        "serial_number": "SN-99881122",
        "name": "ThinkPad P16 Gen 2",
        "manufacturer": "Lenovo",
        "model": "P16-G2",
        "specifications": {"ram": "64GB", "cpu": "i9-13980HX"},
        "category_id": cat.id,
        "department_id": dept.id,
        "vendor_id": vend.id,
        "purchase_cost": 2850.00,
        "salvage_value": 300.00,
        "purchase_date": "2026-01-15",
        "expected_lifespan_months": 36,
        "depreciation_method": "STRAIGHT_LINE",
        "status": "IN_STOCK",
        "condition": "NEW",
        "location": "HQ Central Depot"
    }

    response = client.post(
        "/api/v1/assets",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["asset_tag"] == "AST-2026-0001"
    assert data["serial_number"] == "SN-99881122"
    assert data["depreciation"] is not None
    assert data["depreciation"]["current_book_value"] > 0


def test_create_asset_duplicate_tag(client, manager_token, db_session):
    cat = db_session.query(AssetCategory).first()
    payload = {
        "asset_tag": "AST-DUP-01",
        "serial_number": "SN-001",
        "name": "Laptop 1",
        "manufacturer": "Dell",
        "model": "XPS 15",
        "category_id": cat.id,
        "purchase_cost": 2000.0,
        "purchase_date": "2026-01-01",
    }
    # First create
    r1 = client.post("/api/v1/assets", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
    assert r1.status_code == status.HTTP_201_CREATED

    # Second create with duplicate tag but different serial
    payload2 = dict(payload)
    payload2["serial_number"] = "SN-002"
    r2 = client.post("/api/v1/assets", json=payload2, headers={"Authorization": f"Bearer {manager_token}"})
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in r2.json()["detail"]


def test_create_asset_duplicate_serial(client, manager_token, db_session):
    cat = db_session.query(AssetCategory).first()
    payload = {
        "asset_tag": "AST-SN-01",
        "serial_number": "SN-SAME-123",
        "name": "Laptop 1",
        "manufacturer": "Dell",
        "model": "XPS 15",
        "category_id": cat.id,
        "purchase_cost": 2000.0,
        "purchase_date": "2026-01-01",
    }
    r1 = client.post("/api/v1/assets", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
    assert r1.status_code == status.HTTP_201_CREATED

    payload2 = dict(payload)
    payload2["asset_tag"] = "AST-SN-02"
    r2 = client.post("/api/v1/assets", json=payload2, headers={"Authorization": f"Bearer {manager_token}"})
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in r2.json()["detail"]


def test_read_only_user_cannot_create_asset(client, readonly_token, db_session):
    cat = db_session.query(AssetCategory).first()
    payload = {
        "asset_tag": "AST-RO-01",
        "serial_number": "SN-RO-01",
        "name": "Laptop",
        "manufacturer": "Dell",
        "model": "XPS",
        "category_id": cat.id,
        "purchase_cost": 1500.0,
        "purchase_date": "2026-01-01",
    }
    response = client.post(
        "/api/v1/assets",
        json=payload,
        headers={"Authorization": f"Bearer {readonly_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
