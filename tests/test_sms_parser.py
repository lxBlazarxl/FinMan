from app.models.enums import TransactionType
from app.schemas.sms import ConfidenceLevel
from app.services.sms_parser import parse_bank_sms


def test_sms_parser_sbi_expense():
    sms = "Your a/c XX1234 is debited by Rs.450.00 on 28Sep26 transfer to Swiggy UPI Ref 429182. Avl Bal Rs.14,200.50"
    res = parse_bank_sms(sms)
    assert res.amount == 450.0
    assert res.type == TransactionType.EXPENSE
    assert res.merchant is not None
    assert "Swiggy" in res.merchant
    assert res.suggested_category == "Food & Dining"


def test_sms_parser_hdfc_expense():
    sms = "Alert: Rs. 1,250.00 spent on HDFC Card ending 4321 at DMART MUMBAI on 29-SEP-26. Avl limit: 45,000.00"
    res = parse_bank_sms(sms)
    assert res.amount == 1250.0
    assert res.type == TransactionType.EXPENSE
    assert res.merchant is not None
    assert "DMART" in res.merchant
    assert res.suggested_category == "Groceries"


def test_sms_parser_upi_expense():
    sms = "Paid Rs. 35.00 to RAMESH TEA STALL via UPI"
    res = parse_bank_sms(sms)
    assert res.amount == 35.0
    assert res.type == TransactionType.EXPENSE
    assert res.merchant is not None
    assert "RAMESH" in res.merchant
    assert res.suggested_category == "Food & Dining"


def test_sms_parser_income_salary():
    sms = "A/c XX1234 credited with Rs. 50,000.00 on 01-Oct-26 by SALARY"
    res = parse_bank_sms(sms)
    assert res.amount == 50000.0
    assert res.type == TransactionType.INCOME
    assert res.merchant is not None
    assert "SALARY" in res.merchant.upper()


def test_sms_parser_garbage_low_confidence():
    sms = "Hey, are you free for lunch tomorrow?"
    res = parse_bank_sms(sms)
    assert res.confidence == ConfidenceLevel.LOW
    assert res.amount is None
