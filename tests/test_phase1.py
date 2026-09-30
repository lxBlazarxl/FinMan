import pytest
from fastapi.testclient import TestClient

from app.core.database import engine
from app.models.base import Base
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def auth_register_household_and_login(
    family_name: str,
    admin_name: str,
    phone: str,
    password: str,
):
    resp = client.post(
        "/api/v1/auth/register-household",
        json={
            "household_name": family_name,
            "admin_name": admin_name,
            "phone_number": phone,
            "password": password,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"
    return data


def login(phone: str, password: str):
    return _login(phone, password)


def _login(phone: str, password: str):
    resp = client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "password": password},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    return data


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_register_household_and_admin_login():
    data = auth_register_household_and_login(
        family_name="Sharma Family",
        admin_name="Rajesh",
        phone="9876543210",
        password="password123",
    )
    assert data["user"]["role"] == "ADMIN"


def test_admin_creates_member():
    admin = auth_register_household_and_login(
        family_name="Sharma Family",
        admin_name="Rajesh",
        phone="9876543210",
        password="password123",
    )
    headers = {"Authorization": f"Bearer {admin['access_token']}"}

    resp = client.post(
        "/api/v1/household/members",
        headers=headers,
        json={
            "name": "Aarav",
            "phone_number": "9876543212",
            "password": "password123",
            "initial_account_name": "Pocket Cash",
        },
    )
    assert resp.status_code == 200, resp.text
    member = resp.json()
    assert member["role"] == "MEMBER"


def test_member_forbidden_from_admin_routes():
    admin = auth_register_household_and_login(
        family_name="Sharma Family",
        admin_name="Rajesh",
        phone="9876543210",
        password="password123",
    )

    headers = {"Authorization": f"Bearer {admin['access_token']}"}
    resp = client.post(
        "/api/v1/household/members",
        headers=headers,
        json={
            "name": "Aarav",
            "phone_number": "9876543212",
            "password": "password123",
            "initial_account_name": "Pocket Cash",
        },
    )
    assert resp.status_code == 200, resp.text

    member_login = login(phone="9876543212", password="password123")
    member_headers = {"Authorization": f"Bearer {member_login['access_token']}"}

    resp = client.get(
        "/api/v1/balances/household",
        headers=member_headers,
    )
    assert resp.status_code == 403

    resp = client.get(
        "/api/v1/household/members",
        headers=member_headers,
    )
    assert resp.status_code == 403


def test_account_creation_and_balance_isolation():
    admin = auth_register_household_and_login(
        family_name="Sharma Family",
        admin_name="Rajesh",
        phone="9876543210",
        password="password123",
    )
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    resp = client.post(
        "/api/v1/household/members",
        headers=admin_headers,
        json={
            "name": "Aarav",
            "phone_number": "9876543212",
            "password": "password123",
            "initial_account_name": "Pocket Cash",
        },
    )
    assert resp.status_code == 200, resp.text

    member_login = login(phone="9876543212", password="password123")
    member_headers = {"Authorization": f"Bearer {member_login['access_token']}"}

    resp = client.post(
        "/api/v1/accounts",
        headers=admin_headers,
        json={
            "name": "SBI Salary",
            "type": "BANK",
            "initial_balance": 10000.0,
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.post(
        "/api/v1/accounts",
        headers=member_headers,
        json={
            "name": "Pocket Cash",
            "type": "CASH",
            "initial_balance": 500.0,
        },
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/api/v1/balances/me", headers=member_headers)
    assert resp.status_code == 200
    assert resp.json()["total_balance"] == 500.0

    resp = client.get("/api/v1/balances/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total_balance"] == 10000.0

    resp = client.get("/api/v1/balances/household", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total_household_balance"] == 10500.0
