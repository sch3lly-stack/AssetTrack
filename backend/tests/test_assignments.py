from datetime import date
from fastapi import status
from app.models.asset import Asset, AssetStatus, AssetCondition, DepreciationMethod
from app.models.category import AssetCategory
from app.models.employee import Employee


def create_sample_asset(db_session, tag="AST-ASG-01", sn="SN-ASG-01"):
    cat = db_session.query(AssetCategory).first()
    asset = Asset(
        asset_tag=tag,
        serial_number=sn,
        name="MacBook Pro",
        manufacturer="Apple",
        model="M3 Pro",
        category_id=cat.id,
        purchase_cost=2500.0,
        purchase_date=date(2025, 1, 1),
        expected_lifespan_months=36,
        depreciation_method=DepreciationMethod.STRAIGHT_LINE,
        status=AssetStatus.IN_STOCK,
        condition=AssetCondition.NEW,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_assignment_auto_approve_by_manager(client, manager_token, db_session):
    asset = create_sample_asset(db_session, "AST-AA-01", "SN-AA-01")
    emp = db_session.query(Employee).first()

    payload = {
        "asset_id": asset.id,
        "employee_id": emp.id,
        "assigned_date": "2026-02-01",
        "expected_return_date": "2027-02-01",
        "condition_on_assignment": "NEW",
        "assignment_notes": "Deployment for dev lead"
    }

    response = client.post(
        "/api/v1/assignments",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert data["asset_tag"] == "AST-AA-01"

    # Verify asset status updated to ASSIGNED
    db_session.refresh(asset)
    assert asset.status == AssetStatus.ASSIGNED


def test_prevent_double_active_assignment(client, manager_token, db_session):
    asset = create_sample_asset(db_session, "AST-CONFLICT-01", "SN-CONF-01")
    emp = db_session.query(Employee).first()

    payload = {
        "asset_id": asset.id,
        "employee_id": emp.id,
        "assigned_date": "2026-02-01",
        "condition_on_assignment": "EXCELLENT",
    }
    # First assignment succeeds
    r1 = client.post("/api/v1/assignments", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
    assert r1.status_code == status.HTTP_201_CREATED

    # Attempt second active assignment to the same asset
    r2 = client.post("/api/v1/assignments", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
    assert r2.status_code == status.HTTP_409_CONFLICT
    assert "already has an active assignment" in r2.json()["detail"]


def test_return_asset_workflow(client, manager_token, tech_token, db_session):
    asset = create_sample_asset(db_session, "AST-RET-01", "SN-RET-01")
    emp = db_session.query(Employee).first()

    # Assign
    r1 = client.post(
        "/api/v1/assignments",
        json={"asset_id": asset.id, "employee_id": emp.id, "assigned_date": "2026-01-01"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assign_id = r1.json()["id"]

    # Return with DAMAGED condition
    ret_payload = {
        "returned_date": "2026-03-01",
        "condition_on_return": "DAMAGED",
        "return_notes": "Liquid spill reported on keyboard"
    }
    r2 = client.post(
        f"/api/v1/assignments/{assign_id}/return",
        json=ret_payload,
        headers={"Authorization": f"Bearer {tech_token}"}
    )
    assert r2.status_code == status.HTTP_200_OK
    data = r2.json()
    assert data["status"] == "RETURNED"
    assert data["condition_on_return"] == "DAMAGED"

    # Asset condition should now be DAMAGED and routed to UNDER_MAINTENANCE
    db_session.refresh(asset)
    assert asset.condition == AssetCondition.DAMAGED
    assert asset.status == AssetStatus.UNDER_MAINTENANCE
