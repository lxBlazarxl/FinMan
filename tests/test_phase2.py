import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import engine
from app.models.base import Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _register_household():
    r = client.post(
        "/api/v1/auth/register-household",
        json={
            "household_name": "Sharma Family",
            "admin_name": "Rajesh Sharma",
            "phone_number": "9876543210",
            "password": "password123",
        },
    )
    assert r.status_code == 200, r.text
    admin_token = r.json()["access_token"]

    m = client.post(
        "/api/v1/household/members",
        json={
            "name": "Pooja Sharma",
            "phone_number": "9876543211",
            "password": "password123",
            "initial_account_name": "Pocket Cash",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert m.status_code == 200, m.text


def _login(phone: str, password: str = "password123") -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _create_account(token: str, name: str, initial_balance: float):
    r = client.post(
        "/api/v1/accounts",
        json={"name": name, "type": "BANK", "initial_balance": initial_balance},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _create_member_as_admin(token: str, name: str, phone: str):
    r = client.post(
        "/api/v1/household/members",
        json={"name": name, "phone_number": phone, "password": "password123", "initial_account_name": "Pocket Cash"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _post_transaction(token: str, account_id: str, amount: float, category: str):
    r = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "type": "EXPENSE",
            "amount": amount,
            "category": category,
            "description": None,
            "raw_sms": None,
            "date": None,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_parse_sms_endpoint():
    r = client.post(
        "/api/v1/transactions/parse-sms",
        json={
            "sms_text": "Your a/c XX1234 is debited by Rs.450.00 on 28Sep26 transfer to Swiggy UPI Ref 429182.  Avl Bal Rs.14,200.50",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["amount"] == 450.0
    assert data["type"] == "EXPENSE"
    assert data["suggested_category"] == "Food & Dining"
    assert data["confidence"] == "HIGH"

    r2 = client.post(
        "/api/v1/transactions/parse-sms",
        json={"sms_text": "Random message without numbers"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["confidence"] == "LOW"
    assert data2["amount"] is None


def test_transaction_creation_and_balance_deduction():
    _register_household()
    member_token = _login("9876543211")

    acc = _create_account(member_token, "SBI Bank", 5000.0)
    _post_transaction(member_token, acc["id"], 1200.0, "Groceries")

    r = client.get(
        "/api/v1/balances/me",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert r.status_code == 200
    assert r.json()["total_balance"] == 3800.0


def test_transaction_deletion_and_balance_restoration():
    _register_household()
    admin_token = _login("9876543210")

    acc = _create_account(admin_token, "SBI Bank", 5000.0)
    tx = _post_transaction(admin_token, acc["id"], 1200.0, "Groceries")

    r = client.delete(
        f"/api/v1/transactions/{tx['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200

    r2 = client.get(
        "/api/v1/balances/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["total_balance"] == 5000.0


def test_transaction_filters_and_member_isolation():
    _register_household()
    admin_token = _login("9876543210")

    _create_member_as_admin(admin_token, "Kid", "9876543299")
    kid_token = _login("9876543299")

    kid_acc = _create_account(kid_token, "Kid Account", 1000.0)
    _post_transaction(kid_token, kid_acc["id"], 150.0, "Stationery")

    admin_acc = _create_account(admin_token, "Admin Account", 1000.0)
    _post_transaction(admin_token, admin_acc["id"], 500.0, "Utilities")

    r_kid = client.get(
        "/api/v1/transactions?category=Stationery",
        headers={"Authorization": f"Bearer {kid_token}"},
    )
    assert r_kid.status_code == 200
    assert len(r_kid.json()) >= 1
    assert any(t.get("category") == "Stationery" for t in r_kid.json())

    r_admin = client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_admin.status_code == 200
    assert len(r_admin.json()) == 2

    r_stationery = client.get(
        "/api/v1/transactions?category=Stationery&limit=50&offset=0",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_stationery.status_code == 200
    assert len(r_stationery.json()) == 1


def test_monthly_analytics_and_rbac():
    _register_household()
    admin_token = _login("9876543210")
    member_token = _login("9876543211")

    admin_acc = _create_account(admin_token, "Admin Bank", 5000.0)
    _post_transaction(admin_token, admin_acc["id"], 2000.0, "Groceries")
    _post_transaction(admin_token, admin_acc["id"], 500.0, "Transport")

    r = client.get(
        "/api/v1/analytics/category-breakdown?scope=household",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_expenses"] == 2500.0
    cats = {c["category"]: c for c in data["categories"]}
    assert cats["Groceries"]["percentage"] == 80.0
    assert cats["Transport"]["percentage"] == 20.0

    r2 = client.get(
        "/api/v1/analytics/monthly-summary?scope=household",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["total_expense"] == 2500.0

    r3 = client.get(
        "/api/v1/analytics/monthly-summary?scope=household",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert r3.status_code == 403
