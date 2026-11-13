import csv
import io
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetStatus, AssetCondition, DepreciationMethod
from app.models.category import AssetCategory
from app.models.department import Department
from app.models.vendor import Vendor


def export_assets_to_csv(assets: List[Asset]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Asset Tag", "Name", "Manufacturer", "Model", "Serial Number",
        "Category", "Department", "Vendor", "Purchase Cost", "Salvage Value",
        "Purchase Date", "Lifespan Months", "Depreciation Method", "Status",
        "Condition", "Location", "Notes"
    ]
    writer.writerow(headers)

    for a in assets:
        writer.writerow([
            a.asset_tag,
            a.name,
            a.manufacturer,
            a.model,
            a.serial_number,
            a.category.name if a.category else "",
            a.department.name if a.department else "",
            a.vendor.name if a.vendor else "",
            f"{float(a.purchase_cost):.2f}",
            f"{float(a.salvage_value):.2f}",
            a.purchase_date.strftime("%Y-%m-%d") if a.purchase_date else "",
            a.expected_lifespan_months,
            a.depreciation_method.value,
            a.status.value,
            a.condition.value,
            a.location,
            a.notes or ""
        ])

    return output.getvalue()


def import_assets_from_csv(csv_content: str, db: Session) -> Tuple[int, List[str]]:
    reader = csv.DictReader(io.StringIO(csv_content))
    created_count = 0
    errors = []

    # Cache categories, departments, vendors
    categories = {c.code.upper(): c.id for c in db.query(AssetCategory).all()}
    categories_by_name = {c.name.upper(): c.id for c in db.query(AssetCategory).all()}
    departments = {d.code.upper(): d.id for d in db.query(Department).all()}
    vendors = {v.name.upper(): v.id for v in db.query(Vendor).all()}

    default_cat_id = next(iter(categories.values()), None)

    for line_num, row in enumerate(reader, start=2):
        asset_tag = row.get("asset_tag", "").strip() or row.get("Asset Tag", "").strip()
        serial_number = row.get("serial_number", "").strip() or row.get("Serial Number", "").strip()
        name = row.get("name", "").strip() or row.get("Name", "").strip()
        manufacturer = row.get("manufacturer", "").strip() or row.get("Manufacturer", "").strip() or "Generic"
        model = row.get("model", "").strip() or row.get("Model", "").strip() or "Standard"

        if not asset_tag or not serial_number or not name:
            errors.append(f"Row {line_num}: Missing required field (asset_tag, serial_number, or name)")
            continue

        # Check existing
        existing_tag = db.query(Asset).filter(Asset.asset_tag == asset_tag).first()
        if existing_tag:
            errors.append(f"Row {line_num}: Asset tag '{asset_tag}' already exists")
            continue

        existing_sn = db.query(Asset).filter(Asset.serial_number == serial_number).first()
        if existing_sn:
            errors.append(f"Row {line_num}: Serial number '{serial_number}' already exists")
            continue

        # Resolve category
        cat_key = (row.get("category_code") or row.get("Category") or "").strip().upper()
        cat_id = categories.get(cat_key) or categories_by_name.get(cat_key) or default_cat_id
        if not cat_id:
            errors.append(f"Row {line_num}: Category '{cat_key}' not found and no default available")
            continue

        # Resolve department
        dept_key = (row.get("department_code") or row.get("Department") or "").strip().upper()
        dept_id = departments.get(dept_key)

        # Resolve vendor
        vend_key = (row.get("vendor_name") or row.get("Vendor") or "").strip().upper()
        vend_id = vendors.get(vend_key)

        # Parse cost
        try:
            cost_str = row.get("purchase_cost") or row.get("Purchase Cost") or "0.0"
            cost = float(str(cost_str).replace("$", "").replace(",", ""))
        except ValueError:
            cost = 0.0

        # Parse purchase date
        p_date_str = row.get("purchase_date") or row.get("Purchase Date") or ""
        p_date = date.today()
        if p_date_str:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    p_date = datetime.strptime(p_date_str.strip(), fmt).date()
                    break
                except ValueError:
                    pass

        status_val = (row.get("status") or row.get("Status") or "IN_STOCK").strip().upper()
        status_enum = AssetStatus.IN_STOCK
        try:
            status_enum = AssetStatus(status_val)
        except ValueError:
            pass

        condition_val = (row.get("condition") or row.get("Condition") or "NEW").strip().upper()
        condition_enum = AssetCondition.NEW
        try:
            condition_enum = AssetCondition(condition_val)
        except ValueError:
            pass

        location = row.get("location") or row.get("Location") or "HQ Central Storage"

        new_asset = Asset(
            asset_tag=asset_tag,
            serial_number=serial_number,
            name=name,
            manufacturer=manufacturer,
            model=model,
            specifications={},
            category_id=cat_id,
            department_id=dept_id,
            vendor_id=vend_id,
            purchase_cost=cost,
            salvage_value=0.0,
            purchase_date=p_date,
            expected_lifespan_months=36,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=status_enum,
            condition=condition_enum,
            location=location,
            notes=row.get("notes") or row.get("Notes")
        )
        db.add(new_asset)
        created_count += 1

    if created_count > 0:
        db.commit()

    return created_count, errors
