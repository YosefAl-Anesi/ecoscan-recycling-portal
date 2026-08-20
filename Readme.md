# EcoScan | Smart Recycling Verification Portal

**Course:** BIT2083 Fundamental of Computational Thinking  
**Institution:** City University Malaysia (Cyberjaya Campus)  
**Target SDG:** SDG 11 - Sustainable Cities and Communities / SDG 12 - Responsible Consumption & Production  

---

## Project Overview
EcoScan is a Streamlit-based web application designed to incentivize community waste recycling. To prevent reward spoofing, the platform uses a **Two-Factor Hardware Verification Workflow**:
1. **Phase 1 (Dynamic Verification):** An e-paper/terminal screen displays a Time-based One-Time Password (TOTP) QR code generated via SHA-256 that refreshes every 30 seconds.
2. **Phase 2 (Static Verification):** Once the active time-window token is validated, the user scans a physical permanent QR code attached to the waste receptacle chassis to claim points.

---

## Key Features
- **Dynamic 30s TOTP Token:** SHA-256 algorithm locked to `time.time() // 30` time blocks.
- **Computer Vision Integration:** OpenCV (`cv2.QRCodeDetector`) for server-side image decoding and parsing.
- **User Management & Leaderboard:** SQLite3 backend handling user authentication, timestamped scan transactions, and dynamic score updating.
- **Dual Interface Modes:** Terminal display view for bin hardware and scanner portal for user devices.

---

## Tech Stack & Dependencies
- **Language:** Python 3.x
- **Framework:** Streamlit
- **Database:** SQLite3
- **Libraries:** OpenCV (`opencv-python`), `qrcode`, `pillow`, `numpy`, `hashlib`

---

## System Setup & Execution Instructions

### 1. Clone Repository & Install Dependencies
```bash
git clone [https://github.com/YosefAl-Anesi/ecoscan-recycling-portal.git](https://github.com/YosefAl-Anesi/ecoscan-recycling-portal.git)
cd ecoscan-recycling-portal
pip install -r requirements.txt