#%%writefile app.py

import streamlit as st
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import tempfile
import time
import re
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --------------------------------------------------
# TWILIO CONFIG
# --------------------------------------------------
ACCOUNT_SID = "ACb6480ba01f5df75da0cc99427a0ed31d"
AUTH_TOKEN = "0fddced93f399c8097b264d8f64e76fc"
TWILIO_NUMBER = "+19793155806"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# --------------------------------------------------
# PHONE FORMAT
# --------------------------------------------------
def format_phone(num):
    num = num.strip().replace(" ", "")
    if re.fullmatch(r"\d{10}", num):
        return "+91" + num
    if re.fullmatch(r"\+91\d{10}", num):
        return num
    return None

# --------------------------------------------------
# SAFE SMS SENDER (LIMIT AWARE)
# --------------------------------------------------
def send_sms_safe(to, message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=to
        )
        return True
    except TwilioRestException as e:
        if "63038" in str(e):
            st.warning("⚠️ Daily SMS limit reached (Twilio Trial)")
        else:
            st.warning("⚠️ SMS failed")
        return False

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config("Wildlife Detection System", layout="wide")

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
for key in ["logged_in", "phone", "welcome_sent", "alert_sent"]:
    if key not in st.session_state:
        st.session_state[key] = False

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
def home():
    st.title("🦁 Wildlife Detection & Alert System")

    st.markdown("""
    ### 📌 About the Project
    This system detects **wild animals** using **YOLO deep learning models**
    and sends **real-time SMS alerts** to prevent human–wildlife conflict.

    **Technologies Used**
    - YOLO (Object Detection)
    - OpenCV
    - Streamlit
    - Twilio SMS API

    **Applications**
    - Forest surveillance
    - Wildlife protection
    - Smart villages
    - Border & night monitoring
    """)

    st.divider()
    if st.button("🔐 Login to Continue"):
        st.session_state.page = "login"

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
def login():
    st.title("🔐 Login")

    phone = st.text_input("Enter Mobile Number (India)", placeholder="939030XXXX")
    phone = format_phone(phone)

    if st.button("Login"):
        if not phone:
            st.error("Enter valid 10-digit Indian number")
            return

        st.session_state.logged_in = True
        st.session_state.phone = phone

        # Send welcome SMS ONLY ONCE
        if not st.session_state.welcome_sent:
            send_sms_safe(
                phone,
                "✅ Login Successful! Wildlife Detection System Activated."
            )
            st.session_state.welcome_sent = True

        st.success("Login successful")
        st.session_state.page = "detect"

# --------------------------------------------------
# DETECTION PAGE
# --------------------------------------------------
def detection():
    st.title("🦁 Wildlife Detection Dashboard")

    model_path = st.sidebar.text_input(
        "YOLO Model Path",
        "C:/Users/kbdpa.TRIVEDI/JC-Kavilesw-2b99/newDataset/yolov11/best.pt"
    )

    if st.sidebar.button("Load Model"):
        st.session_state.model = YOLO(model_path)
        st.sidebar.success("Model Loaded")

    if "model" not in st.session_state:
        st.warning("Load model first")
        return

    model = st.session_state.model

    CLASS_NAMES = [
        "Lion","Tiger","Leopard","Elephant","Cheetah",
        "Fox","Monkey","Deer","Bear","Buffalo",
        "Hyena","Rhino","Wolf","Zebra","Jaguar"
    ]

    mode = st.sidebar.radio("Mode", ["Image", "Video"])

    # ---------------- IMAGE ----------------
    if mode == "Image":
        img_file = st.file_uploader("Upload Image", ["jpg","png","jpeg"])
        if img_file:
            img = Image.open(img_file).convert("RGB")
            results = model(np.array(img)[:, :, ::-1])
            annotated = results[0].plot()

            if results[0].boxes and not st.session_state.alert_sent:
                animals = {CLASS_NAMES[int(b.cls)] for b in results[0].boxes}
                send_sms_safe(
                    st.session_state.phone,
                    f"🚨 ALERT! Detected: {', '.join(animals)}"
                )
                st.session_state.alert_sent = True

            st.image(annotated[:, :, ::-1], use_column_width=True)

    # ---------------- VIDEO ----------------
    else:
        vid = st.file_uploader("Upload Video", ["mp4","avi"])
        if vid:
            temp = tempfile.NamedTemporaryFile(delete=False)
            temp.write(vid.read())
            cap = cv2.VideoCapture(temp.name)
            stframe = st.empty()

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                results = model(frame)
                annotated = results[0].plot()

                if results[0].boxes and not st.session_state.alert_sent:
                    animals = {CLASS_NAMES[int(b.cls)] for b in results[0].boxes}
                    send_sms_safe(
                        st.session_state.phone,
                        f"🚨 ALERT! Detected: {', '.join(animals)}"
                    )
                    st.session_state.alert_sent = True

                stframe.image(annotated[:, :, ::-1], channels="RGB")
                time.sleep(0.03)

            cap.release()

# --------------------------------------------------
# ROUTING
# --------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    home()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "detect":
    detection()
