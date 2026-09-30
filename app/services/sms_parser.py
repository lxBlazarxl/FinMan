import re
from typing import Optional

from app.models.enums import TransactionType
from app.schemas.sms import ConfidenceLevel, SMSParseResult


def _to_float(value: str) -> float:
    return float(value.strip().replace(",", ""))


def _infer_category(merchant: str) -> str:
    if not merchant:
        return "Miscellaneous"
    m = merchant.lower()
    if any(x in m for x in ["swiggy", "zomato", "tea", "chai", "cafe", "restaurant", "food"]):
        return "Food & Dining"
    if any(x in m for x in ["dmart", "kirana", "bigbasket", "blinkit", "zepto", "groceries", "supermarket"]):
        return "Groceries"
    if any(x in m for x in ["uber", "ola", "auto", "metro", "petrol", "fuel", "rickshaw", "irctc"]):
        return "Transport"
    if any(x in m for x in ["hospital", "pharmacy", "apollo", "1mg", "medical", "clinic"]):
        return "Medical"
    if any(x in m for x in ["electricity", "gas", "recharge", "airtel", "jio", "bescom", "tata power", "bill"]):
        return "Utilities"
    if any(x in m for x in ["rent", "society", "maintenance", "landlord"]):
        return "Housing & Rent"
    return "Miscellaneous"


def parse_bank_sms(sms_text: str) -> SMSParseResult:
    try:
        if not sms_text or not isinstance(sms_text, str):
            return SMSParseResult(confidence=ConfidenceLevel.LOW)
        text = sms_text.strip()

        m_upi = re.search(
            r"(?:Paid|Sent)\s+(?:Rs\.?|INR)?\s*([0-9,.]+)\s+to\s+(.+?)(?:\s+via|\s+using|\s+UPI|$)",
            text,
            re.IGNORECASE,
        )
        if m_upi:
            amt = _to_float(m_upi.group(1))
            merchant = m_upi.group(2).strip()
            return SMSParseResult(
                amount=amt,
                type=TransactionType.EXPENSE,
                merchant=merchant,
                suggested_category=_infer_category(merchant),
                bank_name="UPI",
                confidence=ConfidenceLevel.HIGH,
            )

        m_hdfc = re.search(
            r"(?:Rs\.?|INR)?\s*([0-9,.]+)\s+spent\s+on.+?\bat\s+(.+?)(?:\s+on|\s+Avl|$)",
            text,
            re.IGNORECASE,
        )
        if m_hdfc:
            amt = _to_float(m_hdfc.group(1))
            merchant = m_hdfc.group(2).strip()
            return SMSParseResult(
                amount=amt,
                type=TransactionType.EXPENSE,
                merchant=merchant,
                suggested_category=_infer_category(merchant),
                bank_name="HDFC",
                confidence=ConfidenceLevel.HIGH,
            )

        m_sbi = re.search(
            r"debited\s+by\s+(?:Rs\.?|INR)?\s*([0-9,.]+).+?transfer\s+to\s+(.+?)(?:\s+UPI|\s+Ref|\s+Avl|$)",
            text,
            re.IGNORECASE,
        )
        if m_sbi:
            amt = _to_float(m_sbi.group(1))
            merchant = m_sbi.group(2).strip()
            m_bal = re.search(
                r"Avl\s*Bal(?:ance)?\s*(?:Rs\.?|INR)?\s*([0-9,.]+)",
                text,
                re.IGNORECASE,
            )
            bal = _to_float(m_bal.group(1)) if m_bal else None
            return SMSParseResult(
                amount=amt,
                type=TransactionType.EXPENSE,
                merchant=merchant,
                detected_balance=bal,
                suggested_category=_infer_category(merchant),
                bank_name="SBI",
                confidence=ConfidenceLevel.HIGH,
            )

        m_inc = re.search(
            r"credited\s+with\s+(?:Rs\.?|INR)?\s*([0-9,.]+).+?(?:by|from)\s+(.+?)(?:\.|$)",
            text,
            re.IGNORECASE,
        )
        if m_inc:
            amt = _to_float(m_inc.group(1))
            merchant = m_inc.group(2).strip()
            return SMSParseResult(
                amount=amt,
                type=TransactionType.INCOME,
                merchant=merchant,
                suggested_category=_infer_category(merchant),
                bank_name=None,
                confidence=ConfidenceLevel.HIGH,
            )

        return SMSParseResult(confidence=ConfidenceLevel.LOW)
    except Exception:
        return SMSParseResult(confidence=ConfidenceLevel.LOW)
