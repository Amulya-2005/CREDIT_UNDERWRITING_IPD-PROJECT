import streamlit as st
import pandas as pd
import re
import uuid
import smtplib
from email.message import EmailMessage
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

st.set_page_config(page_title="AI Credit Underwriting", layout="wide")

# Dummy Model with updated logic
class DummyModel:
    def _init_(self):
        self.feature_names_in_ = [
            'applicant_age', 'income_annum', 'cibil_score', 'loan_amount',
            'loan_interest', 'loan_percent_income', 'loan_term', 'active_loans',
            'gender_Male', 'gender_Other',
            'marital_status_Single', 'employee_status_Self-Employed',
            'employee_status_Unemployed', 'residence_type_Owned',
            'residence_type_Rented', 'loan_type_House', 'loan_type_Personal',
            'loan_purpose_Business Expansion'
        ]

    def predict(self, X):
        return [1 if x['cibil_score'] >= 700 and x['loan_percent_income'] < 70 else 0 for _, x in X.iterrows()]

    def predict_proba(self, X):
        return [[0.2, 0.8] if self.predict(X)[i] == 1 else [0.9, 0.1] for i in range(len(X))]

model = DummyModel()
submitted_data = []

# Email function

def send_approval_email(to_email, applicant_name, applicant_id):
    EMAIL_ADDRESS = "your_email@example.com"
    EMAIL_PASSWORD = "your_email_password"

    msg = EmailMessage()
    msg['Subject'] = 'Loan Application Approved'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"""Dear {applicant_name},

Congratulations! Your loan application (ID: {applicant_id}) has been approved.

Best regards,
Finance Team
""")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Phone validation

def is_valid_phone(p):
    return re.fullmatch(r"[6-9][0-9]{9}", p) and p not in ["0000000000", "9999999999"]

# OCR from uploaded file

def extract_text_from_file(uploaded_file):
    poppler_path = r"C:\Users\anjali\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
    if uploaded_file.name.endswith(".pdf"):
        images = convert_from_bytes(uploaded_file.read(), dpi=300, poppler_path=poppler_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    else:
        image = Image.open(uploaded_file)
        return pytesseract.image_to_string(image)

# Session state setup
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

pages = ["Personal Information", "Loan Details", "Upload Documents", "Final Decision"]
page = pages[st.session_state.current_page]

# Sidebar Chatbot
st.sidebar.title("🤖 Finance Chatbot")
user_q = st.sidebar.text_input("Ask about loans, CIBIL, etc...")
if user_q:
    if "cibil" in user_q.lower():
        st.sidebar.info("CIBIL score is influenced by timely payments, credit usage, and inquiries.")
    elif "loan" in user_q.lower():
        st.sidebar.info("Loan eligibility depends on income, credit score, and obligations.")
    elif "interest" in user_q.lower():
        st.sidebar.info("Interest rates vary based on loan type, bank, and applicant profile.")
    else:
        st.sidebar.info("This is a basic finance assistant. For legal advice, consult a financial expert.")

# Personal Info Page
if page == "Personal Information":
    st.subheader("Personal Information")
    name = st.text_input("Applicant Name", value=st.session_state.user_data.get("name", ""))
    age = st.number_input("Age", min_value=18, max_value=70, step=1, value=st.session_state.user_data.get("applicant_age", 18))
    gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(st.session_state.user_data.get("gender", "Male")))
    income = st.number_input("Annual Income (in ₹)", min_value=0.0, value=st.session_state.user_data.get("income_annum", 0.0))
    email = st.text_input("Email Address", value=st.session_state.user_data.get("email", ""))
    phone = st.text_input("Phone Number", value=st.session_state.user_data.get("phone", ""))
    address = st.text_area("Permanent Address", value=st.session_state.user_data.get("address", ""))

    if st.button("Save Personal Info"):
        if name and income > 0 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", email) and is_valid_phone(phone):
            if "applicant_id" not in st.session_state.user_data:
                st.session_state.user_data["applicant_id"] = str(uuid.uuid4())
            st.session_state.user_data.update({"name": name, "applicant_age": age, "gender": gender,
                                               "income_annum": income, "email": email, "phone": phone,
                                               "address": address})
            st.success("✅ Personal Info Saved")
        else:
            st.warning("❌ Enter valid name, income, email, and phone number.")

    if st.button("Next ➡"):
        st.session_state.current_page = 1

# Loan Details Page
elif page == "Loan Details":
    st.subheader("Loan Details")
    marital_status = st.selectbox("Marital Status", ["Single", "Married"], index=["Single", "Married"].index(st.session_state.user_data.get("marital_status", "Single")))
    emp_status = st.selectbox("Employment Status", ["Employed", "Unemployed", "Self-Employed"],
                              index=["Employed", "Unemployed", "Self-Employed"].index(st.session_state.user_data.get("employee_status", "Employed")))
    residence = st.selectbox("Residence Type", ["Owned", "Rented", "Mortgaged"], index=["Owned", "Rented", "Mortgaged"].index(st.session_state.user_data.get("residence_type", "Owned")))
    cibil = st.slider("CIBIL Score", min_value=300, max_value=900, value=st.session_state.user_data.get("cibil_score", 650))
    loan_amount = st.number_input("Loan Amount (in ₹)", min_value=10000.0, value=st.session_state.user_data.get("loan_amount", 10000.0))
    loan_interest = st.number_input("Loan Interest (%)", min_value=1.0, max_value=30.0, value=st.session_state.user_data.get("loan_interest", 10.0))
    loan_type = st.selectbox("Loan Type", ["House", "Vehicle", "Education", "Gold", "Personal", "Business"],
                             index=["House", "Vehicle", "Education", "Gold", "Personal", "Business"].index(st.session_state.user_data.get("loan_type", "House")))
    purpose = st.text_input("Purpose of Loan", value=st.session_state.user_data.get("loan_purpose", ""))
    loan_term = st.number_input("Loan Term (in months)", min_value=6, max_value=360, value=st.session_state.user_data.get("loan_term", 60))
    active_loans = st.number_input("Number of Active Loans", min_value=0, step=1, value=st.session_state.user_data.get("active_loans", 0))

    percent_income = loan_amount / max(st.session_state.user_data.get("income_annum", 1), 1) * 100

    if st.button("Save Loan Details"):
        if purpose and loan_amount < st.session_state.user_data.get("income_annum", 1) * 10:
            st.session_state.user_data.update({"marital_status": marital_status, "employee_status": emp_status,
                                               "residence_type": residence, "cibil_score": cibil,
                                               "loan_amount": loan_amount, "loan_interest": loan_interest,
                                               "loan_percent_income": percent_income, "loan_type": loan_type,
                                               "loan_purpose": purpose, "loan_term": loan_term,
                                               "active_loans": active_loans})
            submitted_data.append(st.session_state.user_data.copy())
            st.success("✅ Loan Info Saved")
        else:
            st.warning("Enter a valid loan purpose and ensure amount is reasonable.")

    if st.button("Next ➡", key="to_docs"):
        st.session_state.current_page = 2
    if st.button("⬅ Previous", key="back1"):
        st.session_state.current_page = 0

# Upload Documents Page
elif page == "Upload Documents":
    st.subheader("Upload Documents")
    aadhar = st.file_uploader("Upload Aadhar Card (Image or PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
    pan = st.file_uploader("Upload PAN Card")

    if aadhar:
        st.session_state.aadhar_file = aadhar
        try:
            text = extract_text_from_file(aadhar)
            st.session_state.user_data["aadhar_text"] = text
        except Exception as e:
            st.warning(f"Could not extract Aadhar name: {e}")

    if pan:
        st.session_state.pan_file = pan

    if st.button("⬅ Previous", key="back2"):
        st.session_state.current_page = 1
    if st.button("Next ➡", key="to_final"):
        st.session_state.current_page = 3

# Final Decision Page
elif page == "Final Decision":
    st.subheader("Final Decision")

    try:
        input_df = pd.DataFrame([st.session_state.user_data])
        input_df = pd.get_dummies(input_df, columns=["gender", "marital_status", "employee_status",
                                                     "residence_type", "loan_purpose", "loan_type"], drop_first=True)
        for col in model.feature_names_in_:
            if col not in input_df.columns:
                input_df[col] = 0
        input_df = input_df[model.feature_names_in_]

        pred = model.predict(input_df)[0]
        proba = model.predict_proba(input_df)[0][1]

        extracted_text = st.session_state.user_data.get("aadhar_text", "").lower().replace(" ", "")
        applicant_name = st.session_state.user_data.get("name", "").lower().replace(" ", "")

        if applicant_name not in extracted_text:
            st.error("❌ Applicant name not found in uploaded Aadhar document.")
            st.info(f"Applicant Name: {applicant_name}")
            st.stop()

        if st.button("Submit Application"):
            if pred == 1:
                st.success("Loan Approved ✅")
                try:
                    send_approval_email(st.session_state.user_data.get("email", ""),
                                        st.session_state.user_data.get("name", ""),
                                        st.session_state.user_data.get("applicant_id", ""))
                    st.info("Approval email sent to applicant.")
                except Exception as e:
                    st.warning(f"Failed to send approval email: {e}")
            else:
                st.error("Loan Rejected ❌")
                st.info(f"Model Confidence: {round(proba * 100, 2)}%")
                st.markdown("#### Tips to Improve Approval Chances")
                st.markdown("""
                - Improve your CIBIL score above 700.
                - Keep loan amount relative to your income lower.
                - Close or reduce other active loans.
                - Ensure consistent employment or income proof.
                """)
    except Exception as e:
        st.error(f"💥 Prediction failed: {e}")
        st.stop()
