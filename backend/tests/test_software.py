from fastapi import status
from app.models.employee import Employee


def test_software_license_and_seat_cap(client, manager_token, db_session):
    # 1. Create product
    prod_resp = client.post(
        "/api/v1/software/products",
        json={"name": "Figma Enterprise", "publisher": "Figma", "category": "Design"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert prod_resp.status_code == status.HTTP_201_CREATED
    product_id = prod_resp.json()["id"]

    # 2. Create license with only 1 seat
    lic_resp = client.post(
        "/api/v1/software/licenses",
        json={
            "software_id": product_id,
            "license_key": "FIGMA-SEAT-1",
            "license_type": "SUBSCRIPTION",
            "total_seats": 1,
            "cost": 500.0,
            "purchase_date": "2026-01-01"
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert lic_resp.status_code == status.HTTP_201_CREATED
    lic_id = lic_resp.json()["id"]

    emp = db_session.query(Employee).first()

    # 3. Assign the 1 available seat
    assign1 = client.post(
        f"/api/v1/software/licenses/{lic_id}/assign",
        json={"license_id": lic_id, "employee_id": emp.id, "assigned_date": "2026-01-10"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert assign1.status_code == status.HTTP_200_OK

    # 4. Attempt to allocate a second seat when total_seats = 1
    assign2 = client.post(
        f"/api/v1/software/licenses/{lic_id}/assign",
        json={"license_id": lic_id, "employee_id": emp.id, "assigned_date": "2026-01-11"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert assign2.status_code == status.HTTP_400_BAD_REQUEST
    assert "License seat capacity reached" in assign2.json()["detail"]


def test_license_utilization_report(client, manager_token):
    resp = client.get("/api/v1/software/utilization-report", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)
