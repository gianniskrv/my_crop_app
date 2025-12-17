import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import date, datetime
import time
import smtplib
import ssl
import random
import json
import os
from email.message import EmailMessage

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 📂 FILE DATABASE SYSTEM (JSON) - Η ΚΑΡΔΙΑ ΤΟΥ ΣΥΓΧΡΟΝΙΣΜΟΥ
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "messages": "messages.json"
}

# Helper: Convert dates to string for JSON
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

# Helper: Load Data
def load_data(key, default_val):
    filename = FILES[key]
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Αν είναι λίστες (history, expenses), πρέπει να μετατρέψουμε τα strings πίσω σε dates
                if key in ['history', 'expenses']:
                    for item in data:
                        if 'date' in item:
                            try:
                                item['date'] = date.fromisoformat(item['date'])
                            except:
                                pass
                return data
        except:
            return default_val
    return default_val

# Helper: Save Data
def save_data(key, data):
    filename = FILES[key]
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, default=json_serial, indent=4, ensure_ascii=False)

# ==============================================================================
# 🎨 UI & DESIGN (CSS)
# ==============================================================================
def local_css():
    st.markdown("""
    <style>
        .stApp { background-image: linear-gradient(to bottom right, #ebf7eb, #e3f2fd); }
        [data-testid="stSidebar"] { background-image: linear-gradient(180deg, #f1f8e9, #ffffff); border-right: 1px solid #c8e6c9; }
        .stButton>button { color: white; background-color: #2e7d32; border-radius: 12px; border: none; transition: 0.3s; }
        .stButton>button:hover { background-color: #1b5e20; transform: scale(1.02); }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { background-color: #ffffff; border-radius: 8px; border: 1px solid #a5d6a7; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 👤 SESSION STATE INITIALIZATION (LOAD FROM DISK)
# ==============================================================================

# 1. USERS
default_users = {
    "GiannisKrv": {
        "password": "21041414", 
        "role": "owner", 
        "name": "Γιάννης", 
        "email": "johnkrv1@gmail.com",
        "phone": "6912345678"
    }
}
# Φορτώνουμε από το αρχείο, αν δεν υπάρχει παίρνουμε τα defaults
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data("users", default_users)
    # Διασφάλιση ότι ο Owner υπάρχει πάντα
    if "GiannisKrv" not in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"] = default_users["GiannisKrv"]
        save_data("users", st.session_state.users_db)

# 2. OTHER DATA
if 'history_log' not in st.session_state:
    st.session_state.history_log = load_data("history", [])

if 'expenses_log' not in st.session_state:
    st.session_state.expenses_log = load_data("expenses", [])

if 'support_messages' not in st.session_state:
    st.session_state.support_messages = load_data("messages", [])

# AUTH STATE
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'current_username' not in st.session_state: st.session_state.current_username = None

# RESET PASSWORD STATE
if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1 
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None
if 'reset_email_target' not in st.session_state: st.session_state.reset_email_target = None
if 'reset_username_target' not in st.session_state: st.session_state.reset_username_target = None

# ==============================================================================
# 📧 EMAIL FUNCTIONS
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
    except Exception as e:
        # st.error(f"Error sending email: {e}") 
        return False

# --- HELPER: CSV ---
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- AUTH FUNCTIONS ---
def login_user(username, password):
    # Επαναφόρτωση για να είμαστε σίγουροι ότι έχουμε τα τελευταία δεδομένα
    st.session_state.users_db = load_data("users", st.session_state.users_db)
    
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.session_state.current_username = username
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Λάθος κωδικός πρόσβασης.")
    else:
        st.error("Ο χρήστης δεν βρέθηκε.")

def register_user(new_user, new_pass, new_name, new_email, new_phone):
    # Επαναφόρτωση
    st.session_state.users_db = load_data("users", st.session_state.users_db)
    
    if new_user in st.session_state.users_db:
        st.warning("Το όνομα χρήστη υπάρχει ήδη.")
    else:
        st.session_state.users_db[new_user] = {
            "password": new_pass, 
            "role": "user", 
            "name": new_name, 
            "email": new_email,
            "phone": new_phone
        }
        # ΑΠΟΘΗΚΕΥΣΗ ΣΤΟ ΑΡΧΕΙΟ
        save_data("users", st.session_state.users_db)
        
        st.success("Επιτυχία! Ο λογαριασμός δημιουργήθηκε και αποθηκεύτηκε.")
        send_email_notification(new_email, "Καλωσήρισες στο AgroManager", f"Γεια σου {new_name},\nΟ λογαριασμός σου ενεργοποιήθηκε.")

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_username = None
    st.rerun()

# ==================================================
# 🔐 LOGIN SCREEN
# ==================================================
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🔐 AgroManager Pro</h1>", unsafe_allow_html=True)
    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    
    with col_login:
        if st.session_state.reset_mode:
            st.markdown("### 🔄 Ανάκτηση Κωδικού")
            if st.session_state.reset_step == 1:
                email_input = st.text_input("Εισάγετε το Email σας:")
                col_r1, col_r2 = st.columns(2)
                if col_r1.button("Αποστολή Κωδικού", use_container_width=True):
                    # Load fresh users
                    st.session_state.users_db = load_data("users", st.session_state.users_db)
                    found_user = None
                    for uname, udata in st.session_state.users_db.items():
                        if udata.get('email') == email_input:
                            found_user = uname
                            break
                    if found_user:
                        otp = str(random.randint(100000, 999999))
                        st.session_state.reset_otp = otp
                        st.session_state.reset_email_target = email_input
                        st.session_state.reset_username_target = found_user
                        sent = send_email_notification(email_input, "🔑 Κωδικός Επαναφοράς", f"Κωδικός: {otp}")
                        if sent:
                            st.session_state.reset_step = 2
                            st.toast("Ο κωδικός εστάλη!", icon="📧")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Πρόβλημα αποστολής email.")
                    else:
                        st.error("Δεν βρέθηκε χρήστης.")
                if col_r2.button("Πίσω", use_container_width=True):
                    st.session_state.reset_mode = False
                    st.rerun()
            elif st.session_state.reset_step == 2:
                st.write(f"Κωδικός εστάλη στο: **{st.session_state.reset_email_target}**")
                code_input = st.text_input("6ψήφιος κωδικός:")
                new_password = st.text_input("Νέος Κωδικός:", type="password")
                if st.button("💾 Αλλαγή", use_container_width=True):
                    if code_input == st.session_state.reset_otp:
                        if new_password:
                            uname = st.session_state.reset_username_target
                            st.session_state.users_db[uname]['password'] = new_password
                            # SAVE
                            save_data("users", st.session_state.users_db)
                            st.success("Επιτυχία!")
                            st.session_state.reset_mode = False
                            st.session_state.reset_step = 1
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("Δώστε κωδικό.")
                    else:
                        st.error("Λάθος κωδικός.")
                if st.button("Ακύρωση"):
                    st.session_state.reset_mode = False
                    st.session_state.reset_step = 1
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑 Σύνδεση", "📝 Εγγραφή"])
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submit_login = st.form_submit_button("Είσοδος", use_container_width=True)
                    if submit_login:
                        login_user(username, password)
                st.markdown("---")
                if st.button("🆘 Ξέχασα τον κωδικό μου", type="secondary", use_container_width=True):
                    st.session_state.reset_mode = True
                    st.rerun()
            with tab2:
                with st.form("register_form", clear_on_submit=False):
                    st.write("Δημιουργήστε νέο λογαριασμό:")
                    new_user = st.text_input("Επιθυμητό Username")
                    new_pass = st.text_input("Επιθυμητό Password", type="password")
                    new_name = st.text_input("Ονοματεπώνυμο")
                    new_email = st.text_input("Email")
                    new_phone = st.text_input("Κινητό Τηλέφωνο")
                    submit_register = st.form_submit_button("Δημιουργία Λογαριασμού", use_container_width=True)
                    if submit_register:
                        if new_user and new_pass and new_name and new_email and new_phone:
                            register_user(new_user, new_pass, new_name, new_email, new_phone)
                        else:
                            st.warning("Παρακαλώ συμπληρώστε ΟΛΑ τα πεδία.")

else:
    # ==================================================
    # 📱 APP MAIN
    # ==================================================
    with st.sidebar:
        user_role = st.session_state.current_user['role']
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        st.caption(f"Role: {user_role.upper()}")
        st.divider()
        menu_options = [
            "📝 Νέα Καταγραφή (Έσοδα)", "💸 Έξοδα & Ταμείο",          
            "🗂️ Βιβλιοθήκη & Οικονομικά", "☁️ Καιρός & Γεωργία Ακριβείας", 
            "👤 Το Προφίλ μου", "🆘 Βοήθεια & Υποστήριξη"
        ]
        if user_role in ['owner', 'admin']: menu_options.append("📨 Εισερχόμενα Μηνύματα")
        if user_role == 'owner': menu_options.append("👥 Διαχείριση Χρηστών")
        menu_choice = st.radio("Πλοήγηση", menu_options)
        st.divider()
        if st.button("🚪 Αποσύνδεση"): logout()

    # --- CROPS ---
    default_crops = [
        {"name": "Βαμβάκι", "category": "Βιομηχανικά"}, {"name": "Σιτάρι Σκληρό", "category": "Σιτηρά"},
        {"name": "Καλαμπόκι", "category": "Σιτηρά"}, {"name": "Ηλίανθος", "category": "Βιομηχανικά"},
        {"name": "Ελιά (Λαδοελιά)", "category": "Δέντρα"}, {"name": "Ελιά (Βρώσιμη)", "category": "Δέντρα"},
        {"name": "Πορτοκαλιά", "category": "Εσπεριδοειδή"}, {"name": "Ροδακινιά", "category": "Πυρηνόκαρπα"},
        {"name": "Τομάτα", "category": "Κηπευτικά"}, {"name": "Πατάτα", "category": "Κηπευτικά"},
        {"name": "Αμπέλι (Οινοποιήσιμο)", "category": "Αμπέλι"}
    ]

    st.markdown("<h1 style='color:#1b5e20;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)

    # 1. INCOME
    if menu_choice == "📝 Νέα Καταγραφή (Έσοδα)":
        st.header("Εισαγωγή Παραγωγής & Πωλήσεων")
        with st.container(border=True):
            crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
            selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
            current_name = selected_option if "➕" not in selected_option else ""
            current_category = ""
            if "➕" in selected_option:
                c1, c2 = st.columns(2)
                current_name = c1.text_input("Όνομα Καλλιέργειας")
                current_category = c2.text_input("Κατηγορία")
            else:
                for c in default_crops:
                    if c['name'] == selected_option:
                        current_category = c['category']
                        break
                st.info(f"Κατηγορία: **{current_category}**")

        st.divider()
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            rec_date = c1.date_input("Ημερομηνία", date.today())
            rec_variety = c2.text_input("Ποικιλία")
            st.write("💰 **Οικονομικά**")
            c3, c4, c5 = st.columns(3)
            rec_qty = c3.number_input("Ποσότητα (kg)", min_value=0, step=10)
            rec_moisture = c4.number_input("Υγρασία (%)", min_value=0.0, step=0.1)
            rec_price = c5.number_input("Τιμή (€/kg)", min_value=0.0, step=0.01)
            total_revenue = rec_qty * rec_price
            if total_revenue > 0: st.markdown(f"### 💵 Έσοδο: **{total_revenue:.2f} €**")
            notes = st.text_area("Σημειώσεις")
            if st.form_submit_button("💾 Αποθήκευση"):
                if current_name:
                    new_entry = {
                        "user": st.session_state.current_user['name'],
                        "date": rec_date, "year": rec_date.year, "type": "income",
                        "name": current_name, "category": current_category, "variety": rec_variety,
                        "quantity": rec_qty, "moisture": rec_moisture, "price": rec_price,
                        "revenue": total_revenue, "notes": notes
                    }
                    st.session_state.history_log.append(new_entry)
                    save_data("history", st.session_state.history_log) # SAVE
                    st.success("Αποθηκεύτηκε!")
                else:
                    st.error("Συμπλήρωσε όνομα.")

    # 2. EXPENSES
    elif menu_choice == "💸 Έξοδα & Ταμείο":
        st.header("💸 Διαχείριση Εξόδων")
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            exp_date = col1.date_input("Ημερομηνία", date.today())
            exp_cat = col2.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο", "Σπόροι", "Εργατικά", "Ρεύμα", "Μηχανήματα", "Άλλα"])
            desc = st.text_input("Περιγραφή")
            c1, c2, c3 = st.columns(3)
            amount_net = c1.number_input("Καθαρή Αξία (€)", min_value=0.0, step=1.0)
            vat_rate = c2.selectbox("ΦΠΑ (%)", [0, 6, 13, 24], index=2)
            amount_total = amount_net * (1 + vat_rate/100)
            c3.metric("Τελικό Ποσό", f"{amount_total:.2f} €")
            if st.form_submit_button("💾 Καταχώρηση"):
                if amount_net > 0:
                    entry = {
                        "user": st.session_state.current_user['name'],
                        "date": exp_date, "year": exp_date.year, "type": "expense",
                        "category": exp_cat, "description": desc,
                        "amount_net": amount_net, "vat_rate": vat_rate, "amount_total": amount_total
                    }
                    st.session_state.expenses_log.append(entry)
                    save_data("expenses", st.session_state.expenses_log) # SAVE
                    st.success("Καταχωρήθηκε!")
                else:
                    st.warning("Εισάγετε ποσό.")

    # 3. LIBRARY
    elif menu_choice == "🗂️ Βιβλιοθήκη & Οικονομικά":
        # RELOAD DATA to see updates from others
        st.session_state.history_log = load_data("history", [])
        st.session_state.expenses_log = load_data("expenses", [])
        
        st.header("🗂️ Οικονομική Εικόνα")
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        
        years = sorted(list(set(df_inc['year'].unique().tolist() + df_exp['year'].unique().tolist())), reverse=True)
        if not years:
            st.info("Δεν υπάρχουν δεδομένα.")
        else:
            sel_year = st.selectbox("Έτος", years)
            d_inc = df_inc[df_inc['year'] == sel_year] if not df_inc.empty else pd.DataFrame()
            d_exp = df_exp[df_exp['year'] == sel_year] if not df_exp.empty else pd.DataFrame()
            
            rev = d_inc['revenue'].sum() if not d_inc.empty else 0
            exp = d_exp['amount_total'].sum() if not d_exp.empty else 0
            profit = rev - exp
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Έσοδα", f"{rev:.2f}€")
            c2.metric("Έξοδα", f"{exp:.2f}€")
            c3.metric("Κέρδος", f"{profit:.2f}€", delta=f"{profit:.2f}€")
            
            t1, t2, t3 = st.tabs(["Έσοδα", "Έξοδα", "Export"])
            with t1: st.dataframe(d_inc, use_container_width=True)
            with t2: st.dataframe(d_exp, use_container_width=True)
            with t3:
                if not d_inc.empty: st.download_button("CSV Έσοδα", convert_df(d_inc), f"inc_{sel_year}.csv")
                if not d_exp.empty: st.download_button("CSV Έξοδα", convert_df(d_exp), f"exp_{sel_year}.csv")

    # 4. PRECISION AG
    elif menu_choice == "☁️ Καιρός & Γεωργία Ακριβείας":
        st.header("🌦️ Precision Agriculture")
        city = st.text_input("Περιοχή", "Larissa")
        if city:
            try:
                geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1").json()
                if "results" in geo:
                    lat, lon = geo['results'][0]['latitude'], geo['results'][0]['longitude']
                    w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation&daily=temperature_2m_max,temperature_2m_min").json()
                    curr = w['current']
                    daily = w['daily']
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Θερμοκρασία", f"{curr['temperature_2m']}°C")
                    c2.metric("Υγρασία", f"{curr['relative_humidity_2m']}%")
                    c3.metric("Βροχή", f"{curr['precipitation']}mm")
                    
                    st.divider()
                    st.subheader("🧬 GDD Calculator")
                    with st.container(border=True):
                        col_a, col_b = st.columns(2)
                        crop = col_a.selectbox("Καλλιέργεια", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "✏️ Custom"])
                        var = col_b.text_input("Ποικιλία")
                        
                        tbase = 10.0
                        if crop == "Βαμβάκι": tbase = 15.6
                        elif crop == "✏️ Custom": tbase = st.number_input("Tbase (°C)", 10.0)
                        
                        tavg = (daily['temperature_2m_max'][0] + daily['temperature_2m_min'][0]) / 2
                        gdd = max(0, tavg - tbase)
                        st.info(f"GDD Σήμερα: **{gdd:.1f}** (Tbase: {tbase})")

                    st.divider()
                    st.subheader("🧪 VRT Calculator")
                    with st.container(border=True):
                        target = st.number_input("Στόχος (kg/στρ)", 400)
                        fert = st.selectbox("Λίπασμα", ["Ουρία (46)", "Νιτρική (34.5)", "✏️ Custom"])
                        
                        units = 4.5 # Default Cotton
                        n_perc = 0.46
                        if fert == "Νιτρική (34.5)": n_perc = 0.345
                        elif fert == "✏️ Custom": n_perc = st.number_input("N %", 20.0)/100
                        
                        req = (target / 100) * units
                        dose = (req / n_perc) / 0.8 if n_perc > 0 else 0
                        st.success(f"Δόση: **{dose:.1f} kg/στρ**")

            except: st.error("Error fetching weather.")

    # 5. PROFILE
    elif menu_choice == "👤 Το Προφίλ μου":
        st.header("👤 Edit Profile")
        ud = st.session_state.current_user
        with st.form("prof"):
            nm = st.text_input("Όνομα", ud['name'])
            em = st.text_input("Email", ud.get('email',''))
            ph = st.text_input("Phone", ud.get('phone',''))
            pw = st.text_input("New Pass", type="password")
            if st.form_submit_button("Save"):
                un = st.session_state.current_username
                st.session_state.users_db[un]['name'] = nm
                st.session_state.users_db[un]['email'] = em
                st.session_state.users_db[un]['phone'] = ph
                if pw: st.session_state.users_db[un]['password'] = pw
                
                save_data("users", st.session_state.users_db) # SAVE
                st.session_state.current_user = st.session_state.users_db[un]
                st.success("Updated!")
                st.rerun()

    # 6. SUPPORT
    elif menu_choice == "🆘 Βοήθεια & Υποστήριξη":
        st.header("Support")
        with st.form("supp"):
            subj = st.text_input("Subject")
            msg = st.text_area("Message")
            if st.form_submit_button("Send"):
                st.session_state.support_messages.append({
                    "user": st.session_state.current_user['name'],
                    "subject": subj, "message": msg, "timestamp": str(datetime.now())
                })
                save_data("messages", st.session_state.support_messages) # SAVE
                send_email_notification("johnkrv1@gmail.com", f"Support: {subj}", msg)
                st.success("Sent!")

    # 7. INBOX (ADMIN)
    elif menu_choice == "📨 Εισερχόμενα Μηνύματα":
        st.session_state.support_messages = load_data("messages", [])
        st.dataframe(pd.DataFrame(st.session_state.support_messages))

    # 8. USERS (OWNER)
    elif menu_choice == "👥 Διαχείριση Χρηστών":
        # RELOAD USERS
        st.session_state.users_db = load_data("users", st.session_state.users_db)
        
        st.header("Users")
        with st.expander("Add User"):
            with st.form("add_u"):
                u = st.text_input("Username")
                p = st.text_input("Pass")
                n = st.text_input("Name")
                e = st.text_input("Email")
                ph = st.text_input("Phone")
                r = st.selectbox("Role", ["user", "admin"])
                if st.form_submit_button("Create"):
                    if u not in st.session_state.users_db:
                        st.session_state.users_db[u] = {"password":p, "role":r, "name":n, "email":e, "phone":ph}
                        save_data("users", st.session_state.users_db) # SAVE
                        st.success("Created!")
                        st.rerun()
                    else: st.warning("Exists.")
        
        st.divider()
        for uname, data in st.session_state.users_db.items():
            c1, c2, c3, c4 = st.columns(4)
            c1.write(uname)
            c2.write(data['name'])
            
            if uname == "GiannisKrv": c3.error("OWNER")
            else:
                idx = 0 if data['role'] == 'user' else 1
                new_r = c3.selectbox("Role", ["user", "admin"], index=idx, key=f"r_{uname}", label_visibility="collapsed")
                if new_r != data['role']:
                    st.session_state.users_db[uname]['role'] = new_r
                    save_data("users", st.session_state.users_db) # SAVE
                    st.rerun()
            
            # Delete button logic could go here
