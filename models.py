# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime
import os
from config import DB_PATH

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def now():
    return datetime.datetime.utcnow()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)  # human id like COLG24S12345
    name = Column(String, nullable=False)
    dob = Column(String)  # iso date string or text
    gender = Column(String)
    email = Column(String, index=True)
    mobile = Column(String)
    program = Column(String)
    year = Column(String)
    department = Column(String)
    address = Column(Text)
    guardian_name = Column(String)
    guardian_contact = Column(String)
    photo_path = Column(String)
    created_at = Column(DateTime, default=now)

    admissions = relationship("Admission", back_populates="student")
    fees = relationship("Fee", back_populates="student")
    hostels = relationship("HostelAllocation", back_populates="student")
    exams = relationship("Exam", back_populates="student")

class Admission(Base):
    __tablename__ = "admissions"
    id = Column(Integer, primary_key=True)
    admission_id = Column(String, unique=True, index=True)
    student_id_fk = Column(Integer, ForeignKey("students.id"))
    submitted_at = Column(DateTime, default=now)
    source = Column(String)
    documents = Column(Text)
    status = Column(String, default="Pending")
    remarks = Column(Text)

    student = relationship("Student", back_populates="admissions")

class Fee(Base):
    __tablename__ = "fees"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=now)
    student_id_fk = Column(Integer, ForeignKey("students.id"))
    name = Column(String)
    amount = Column(Float)
    payment_mode = Column(String)
    transaction_id = Column(String)
    invoice_path = Column(String)
    balance_after = Column(Float, default=0.0)
    purpose = Column(String)
    notes = Column(Text)
    recorded_by = Column(String)

    student = relationship("Student", back_populates="fees")

class HostelAllocation(Base):
    __tablename__ = "hostel"
    id = Column(Integer, primary_key=True)
    allocation_id = Column(String, unique=True, index=True)
    student_id_fk = Column(Integer, ForeignKey("students.id"))
    block = Column(String)
    room_no = Column(String)
    bed_no = Column(String)
    move_in = Column(String)
    move_out = Column(String, nullable=True)
    status = Column(String, default="Requested")
    requested_at = Column(DateTime, default=now)
    allocated_by = Column(String)
    notes = Column(Text)

    student = relationship("Student", back_populates="hostels")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    exam_id = Column(String, unique=True, index=True)
    student_id_fk = Column(Integer, ForeignKey("students.id"))
    subject_code = Column(String)
    subject_name = Column(String)
    marks = Column(Float)
    status = Column(String)  # Pass/Fail
    graded_at = Column(DateTime, default=now)
    graded_by = Column(String)
    notes = Column(Text)

    student = relationship("Student", back_populates="exams")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")  # admin, accounts, warden, faculty, viewer
    display_name = Column(String)
    created_at = Column(DateTime, default=now)

def init_db():
    Base.metadata.create_all(bind=engine)
