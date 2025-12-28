import streamlit as st
import sqlite3
from fpdf import FPDF
import os
import re
import json
import uuid
import time

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect('students.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS students (
    roll_no TEXT PRIMARY KEY,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    course TEXT,
    cgpa REAL,
    grade TEXT
)
''')
conn.commit()

# ---------- LOGGING SYSTEM ----------
LOG_FILE = "logs/app_logs.log"

def log_action(action, start_time, headers=None):
    end_time = time.time()
    log_entry = {
        "transaction_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "action": action,
        "time_taken_ms": int((end_time - start_time) * 1000),
        "headers": headers or {}
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# ---------- HELPER FUNCTIONS ----------
def generate_roll_no(course):
    year = st.session_state.get("year", 2025)
    c.execute("SELECT COUNT(*) FROM students WHERE course=?", (course,))
    count = c.fetchone()[0] + 1
    return f"{year}R1{course.upper()}{count}"

def add_student(first, middle, last, phone, email, address, course, cgpa):
    roll_no = generate_roll_no(course)
    c.execute('''
        INSERT INTO students
        (roll_no, first_name, middle_name, last_name, phone, email, address, course, cgpa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (roll_no, first, middle, last, phone, email, address, course, cgpa))
    conn.commit()
    st.success(f"Student added with Roll No: {roll_no}")
    return roll_no

def list_students():
    c.execute("SELECT * FROM students ORDER BY roll_no")
    return c.fetchall()

def update_student(roll_no, first, middle, last, phone, email, address, course, cgpa, grade):
    c.execute('''
        UPDATE students 
        SET first_name=?, middle_name=?, last_name=?, phone=?, email=?, address=?, course=?, cgpa=?, grade=? 
        WHERE roll_no=?
    ''', (first, middle, last, phone, email, address, course, cgpa, grade, roll_no))
    conn.commit()
    st.success(f"Student {roll_no} updated successfully!")

# ---------- VALIDATION FUNCTIONS ----------
def validate_phone(phone):
    return re.fullmatch(r'\d{10}', phone)

def validate_email(email):
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)

# ---------- STREAMLIT UI ----------
st.title("Student Management System")

menu = ["Register Student", "List Students", "Update Student"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register Student":
    st.subheader("Register Student")
    with st.form("student_form"):
        first_name = st.text_input("First Name")
        middle_name = st.text_input("Middle Name")
        last_name = st.text_input("Last Name")
        phone = st.text_input("Phone Number (10 digits)")
        email = st.text_input("Email")
        address = st.text_area("Address")
        course = st.selectbox("Course", ["MCA", "MBA", "MTECH", "BTECH"])
        cgpa = st.number_input("CGPA", 0.0, 10.0, 0.0, 0.01)
        submitted = st.form_submit_button("Register")
        
        if submitted:
            start_time = time.time()
            if not validate_phone(phone):
                st.error("Invalid phone number. Must be 10 digits.")
            elif not validate_email(email):
                st.error("Invalid email address.")
            else:
                roll_no = add_student(first_name, middle_name, last_name, phone, email, address, course, cgpa)
                log_action(f"Registered student {roll_no}", start_time, headers={"user_agent": st.session_state.get('user_agent', 'N/A')})

elif choice == "List Students":
    st.subheader("List of Students")
    start_time = time.time()
    students = list_students()
    st.table(students)
    log_action("Listed students", start_time)

elif choice == "Update Student":
    st.subheader("Update Student Details")
    roll_no = st.text_input("Enter Roll Number")
    
    # Load student
    if st.button("Load Student"):
        c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
        student = c.fetchone()
        if student:
            # Store in session_state
            st.session_state['student'] = student
        else:
            st.error("Student not found!")
            st.session_state['student'] = None

    # If student is loaded, show editable fields
    if 'student' in st.session_state and st.session_state['student']:
        student = st.session_state['student']
        first_name = st.text_input("First Name", student[1])
        middle_name = st.text_input("Middle Name", student[2])
        last_name = st.text_input("Last Name", student[3])
        phone = st.text_input("Phone Number (10 digits)", student[4])
        email = st.text_input("Email", student[5])
        address = st.text_area("Address", student[6])
        course = st.selectbox("Course", ["MCA", "MBA", "MTECH", "BTECH"],
                              index=["MCA","MBA","MTECH","BTECH"].index(student[7]))
        cgpa = st.number_input("CGPA", 0.0, 10.0, student[8], 0.01)
        grade = st.text_input("Grade", student[9] if student[9] else "")

        if st.button("Update"):
            start_time = time.time()
            # Validations
            if not re.fullmatch(r'\d{10}', phone):
                st.error("Invalid phone number")
            elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Invalid email")
            else:
                update_student(roll_no, first_name, middle_name, last_name, phone, email, address, course, cgpa, grade)
                log_action(f"Updated student {roll_no}", start_time)
                # Clear session_state after update
                st.session_state['student'] = None
