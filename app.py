import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from datetime import date, datetime, timedelta
import time
import json
import os
from fpdf import FPDF
import smtplib
import ssl
import random
import base64
from email.message import EmailMessage

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 📧 ΡΥΘΜΙΣΕΙΣ EMAIL
# ==============================================================================
EMAIL_SENDER = "johnkrv1@gmail.com"
EMAIL_PASSWORD = "bcgb tdmn sjwe ajnt"

def send_email(receiver, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

# ==============================================================================
# 💾 DATABASE SYSTEM (PERSISTENT STORAGE)
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "inventory": "inventory.json",
    "machinery": "machinery.json",
    "calendar": "calendar.json",
    "messages": "messages.json"
}

# ΑΓΡΟΝΟΜΙΚΗ ΒΑΣΗ
CROP_STANDARDS = {
    "Σιτάρι (Χειμερινό)": {"tbase": 0.0, "target_gdd": 2100},
    "Βαμβάκι": {"tbase": 15.6, "target_gdd": 2200},
    "Καλαμπόκι (FAO 700)": {"tbase": 10.0, "target_gdd": 1700},
    "Καλαμπόκι (FAO 400)": {"tbase": 10.0, "target_gdd": 1400},
    "Βιομηχανική Τομάτα": {"tbase": 10.0, "target_gdd": 1450},
    "Μηδική": {"tbase": 5.0, "target_gdd": 450},
    "Ηλίανθος": {"tbase": 6.0, "target_gdd": 1600},
    "Custom": {"tbase": 10.0, "target_gdd": 2000}
}

def date_handler(obj):
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    return obj

def load_data():
    # 1. Φόρτωση Χρηστών
    if os.path.exists(FILES["users"]):
        try:
            with open(FILES["users"], 'r', encoding='utf-8') as f:
                st.session_state.users_db = json.load(f)
        except:
            st.session_state.users_db = {}
    else:
        st.session_state.users_db = {}

    # --- EMERGENCY FIX: FORCE PASSWORD UPDATE ---
    # Αυτό το κομμάτι τρέχει ΠΑΝΤΑ και διορθώνει τον κωδικό σου
    # ακόμα και αν έχει αποθηκευτεί λάθος στο παρελθόν.
    
    # Αν δεν υπάρχει, τον φτιάχνουμε
    if "GiannisKrv" not in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"] = {
            "name": "Γιάννης", 
            "email": "johnkrv1@gmail.com", 
            "phone": ""
        }
    
    # ΚΑΡΦΩΤΗ ΑΝΑΝΕΩΣΗ ΚΩΔΙΚΟΥ ΚΑΙ ΡΟΛΟΥ
    st.session_state.users_db["GiannisKrv"]["password"] = "21041414"
    st.session_state.users_db["GiannisKrv"]["role"] = "owner"
    
    # Σώζουμε αμέσως την αλλαγή
    save_data("users")

    # 3. Φόρτωση ΟΛΩΝ των άλλων αρχείων
    for key, file_path in FILES.items():
        if key == "users": continue
        
        state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
            
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for d in data:
                            if 'date' in d and isinstance(d['date'], str):
                                try: d['date'] = datetime.strptime(d['date'][:10], "%Y-%m-%d").date()
                                except: pass
                    st.session_state[state_key] = data
            except:
                st.session_state[state_key] = []
        else:
            st.session_state[state_key] = []

def save_data(key):
    target_file = FILES.get(key)
    
    if key == "users":
        data_to_save = st.session_state.users_db
    elif key in ["history", "expenses"]:
        data_to_save = st.session_state.get(f"{key}_log", [])
    else:
        data_to_save = st.session_state.get(f"{key}_db", [])
        
    if target_file:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, default=date_handler, indent=4, ensure_ascii=False)

def image_to_base64(uploaded_file):
    if uploaded_file is None: return None
    try: return base64.b64encode(uploaded_file.getvalue()).decode()
    except: return None

# ==============================================================================
# 🎨 UI & CSS (ΜΕ ΚΡΥΦΟ MANAGE APP)
# ==============================================================================

hide_dev_style = ""
if st.session_state.get('current_username') != "GiannisKrv":
    hide_dev_style = """
        <style>
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;} 
            header {visibility: hidden;} 
            .stDeployButton {display:none;} 
        </style>
    """

st.markdown(hide_dev_style, unsafe_allow_html=True)

st.markdown("""
<style>
    /* Dynamic Background */
    .stApp {
        background: linear-gradient(-45deg, #f1f8e9, #dcedc8, #fffde7, #e3f2fd);
        background-size: 400% 400%;
        animation: agroAnim 25s ease infinite;
    }
    @keyframes agroAnim {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    div[data-testid="stSidebar"] {
        background-color: rgba(240, 242, 246, 0.85) !important;
        border-right: 1px solid rgba(209, 213, 219, 0.5);
        backdrop-filter: blur(8px);
    }
    .stButton>button { border-radius: 12px; font-weight: 600; transition: 0.3s; border: 1px solid #e0e0e0; }
    .stButton>button:hover { transform: scale(1.02); border-color: #2e7d32; color: #2e7d32; }
    button[kind="primary"] { background-color: #2e7d32 !important; border: none !important; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #1b5e20; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-weight: bold; color: #555; }
    div[data-testid="stExpander"] { 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.08); 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        margin-bottom: 12px;
        border: none !important;
    }
    div[data-testid="stExpander"] details summary p { font-weight: bold; font-size: 1.1rem; color: #2e7d32; }
    h1, h2, h3 { color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 👤 AUTH & SESSION
# ==============================================================================
if 'data_loaded' not in st.session_state: load_data(); st.session_state.data_loaded = True
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'weather_data' not in st.session_state: st.session_state.weather_data = None
if 'weather_loc_name' not in st.session_state: st.session_state.weather_loc_name = ""
if 'current_username' not in st.session_state: st.session_state.current_username = None
if 'active_page' not in st.session_state: st.session_state.active_page = "Dashboard"

if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1 
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None
if 'reset_email_target' not in st.session_state: st.session_state.reset_email_target = None
if 'reset_username_target' not in st.session_state: st.session_state.reset_username_target = None

def login_user(username, password):
    # Επαναφόρτωση για να είμαστε σίγουροι ότι βλέπουμε την τελευταία έκδοση
    if username == "GiannisKrv" and password == "21041414":
        st.session_state.authenticated = True
        st.session_state.current_user = st.session_state.users_db["GiannisKrv"]
        st.session_state.current_username = username
        st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
        time.sleep(0.5)
        st.rerun()
    elif username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.session_state.current_username = username
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(0.5)
            st.rerun()
        else: st.error("Λάθος κωδικός.")
    else: st.error("Ο χρήστης δεν βρέθηκε.")

def register_user(new_user, new_pass, new_name, new_email, new_phone):
    if new_user in st.session_state.users_db: st.warning("Το όνομα χρήστη υπάρχει ήδη.")
    else:
        st.session_state.users_db[new_user] = {"password": new_pass, "role": "user", "name": new_name, "email": new_email, "phone": new_phone}
        save_data("users")
        send_email(new_email, "🌱 Καλωσήρθες στο AgroManager Pro", f"Γεια σου {new_name},\n\nΟ λογαριασμός σου δημιουργήθηκε!\nUsername: {new_user}\nPassword: {new_pass}")
        send_email(EMAIL_SENDER, "🔔 Νέα Εγγραφή Χρήστη", f"Νέος χρήστης:\nΌνομα: {new_name}\nUsername: {new_user}\nEmail: {new_email}")
        st.success("Ο λογαριασμός δημιουργήθηκε! Εστάλη email επιβεβαίωσης.")

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_username = None
    st.rerun()

# ==================================================
# 🔐 LOGIN SCREEN
# ==================================================
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: grey;'>Η έξυπνη πλατφόρμα διαχείρισης</p>", unsafe_allow_html=True)
            st.divider()

            if st.session_state.reset_mode:
                st.markdown("### 🔄 Ανάκτηση Κωδικού")
                if st.session_state.reset_step == 1:
                    st.info("Συμπληρώστε τα στοιχεία ταυτοποίησης.")
                    r_user = st.text_input("Username")
                    r_name = st.text_input("Ονοματεπώνυμο")
                    r_email = st.text_input("Email")
                    r_phone = st.text_input("Τηλέφωνο")
                    col_r1, col_r2 = st.columns(2)
                    if col_r1.button("📩 Αποστολή Κωδικού", use_container_width=True, type="primary"):
                        found = False
                        if r_user in st.session_state.users_db:
                            u_data = st.session_state.users_db[r_user]
                            if (u_data['name'] == r_name and u_data['email'] == r_email and u_data.get('phone') == r_phone):
                                found = True
                                otp = str(random.randint(100000, 999999))
                                st.session_state.reset_otp = otp
                                st.session_state.reset_email_target = r_email
                                st.session_state.reset_username_target = r_user
                                if send_email(r_email, "🔑 Κωδικός Επαναφοράς", f"Κωδικός: {otp}"):
                                    st.session_state.reset_step = 2; st.toast("Εστάλη!", icon="📧"); time.sleep(1); st.rerun()
                                else: st.error("Σφάλμα Email.")
                        if not found: st.error("Λάθος στοιχεία.")
                    if col_r2.button("Πίσω", use_container_width=True): st.session_state.reset_mode = False; st.rerun()
                elif st.session_state.reset_step == 2:
                    st.success("Κωδικός εστάλη στο email σας.")
                    code_input = st.text_input("6ψήφιος κωδικός OTP:")
                    new_password = st.text_input("Νέος Κωδικός:", type="password")
                    if st.button("💾 Αποθήκευση", use_container_width=True, type="primary"):
                        if code_input == st.session_state.reset_otp:
                            st.session_state.users_db[st.session_state.reset_username_target]['password'] = new_password
                            save_data("users")
                            st.success("Ο κωδικός άλλαξε!")
                            st.session_state.reset_mode = False; st.session_state.reset_step = 1; time.sleep(2); st.rerun()
                        else: st.error("Λάθος OTP.")
            else:
                tab_login, tab_register = st.tabs(["🔑 Σύνδεση", "📝 Εγγραφή"])
                with tab_login:
                    username = st.text_input("Username", key="login_user")
                    password = st.text_input("Password", type="password", key="login_pass")
                    if st.button("🚀 Είσοδος", use_container_width=True, type="primary"): login_user(username, password)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🆘 Ξέχασα τον κωδικό μου", type="secondary", use_container_width=True): st.session_state.reset_mode = True; st.rerun()
                with tab_register:
                    new_user = st.text_input("Username", key="reg_user")
                    new_pass = st.text_input("Password", type="password", key="reg_pass")
                    new_name = st.text_input("Όνομα", key="reg_name")
                    new_email = st.text_input("Email", key="reg_email")
                    new_phone = st.text_input("Τηλέφωνο", key="reg_phone")
                    if st.button("✅ Δημιουργία Λογαριασμού", use_container_width=True, type="primary"):
                        if new_user and new_pass and new_name and new_email and new_phone:
                            with st.spinner("Δημιουργία..."): register_user(new_user, new_pass, new_name, new_email, new_phone)
                        else: st.error("Συμπληρώστε όλα τα πεδία.")

else:
    # ==================================================
    # 📱 MAIN APP (LOGGED IN)
    # ==================================================
    current_role = st.session_state.current_user.get('role', 'user')
    is_owner = (current_role == 'owner')
    is_admin = (current_role == 'admin')

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/606/606676.png", width=80) 
        st.markdown(f"## 👤 {st.session_state.current_user['name']}")
        
        if is_owner: st.warning("🔒 OWNER ACCOUNT")
        elif is_admin: st.info("🛡️ ADMIN ACCOUNT")
        else: st.success("🌾 MEMBER ACCOUNT")
        
        st.divider()

        with st.expander("🚜 Διαχείριση & Οργάνωση", expanded=True):
            opt_mng = option_menu(None, ["Dashboard", "Οικονομικά", "Αποθήκη", "Μηχανήματα", "Ημερολόγιο"], 
                icons=["speedometer2", "wallet2", "box-seam", "truck", "calendar-check"], default_index=0, key="nav_mng")

        with st.expander("🌦️ Γεωργία & Καιρός", expanded=True):
            opt_agro = option_menu(None, ["Καιρός", "GDD & Ανάπτυξη"], 
                icons=["cloud-sun", "graph-up-arrow"], default_index=0, key="nav_agro")

        with st.expander("⚙️ Γενικά & Προφίλ", expanded=True):
            gen_options = ["Μηνύματα", "Βοήθεια", "Το Προφίλ μου"]
            gen_icons = ["chat-text", "life-preserver", "person-circle"]
            if is_owner or is_admin:
                gen_options.append("Διαχείριση Χρηστών")
                gen_icons.append("people-fill")
            gen_options.append("Logout")
            gen_icons.append("box-arrow-right")
            opt_gen = option_menu(None, gen_options, icons=gen_icons, default_index=0, key="nav_gen")

    if 'prev_nav_mng' not in st.session_state: st.session_state.prev_nav_mng = opt_mng
    if 'prev_nav_agro' not in st.session_state: st.session_state.prev_nav_agro = opt_agro
    if 'prev_nav_gen' not in st.session_state: st.session_state.prev_nav_gen = opt_gen

    if opt_mng != st.session_state.prev_nav_mng:
        st.session_state.active_page = opt_mng
        st.session_state.prev_nav_mng = opt_mng
    elif opt_agro != st.session_state.prev_nav_agro:
        st.session_state.active_page = opt_agro
        st.session_state.prev_nav_agro = opt_agro
    elif opt_gen != st.session_state.prev_nav_gen:
        st.session_state.active_page = opt_gen
        st.session_state.prev_nav_gen = opt_gen

    selected = st.session_state.active_page

    # ==================================================
    # 📄 CONTENT RENDERER
    # ==================================================

    if selected == "Dashboard":
        st.title("📊 Επισκόπηση & Στατιστικά")
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        rev = df_inc['revenue'].sum() if not df_inc.empty else 0
        exp = df_exp['amount_total'].sum() if not df_exp.empty else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            with st.container(border=True): st.metric("💰 Ταμείο", f"{rev - exp:.2f} €")
        with c2:
            with st.container(border=True): st.metric("📈 Έσοδα", f"{rev:.2f} €", delta="Σύνολο")
        with c3:
            with st.container(border=True): st.metric("💸 Έξοδα", f"{exp:.2f} €", delta="Σύνολο", delta_color="inverse")
        with c4:
            tasks = st.session_state.calendar_db
            pending = len([t for t in tasks if not t.get('done', False)])
            with st.container(border=True): st.metric("📅 Εκκρεμότητες", f"{pending}", delta="Εργασίες")
        st.divider()
        if not df_inc.empty:
            df_inc['year'] = pd.to_datetime(df_inc['date']).dt.year
            yearly_inc = df_inc.groupby('year')['revenue'].sum().reset_index()
            fig = px.bar(yearly_inc, x='year', y='revenue', title="Έσοδα ανά Έτος", color='revenue', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

    elif selected == "Οικονομικά":
        st.title("📝 Διαχείριση Οικονομικών")
        t1, t2, t3 = st.tabs(["💵 Έσοδα", "💸 Έξοδα", "🖨️ Export"])
        with t1:
            with st.expander("➕ Νέα Καταγραφή", expanded=True):
                with st.form("inc_form"):
                    c1, c2 = st.columns(2)
                    name = c1.selectbox("Καλλιέργεια", ["Βαμβάκι", "Σιτάρι", "Καλαμπόκι", "Ελιά"])
                    qty = c2.number_input("Ποσότητα (kg)", 0.0)
                    price = st.number_input("Τιμή (€/kg)", 0.0)
                    if st.form_submit_button("💾 Αποθήκευση"):
                        st.session_state.history_log.append({"date": date.today(), "type": "income", "name": name, "quantity": qty, "price": price, "revenue": qty*price})
                        save_data("history"); st.success("ΟΚ!"); st.rerun()
        with t2:
            with st.expander("➕ Νέο Έξοδο", expanded=True):
                with st.form("exp_form"):
                    cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο"])
                    amount = st.number_input("Ποσό (€)", 0.0)
                    desc = st.text_input("Περιγραφή")
                    if st.form_submit_button("💾 Αποθήκευση"):
                        st.session_state.expenses_log.append({"date": date.today(), "type": "expense", "category": cat, "description": desc, "amount_total": amount})
                        save_data("expenses"); st.success("ΟΚ!"); st.rerun()
        with t3:
            c1,c2 = st.columns(2)
            if st.session_state.history_log: c1.download_button("📥 Λήψη CSV Εσόδων", pd.DataFrame(st.session_state.history_log).to_csv(index=False), "in.csv")
            if st.session_state.expenses_log: c2.download_button("📥 Λήψη CSV Εξόδων", pd.DataFrame(st.session_state.expenses_log).to_csv(index=False), "out.csv")

    elif selected == "Αποθήκη":
        st.title("📦 Αποθήκη")
        with st.expander("➕ Διαχείριση Stock", expanded=True):
            with st.form("stock_form"):
                item = st.text_input("Προϊόν")
                qty = st.number_input("Ποσότητα", step=1.0)
                if st.form_submit_button("💾 Ενημέρωση"):
                    st.session_state.inventory_db.append({"item": item, "quantity": qty})
                    save_data("inventory"); st.success("ΟΚ!"); st.rerun()
        if st.session_state.inventory_db: st.dataframe(pd.DataFrame(st.session_state.inventory_db), use_container_width=True)

    elif selected == "Μηχανήματα":
        st.title("🚜 Στόλος")
        with st.expander("➕ Νέο Μηχάνημα", expanded=True):
            with st.form("mach_form"):
                m_name = st.text_input("Όνομα")
                m_hours = st.number_input("Ώρες", 0)
                if st.form_submit_button("💾 Προσθήκη"):
                    st.session_state.machinery_db.append({"name": m_name, "hours": m_hours})
                    save_data("machinery"); st.rerun()
        if st.session_state.machinery_db: st.dataframe(pd.DataFrame(st.session_state.machinery_db), use_container_width=True)

    elif selected == "Ημερολόγιο":
        st.title("📅 Εργασίες")
        with st.form("task_form"):
            c1, c2 = st.columns([3, 1])
            tt = c1.text_input("Τίτλος")
            td = c2.date_input("Ημερομηνία")
            if st.form_submit_button("➕ Προσθήκη Εργασίας"):
                st.session_state.calendar_db.append({"title": tt, "date": td, "done": False})
                save_data("calendar"); st.rerun()
        st.write("---")
        for i, t in enumerate(st.session_state.calendar_db):
            c1, c2 = st.columns([0.1, 0.9])
            done = c1.checkbox("", t.get('done', False), key=f"t_{i}")
            if done != t.get('done', False): t['done'] = done; save_data("calendar"); st.rerun()
            c2.write(f"~~{t['title']}~~" if done else f"**{t['title']}**")

    # --- ΚΑΙΡΟΣ ---
    elif selected == "Καιρός":
        st.title("🌦️ Καιρός & Πρόγνωση")
        mode = st.radio("Τοποθεσία:", ["🔍 Πόλη", "📍 Συντεταγμένες"], horizontal=True)
        lat, lon = 39.6390, 22.4191
        display_name = "Λάρισα"
        if mode == "🔍 Πόλη":
            sc = st.text_input("Πόλη (π.χ. Λάρισα)")
            if sc:
                try:
                    r = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={sc}&count=1&language=el&format=json").json()
                    if "results" in r:
                        lat, lon = r['results'][0]['latitude'], r['results'][0]['longitude']
                        display_name = r['results'][0]['name']
                except: pass
        else:
            c1, c2 = st.columns(2)
            lat = c1.number_input("Lat", 39.6390)
            lon = c2.number_input("Lon", 22.4191)

        if st.button("🔄 Λήψη Καιρού", type="primary"):
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
                st.session_state.weather_data = requests.get(url).json()
                st.session_state.weather_loc_name = display_name
                st.rerun()
            except: st.error("Σφάλμα σύνδεσης.")

        if st.session_state.weather_data:
            d = st.session_state.weather_data
            curr = d.get('current', {})
            st.success(f"📍 {st.session_state.weather_loc_name}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Θερμοκρασία", f"{curr.get('temperature_2m', '-')} °C")
            with c2: st.metric("Υγρασία", f"{curr.get('relative_humidity_2m', '-')} %")
            with c3: st.metric("Βροχή", f"{curr.get('precipitation', '-')} mm")
            with c4: st.metric("Άνεμος", f"{curr.get('wind_speed_10m', '-')} km/h")
            daily = d.get('daily', {})
            if daily:
                chart_df = pd.DataFrame({"Date": daily['time'], "Max Temp": daily['temperature_2m_max']})
                st.subheader("📈 Διάγραμμα Θερμοκρασίας")
                st.line_chart(chart_df.set_index("Date"))

    # --- GDD ---
    elif selected == "GDD & Ανάπτυξη":
        st.title("📈 Ανάπτυξη & Εργαλεία")
        
        if not st.session_state.weather_data:
            st.warning("⚠️ Πηγαίνετε στην καρτέλα 'Καιρός' και πατήστε 'Λήψη Καιρού' πρώτα!")
            if st.button("🔄 Λήψη Δεδομένων Καιρού Τώρα"):
                try:
                    url = "https://api.open-meteo.com/v1/forecast?latitude=39.6390&longitude=22.4191&daily=temperature_2m_max,temperature_2m_min&past_days=30&timezone=auto"
                    st.session_state.weather_data = requests.get(url).json()
                    st.session_state.weather_loc_name = "Λάρισα (Auto)"
                    st.rerun()
                except: st.error("Σφάλμα.")
        
        if st.session_state.weather_data:
            d = st.session_state.weather_data
            daily = d.get('daily', {})
            
            with st.container(border=True):
                st.subheader("🧬 Υπολογισμός GDD")
                c_crop, c_input = st.columns(2)
                selected_standard_key = c_crop.selectbox("Επιλέξτε Είδος", list(CROP_STANDARDS.keys()))
                crop_data = CROP_STANDARDS[selected_standard_key]
                final_crop_name = c_input.text_input("Ονομασία Αγροτεμαχίου", value=selected_standard_key)
                c_var, c_params = st.columns(2)
                variety_name = c_var.text_input("Ποικιλία", value="Standard")
                if "Custom" in selected_standard_key:
                    tbase = c_params.number_input("Tbase (°C)", value=10.0)
                    target_gdd = c_params.number_input("Στόχος GDD", value=2000)
                else:
                    tbase = crop_data['tbase']
                    target_gdd = crop_data['target_gdd']
                    c_params.info(f"⚙️ Tbase: **{tbase}°C** (Αυτόματο)")

                dates = daily['time']
                gdd_cum, acc = [], 0
                tmax_vals, tmin_vals, day_gdd_vals = [], [], []

                for i in range(len(dates)):
                    tmax = daily['temperature_2m_max'][i]
                    tmin = daily['temperature_2m_min'][i]
                    if tmax is not None and tmin is not None:
                        avg = (tmax + tmin) / 2
                        day_gdd = max(avg - tbase, 0)
                        acc += day_gdd
                        gdd_cum.append(acc)
                        tmax_vals.append(tmax)
                        tmin_vals.append(tmin)
                        day_gdd_vals.append(day_gdd)
                
                fig = px.area(pd.DataFrame({"Date": dates, "GDD": gdd_cum}), x='Date', y='GDD', title=f"Πρόοδος: {final_crop_name} ({variety_name})", color_discrete_sequence=['#2e7d32'])
                fig.add_hline(y=target_gdd, line_dash="dot", line_color="red", annotation_text="Στόχος")
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"Συνολικοί Βαθμοί: **{acc:.1f}**")

                st.subheader("📋 Αναλυτικός Πίνακας")
                df_table = pd.DataFrame({
                    "Ημερομηνία": dates,
                    "Max Temp (°C)": tmax_vals,
                    "Min Temp (°C)": tmin_vals,
                    "Ημερήσιο GDD": day_gdd_vals,
                    "Συνολικό GDD": gdd_cum
                })
                st.dataframe(df_table, use_container_width=True, hide_index=True)

            st.divider()
            
            with st.container(border=True):
                st.subheader("🧪 VRT Λίπανση")
                v1, v2 = st.columns(2)
                crop_sel = v2.selectbox("Είδος Καλλιέργειας", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "Άλλο (Custom)"])
                if crop_sel == "Άλλο (Custom)":
                    custom_crop = v2.text_input("Όνομα Καλλιέργειας", value="Πατάτα")
                    rem_coef = v2.number_input("Ανάγκες σε Άζωτο (Μονάδες/100kg)", 1.0, 10.0, 3.0)
                else:
                    if crop_sel == "Βαμβάκι": rem_coef = 4.5
                    elif crop_sel == "Καλαμπόκι": rem_coef = 3.0
                    else: rem_coef = 3.0
                vrt_variety = v2.text_input("Ποικιλία", key="vrt_var")
                yld = v2.number_input("Στόχος (kg/στρ)", 400)
                fert_options = ["Ουρία (46-0-0)", "Νιτρική (34.5-0-0)", "Θειική Αμμωνία (21-0-0)", "NPK (20-20-20)", "Άλλο (Custom)"]
                fert = v1.selectbox("Λίπασμα", fert_options)
                n_per = 0.0
                if fert == "Άλλο (Custom)":
                    custom_n = v1.number_input("Περιεκτικότητα Αζώτου (%)", min_value=1.0, max_value=100.0, value=26.0)
                    n_per = custom_n / 100.0
                else:
                    if "46" in fert: n_per = 0.46
                    elif "34.5" in fert: n_per = 0.345
                    elif "21" in fert: n_per = 0.21
                    elif "20" in fert: n_per = 0.20
                dose = ((yld/100)*rem_coef) / n_per / 0.8
                st.success(f"👉 Δόση: **{dose:.1f} kg/στρ**")

            st.divider()
            st.subheader("🛠️ Εξωτερικά Εργαλεία")
            st.link_button("🌐 EffiSpray.com", "https://www.effispray.com/el")
            with st.expander("📺 Προβολή"):
                components.iframe("https://www.effispray.com/el", height=600, scrolling=True)

    elif selected == "Μηνύματα":
        st.title("💬 Μηνύματα")
        if is_owner:
            tab_inbox, tab_sent, tab_global = st.tabs(["📥 Εισερχόμενα", "📤 Απεσταλμένα", "🌐 Global"])
        else:
            tab_inbox, tab_sent = st.tabs(["📥 Εισερχόμενα", "📤 Απεσταλμένα"])
        with st.expander("✉️ Νέο Μήνυμα"):
            with st.form("msg_form"):
                recipients = list(st.session_state.users_db.keys()) if (is_owner or is_admin) else ["Support"]
                if st.session_state.current_username in recipients: recipients.remove(st.session_state.current_username)
                to_user = st.selectbox("Προς:", recipients)
                subj = st.text_input("Θέμα")
                body = st.text_area("Μήνυμα")
                if st.form_submit_button("🚀 Αποστολή"):
                    st.session_state.messages_db.append({"from": st.session_state.current_username, "to": to_user, "subject": subj, "body": body, "timestamp": str(datetime.now())})
                    save_data("messages"); st.success("Εστάλη!"); st.rerun()
        my_inbox = [m for m in st.session_state.messages_db if m.get('to') == st.session_state.current_username or (m.get('to') == "Support" and (is_owner or is_admin))]
        my_sent = [m for m in st.session_state.messages_db if m.get('from') == st.session_state.current_username]
        with tab_inbox:
            for m in reversed(my_inbox):
                with st.container(border=True):
                    st.write(f"**Από:** {m.get('from')} | **Θέμα:** {m.get('subject')}")
                    with st.expander("Διαβάστε"):
                        st.write(m.get('body'))
                        if m.get('image'): st.image(base64.b64decode(m.get('image')))
        with tab_sent:
            for m in reversed(my_sent): st.info(f"Προς: {m.get('to')} | {m.get('body')}")
        if is_owner:
            with tab_global: st.dataframe(pd.DataFrame(st.session_state.messages_db))

    elif selected == "Βοήθεια":
        st.title("🆘 Help Desk")
        with st.form("help"):
            sub = st.text_input("Θέμα")
            desc = st.text_area("Περιγραφή")
            img = st.file_uploader("Φωτογραφία", type=['png','jpg'])
            if st.form_submit_button("🚀 Αποστολή"):
                img_str = image_to_base64(img)
                st.session_state.messages_db.append({"from": st.session_state.current_username, "to": "Support", "subject": f"[TICKET] {sub}", "body": desc, "image": img_str, "timestamp": str(datetime.now())})
                save_data("messages"); send_email(EMAIL_SENDER, "Ticket", f"{sub}\n{desc}"); st.success("OK")

    elif selected == "Το Προφίλ μου":
        st.title("👤 Προφίλ")
        curr_uname = st.session_state.current_username
        if curr_uname in st.session_state.users_db:
            curr_u = st.session_state.users_db[curr_uname]
            with st.form("prof"):
                c1, c2 = st.columns(2)
                new_name = c1.text_input("Ονοματεπώνυμο", value=curr_u.get('name', ''))
                new_email = c2.text_input("Email", value=curr_u.get('email', ''))
                new_phone = st.text_input("Τηλέφωνο", value=curr_u.get('phone', ''))
                st.markdown("---")
                new_pass = st.text_input("Νέος Κωδικός (αφήστε κενό αν δεν θέλετε αλλαγή)", type="password")
                if st.form_submit_button("💾 Αποθήκευση Αλλαγών"):
                    st.session_state.users_db[curr_uname]['name'] = new_name
                    st.session_state.users_db[curr_uname]['email'] = new_email
                    st.session_state.users_db[curr_uname]['phone'] = new_phone
                    if new_pass: st.session_state.users_db[curr_uname]['password'] = new_pass
                    save_data("users"); st.session_state.current_user = st.session_state.users_db[curr_uname]; st.success("Το προφίλ ενημερώθηκε επιτυχώς!"); time.sleep(1); st.rerun()
        else: st.error("Σφάλμα φόρτωσης προφίλ.")

    elif selected == "Διαχείριση Χρηστών":
        if current_role not in ['owner', 'admin']: st.error("⛔ Απαγορεύεται η πρόσβαση.")
        else:
            st.title("👥 Διαχείριση Χρηστών")
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 3, 2, 2, 2])
            c1.markdown("**Username**"); c2.markdown("**Όνομα**"); c3.markdown("**Email**"); c4.markdown("**Credentials**"); c5.markdown("**Role**"); c6.markdown("**Show/Hide**")
            st.divider()
            for uname, udata in st.session_state.users_db.items():
                c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 3, 2, 2, 2])
                c1.write(uname); c2.write(udata['name']); c3.write(udata['email'])
                key_vis = f"vis_{uname}"
                if key_vis not in st.session_state: st.session_state[key_vis] = False
                if st.session_state[key_vis]:
                    c4.warning(f"🔑: {udata['password']}"); c4.caption(f"📞: {udata.get('phone', '-')}"); icon = "🙈 Hide"
                else: c4.write("******"); icon = "👁️ Show"
                if c6.button(icon, key=f"btn_{uname}"): st.session_state[key_vis] = not st.session_state[key_vis]; st.rerun()
                u_role = udata.get('role', 'user')
                if is_owner:
                    if uname == "GiannisKrv": c5.success("OWNER")
                    else:
                        new_r = c5.selectbox("", ["user", "admin"], index=0 if u_role=="user" else 1, key=f"r_{uname}", label_visibility="collapsed")
                        if new_r != u_role: st.session_state.users_db[uname]['role'] = new_r; save_data("users"); st.rerun()
                else: c5.write(u_role.upper())
                st.markdown("---")

    elif selected == "Logout":
        logout()
