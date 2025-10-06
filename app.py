# app.py
import streamlit as st
from models import SessionLocal, Student, Admission, Fee, HostelAllocation, Exam, User
from utils import gen_student_id, gen_generic_id, hash_password, verify_password, export_csv_all
from receipts import build_and_save_receipt
from config import RECEIPTS_FOLDER
from sqlalchemy.exc import IntegrityError
import pandas as pd
import os
import datetime
import pathlib

st.set_page_config(page_title="College ERP", layout="wide")

# simple session-state auth
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def login_ui():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        s = SessionLocal()
        user = s.query(User).filter_by(username=username).first()
        if user and verify_password(user.hashed_password, password):
            st.session_state.logged_in = True
            st.session_state.user = {"username": user.username, "role": user.role, "display_name": user.display_name}
            st.sidebar.success(f"Welcome {user.display_name} ({user.role})")
        else:
            st.sidebar.error("Invalid creds")
        s.close()

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

def require_login():
    if not st.session_state.logged_in:
        st.sidebar.info("Please login")
        login_ui()
        st.stop()

def header():
    st.title("College ERP — Streamlit PoC")
    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as: **{st.session_state.user['display_name']}** ({st.session_state.user['username']})")
        if st.sidebar.button("Logout"):
            logout()
            st.experimental_rerun()

# start
header()
if not st.session_state.logged_in:
    login_ui()
    st.stop()

# menu
menu = ["Admissions", "Fees", "Hostel", "Exams", "Dashboard", "Admin"]
choice = st.sidebar.selectbox("Go to", menu)

s = SessionLocal()

# ----- Admissions -----
if choice == "Admissions":
    st.header("Admissions")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("New Admission Form")
        name = st.text_input("Full name")
        dob = st.date_input("DOB", value=datetime.date(2003,1,1))
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        email = st.text_input("Email")
        mobile = st.text_input("Mobile")
        program = st.text_input("Program")
        year = st.text_input("Year")
        dept = st.text_input("Department")
        address = st.text_area("Address")
        guardian_name = st.text_input("Guardian name")
        guardian_contact = st.text_input("Guardian contact")
        if st.button("Submit Admission"):
            # basic validation
            if not name or not email:
                st.error("Name and email required")
            else:
                sid = gen_student_id()
                st_obj = Student(student_id=sid, name=name, dob=dob.isoformat(), gender=gender,
                                 email=email, mobile=mobile, program=program, year=year,
                                 department=dept, address=address, guardian_name=guardian_name,
                                 guardian_contact=guardian_contact)
                s.add(st_obj)
                s.commit()
                adm_id = gen_generic_id("ADM")
                admission = Admission(admission_id=adm_id, student_id_fk=st_obj.id, source="Online", status="Approved")
                s.add(admission)
                s.commit()
                st.success(f"Admission recorded for {name} — Student ID: {sid}")
    with col2:
        st.subheader("Search Students")
        q = st.text_input("Search by name, student id or email")
        if st.button("Search"):
            qry = s.query(Student)
            rows = []
            if q:
                rows = qry.filter((Student.name.ilike(f"%{q}%")) | (Student.student_id.ilike(f"%{q}%")) | (Student.email.ilike(f"%{q}%"))).all()
            else:
                rows = qry.limit(50).all()
            df = pd.DataFrame([{
                "student_id": r.student_id, "name": r.name, "email": r.email, "mobile": r.mobile,
                "program": r.program, "year": r.year
            } for r in rows])
            st.dataframe(df)

# ----- Fees -----
elif choice == "Fees":
    st.header("Fees & Receipts")
    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader("Record Payment (Manual / Testing)")
        student_query = st.text_input("Student ID or email")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=1000.0)
        mode = st.selectbox("Payment mode", ["Cash","UPI","Card","Netbanking","Gateway"])
        purpose = st.text_input("Purpose", "Tuition")
        txn = st.text_input("Transaction ID (optional)")
        recorded_by = st.text_input("Recorded by", st.session_state.user['username'])
        if st.button("Record Payment"):
            # locate student
            student = None
            if student_query:
                student = s.query(Student).filter((Student.student_id==student_query)|(Student.email==student_query)).first()
            if not student:
                st.error("Student not found — please use Student ID or registered email.")
            else:
                receipt_id = gen_generic_id("REC")
                # compute balance: latest fee balance, naive
                last_fee = s.query(Fee).filter_by(student_id_fk=student.id).order_by(Fee.timestamp.desc()).first()
                last_balance = last_fee.balance_after if last_fee else 0.0
                balance_after = last_balance - amount
                fee = Fee(receipt_id=receipt_id, student_id_fk=student.id, name=student.name,
                          amount=amount, payment_mode=mode, transaction_id=txn or receipt_id,
                          balance_after=balance_after, purpose=purpose, recorded_by=recorded_by)
                s.add(fee)
                s.commit()
                # generate PDF receipt
                try:
                    build_and_save_receipt(s, fee)
                except Exception as e:
                    st.warning("Receipt generation failed: " + str(e))
                st.success(f"Payment recorded. Receipt ID: {receipt_id}")
    with col2:
        st.subheader("Recent Payments")
        rows = s.query(Fee).order_by(Fee.timestamp.desc()).limit(20).all()
        df = pd.DataFrame([{"receipt_id":r.receipt_id, "student": r.name, "student_id": getattr(r.student,'student_id',''),
                            "amount": r.amount, "mode": r.payment_mode, "ts": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "invoice": r.invoice_path} for r in rows])
        st.dataframe(df)

# ----- Hostel -----
elif choice == "Hostel":
    st.header("Hostel Management")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Request / Allocate")
        student_q = st.text_input("Student ID or Email for hostel")
        block = st.text_input("Block (A/B/C)")
        room = st.text_input("Room No")
        bed = st.text_input("Bed No")
        move_in = st.date_input("Move-in date", value=datetime.date.today())
        notes = st.text_area("Notes")
        if st.button("Create/Allocate"):
            student = s.query(Student).filter((Student.student_id==student_q)|(Student.email==student_q)).first()
            if not student:
                st.error("Student not found")
            else:
                alloc_id = gen_generic_id("HST")
                h = HostelAllocation(allocation_id=alloc_id, student_id_fk=student.id, block=block, room_no=room, bed_no=bed,
                                    move_in=move_in.isoformat(), status="Allocated", allocated_by=st.session_state.user['username'], notes=notes)
                s.add(h)
                s.commit()
                st.success(f"Hostel allocated: {block}-{room}-{bed} to {student.name}")
    with col2:
        st.subheader("Hostel Occupancy")
        rows = s.query(HostelAllocation).all()
        df = pd.DataFrame([{"alloc_id":r.allocation_id, "student": getattr(r.student,'name',''), "block": r.block, "room": r.room_no, "bed": r.bed_no, "status": r.status} for r in rows])
        st.dataframe(df)

# ----- Exams -----
elif choice == "Exams":
    st.header("Exams & Marks")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upload Marks (single)")
        student_q = st.text_input("Student ID or Email for marks")
        subj_code = st.text_input("Subject Code")
        subj_name = st.text_input("Subject Name")
        marks = st.number_input("Marks", min_value=0.0, max_value=100.0, value=0.0)
        graded_by = st.text_input("Graded by", st.session_state.user['username'])
        if st.button("Save Marks"):
            student = s.query(Student).filter((Student.student_id==student_q)|(Student.email==student_q)).first()
            if not student:
                st.error("Student not found")
            else:
                exid = gen_generic_id("EXM")
                status = "Pass" if marks >= 40 else "Fail"
                ex = Exam(exam_id=exid, student_id_fk=student.id, subject_code=subj_code, subject_name=subj_name, marks=marks, status=status, graded_by=graded_by)
                s.add(ex)
                s.commit()
                st.success(f"Saved marks for {student.name}: {marks} ({status})")
    with col2:
        st.subheader("Recent Grades")
        rows = s.query(Exam).order_by(Exam.graded_at.desc()).limit(30).all()
        df = pd.DataFrame([{"exam_id":r.exam_id,"student": getattr(r.student,'name',''), "subject": r.subject_name, "marks": r.marks, "status": r.status} for r in rows])
        st.dataframe(df)

# ----- Dashboard -----
elif choice == "Dashboard":
    st.header("Dashboard")
    total_students = s.query(Student).count()
    total_fees = s.query(Fee).with_entities(func_sum:=Fee.amount).all()
    # compute total fees sum safely
    total_fees_val = 0.0
    for row in s.query(Fee).all():
        total_fees_val += (row.amount or 0.0)
    st.metric("Total Students", total_students)
    st.metric("Total Fees Collected (₹)", f"{total_fees_val:.2f}")
    # simple charts - fees by month
    fees = pd.DataFrame([{"amount":f.amount, "ts": f.timestamp} for f in s.query(Fee).all()])
    if not fees.empty:
        fees['month'] = pd.to_datetime(fees['ts']).dt.to_period('M').astype(str)
        fees_by_month = fees.groupby('month')['amount'].sum().reset_index()
        st.plotly_chart(__import__("plotly.express").express.bar(fees_by_month, x='month', y='amount', title="Fees by month"))
    # hostel occupancy
    hostel_rows = pd.DataFrame([{"block":h.block, "status": h.status} for h in s.query(HostelAllocation).all()])
    if not hostel_rows.empty:
        occ = hostel_rows.groupby('block').size().reset_index(name='count')
        st.plotly_chart(__import__("plotly.express").express.pie(occ, names='block', values='count', title="Hostel occupancy by block"))

# ----- Admin -----
elif choice == "Admin":
    st.header("Admin Tools")
    if st.session_state.user['role'] != "admin":
        st.warning("Admin tools available only to admin users.")
    else:
        st.subheader("User management (create user)")
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["admin","accounts","warden","faculty","viewer"])
        disp = st.text_input("Display name")
        if st.button("Create User"):
            from utils import hash_password
            from models import User
            try:
                u = User(username=uname, hashed_password=hash_password(pwd), role=role, display_name=disp)
                s.add(u); s.commit()
                st.success("User created")
            except IntegrityError:
                s.rollback()
                st.error("Username exists")
        st.subheader("Backup DB / Export CSVs")
        if st.button("Export CSV Backups"):
            paths = export_csv_all()
            st.success("Backups created")
            for k,v in paths.items():
                st.write(f"{k}: {v}")
        st.subheader("Manual DB download")
        db_path = os.path.join(os.path.dirname(__file__), "college_erp.db")
        if os.path.exists(db_path):
            st.download_button("Download DB file", data=open(db_path,"rb"), file_name="college_erp.db")

s.close()
