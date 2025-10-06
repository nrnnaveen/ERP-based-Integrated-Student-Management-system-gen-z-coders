# webhook_forwarder.py
from flask import Flask, request, jsonify
from models import SessionLocal, Student, Fee
from utils import gen_generic_id
import os

app = Flask(__name__)

SHARED_SECRET = os.environ.get("WEBHOOK_SECRET", "webhook_secret_change")

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"error":"no json"}), 400
    if payload.get("secret") != SHARED_SECRET:
        return jsonify({"error":"unauthorized"}), 401
    student_id = payload.get("student_id")
    amount = float(payload.get("amount", 0))
    txn = payload.get("transaction_id") or gen_generic_id("TXN")
    s = SessionLocal()
    # find student by student_id field (human id)
    st = s.query(Student).filter(Student.student_id==student_id).first()
    if not st:
        s.close()
        return jsonify({"error":"student not found"}), 404
    receipt_id = gen_generic_id("REC")
    # compute balance naive
    last = s.query(Fee).filter(Fee.student_id_fk==st.id).order_by(Fee.timestamp.desc()).first()
    last_balance = last.balance_after if last else 0.0
    balance_after = last_balance - amount
    fee = Fee(receipt_id=receipt_id, student_id_fk=st.id, name=st.name, amount=amount, payment_mode="Gateway", transaction_id=txn, balance_after=balance_after, purpose=payload.get("purpose","Tuition"), recorded_by="gateway")
    s.add(fee)
    s.commit()
    s.close()
    return jsonify({"status":"ok","receipt_id":receipt_id})

if __name__ == "__main__":
    app.run(port=9000)
