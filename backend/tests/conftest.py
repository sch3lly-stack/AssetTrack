import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.category import AssetCategory
from app.models.department import Department
from app.models.vendor import Vendor
from app.models.employee import Employee
from app.models.asset import Asset, AssetStatus, AssetCondition, DepreciationMethod
from app.utils.security import hash_password, create_access_token

# Use isolated SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Create test fixtures
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Admin Tester",
        role=UserRole.ADMIN,
        is_active=True,
    )
    manager = User(
        email="manager@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Manager Tester",
        role=UserRole.ASSET_MANAGER,
        is_active=True,
    )
    tech = User(
        email="tech@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Tech Tester",
        role=UserRole.TECHNICIAN,
        is_active=True,
    )
    readonly = User(
        email="readonly@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="ReadOnly Tester",
        role=UserRole.READ_ONLY,
        is_active=True,
    )
    dept = Department(name="Engineering", code="ENG", description="Eng Dept")
    cat = AssetCategory(name="Laptops", code="LAP", description="Laptop computers")
    vendor = Vendor(name="Dell", email="dell@test.com")
    
    session.add_all([admin, manager, tech, readonly, dept, cat, vendor])
    session.commit()

    emp = Employee(
        employee_id_number="EMP-001",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@test.com",
        job_title="Software Engineer",
        department_id=dept.id,
    )
    session.add(emp)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db_session):
    user = db_session.query(User).filter(User.email == "admin@test.com").first()
    return create_access_token(subject=user.id, role=user.role.value)


@pytest.fixture
def manager_token(db_session):
    user = db_session.query(User).filter(User.email == "manager@test.com").first()
    return create_access_token(subject=user.id, role=user.role.value)


@pytest.fixture
def tech_token(db_session):
    user = db_session.query(User).filter(User.email == "tech@test.com").first()
    return create_access_token(subject=user.id, role=user.role.value)


@pytest.fixture
def readonly_token(db_session):
    user = db_session.query(User).filter(User.email == "readonly@test.com").first()
    return create_access_token(subject=user.id, role=user.role.value)
