import io
from fastapi import status
from app.models.category import AssetCategory


def test_export_assets_csv(client, manager_token):
    response = client.get("/api/v1/assets/export/csv", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]
    assert "Asset Tag,Name,Manufacturer,Model,Serial Number" in response.text


def test_import_assets_csv(client, manager_token, db_session):
    cat = db_session.query(AssetCategory).first()
    csv_data = (
        "Asset Tag,Name,Manufacturer,Model,Serial Number,Category,Purchase Cost,Purchase Date\n"
        f"AST-CSV-99,Test Laptop CSV,Apple,MacBook,SN-CSV-99,{cat.code},1999.00,2026-01-01\n"
    )

    file_bytes = io.BytesIO(csv_data.encode("utf-8"))
    response = client.post(
        "/api/v1/assets/import/csv",
        files={"file": ("test.csv", file_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["imported_count"] == 1
    assert len(data["errors"]) == 0
