import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import base64
from streamlit.delta_generator import DeltaGenerator
from urllib.request import urlopen
import json

# Helper function to create tables in SQLite
#@st.cache_resource(allow_output_mutation=True)
def create_tables():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            designation TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            check_in DATETIME NOT NULL,
            check_out DATETIME,
            date DATE NOT NULL -- New column for the date of the attendance record
        )
    """)
    conn.commit()
    conn.close()

# Helper function to insert new employee
def insert_employee(name, dept, email, password, designation):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, dept, email, password, designation)
        VALUES (?, ?, ?, ?, ?)
    """, (name, dept, email, password, designation))
    conn.commit()
    conn.close()

# Helper function to log attendance
def log_attendance(employee_id, check_in, check_out):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    if check_in and check_out:
        cursor.execute("""
            INSERT INTO attendance (employee_id, check_in, check_out, date)
            VALUES (?, ?, ?, ?)
        """, (employee_id, check_in, check_out, date.today()))
    elif check_in:
        cursor.execute("""
            INSERT INTO attendance (employee_id, check_in, date)
            VALUES (?, ?, ?)
        """, (employee_id, check_in, date.today()))
    elif check_out:
        cursor.execute("""
            UPDATE attendance
            SET check_out = ?
            WHERE employee_id = ? AND check_out IS NULL
        """, (check_out, employee_id))

    conn.commit()
    conn.close()
class Session_State:
    def __init__(self):
        self.authenticated = False
        self.email = ""
        self.designation = ""
        self.hide_signup = False
        self.ip_checked = False
session=Session_State()
# Helper function to get all attendance records for a specific employee
def get_employee_attendance(employee_id):
    conn = sqlite3.connect("attendance.db")
    query = f"SELECT * FROM attendance WHERE employee_id = {employee_id}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to get all attendance records for all employees
def get_all_attendance():
    conn = sqlite3.connect("attendance.db")
    query = """
        SELECT e.name, e.dept, e.designation, a.check_in, a.check_out, a.date 
        FROM attendance AS a
        JOIN employees AS e ON a.employee_id = e.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to get attendance records of all employees of a specific department
def get_all_attendance_by_department(department):
    conn = sqlite3.connect("attendance.db")
    query = f"""
        SELECT e.name, e.dept, e.designation, a.check_in, a.check_out, a.date 
        FROM attendance AS a
        JOIN employees AS e ON a.employee_id = e.id
        WHERE e.dept = '{department}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Helper function to check if the user is an admin based on their email
def is_admin(email):
    # Replace this with your actual implementation
    return email == "admin@example.com"

# Helper function to get employee ID from the database based on the email
def get_employee_id(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE email = ?", (email,))
    employee_id = cursor.fetchone()
    conn.close()
    return employee_id[0] if employee_id else None

# Helper function to clean attendance records for the next day
def clean_attendance():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # Calculate the next day's date
    next_day = date.today() + timedelta(days=1)

    # Delete attendance records for the next day
    cursor.execute("DELETE FROM attendance WHERE date = ?", (next_day,))

    conn.commit()
    conn.close()

def is_email_unique(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM employees WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return not result
# Rest of the
#
#ALLOWED_IP_ADDRESSES = ["124.109.36.140","58.65.179.195","115.186.167.133"]
def get_user_ip():
    data = json.load(urlopen("http://httpbin.org/ip"))
    return data["origin"]
def get_employee_password(email):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM employees WHERE email = ?", (email,))
    password = cursor.fetchone()
    conn.close()
    return password[0] if password else None
# Define a custom SessionState class to handle attribute initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = ""
    st.session_state.designation = ""
    st.session_state.hide_signup = False
def main():
    favicon_path = "KP favicon (1).png"  # Replace with the filename of your custom favicon
    st.set_page_config(page_title="KP Leads", page_icon=favicon_path)
    st.title("Kp Leads Employee Attendance")
    #if not session.ip_checked:
        #user_ip = get_user_ip()
    #if user_ip not in ALLOWED_IP_ADDRESSES:
      #  st.error("Access denied. Your IP address is not allowed.")
       # return
    #session.ip_checked = True

    create_tables()

    # Handle URL parameters to show/hide signup button for admins
    if st.session_state.authenticated and st.session_state.designation == "Admin":
        hide_signup = st.experimental_get_query_params().get("hide_signup")
        hide_signup = hide_signup[0] if hide_signup else "false"
        hide_signup = hide_signup.lower() == "true"
        st.session_state.hide_signup = hide_signup
    logo_image = "KP favicon (1).png"
    # Authentication
    col_container = st.container()
    col_container.write("")
    col1, col2, col3 = col_container.columns([1, 2, 1])

    # Display the image in the center column with size 300x300
    col2.image(logo_image, width=200)
    st.sidebar.title("Authentication")

    # Signup Page (Only show if signup is not hidden for admins)
    if not st.session_state.hide_signup and st.sidebar.checkbox("Sign Up"):

        st.subheader("Sign Up")
        name = st.text_input("Name")
        dept = st.selectbox("Department",
                            ["QA", "FE Live", "FE Closing", "Medicare", "MVA", "IT", "Development", "HR"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        designation = st.selectbox("Designation",
                                   ["Admin", "Team Lead", "Manager", "Intern", "Verifiers", "Closers", "Assistant","Executive"])

        if st.button("Sign Up"):
            if is_email_unique(email):
                insert_employee(name, dept, email, password, designation)
                st.success("Account created successfully. Please sign in.")
            else:
                st.error("Email already exists. Please choose a different email.")

    # Login Page
    else:
        st.subheader("Sign In")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Perform login and redirect to dashboard
            employee_id = get_employee_id(email)
            if employee_id is not None:
                conn = sqlite3.connect("attendance.db")
                cursor = conn.cursor()
                cursor.execute("SELECT password, designation FROM employees WHERE email = ?", (email,))
                result = cursor.fetchone()
                conn.close()

                if result and result[0] == password:
                    st.session_state.authenticated = True
                    st.session_state.email = email
                    designation = result[1]
                    st.session_state.designation = designation
                else:
                    st.error("Wrong email or password. Please try again.")

    # Logout Button
    if st.session_state.authenticated:
        st.sidebar.text(f"Logged in as: {st.session_state.email}")
        logout = st.sidebar.button("Logout")
        if logout:
            st.session_state.authenticated = False
            st.session_state.email = ""
            st.session_state.designation = ""
            st.experimental_rerun()

    # Dashboard
    if st.session_state.authenticated:
        st.title("Employee Dashboard")
        employee_id = get_employee_id(st.session_state.email)

        # For all authenticated users, show Check-In and Check-Out buttons.
        check_in = st.button("Check In")
        check_out = st.button("Check Out")
        if check_in:
            log_attendance(employee_id, datetime.now(), None)
            st.success("Checked in successfully.")
        if check_out:
            log_attendance(employee_id, None, datetime.now())
            st.success("Checked out successfully.")

    # For Admin and Team Lead, show additional functionalities.
    if st.session_state.authenticated and st.session_state.designation == "Admin":
        st.title("Admin Panel")

        # Button to hide signup for all users
        hide_signup = st.sidebar.checkbox("Hide Signup Button")
        st.experimental_set_query_params(hide_signup=hide_signup)

        # Clean Attendance Button
        if st.button("Clean Attendance for Next Day"):
            clean_attendance()
            st.success("Attendance records for the next day cleaned successfully.")

        # Download Attendance Button
        if st.button("Download Attendance"):
            df = get_all_attendance()
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="attendance.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
        if st.button("Forget Password"):
            st.subheader("Forget Password")
            email_to_reset = st.text_input("Employee Email to Reset Password")

            show_password = st.button("Show Password")
            password_placeholder = st.empty()

            if show_password:
                password = get_employee_password(email_to_reset)
                if password:
                    password_placeholder.text_input("Password", value=password, type="password")
                else:
                    st.error("Employee with the provided email does not exist.")





        # For Admin and Team Lead, show attendance records for employees of respective departments.
        if st.session_state.designation in ["Admin", "Team Lead", "Executives"]:
            department = st.selectbox("Select Department",
                                      ["QA", "FE Live", "FE Closing", "Medicare", "MVA", "IT", "Development", "HR"])
            df = get_all_attendance_by_department(department)
            st.dataframe(df)



if __name__ == "__main__":
    main()



