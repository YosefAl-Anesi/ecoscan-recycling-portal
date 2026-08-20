import sqlite3
import time
import hashlib
import io
import cv2
import numpy as np
import qrcode
from PIL import Image
import streamlit as st

# --- CONFIGURATION ---
PERMANENT_QR_DATA = "BIN_LOCATION_01_PERMANENT_STATIC_TOKEN"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def register_user(username, password):
    if not username or not password:
        return False, "Username and password required."
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, points) VALUES (?, ?, 0)", (username, pwd_hash))
        conn.commit()
        conn.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists."

def authenticate_user(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, pwd_hash))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_points(username, points=10):
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username = ?", (points, username))
    c.execute("INSERT INTO scans (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def get_user_points(username):
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_leaderboard():
    conn = sqlite3.connect("recycling.db")
    c = conn.cursor()
    c.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# --- HELPER FUNCTIONS ---
def get_current_30s_token():
    time_block = int(time.time() // 30)
    return hashlib.sha256(f"SECRET_BIN_SEED_{time_block}".encode()).hexdigest()[:8]

def generate_qr_image(data):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def decode_qr(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img_np)
    return data if data else None

# --- UI PAGE CONFIG & THEME INJECTION ---
st.set_page_config(
    page_title="EcoScan | Smart Recycling Portal",
    page_icon="♻️",
    layout="centered"
)

# Custom Enterprise CSS Overlay
st.markdown("""
<style>
    /* Dark Slate Theme Variables */
    :root {
        --bg-main: #0F172A;
        --bg-card: #1E293B;
        --border-color: #334155;
        --accent-green: #10B981;
        --accent-hover: #059669;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
    }

    /* Global Body Adjustments */
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Clean Card UI Containers */
    .css-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    /* Custom Headers */
    .portal-header {
        text-align: center;
        padding: 10px 0 25px 0;
    }
    .portal-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        margin: 0;
    }
    .portal-header p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-top: 6px;
    }

    /* Streamlit Buttons Styling */
    .stButton > button {
        width: 100%;
        background-color: var(--accent-green) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: var(--accent-hover) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #020617;
        border-right: 1px solid var(--border-color);
    }

    /* Input Controls */
    .stTextInput > div > div > input {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    /* Status Badges */
    .status-badge-verified {
        background-color: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-locked {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }

    /* File Uploader Custom Styling */
    section[data-testid="stFileUploader"] {
        background-color: var(--bg-card);
        border: 1px dashed var(--border-color);
        border-radius: 10px;
        padding: 15px;
    }

    /* Hide standard Streamlit header/footer noise */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session State Initializations
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None
if "step1_passed" not in st.session_state:
    st.session_state["step1_passed"] = False

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color: #F8FAFC; font-size: 1.3rem; margin-bottom: 20px;'>EcoScan OS</h2>", unsafe_allow_html=True)
    
    if st.session_state["logged_in_user"]:
        st.markdown(f"""
        <div style="background: #1E293B; padding: 14px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;">
            <p style="margin:0; font-size: 0.8rem; color: #94A3B8;">AUTHENTICATED USER</p>
            <p style="margin:0; font-weight: 600; color: #F8FAFC;">{st.session_state['logged_in_user']}</p>
            <p style="margin:8px 0 0 0; font-size: 1.1rem; font-weight: 700; color: #10B981;">{get_user_points(st.session_state['logged_in_user'])} PTS</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sign Out"):
            st.session_state["logged_in_user"] = None
            st.session_state["step1_passed"] = False
            st.rerun()

    mode = st.radio("Interface Mode", ["Laptop (Bin Display)", "Phone (Scanner)", "Leaderboard"])

# ==========================================
# FRAGMENT: LAPTOP DISPLAY MONITOR
# ==========================================
@st.fragment(run_every="1s")
def render_bin_monitor():
    current_token = get_current_30s_token()
    qr_bytes = generate_qr_image(current_token)
    time_left = 30 - (int(time.time()) % 30)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(qr_bytes, width=220)
        st.caption(f"Security Hash: `{current_token}`")

    with col2:
        st.markdown(
            f"""
            <div style="background: #020617; border: 1px solid #334155; border-radius: 10px; padding: 20px; text-align: center;">
                <p style="margin:0; color: #94A3B8; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.05em;">TOKEN REFRESH</p>
                <h1 style="margin: 8px 0; color: #10B981; font-size: 52px; font-weight: 800;">{time_left}s</h1>
                <p style="margin:0; color: #64748B; font-size: 0.75rem;">SHA-256 Synchronized</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ==========================================
# MODE 1: LAPTOP DISPLAY
# ==========================================
if mode == "Laptop (Bin Display)":
    st.markdown("""
    <div class="portal-header">
        <h1>Bin Monitor Station</h1>
        <p>Live Node Display & Security Verification Interface</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-size: 1.1rem; color: #F8FAFC;'>Dynamic Verification Node</h3>", unsafe_allow_html=True)
    render_bin_monitor()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-size: 1.1rem; color: #F8FAFC;'>Static Bin Identification</h3>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])
    with col_a:
        perm_qr_bytes = generate_qr_image(PERMANENT_QR_DATA)
        st.image(perm_qr_bytes, width=130)
    with col_b:
        st.write("Deploy this physical token directly onto the waste receptacle chassis.")
        st.download_button("Download High-Res Token", data=perm_qr_bytes, file_name="bin_permanent_token.png", mime="image/png")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MODE 2: PHONE SCANNER
# ==========================================
elif mode == "Phone (Scanner)":
    st.markdown("""
    <div class="portal-header">
        <h1>Verification Portal</h1>
        <p>Two-Factor Hardware Recycling Validator</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state["logged_in_user"]:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Authentication", "New Account"])
        
        with tab_login:
            login_user = st.text_input("Username", key="login_u")
            login_pass = st.text_input("Password", type="password", key="login_p")
            if st.button("Sign In"):
                if authenticate_user(login_user, login_pass):
                    st.session_state["logged_in_user"] = login_user
                    st.success("Authenticated successfully.")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with tab_register:
            reg_user = st.text_input("Choose Username", key="reg_u")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_p")
            if st.button("Create Account"):
                success, msg = register_user(reg_user, reg_pass)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Step 1 Container
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        col_s1_a, col_s1_b = st.columns([2, 1])
        with col_s1_a:
            st.markdown("<h3 style='margin:0; font-size: 1.1rem;'>Phase 1: Dynamic Monitor Auth</h3>", unsafe_allow_html=True)
        with col_s1_b:
            if st.session_state["step1_passed"]:
                st.markdown("<div style='text-align:right;'><span class='status-badge-verified'>VERIFIED</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:right;'><span class='status-badge-locked'>PENDING</span></div>", unsafe_allow_html=True)

        if st.session_state["step1_passed"]:
            st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; margin-top: 10px;'>Session lock acquired. Dynamic check complete.</p>", unsafe_allow_html=True)
            if st.button("Clear Authorization", key="reset_s1"):
                st.session_state["step1_passed"] = False
                st.rerun()
        else:
            st.markdown("<p style='color: #94A3B8; font-size: 0.85rem;'>Capture the dynamic 30s token displayed on the terminal monitor.</p>", unsafe_allow_html=True)
            file_step1 = st.file_uploader("Upload Phase 1 Image", type=["jpg", "jpeg", "png"], key="step1_file")
            
            if file_step1 is not None:
                scanned_data = decode_qr(file_step1)
                valid_tokens = [
                    get_current_30s_token(),
                    hashlib.sha256(f"SECRET_BIN_SEED_{int(time.time() // 30) - 1}".encode()).hexdigest()[:8]
                ]
                if scanned_data in valid_tokens:
                    st.session_state["step1_passed"] = True
                    st.success("Phase 1 Validated. Session Lock Granted.")
                    st.rerun()
                else:
                    st.error("Token invalid or expired. Resubmit image.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Step 2 Container
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='margin:0 0 10px 0; font-size: 1.1rem;'>Phase 2: Hardware Receptacle Scan</h3>", unsafe_allow_html=True)
        
        if not st.session_state["step1_passed"]:
            st.info("🔒 Complete Phase 1 authorization to unlock hardware scanning.")
        else:
            st.markdown("<p style='color: #94A3B8; font-size: 0.85rem;'>Capture the static token attached to the bin chassis.</p>", unsafe_allow_html=True)
            file_step2 = st.file_uploader("Upload Phase 2 Image", type=["jpg", "jpeg", "png"], key="step2_file")
            
            if file_step2 is not None:
                scanned_perm = decode_qr(file_step2)
                if scanned_perm == PERMANENT_QR_DATA:
                    add_points(st.session_state["logged_in_user"], 10)
                    st.balloons()
                    st.success(f"Transaction Complete. +10 PTS committed to account {st.session_state['logged_in_user']}.")
                    st.session_state["step1_passed"] = False
                else:
                    st.error("Invalid physical token detected.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MODE 3: LEADERBOARD
# ==========================================
else:
    st.markdown("""
    <div class="portal-header">
        <h1>Recycling Leaderboard</h1>
        <p>Global System Contribution Rankings</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    board = get_leaderboard()
    if board:
        formatted_board = [{"Rank": f"#{idx + 1}", "User": row[0], "Points": f"{row[1]} PTS"} for idx, row in enumerate(board)]
        st.table(formatted_board)
    else:
        st.info("No transaction data available.")
    st.markdown('</div>', unsafe_allow_html=True)