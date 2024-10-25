import streamlit as st
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Set page configuration and custom styles for mobile
st.set_page_config(page_title="Pro Medication Manager", layout="centered")

# Custom CSS for mobile resolution
st.markdown("""
    <style>
        .block-container { padding: 1rem; max-width: 100%; }
        .stButton>button, .stTextInput>input, .stNumberInput>input {
            width: 100%; padding: 0.5rem; margin-bottom: 0.5rem;
        }
        .stAlert, .stMarkdown { text-align: center; font-size: 1.2em; }
        .medication-card { padding: 1rem; border-radius: 10px; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "medications" not in st.session_state:
    st.session_state.medications = []
if "intake_history" not in st.session_state:
    st.session_state.intake_history = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []

# Functions
def add_medication(name, dosage, stock, intake_times, notes, category, image=None):
    st.session_state.medications.append({
        "name": name, "dosage": dosage, "stock": stock,
        "intake_times": intake_times, "last_taken": None,
        "notes": notes, "category": category, "image": image
    })

def log_intake(med_name, time):
    st.session_state.intake_history.append({"name": med_name, "time": time})

def check_stock():
    low_stock_meds = [med for med in st.session_state.medications if med["stock"] <= 5]
    if low_stock_meds:
        for med in low_stock_meds:
            st.warning(f"⚠️ Low Stock Alert: Only {med['stock']} units left for {med['name']}!")

def export_to_pdf():
    pdf_path = "medications.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Medication List")
    c.drawString(100, 730, "Name              Dosage              Notes")

    y = 710
    for med in st.session_state.medications:
        c.drawString(100, y, f"{med['name']}          {med['dosage']}          {med['notes']}")
        y -= 20

    c.save()
    return pdf_path

def export_to_csv():
    csv_path = "medications.csv"
    df = pd.DataFrame(st.session_state.medications)
    df.to_csv(csv_path, index=False)
    return csv_path

# Title
st.title("💊 Professional Medication Manager")

# Medication Entry
with st.expander("➕ Add Medication"):
    name = st.text_input("Medication Name")
    dosage = st.text_input("Dosage (e.g., 1 tablet)")
    stock = st.number_input("Stock (units)", min_value=0, step=1)
    intake_times = st.multiselect("Intake Times", ["Morning", "Afternoon", "Evening", "Night"])
    notes = st.text_area("Notes (e.g., take with food)")
    category = st.selectbox("Category", ["Prescription", "Over-the-Counter", "Vitamins", "Others"])
    image = st.file_uploader("Upload Image (Optional)", type=["jpg", "jpeg", "png"])

    if st.button("Add Medication"):
        if name and dosage and stock > 0 and intake_times:
            add_medication(name, dosage, stock, intake_times, notes, category, image)
            st.success(f"Medication '{name}' added!")
            st.experimental_rerun()

# Search Functionality
st.subheader("🔍 Search Medications")
search_term = st.text_input("Search by Name")
filtered_medications = [med for med in st.session_state.medications if search_term.lower() in med["name"].lower()]

# Editable Medication List
st.subheader("📋 Your Medications")
medications_to_display = filtered_medications if search_term else st.session_state.medications
medications_df = pd.DataFrame(medications_to_display)

if not medications_df.empty:
    medications_df['action'] = medications_df.apply(lambda x: f"Edit {x['name']}", axis=1)
    editable_df = st.dataframe(medications_df[['name', 'dosage', 'notes', 'stock', 'category', 'action']])

    for i in range(len(st.session_state.medications)):
        if editable_df.iloc[i]['action']:
            st.session_state.medications[i]['dosage'] = editable_df.iloc[i]['dosage']
            st.session_state.medications[i]['notes'] = editable_df.iloc[i]['notes']
            st.session_state.medications[i]['stock'] = editable_df.iloc[i]['stock']

# Export PDF and CSV Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Export Medications to PDF"):
        pdf_path = export_to_pdf()
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_path)

with col2:
    if st.button("Export Medications to CSV"):
        csv_path = export_to_csv()
        with open(csv_path, "rb") as f:
            st.download_button("Download CSV", f, file_name=csv_path)

# Reminders and Notifications
st.subheader("⏰ Daily Reminders")
reminder_time = st.time_input("Set Reminder Time")
if st.button("Set Reminder"):
    for med in st.session_state.medications:
        st.session_state.reminders.append({"name": med["name"], "time": reminder_time, "completed": False})
    st.success("Reminder set for all medications")

# Reminder Notifications
st.subheader("🔔 Reminder Alerts")
current_time = datetime.now().time()
for reminder in st.session_state.reminders:
    if not reminder["completed"] and reminder["time"] <= current_time:
        st.warning(f"Time to take {reminder['name']}!")
        if st.button(f"Mark {reminder['name']} as Taken", key=f"reminder-{reminder['name']}"):
            reminder["completed"] = True
            st.success(f"Marked {reminder['name']} as taken")

# Stock Check Alerts
st.subheader("⚠️ Stock Alerts")
check_stock()

# Intake History
st.subheader("📅 Intake History")
if st.session_state.intake_history:
    intake_df = pd.DataFrame(st.session_state.intake_history)
    intake_df["time"] = pd.to_datetime(intake_df["time"])
    intake_df["date"] = intake_df["time"].dt.date
    intake_df["time_only"] = intake_df["time"].dt.time
    st.write(intake_df[["name", "date", "time_only"]])
else:
    st.info("No intake history available")

# Analytics (Adherence Tracker)
st.subheader("📈 Medication Adherence")
total_doses = len(st.session_state.intake_history)
expected_doses = len(st.session_state.medications) * len(st.session_state.reminders)
if expected_doses > 0:
    adherence_rate = (total_doses / expected_doses) * 100
    st.write(f"Adherence Rate: {adherence_rate:.2f}%")
else:
    st.write("Set reminders and take medications to track adherence.")

st.caption("Manage medications, reminders, and stock seamlessly with this professional medication manager.")
