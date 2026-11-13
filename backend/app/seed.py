import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole,
    Department,
    Employee,
    AssetCategory,
    Vendor,
    Asset, AssetStatus, AssetCondition, DepreciationMethod,
    AssetAssignment, AssignmentStatus,
    SoftwareProduct, SoftwareLicense, LicenseAssignment, LicenseType,
    MaintenanceRecord, MaintenanceType, MaintenanceStatus,
    Warranty, WarrantyType,
    Notification, NotificationSeverity,
)
from app.utils.security import hash_password
from app.services.qr_service import generate_asset_qr


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).count() > 0:
        print("Database already contains data. Skipping initial seed.")
        db.close()
        return

    print("Seeding enterprise demonstration data...")

    # 1. Users
    admin_user = User(
        email="admin@assettrack.io",
        hashed_password=hash_password("Admin123!Secure"),
        full_name="Sarah Connor (Chief Information Officer)",
        role=UserRole.ADMIN,
        is_active=True,
    )
    manager_user = User(
        email="manager@assettrack.io",
        hashed_password=hash_password("Manager123!Secure"),
        full_name="Marcus Vance (IT Asset Manager)",
        role=UserRole.ASSET_MANAGER,
        is_active=True,
    )
    tech_user = User(
        email="technician@assettrack.io",
        hashed_password=hash_password("Tech123!Secure"),
        full_name="Elena Rostova (Lead Systems Technician)",
        role=UserRole.TECHNICIAN,
        is_active=True,
    )
    auditor_user = User(
        email="auditor@assettrack.io",
        hashed_password=hash_password("Auditor123!Secure"),
        full_name="David Chen (Compliance Auditor)",
        role=UserRole.READ_ONLY,
        is_active=True,
    )
    db.add_all([admin_user, manager_user, tech_user, auditor_user])
    db.commit()

    # 2. Departments
    depts = [
        Department(name="Information Technology", code="IT", description="Enterprise infrastructure, systems, and security operations"),
        Department(name="Engineering & Product", code="ENG", description="Software engineering, QA, DevOps, and systems architecture"),
        Department(name="Operations", code="OPS", description="Business logistics, facilities, and supply chain"),
        Department(name="Finance & Accounting", code="FIN", description="Corporate accounting, payroll, and financial planning"),
        Department(name="Design & Creative", code="DES", description="Brand design, product UX, and multimedia creative services"),
        Department(name="People Operations", code="HR", description="Talent acquisition, employee experience, and HR business partners"),
    ]
    db.add_all(depts)
    db.commit()

    # 3. Vendors
    vendors = [
        Vendor(name="Apple Inc.", contact_person="Enterprise Sales Group", email="enterprise@apple.com", phone="+1-800-692-7753", address="1 Apple Park Way, Cupertino, CA", website="https://apple.com"),
        Vendor(name="Dell Technologies", contact_person="Robert Kincaid", email="robert.k@dell.com", phone="+1-800-456-3355", address="One Dell Way, Round Rock, TX", website="https://dell.com"),
        Vendor(name="Lenovo Enterprise", contact_person="Lisa Zhao", email="lzhao@lenovo.com", phone="+1-855-253-6686", address="8001 Development Dr, Morrisville, NC", website="https://lenovo.com"),
        Vendor(name="Cisco Systems", contact_person="Global Partner Support", email="partners@cisco.com", phone="+1-800-553-6387", address="170 W Tasman Dr, San Jose, CA", website="https://cisco.com"),
        Vendor(name="CDW Corporation", contact_person="Account Representative", email="orders@cdw.com", phone="+1-800-800-4239", address="200 N Milwaukee Ave, Vernon Hills, IL", website="https://cdw.com"),
    ]
    db.add_all(vendors)
    db.commit()

    # 4. Categories
    categories = [
        AssetCategory(name="Laptops", code="LAP", description="Portable workstations and developer notebooks", default_lifespan_months=36, default_depreciation_method="STRAIGHT_LINE"),
        AssetCategory(name="Desktop Workstations", code="DSK", description="High-performance compute and creative desktops", default_lifespan_months=48, default_depreciation_method="STRAIGHT_LINE"),
        AssetCategory(name="Rack Servers", code="SRV", description="Enterprise compute blades and 1U/2U rack units", default_lifespan_months=60, default_depreciation_method="DOUBLE_DECLINING"),
        AssetCategory(name="Networking Equipment", code="NET", description="Core switches, routers, security gateways, and firewalls", default_lifespan_months=60, default_depreciation_method="STRAIGHT_LINE"),
        AssetCategory(name="Monitors & Displays", code="MON", description="UltraWide and 4K calibrated color displays", default_lifespan_months=48, default_depreciation_method="STRAIGHT_LINE"),
        AssetCategory(name="Mobile Devices", code="MOB", description="Corporate smartphones and field tablets", default_lifespan_months=24, default_depreciation_method="DOUBLE_DECLINING"),
    ]
    db.add_all(categories)
    db.commit()

    # 5. Employees
    it_dept = depts[0]
    eng_dept = depts[1]
    fin_dept = depts[3]
    des_dept = depts[4]

    employees = [
        Employee(employee_id_number="EMP-0101", first_name="Alex", last_name="Mercer", email="alex.mercer@company.com", job_title="Staff Site Reliability Engineer", department_id=eng_dept.id),
        Employee(employee_id_number="EMP-0102", first_name="Priya", last_name="Nair", email="priya.nair@company.com", job_title="Principal Frontend Architect", department_id=eng_dept.id),
        Employee(employee_id_number="EMP-0103", first_name="Carlos", last_name="Mendez", email="carlos.m@company.com", job_title="Senior Data Scientist", department_id=eng_dept.id),
        Employee(employee_id_number="EMP-0201", first_name="Hannah", last_name="Kim", email="hannah.kim@company.com", job_title="IT Operations Specialist", department_id=it_dept.id),
        Employee(employee_id_number="EMP-0301", first_name="Jordan", last_name="Bell", email="jordan.bell@company.com", job_title="VP of Product Experience", department_id=des_dept.id),
        Employee(employee_id_number="EMP-0401", first_name="Claire", last_name="Sterling", email="claire.s@company.com", job_title="Director of Financial Planning", department_id=fin_dept.id),
    ]
    db.add_all(employees)
    db.commit()

    # 6. Assets
    lap_cat = categories[0]
    srv_cat = categories[2]
    net_cat = categories[3]
    mon_cat = categories[4]

    apple_v = vendors[0]
    dell_v = vendors[1]
    cisco_v = vendors[3]

    assets = [
        Asset(
            asset_tag="AST-2024-0012",
            serial_number="C02GL01AMD6R",
            name="MacBook Pro 16\" (M3 Max)",
            manufacturer="Apple",
            model="MacBookPro18,2",
            specifications={"cpu": "Apple M3 Max 16-Core", "ram": "64GB Unified", "storage": "2TB NVMe SSD", "display": "16.2 Liquid Retina XDR"},
            category_id=lap_cat.id,
            department_id=eng_dept.id,
            vendor_id=apple_v.id,
            purchase_cost=3899.00,
            salvage_value=500.00,
            purchase_date=date(2024, 2, 15),
            expected_lifespan_months=36,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.ASSIGNED,
            condition=AssetCondition.EXCELLENT,
            location="HQ - 4th Floor Tech Hub",
            notes="Standard high-spec engineering laptop",
        ),
        Asset(
            asset_tag="AST-2024-0015",
            serial_number="C02HM02QMD6S",
            name="MacBook Pro 14\" (M3 Pro)",
            manufacturer="Apple",
            model="MacBookPro18,3",
            specifications={"cpu": "Apple M3 Pro 12-Core", "ram": "36GB Unified", "storage": "1TB NVMe SSD"},
            category_id=lap_cat.id,
            department_id=des_dept.id,
            vendor_id=apple_v.id,
            purchase_cost=2499.00,
            salvage_value=300.00,
            purchase_date=date(2024, 3, 10),
            expected_lifespan_months=36,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.ASSIGNED,
            condition=AssetCondition.EXCELLENT,
            location="HQ - Creative Studio",
            notes="Design workstation laptop",
        ),
        Asset(
            asset_tag="AST-2023-0089",
            serial_number="8H29KQ3",
            name="Dell Precision 5680 Workstation",
            manufacturer="Dell",
            model="Precision 5680",
            specifications={"cpu": "Intel Core i9-13900H", "gpu": "NVIDIA RTX 3500 Ada 12GB", "ram": "64GB DDR5", "storage": "2TB SSD"},
            category_id=lap_cat.id,
            department_id=eng_dept.id,
            vendor_id=dell_v.id,
            purchase_cost=3450.00,
            salvage_value=400.00,
            purchase_date=date(2023, 8, 20),
            expected_lifespan_months=36,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.ASSIGNED,
            condition=AssetCondition.GOOD,
            location="HQ - Engineering Lab 2",
            notes="Data science mobile compute workstation",
        ),
        Asset(
            asset_tag="AST-2025-0044",
            serial_number="5F82LP1",
            name="Dell PowerEdge R760 Rack Server",
            manufacturer="Dell",
            model="PowerEdge R760 2U",
            specifications={"cpu": "Dual Intel Xeon Platinum 8468V 48-Core", "ram": "512GB ECC DDR5", "storage": "8x 3.84TB NVMe U.2 RAID-10"},
            category_id=srv_cat.id,
            department_id=it_dept.id,
            vendor_id=dell_v.id,
            purchase_cost=18500.00,
            salvage_value=2500.00,
            purchase_date=date(2025, 1, 10),
            expected_lifespan_months=60,
            depreciation_method=DepreciationMethod.DOUBLE_DECLINING,
            status=AssetStatus.IN_STOCK,
            condition=AssetCondition.NEW,
            location="Primary Data Center - Rack 14B",
            notes="Staged for Q1 private cloud virtualization cluster",
        ),
        Asset(
            asset_tag="AST-2022-0051",
            serial_number="FOC2214U09X",
            name="Cisco Catalyst 9300-48P Switch",
            manufacturer="Cisco",
            model="C9300-48P-A",
            specifications={"ports": "48-Port PoE+ Gigabit", "uplinks": "4x 10G SFP+", "stacking": "StackWise-480"},
            category_id=net_cat.id,
            department_id=it_dept.id,
            vendor_id=cisco_v.id,
            purchase_cost=6200.00,
            salvage_value=800.00,
            purchase_date=date(2022, 5, 12),
            expected_lifespan_months=60,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.IN_STOCK,
            condition=AssetCondition.EXCELLENT,
            location="IDF Closet - Floor 3",
            notes="Access layer switch serving east wing",
        ),
        Asset(
            asset_tag="AST-2021-0004",
            serial_number="CN-0J892-74261",
            name="Dell UltraSharp U3223QE 32\" 4K Hub Monitor",
            manufacturer="Dell",
            model="U3223QE",
            specifications={"resolution": "3840 x 2160 at 60Hz", "panel": "IPS Black", "usb_c": "90W Power Delivery Hub"},
            category_id=mon_cat.id,
            department_id=eng_dept.id,
            vendor_id=dell_v.id,
            purchase_cost=849.00,
            salvage_value=100.00,
            purchase_date=date(2021, 10, 5),
            expected_lifespan_months=48,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.UNDER_MAINTENANCE,
            condition=AssetCondition.FAIR,
            location="IT Depot Repair Room",
            notes="Display flickers intermittently when connected over Thunderbolt",
        ),
        Asset(
            asset_tag="AST-2020-0019",
            serial_number="C02DK999MD6K",
            name="MacBook Pro 13\" (Intel Core i7)",
            manufacturer="Apple",
            model="MacBookPro16,2",
            specifications={"cpu": "Quad-Core Intel i7 2.3GHz", "ram": "32GB LPDDR4X", "storage": "512GB SSD"},
            category_id=lap_cat.id,
            department_id=it_dept.id,
            vendor_id=apple_v.id,
            purchase_cost=2199.00,
            salvage_value=150.00,
            purchase_date=date(2020, 6, 18),
            expected_lifespan_months=36,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            status=AssetStatus.PENDING_DISPOSAL,
            condition=AssetCondition.POOR,
            location="IT Storage - Quarantine Shelf C",
            notes="Exceeded 4 years operational lifespan; scheduled for certified e-waste recycling.",
        ),
    ]
    db.add_all(assets)
    db.commit()

    # Generate QR codes
    for a in assets:
        try:
            a.qr_code_path = generate_asset_qr(a)
        except Exception:
            pass
    db.commit()

    # 7. Asset Assignments
    assignments = [
        AssetAssignment(
            asset_id=assets[0].id,
            employee_id=employees[0].id,
            assigned_date=date(2024, 2, 16),
            expected_return_date=date(2027, 2, 16),
            condition_on_assignment="NEW",
            status=AssignmentStatus.ACTIVE,
            approved_by_id=manager_user.id,
            assignment_notes="Primary developer machine for SRE lead",
        ),
        AssetAssignment(
            asset_id=assets[1].id,
            employee_id=employees[4].id,
            assigned_date=date(2024, 3, 11),
            expected_return_date=date(2027, 3, 11),
            condition_on_assignment="NEW",
            status=AssignmentStatus.ACTIVE,
            approved_by_id=manager_user.id,
            assignment_notes="Allocated for UX/UI design team lead",
        ),
        AssetAssignment(
            asset_id=assets[2].id,
            employee_id=employees[2].id,
            assigned_date=date(2023, 8, 25),
            expected_return_date=date(2026, 8, 25),
            condition_on_assignment="EXCELLENT",
            status=AssignmentStatus.ACTIVE,
            approved_by_id=manager_user.id,
            assignment_notes="Configured with local CUDA container environment",
        ),
        AssetAssignment(
            asset_id=assets[4].id,
            employee_id=employees[1].id,
            assigned_date=date(2026, 11, 10),
            expected_return_date=date(2026, 11, 30),
            condition_on_assignment="EXCELLENT",
            status=AssignmentStatus.PENDING_APPROVAL,
            assignment_notes="Temporary assignment request for staging lab load test",
        ),
    ]
    db.add_all(assignments)
    db.commit()

    # 8. Software Products and Licenses
    sw_ms = SoftwareProduct(name="Microsoft 365 E5", publisher="Microsoft Corp.", version="Enterprise 2026", category="Productivity & Security")
    sw_adobe = SoftwareProduct(name="Adobe Creative Cloud Enterprise", publisher="Adobe Systems", version="v2026", category="Design & Creative")
    sw_jb = SoftwareProduct(name="JetBrains All Products Pack", publisher="JetBrains s.r.o.", version="v2026.3", category="Developer Tools")
    sw_cs = SoftwareProduct(name="CrowdStrike Falcon Enterprise", publisher="CrowdStrike", version="v7.12", category="Endpoint Security")

    db.add_all([sw_ms, sw_adobe, sw_jb, sw_cs])
    db.commit()

    lic_ms = SoftwareLicense(
        software_id=sw_ms.id,
        license_key="MS365-E5-ENT-8849-XXXX-YYYY",
        license_type=LicenseType.SUBSCRIPTION,
        total_seats=150,
        cost=85000.00,
        purchase_date=date(2026, 1, 1),
        expiration_date=date(2027, 1, 1),
        vendor_id=vendors[4].id,
        notes="Enterprise-wide productivity, identity, and compliance suite",
    )
    lic_adobe = SoftwareLicense(
        software_id=sw_adobe.id,
        license_key="ADOBE-CC-VIP-9912-AABB-CCDD",
        license_type=LicenseType.SUBSCRIPTION,
        total_seats=25,
        cost=24000.00,
        purchase_date=date(2026, 2, 1),
        expiration_date=date(2027, 2, 1),
        vendor_id=vendors[4].id,
        notes="Reserved for Product and Marketing design teams",
    )
    lic_jb = SoftwareLicense(
        software_id=sw_jb.id,
        license_key="JB-ALL-COMM-2026-9812-7711",
        license_type=LicenseType.SUBSCRIPTION,
        total_seats=50,
        cost=18500.00,
        purchase_date=date(2026, 4, 15),
        expiration_date=date(2027, 4, 15),
        vendor_id=vendors[4].id,
        notes="All IDE developer bundle (IntelliJ, WebStorm, PyCharm, CLion)",
    )

    db.add_all([lic_ms, lic_adobe, lic_jb])
    db.commit()

    # Assign seats
    la1 = LicenseAssignment(license_id=lic_ms.id, employee_id=employees[0].id, assigned_date=date(2026, 1, 5))
    la2 = LicenseAssignment(license_id=lic_ms.id, employee_id=employees[1].id, assigned_date=date(2026, 1, 5))
    la3 = LicenseAssignment(license_id=lic_adobe.id, employee_id=employees[4].id, assigned_date=date(2026, 2, 5))
    la4 = LicenseAssignment(license_id=lic_jb.id, employee_id=employees[0].id, assigned_date=date(2026, 4, 16))
    la5 = LicenseAssignment(license_id=lic_jb.id, employee_id=employees[1].id, assigned_date=date(2026, 4, 16))
    db.add_all([la1, la2, la3, la4, la5])
    db.commit()

    # 9. Maintenance Records
    maint = [
        MaintenanceRecord(
            asset_id=assets[5].id,
            vendor_id=dell_v.id,
            technician_id=tech_user.id,
            maintenance_type=MaintenanceType.REPAIR,
            title="Thunderbolt Controller Diagnostic & Firmware Reflash",
            description="Investigating video signal drops on 4K display. Motherboard diagnostics initiated.",
            cost=240.00,
            scheduled_date=date(2026, 11, 12),
            status=MaintenanceStatus.IN_PROGRESS,
            notes="Dell RMA ticket #988219 opened for replacement mainboard.",
        ),
        MaintenanceRecord(
            asset_id=assets[3].id,
            vendor_id=dell_v.id,
            technician_id=tech_user.id,
            maintenance_type=MaintenanceType.PREVENTATIVE,
            title="Bi-Annual Datacenter Server Thermal Cleaning & BIOS Update",
            description="Clean fan arrays, inspect redundant power supplies, apply urgent microcode patches.",
            cost=350.00,
            scheduled_date=date(2026, 11, 28),
            status=MaintenanceStatus.SCHEDULED,
            notes="Maintenance window scheduled for Saturday 02:00-05:00 UTC",
        ),
    ]
    db.add_all(maint)
    db.commit()

    # 10. Warranties
    warranties = [
        Warranty(
            asset_id=assets[0].id,
            vendor_id=apple_v.id,
            provider_name="AppleCare+ for Enterprise",
            policy_number="AC-ENT-90182-M3",
            warranty_type=WarrantyType.MANUFACTURER,
            start_date=date(2024, 2, 15),
            end_date=date(2027, 2, 15),
            coverage_details="24/7 priority support, next-business-day on-site hardware repair, accidental damage coverage.",
        ),
        Warranty(
            asset_id=assets[3].id,
            vendor_id=dell_v.id,
            provider_name="Dell ProSupport Plus Mission Critical",
            policy_number="DPS-MC-771822",
            warranty_type=WarrantyType.EXTENDED,
            start_date=date(2025, 1, 10),
            end_date=date(2030, 1, 10),
            coverage_details="4-hour 24x7 on-site parts and labor response, dedicated technical account manager.",
        ),
        Warranty(
            asset_id=assets[5].id,
            vendor_id=dell_v.id,
            provider_name="Dell 3-Year Advanced Exchange Service",
            policy_number="DELL-AES-33211",
            warranty_type=WarrantyType.MANUFACTURER,
            start_date=date(2021, 10, 5),
            end_date=date(2024, 10, 5),
            coverage_details="Standard 3-year advanced exchange warranty. (Expired).",
        ),
    ]
    db.add_all(warranties)
    db.commit()

    # 11. System Notifications
    notifs = [
        Notification(
            title="Assignment Request Pending Approval",
            message="Employee Priya Nair requested temporary assignment for Cisco Catalyst 9300-48P Switch (AST-2022-0051).",
            severity=NotificationSeverity.WARNING,
            target_role="ASSET_MANAGER",
            link="/assignments",
        ),
        Notification(
            title="Equipment Under Active Maintenance",
            message="Dell UltraSharp 32\" 4K Monitor (AST-2021-0004) has an in-progress repair ticket with Dell RMA.",
            severity=NotificationSeverity.INFO,
            target_role="TECHNICIAN",
            link="/maintenance",
        ),
        Notification(
            title="End of Life Equipment Notice",
            message="MacBook Pro 13\" (AST-2020-0019) has completed its useful life cycle and is awaiting certified disposal.",
            severity=NotificationSeverity.WARNING,
            target_role="ASSET_MANAGER",
            link="/assets",
        ),
    ]
    db.add_all(notifs)
    db.commit()

    print("Enterprise database successfully seeded with demonstration data!")
    db.close()


if __name__ == "__main__":
    seed_database()
