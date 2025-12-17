import streamlit as st
import pandas as pd
import requests
import datetime as dt
from datetime import date, datetime
import time
import smtplib
import ssl
import random
import json
import os
from email.message import EmailMessage

# --- 1. ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 📂 ΣΥΣΤΗΜΑ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ (JSON FILES)
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "messages": "messages.json"
}

# Helper: Ημερομηνίες σε String
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

# 1. LOAD DATA
def load_data(key, default_val):
    filename = FILES[key]
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Μετατροπή string dates σε objects
                if key in ['history', 'expenses', 'messages']:
                    for item in data:
                        if 'date' in item and item['date']:
                            try:
                                item['date'] = date.fromisoformat(item['date'])
                            except:
                                pass
                return data
        except:
            return default_val
    return default_val

# 2. SAVE DATA
def save_data(key, data):
    filename = FILES[key]
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=json_serial, indent=4, ensure_ascii=False)

# ==============================================================================
# 🎨 UI & DESIGN
# ==============================================================================
def local_css():
    st.markdown("""
    <style>
        .stApp { background-image: linear-gradient(to bottom right, #ebf7eb, #e3f2fd); }
        [data-testid="stSidebar"] { background-image: linear-gradient(180deg, #f1f8e9, #ffffff); border-right: 1px solid #c8e6c9; }
        .stButton>button { color: white; background-color: #2e7d32; border-radius: 12px; border: none; transition: 0.3s; }
        .stButton>button:hover { background-color: #1b5e20; transform: scale(1.02); }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { background-color: #ffffff; border-radius: 8px; border: 1px solid #a5d6a7; }
        
        /* Visible Header for Mobile Menu */
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 👤 INITIALIZATION
# ==============================================================================
default_users = {
    "GiannisKrv": {
        "password": "21041414", 
        "role": "owner", 
        "name": "Γιάννης", 
        "email": "johnkrv1@gmail.com",
        "phone": "6912345678"
    }
}

# Φόρτωση χρηστών (Αν δεν υπάρχει αρχείο, δημιουργείται)
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data("users", default_users)
    if "GiannisKrv" not in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"] = default_users["GiannisKrv"]
        save_data("users", st.session_state.users_db)

# Init variables
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'current_username' not in st.session_state: st.session_state.current_username = None
if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None

# ==============================================================================
# 📧 EMAIL
# ==============================================================================
EMAIL_SENDER = "johnkrv1@gmail.com"
EMAIL_PASSWORD = "kcsq wuoi wnik xzko"

def send_email_notification(receiver_email, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except:
        return False

def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# ==============================================================================
# 🔐 AUTH LOGIC
# ==============================================================================

def perform_login(username, password):
    # Reload fresh data
    users = load_data("users", default_users)
    if username in users:
        if users[username]['password'] == password:
            st.session_state.users_db = users
            st.session_state.authenticated = True
            st.session_state.current_user = users[username]
            st.session_state.current_username = username
            st.success(f"Καλωσήρθες {users[username]['name']}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Λάθος κωδικός.")
    else:
        st.error("Ο χρήστης δεν βρέθηκε.")

def perform_logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_username = None
    st.rerun()

# ==================================================
# 🖥️ LOGIN / REGISTER SCREEN
# ==================================================
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🔐 AgroManager Pro</h1>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        
        # --- RESET PASSWORD ---
        if st.session_state.reset_mode:
            st.warning("🔄 Ανάκτηση Κωδικού")
            if st.session_state.reset_step == 1:
                email_in = st.text_input("Email:")
                if st.button("Αποστολή Κωδικού"):
                    users = load_data("users", default_users)
                    found = False
                    for u, d in users.items():
                        if d.get('email') == email_in:
                            otp = str(random.randint(100000, 999999))
                            st.session_state.reset_otp = otp
                            st.session_state.reset_username_target = u
                            st.session_state.reset_email_target = email_in
                            send_email_notification(email_in, "Reset Password", f"Code: {otp}")
                            st.session_state.reset_step = 2
                            st.toast("Εστάλη!")
                            found = True
                            time.sleep(1)
                            st.rerun()
                    if not found: st.error("Δεν βρέθηκε χρήστης.")
                if st.button("Πίσω"): 
                    st.session_state.reset_mode = False
                    st.rerun()
            
            elif st.session_state.reset_step == 2:
                code_in = st.text_input("Κωδικός (OTP):")
                new_pass = st.text_input("Νέος Κωδικός:", type="password")
                if st.button("Αλλαγή"):
                    if code_in == st.session_state.reset_otp and new_pass:
                        users = load_data("users", default_users)
                        tgt = st.session_state.reset_username_target
                        users[tgt]['password'] = new_pass
                        save_data("users", users)
                        st.success("Άλλαξε! Συνδεθείτε.")
                        st.session_state.reset_mode = False
                        st.session_state.reset_step = 1
                        time.sleep(2)
                        st.rerun()
                    else: st.error("Λάθος κωδικός.")

        # --- LOGIN / REGISTER ---
        else:
            tab_login, tab_reg = st.tabs(["🔑 Είσοδος", "📝 Εγγραφή"])
            
            # LOGIN FORM
            with tab_login:
                with st.form("login_frm"):
                    u_log = st.text_input("Username")
                    p_log = st.text_input("Password", type="password")
                    if st.form_submit_button("Είσοδος", use_container_width=True):
                        perform_login(u_log, p_log)
                st.markdown("---")
                if st.button("🆘 Ξέχασα τον κωδικό", use_container_width=True):
                    st.session_state.reset_mode = True
                    st.rerun()

            # REGISTER FORM (ΔΙΟΡΘΩΜΕΝΗ ΜΕ KEYS ΓΙΑ ΣΤΑΘΕΡΟΤΗΤΑ)
            with tab_reg:
                st.info("Νέος Λογαριασμός")
                with st.form("reg_final"):
                    # Προσθέτουμε keys για να μην χάνεται το input
                    r_user = st.text_input("Username *", key="reg_u")
                    r_pass = st.text_input("Password *", type="password", key="reg_p")
                    r_name = st.text_input("Ονοματεπώνυμο *", key="reg_n")
                    r_email = st.text_input("Email *", key="reg_e")
                    r_phone = st.text_input("Κινητό *", key="reg_ph")
                    
                    submitted = st.form_submit_button("Δημιουργία Λογαριασμού", use_container_width=True)
                    
                    if submitted:
                        if r_user and r_pass and r_name and r_email and r_phone:
                            # 1. Φόρτωση
                            current_users = load_data("users", default_users)
                            
                            # 2. Έλεγχος
                            if r_user in current_users:
                                st.warning("Το Username υπάρχει ήδη.")
                            else:
                                # 3. Εγγραφή
                                current_users[r_user] = {
                                    "password": r_pass,
                                    "role": "user",
                                    "name": r_name,
                                    "email": r_email,
                                    "phone": r_phone
                                }
                                # 4. Αποθήκευση
                                save_data("users", current_users)
                                send_email_notification(r_email, "Welcome", f"Γεια σου {r_name}, καλωσήρθες!")
                                st.success("✅ Ο λογαριασμός δημιουργήθηκε! Πηγαίνετε στην Είσοδο.")
                                time.sleep(2) # Περιμένουμε λίγο να το δει
                                st.rerun() # Refresh για να καθαρίσει
                        else:
                            st.error("⚠️ Παρακαλώ συμπληρώστε ΟΛΑ τα πεδία.")

else:
    # ==================================================
    # 📱 MAIN APP (LOGGED IN)
    # ==================================================
    
    # Load all data fresh on every reload
    st.session_state.history_log = load_data("history", [])
    st.session_state.expenses_log = load_data("expenses", [])
    st.session_state.support_messages = load_data("messages", [])
    
    # Refresh current user data from file (in case role changed)
    all_users = load_data("users", default_users)
    if st.session_state.current_username in all_users:
        st.session_state.current_user = all_users[st.session_state.current_username]
    
    user_data = st.session_state.current_user
    user_role = user_data['role']
    
    with st.sidebar:
        st.write(f"### 👤 {user_data['name']}")
        st.caption(f"Role: {user_role.upper()}")
        
        opts = ["📝 Έσοδα", "💸 Έξοδα", "🗂️ Οικονομικά", "☁️ Precision Ag", "👤 Προφίλ", "🆘 Support"]
        if user_role in ['owner', 'admin']: opts.append("📨 Μηνύματα")
        if user_role == 'owner': opts.append("👥 Users (Owner)")
        
        choice = st.radio("Menu", opts)
        st.divider()
        if st.button("🚪 Logout"): perform_logout()

    st.markdown("<h2 style='color:#1b5e20;'>🌱 AgroManager Pro</h2>", unsafe_allow_html=True)

    # 1. INCOME
    if choice == "📝 Έσοδα":
        st.header("Παραγωγή & Πωλήσεις")
        with st.form("inc_form"):
            col1, col2 = st.columns(2)
            name = col1.selectbox("Καλλιέργεια", ["Βαμβάκι", "Σιτάρι", "Καλαμπόκι", "Ελιά", "Άλλο"])
            qty = col2.number_input("Ποσότητα (kg)", step=10)
            price = st.number_input("Τιμή (€/kg)", step=0.01)
            date_rec = st.date_input("Ημερομηνία", date.today())
            
            if st.form_submit_button("💾 Αποθήκευση"):
                entry = {
                    "user": st.session_state.current_username,
                    "date": date_rec, "year": date_rec.year,
                    "type": "income", "name": name, "quantity": qty, 
                    "price": price, "revenue": qty*price
                }
                st.session_state.history_log.append(entry)
                save_data("history", st.session_state.history_log)
                st.success("Αποθηκεύτηκε!")

    # 2. EXPENSES
    elif choice == "💸 Έξοδα":
        st.header("Διαχείριση Εξόδων")
        with st.form("exp_form"):
            cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο", "Εργατικά", "Άλλο"])
            amount = st.number_input("Ποσό (€)", step=1.0)
            date_exp = st.date_input("Ημερομηνία", date.today())
            desc = st.text_input("Περιγραφή")
            
            if st.form_submit_button("💾 Καταχώρηση"):
                entry = {
                    "user": st.session_state.current_username,
                    "date": date_exp, "year": date_exp.year,
                    "type": "expense", "category": cat, "description": desc,
                    "amount_total": amount
                }
                st.session_state.expenses_log.append(entry)
                save_data("expenses", st.session_state.expenses_log)
                st.success("Αποθηκεύτηκε!")

    # 3. FINANCE
    elif choice == "🗂️ Οικονομικά":
        st.header("Οικονομική Εικόνα")
        df_i = pd.DataFrame(st.session_state.history_log)
        df_e = pd.DataFrame(st.session_state.expenses_log)
        
        rev = df_i['revenue'].sum() if not df_i.empty else 0
        exp = df_e['amount_total'].sum() if not df_e.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Έσοδα", f"{rev:.2f}€")
        c2.metric("Έξοδα", f"{exp:.2f}€")
        c3.metric("Κέρδος", f"{rev-exp:.2f}€")
        
        t1, t2 = st.tabs(["Αναλυτικά Έσοδα", "Αναλυτικά Έξοδα"])
        with t1: st.dataframe(df_i, use_container_width=True)
        with t2: st.dataframe(df_e, use_container_width=True)

    # 4. PRECISION AG
    elif choice == "☁️ Precision Ag":
        st.header("Precision Agriculture Tools")
        
        st.subheader("🧬 GDD Calculator")
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            crop_sel = col_a.selectbox("Καλλιέργεια", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "Custom"])
            
            t_base = 10.0
            if crop_sel == "Βαμβάκι": t_base = 15.6
            elif crop_sel == "Custom": t_base = col_b.number_input("Tbase (°C)", 10.0)
            
            t_max = st.number_input("Max Temp Today (°C)", 25.0)
            t_min = st.number_input("Min Temp Today (°C)", 15.0)
            
            gdd = ((t_max + t_min)/2) - t_base
            st.info(f"GDD: {max(0, gdd):.1f}")

        st.divider()
        st.subheader("🧪 VRT Fertilizer")
        with st.container(border=True):
            col_vrt1, col_vrt2 = st.columns(2)
            crop_f = col_vrt1.selectbox("Καλλιέργεια (VRT)", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "Custom"], key="vrt_c")
            
            units = 4.5
            if crop_f == "Καλαμπόκι": units = 2.5
            elif crop_f == "Σιτάρι": units = 3.0
            elif crop_f == "Custom": units = st.number_input("N units/100kg", 3.0)
            
            target = st.number_input("Στόχος (kg/στρ)", 400)
            fert = st.selectbox("Λίπασμα", ["Ουρία (46)", "Νιτρική (34.5)", "Θειική (21)", "NPK (20)", "Custom"])
            
            n_perc = 0.46
            if "34.5" in fert: n_perc = 0.345
            elif "21" in fert: n_perc = 0.21
            elif "20" in fert: n_perc = 0.20
            elif "Custom" in fert: n_perc = st.number_input("N %", 20.0)/100
            
            req = (target / 100) * units
            dose = (req / n_perc) / 0.8 if n_perc > 0 else 0
            st.success(f"Δόση: {dose:.1f} kg/στρ")

    # 5. PROFILE
    elif choice == "👤 Προφίλ":
        st.header("Επεξεργασία Προφίλ")
        with st.form("prof_upd"):
            nn = st.text_input("Όνομα", user_data['name'])
            ne = st.text_input("Email", user_data.get('email',''))
            np_ph = st.text_input("Τηλέφωνο", user_data.get('phone',''))
            np_pass = st.text_input("Νέος Κωδικός (προαιρετικό)", type="password")
            
            if st.form_submit_button("Αποθήκευση"):
                users = load_data("users", default_users)
                u = st.session_state.current_username
                users[u]['name'] = nn
                users[u]['email'] = ne
                users[u]['phone'] = np_ph
                if np_pass: users[u]['password'] = np_pass
                
                save_data("users", users)
                st.success("Ενημερώθηκε!")
                time.sleep(1)
                st.rerun()

    # 6. SUPPORT
    elif choice == "🆘 Support":
        st.header("Support")
        with st.form("supp_frm"):
            subj = st.text_input("Θέμα")
            msg = st.text_area("Μήνυμα")
            if st.form_submit_button("Αποστολή"):
                st.session_state.support_messages.append({
                    "user": user_data['name'], "email": user_data.get('email'),
                    "subject": subj, "message": msg, "date": str(date.today())
                })
                save_data("messages", st.session_state.support_messages)
                send_email_notification("johnkrv1@gmail.com", f"Support: {subj}", msg)
                st.success("Εστάλη!")

    # 7. INBOX (ADMIN/OWNER)
    elif choice == "📨 Μηνύματα":
        st.header("Εισερχόμενα")
        msgs = load_data("messages", [])
        st.dataframe(pd.DataFrame(msgs))

    # 8. USER MANAGEMENT (OWNER)
    elif choice == "👥 Users (Owner)":
        # FRESH LOAD FOR OWNER
        current_users_list = load_data("users", default_users)
        
        st.header("Διαχείριση Χρηστών")
        st.write("Real-time λίστα χρηστών.")
        
        user_rows = []
        for uname, udata in current_users_list.items():
            user_rows.append({
                "Username": uname,
                "Name": udata['name'],
                "Email": udata.get('email', '-'),
                "Phone": udata.get('phone', '-'),
                "Role": udata['role']
            })
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True)
        
        st.divider()
        st.subheader("✏️ Αλλαγή Ρόλων")
        
        col1, col2, col3 = st.columns(3)
        target_u = col1.selectbox("Επιλογή Χρήστη", list(current_users_list.keys()))
        new_role = col2.selectbox("Νέος Ρόλος", ["user", "admin"])
        
        if col3.button("Ενημέρωση Ρόλου"):
            if target_u == "GiannisKrv":
                st.error("Δεν μπορείτε να αλλάξετε τον Owner.")
            else:
                current_users_list[target_u]['role'] = new_role
                save_data("users", current_users_list)
                st.success(f"Ο χρήστης {target_u} έγινε {new_role}!")
                time.sleep(1)
                st.rerun()
