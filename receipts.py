# receipts.py
from utils import create_receipt_pdf
from datetime import datetime

def build_and_save_receipt(db_session, fee_obj):
    data = {
        "receipt_id": fee_obj.receipt_id,
        "date": fee_obj.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "student_name": fee_obj.name,
        "student_id": getattr(fee_obj.student, "student_id", ""),
        "amount": fee_obj.amount,
        "purpose": fee_obj.purpose,
        "payment_mode": fee_obj.payment_mode,
        "transaction_id": fee_obj.transaction_id,
        "notes": fee_obj.notes or ""
    }
    path = create_receipt_pdf(data)
    fee_obj.invoice_path = path
    db_session.commit()
    return path
