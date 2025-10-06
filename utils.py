# utils.py
import random, time, hashlib, os
from werkzeug.security import generate_password_hash, check_password_hash
from config import RECEIPTS_FOLDER, BACKUP_FOLDER
import pandas as pd
from models import SessionLocal, Student, Fee, Admission, HostelAllocation, Exam
import datetime
import fpdf2

def gen_student_id(prefix="COLG"):
    year = datetime.datetime.utcnow().year % 100
    return f"{prefix}{year:02d}S{random.randint(10000,99999)}"

def gen_generic_id(prefix):
    ts = int(time.time()*1000)
    return f"{prefix}-{ts}-{random.randint(1000,9999)}"

def hash_password(pw):
    return generate_password_hash(pw)

def verify_password(hashed, pw):
    return check_password_hash(hashed, pw)

def export_csv_all(db_path=None):
    # produce CSV files for each table and return filepaths
    s = SessionLocal()
    paths = {}
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # students
    df = pd.read_sql(s.query(Student).statement, s.bind)
    p = os.path.join(BACKUP_FOLDER, f"students_{ts}.csv")
    df.to_csv(p, index=False)
    paths['students'] = p
    df = pd.read_sql(s.query(Admission).statement, s.bind)
    p = os.path.join(BACKUP_FOLDER, f"admissions_{ts}.csv")
    df.to_csv(p, index=False)
    paths['admissions'] = p
    df = pd.read_sql(s.query(Fee).statement, s.bind)
    p = os.path.join(BACKUP_FOLDER, f"fees_{ts}.csv")
    df.to_csv(p, index=False)
    paths['fees'] = p
    df = pd.read_sql(s.query(HostelAllocation).statement, s.bind)
    p = os.path.join(BACKUP_FOLDER, f"hostel_{ts}.csv")
    df.to_csv(p, index=False)
    paths['hostel'] = p
    df = pd.read_sql(s.query(Exam).statement, s.bind)
    p = os.path.join(BACKUP_FOLDER, f"exams_{ts}.csv")
    df.to_csv(p, index=False)
    paths['exams'] = p
    s.close()
    return paths

# simple PDF receipt generator using fpdf2
from fpdf import FPDF

def create_receipt_pdf(receipt_data, out_folder=RECEIPTS_FOLDER):
    """
    receipt_data = {
      'receipt_id','date','student_name','student_id','amount','purpose','payment_mode','transaction_id','notes'
    }
    returns filepath
    """
    os.makedirs(out_folder, exist_ok=True)
    filename = f"{receipt_data['receipt_id']}.pdf"
    path = os.path.join(out_folder, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "INSTITUTION NAME", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Receipt ID: {receipt_data['receipt_id']}", ln=True)
    pdf.cell(0, 8, f"Date: {receipt_data.get('date')}", ln=True)
    pdf.ln(4)
    pdf.cell(0, 8, f"Student: {receipt_data.get('student_name')} ({receipt_data.get('student_id')})", ln=True)
    pdf.cell(0, 8, f"Amount Paid: ₹{receipt_data.get('amount')}", ln=True)
    pdf.cell(0, 8, f"Purpose: {receipt_data.get('purpose')}", ln=True)
    pdf.cell(0, 8, f"Payment Mode: {receipt_data.get('payment_mode')}", ln=True)
    pdf.cell(0, 8, f"Transaction ID: {receipt_data.get('transaction_id')}", ln=True)
    pdf.ln(6)
    pdf.multi_cell(0, 8, f"Notes: {receipt_data.get('notes','')}")
    pdf.output(path)
    return path
