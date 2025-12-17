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
from email.message import EmailMessage

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 🎨 UI & DESIGN (CSS STYLING)
# ==============================================================================
def local_css():
    st.markdown("""
    <style>
        .stApp {
            background-image: linear-gradient(to bottom right, #ebf7eb, #e3f2fd);
        }
        [data-testid="stSidebar"] {
            background-image: linear-gradient(180deg, #f1f8e9, #ffffff);
            border-right: 1px solid #c8e6c9;
        }
        .stButton>button {
            color: white;
            background-color: #2e7d32;
            border-radius: 12px;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #1b5e20;
            transform: scale(1.02);
        }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #a5d6a7;
        }
        
        /* Κρύβουμε μόνο τα περιττά, ΟΧΙ το header για να φαίνεται το μενού στο κινητό */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 👤 SESSION STATE & USERS
# ==============================================================================

if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "user": {
            "password": "123", 
            "role": "user", 
            "name": "Επισκέπτης", 
            "email": "user@example.com",
            "phone": "6900000000"
        }
    }

# OWNER
st.session_state.users_db["GiannisKrv"] = {
    "password": "21041414", 
    "role": "owner", 
    "name": "Γιάννης", 
    "email": "johnkrv1@gmail.com",
    "phone": "6912345678"
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'current_username' not in st.session_state: st.session_state.current_username = None

# --- STATE ΓΙΑ PASSWORD RESET ---
if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1 
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None
if 'reset_email_target' not in st.session_state: st.session_state.reset_email_target = None
if 'reset_username_target' not in st.session_state: st.session_state.reset_username_target = None

# --- STATE ΓΙΑ DATA ---
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'expenses_log' not in st.session_state: st.session_state.expenses_log = []
if 'support_messages' not in st.session_state: st.session_state.support_messages = []

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
        st.error(f"Απέτυχε η αποστολή email. Error: {e}")
        return False

# --- HELPER: CSV ---
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- AUTH FUNCTIONS ---
def login_user(username, password):
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
        st.success("Επιτυχία! Ο λογαριασμός δημιουργήθηκε. Τώρα μπορείτε να συνδεθείτε.")
        send_email_notification(new_email, "Καλωσήρισες στο AgroManager", f"Γεια σου {new_name},\nΟ λογαριασμός σου ενεργοποιήθηκε.")

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_username = None
    st.rerun()

# ==================================================
# 🔐 LOGIC: LOGIN vs RESET PASSWORD
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
            
            # --- LOGIN FORM ---
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
            
            # --- REGISTER FORM (ΔΙΟΡΘΩΜΕΝΗ) ---
            with tab2:
                # Χρησιμοποιούμε st.form για να μην χάνονται τα δεδομένα
                with st.form("register_form", clear_on_submit=False):
                    st.write("Δημιουργήστε νέο λογαριασμό:")
                    new_user = st.text_input("Επιθυμητό Username")
                    new_pass = st.text_input("Επιθυμητό Password", type="password")
                    new_name = st.text_input("Ονοματεπώνυμο")
                    new_email = st.text_input("Email")
                    new_phone = st.text_input("Κινητό Τηλέφωνο")
                    
                    submit_register = st.form_submit_button("Δημιουργία Λογαριασμού", use_container_width=True)
                    
                    if submit_register:
                        # Ελέγχουμε αν ΟΛΑ τα πεδία έχουν συμπληρωθεί
                        if new_user and new_pass and new_name and new_email and new_phone:
                            register_user(new_user, new_pass, new_name, new_email, new_phone)
                        else:
                            st.warning("Παρακαλώ συμπληρώστε ΟΛΑ τα πεδία.")

else:
    # ==================================================
    # 📱 ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ
    # ==================================================
    with st.sidebar:
        user_role = st.session_state.current_user['role']
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        st.caption(f"Role: {user_role.upper()}")
        st.divider()
        
        menu_options = [
            "📝 Νέα Καταγραφή (Έσοδα)", 
            "💸 Έξοδα & Ταμείο",          
            "🗂️ Βιβλιοθήκη & Οικονομικά", 
            "☁️ Καιρός & Γεωργία Ακριβείας", 
            "👤 Το Προφίλ μου",
            "🆘 Βοήθεια & Υποστήριξη"
        ]
        
        if user_role in ['owner', 'admin']:
            menu_options.append("📨 Εισερχόμενα Μηνύματα")
        
        if user_role == 'owner':
            menu_options.append("👥 Διαχείριση Χρηστών")
            
        menu_choice = st.radio("Πλοήγηση", menu_options)
        
        st.divider()
        if st.button("🚪 Αποσύνδεση"):
            logout()

    # --- DB CROPS ---
    default_crops = [
        {"name": "Βαμβάκι", "category": "Βιομηχανικά", "wiki_term": "Βαμβάκι (φυτό)"},
        {"name": "Σιτάρι Σκληρό", "category": "Σιτηρά", "wiki_term": "Σίτος"},
        {"name": "Καλαμπόκι", "category": "Σιτηρά", "wiki_term": "Αραβόσιτος"},
        {"name": "Ηλίανθος", "category": "Βιομηχανικά", "wiki_term": "Ηλίανθος"},
        {"name": "Ελιά (Λαδοελιά)", "category": "Δέντρα", "wiki_term": "Ελιά"},
        {"name": "Ελιά (Βρώσιμη)", "category": "Δέντρα", "wiki_term": "Ελιά"},
        {"name": "Πορτοκαλιά", "category": "Εσπεριδοειδή", "wiki_term": "Πορτοκαλιά"},
        {"name": "Ροδακινιά", "category": "Πυρηνόκαρπα", "wiki_term": "Ροδακινιά"},
        {"name": "Τομάτα", "category": "Κηπευτικά", "wiki_term": "Τομάτα"},
        {"name": "Πατάτα", "category": "Κηπευτικά", "wiki_term": "Πατάτα"},
        {"name": "Αμπέλι (Οινοποιήσιμο)", "category": "Αμπέλι", "wiki_term": "Άμπελος"},
    ]

    st.markdown("<h1 style='color:#1b5e20;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)

    # --------------------------------------------------
    # 1. ΚΑΤΑΓΡΑΦΗ ΕΣΟΔΩΝ
    # --------------------------------------------------
    if menu_choice == "📝 Νέα Καταγραφή (Έσοδα)":
        st.header("Εισαγωγή Παραγωγής & Πωλήσεων")
        
        with st.container(border=True):
            crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
            selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
            
            current_name = ""
            current_category = ""
            
            if selected_option == "➕ Προσθήκη Νέας...":
                col_new1, col_new2 = st.columns(2)
                current_name = col_new1.text_input("Όνομα Καλλιέργειας")
                current_category = col_new2.text_input("Κατηγορία")
            else:
                crop_data = next((item for item in default_crops if item["name"] == selected_option), None)
                if crop_data:
                    current_name = crop_data['name']
                    current_category = crop_data['category']
                    st.info(f"Κατηγορία: **{current_category}**")

        st.divider()
        
        with st.form("entry_form"):
            st.subheader("Στοιχεία Εγγραφής")
            c1, c2 = st.columns(2)
            rec_date = c1.date_input("Ημερομηνία", date.today())
            rec_variety = c2.text_input("Ποικιλία")
            
            st.write("💰 **Οικονομικά & Ποσότητες**")
            c3, c4, c5 = st.columns(3)
            rec_qty = c3.number_input("Ποσότητα (kg)", min_value=0, step=10)
            rec_moisture = c4.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, step=0.1)
            rec_price = c5.number_input("Τιμή Πώλησης (€/kg)", min_value=0.0, step=0.01, format="%.2f")
            
            total_revenue = rec_qty * rec_price
            if rec_qty > 0 and rec_price > 0:
                st.markdown(f"### 💵 Έσοδο: **{total_revenue:.2f} €**")

            notes = st.text_area("Σημειώσεις")
            submitted = st.form_submit_button("💾 Αποθήκευση Εσόδου")
            
            if submitted:
                if not current_name:
                    st.error("Συμπλήρωσε όνομα καλλιέργειας!")
                else:
                    new_entry = {
                        "user": st.session_state.current_user['name'],
                        "date": rec_date,
                        "year": rec_date.year,
                        "type": "income",
                        "name": current_name,
                        "category": current_category,
                        "variety": rec_variety,
                        "quantity": rec_qty,
                        "moisture": rec_moisture,
                        "price": rec_price,
                        "revenue": total_revenue,
                        "notes": notes
                    }
                    st.session_state.history_log.append(new_entry)
                    st.success(f"Καταγράφηκε Έσοδο: {current_name} (+{total_revenue:.2f}€)")
                    
                    user_mail = st.session_state.current_user.get('email')
                    if user_mail and "@" in user_mail:
                        send_email_notification(user_mail, f"Νέα Πώληση: {current_name}", f"Καταχωρήθηκε έσοδο {total_revenue}€.")

    # --------------------------------------------------
    # 2. ΚΑΤΑΓΡΑΦΗ ΕΞΟΔΩΝ
    # --------------------------------------------------
    elif menu_choice == "💸 Έξοδα & Ταμείο":
        st.header("💸 Διαχείριση Εξόδων")
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            exp_date = col1.date_input("Ημερομηνία Εξόδου", date.today())
            exp_cat = col2.selectbox("Κατηγορία Εξόδου", [
                "Λιπάσματα", "Φάρμακα", "Πετρέλαιο", "Σπόροι/Φυτά", 
                "Εργατικά", "Ρεύμα/Νερό", "Μηχανήματα/Service", "Άλλα"
            ])
            
            desc = st.text_input("Περιγραφή", placeholder="π.χ. Αγορά Ουρίας 10 σακιά")
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            
            amount_net = c1.number_input("Καθαρή Αξία (€)", min_value=0.0, step=1.0)
            vat_rate = c2.selectbox("ΦΠΑ (%)", [0, 6, 13, 24], index=2)
            
            vat_amount = amount_net * (vat_rate / 100)
            amount_total = amount_net + vat_amount
            
            c3.metric("Τελικό Ποσό (με ΦΠΑ)", f"{amount_total:.2f} €")
            
            submit_exp = st.form_submit_button("💾 Καταχώρηση Εξόδου")
            
            if submit_exp:
                if amount_net > 0:
                    expense_entry = {
                        "user": st.session_state.current_user['name'],
                        "date": exp_date,
                        "year": exp_date.year,
                        "type": "expense",
                        "category": exp_cat,
                        "description": desc,
                        "amount_net": amount_net,
                        "vat_rate": vat_rate,
                        "vat_amount": vat_amount,
                        "amount_total": amount_total
                    }
                    st.session_state.expenses_log.append(expense_entry)
                    st.success(f"Καταχωρήθηκε έξοδο: -{amount_total:.2f} €")
                else:
                    st.warning("Παρακαλώ εισάγετε ποσό.")

    # --------------------------------------------------
    # 3. ΒΙΒΛΙΟΘΗΚΗ & ΟΙΚΟΝΟΜΙΚΑ
    # --------------------------------------------------
    elif menu_choice == "🗂️ Βιβλιοθήκη & Οικονομικά":
        st.header("🗂️ Οικονομική Εικόνα & Αρχείο")
        
        df_income = pd.DataFrame(st.session_state.history_log)
        df_expense = pd.DataFrame(st.session_state.expenses_log)

        all_years = []
        if not df_income.empty: all_years.extend(df_income['year'].unique())
        if not df_expense.empty: all_years.extend(df_expense['year'].unique())
        unique_years = sorted(list(set(all_years)), reverse=True)
        
        if not unique_years:
            st.info("Δεν υπάρχουν εγγραφές ακόμα.")
        else:
            sel_year = st.selectbox("Επιλέξτε Έτος Οικονομικών", unique_years)
            st.divider()
            
            inc_year = pd.DataFrame()
            exp_year = pd.DataFrame()
            
            if not df_income.empty: 
                inc_year = df_income[df_income['year'] == sel_year]
            if not df_expense.empty: 
                exp_year = df_expense[df_expense['year'] == sel_year]

            total_rev = inc_year['revenue'].sum() if not inc_year.empty else 0.0
            total_exp = exp_year['amount_total'].sum() if not exp_year.empty else 0.0
            net_profit = total_rev - total_exp
            
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Έσοδα", f"{total_rev:.2f} €")
                col2.metric("💸 Έξοδα (με ΦΠΑ)", f"{total_exp:.2f} €")
                col3.metric("📉 ΚΑΘΑΡΟ ΚΕΡΔΟΣ", f"{net_profit:.2f} €", delta=f"{net_profit:.2f} €")
            
            st.markdown("---")
            
            tab_inc, tab_exp, tab_export = st.tabs(["📈 Ανάλυση Εσόδων", "📉 Ανάλυση Εξόδων", "📥 Εξαγωγή Δεδομένων"])
            
            with tab_inc:
                if inc_year.empty:
                    st.info("Κανένα έσοδο.")
                else:
                    st.dataframe(inc_year[['date', 'name', 'quantity', 'price', 'revenue']], use_container_width=True)
            
            with tab_exp:
                if exp_year.empty:
                    st.info("Κανένα έξοδο.")
                else:
                    exp_summary = exp_year.groupby('category')[['amount_net', 'vat_amount', 'amount_total']].sum().reset_index()
                    st.dataframe(exp_summary, use_container_width=True)
                    st.dataframe(exp_year[['date', 'category', 'description', 'amount_total']], use_container_width=True)
            
            with tab_export:
                st.subheader("📥 Λήψη Αρχείων για Excel")
                c_ex1, c_ex2 = st.columns(2)
                
                if not inc_year.empty:
                    csv_inc = convert_df(inc_year)
                    c_ex1.download_button("📄 Κατέβασε τα Έσοδα (CSV)", csv_inc, f"esoda_{sel_year}.csv", 'text/csv')
                else:
                    c_ex1.info("Χωρίς έσοδα.")

                if not exp_year.empty:
                    csv_exp = convert_df(exp_year)
                    c_ex2.download_button("📄 Κατέβασε τα Έξοδα (CSV)", csv_exp, f"exoda_{sel_year}.csv", 'text/csv')
                else:
                    c_ex2.info("Χωρίς έξοδα.")

    # --------------------------------------------------
    # 4. ΚΑΙΡΟΣ & ΓΕΩΡΓΙΑ ΑΚΡΙΒΕΙΑΣ (GDD & VRT)
    # --------------------------------------------------
    elif menu_choice == "☁️ Καιρός & Γεωργία Ακριβείας":
        st.header("🌦️ Καιρός & Γεωργία Ακριβείας")
        
        col_search, col_btn = st.columns([3, 1])
        user_city = col_search.text_input("🔍 Αναζήτηση Περιοχής", value="Larissa")
        
        if user_city:
            try:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={user_city}&count=1&language=el&format=json"
                geo_res = requests.get(geo_url).json()

                if "results" in geo_res:
                    data = geo_res['results'][0]
                    lat, lon = data['latitude'], data['longitude']
                    name, country = data['name'], data.get("country", "")

                    st.success(f"📍 Περιοχή: **{name}, {country}**")

                    weather_url = (
                        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                        "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
                        "&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1"
                    )
                    w_res = requests.get(weather_url).json()
                    curr = w_res['current']
                    daily = w_res['daily']

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🌡️ Θερμοκρασία", f"{curr['temperature_2m']} °C")
                    c2.metric("💧 Υγρασία", f"{curr['relative_humidity_2m']} %")
                    c3.metric("☔ Βροχή", f"{curr['precipitation']} mm")
                    c4.metric("💨 Άνεμος", f"{curr['wind_speed_10m']} km/h")
                    
                    st.divider()
                    
                    # --- GDD CALCULATOR ---
                    st.subheader("🧬 Υπολογιστής Ημεροβαθμών Ανάπτυξης (GDD)")
                    
                    with st.container(border=True):
                        col_crop1, col_crop2 = st.columns(2)
                        crop_gdd_sel = col_crop1.selectbox("Επιλογή Καλλιέργειας:", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "Τομάτα", "✏️ Άλλο / Custom"])
                        variety_gdd = col_crop2.text_input("Ποικιλία (Variety):", placeholder="π.χ. ST-402")
                        
                        t_base = 10.0
                        final_crop_name = crop_gdd_sel
                        
                        if crop_gdd_sel == "✏️ Άλλο / Custom":
                            col_c1, col_c2 = st.columns(2)
                            final_crop_name = col_c1.text_input("Όνομα Καλλιέργειας", placeholder="π.χ. Φιστίκι")
                            t_base = col_c2.number_input("Βασική Θερμοκρασία (Tbase) °C:", min_value=0.0, value=10.0, step=0.1)
                        else:
                            if crop_gdd_sel == "Βαμβάκι": t_base = 15.6
                            elif crop_gdd_sel == "Καλαμπόκι": t_base = 10.0
                            elif crop_gdd_sel == "Σιτάρι": t_base = 0.0
                            elif crop_gdd_sel == "Τομάτα": t_base = 10.0
                        
                        t_max = daily['temperature_2m_max'][0]
                        t_min = daily['temperature_2m_min'][0]
                        gdd = ((t_max + t_min) / 2) - t_base
                        if gdd < 0: gdd = 0
                        
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Μέγιστη", f"{t_max} °C")
                        k2.metric("Ελάχιστη", f"{t_min} °C")
                        k3.metric("Tbase", f"{t_base} °C")
                        
                        st.markdown(f"#### 🌡️ GDD Σήμερα ({final_crop_name} - {variety_gdd}): **{gdd:.1f}**")
                        if gdd > 0: st.success("✅ Το φυτό αναπτύσσεται κανονικά.")
                        else: st.warning("❄️ Η ανάπτυξη έχει σταματήσει.")

                    st.divider()
                    
                    # --- VRT CALCULATOR ---
                    st.subheader("🧪 Υπολογιστής Λίπανσης (VRT Logic)")
                    
                    with st.container(border=True):
                        col_vrt1, col_vrt2 = st.columns(2)
                        crop_fert_sel = col_vrt1.selectbox("Καλλιέργεια:", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "✏️ Άλλο / Custom"])
                        variety_vrt = col_vrt2.text_input("Ποικιλία:", placeholder="π.χ. Pioneer P1570")
                        
                        removal_coeff = 0.0
                        final_fert_crop = crop_fert_sel
                        
                        if crop_fert_sel == "✏️ Άλλο / Custom":
                            col_vc1, col_vc2 = st.columns(2)
                            final_fert_crop = col_vc1.text_input("Όνομα Καλλιέργειας (VRT)", placeholder="π.χ. Ηλίανθος")
                            removal_coeff = col_vc2.number_input("Μονάδες Αζώτου (N) ανά 100kg καρπού:", min_value=0.0, value=3.0, step=0.1)
                        else:
                            if crop_fert_sel == "Βαμβάκι": removal_coeff = 4.5
                            elif crop_fert_sel == "Καλαμπόκι": removal_coeff = 2.5
                            elif crop_fert_sel == "Σιτάρι": removal_coeff = 3.0
                        
                        target_yield = st.number_input("Στόχος Παραγωγής (kg/στρέμμα):", min_value=100, step=50, value=400)
                        n_needs = (target_yield / 100) * removal_coeff
                        
                        fert_sel = st.selectbox("Τύπος Λιπάσματος:", ["Ουρία (46-0-0)", "Νιτρική Αμμωνία (34.5-0-0)", "Θειική Αμμωνία (21-0-0)", "NPK (20-20-20)", "✏️ Άλλο / Custom"])
                        
                        n_content = 0.0
                        final_fert_name = fert_sel
                        
                        if fert_sel == "✏️ Άλλο / Custom":
                            col_f1, col_f2 = st.columns(2)
                            final_fert_name = col_f1.text_input("Όνομα Λιπάσματος", placeholder="π.χ. UTEC 46")
                            n_percent = col_f2.number_input("Περιεκτικότητα N (%):", min_value=0.0, max_value=100.0, step=0.1)
                            n_content = n_percent / 100.0
                        else:
                            if "46" in fert_sel: n_content = 0.46
                            elif "34.5" in fert_sel: n_content = 0.345
                            elif "21" in fert_sel: n_content = 0.21
                            elif "20" in fert_sel: n_content = 0.20
                        
                        if n_content > 0 and removal_coeff > 0:
                            efficiency = 0.8
                            fert_kg = (n_needs / n_content) / efficiency
                            st.info(f"Για στόχο **{target_yield} kg/στρ** {final_fert_crop} ({variety_vrt}), απαιτούνται **{n_needs:.1f} μονάδες Αζώτου**.")
                            st.success(f"👉 Συνιστώμενη Δόση: **{fert_kg:.1f} kg/στρέμμα** {final_fert_name}")
                        elif "✏️" in crop_fert_sel or "✏️" in fert_sel:
                            st.warning("Συμπληρώστε τα πεδία Custom.")

                    st.markdown("---")
                    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
                else:
                    st.warning("Η πόλη δεν βρέθηκε.")
            except:
                st.error("Υπήρξε πρόβλημα με τη σύνδεση.")

        st.divider()
        st.write("### 🚜 Εργαλείο Ψεκασμού (EffiSpray)")
        components.iframe("https://www.effispray.com/el", height=600, scrolling=True)

    # --------------------------------------------------
    # 5. ΠΡΟΦΙΛ ΧΡΗΣΤΗ
    # --------------------------------------------------
    elif menu_choice == "👤 Το Προφίλ μου":
        st.header("👤 Το Προφίλ μου")
        st.caption("Επεξεργασία προσωπικών στοιχείων.")
        
        current_data = st.session_state.current_user
        
        with st.container(border=True):
            with st.form("edit_profile"):
                c1, c2 = st.columns(2)
                new_name = c1.text_input("Ονοματεπώνυμο:", value=current_data['name'])
                new_email = c2.text_input("Email:", value=current_data.get('email', ''))
                
                c3, c4 = st.columns(2)
                new_phone = c3.text_input("Κινητό Τηλέφωνο:", value=current_data.get('phone', ''))
                new_pass = c4.text_input("Αλλαγή Κωδικού (Αφήστε κενό για διατήρηση):", type="password")
                
                if st.form_submit_button("💾 Αποθήκευση"):
                    uname = st.session_state.current_username
                    st.session_state.users_db[uname]['name'] = new_name
                    st.session_state.users_db[uname]['email'] = new_email
                    st.session_state.users_db[uname]['phone'] = new_phone
                    
                    if new_pass:
                        st.session_state.users_db[uname]['password'] = new_pass
                        st.toast("Ο κωδικός άλλαξε!", icon="🔑")
                    
                    st.session_state.current_user = st.session_state.users_db[uname]
                    st.success("Ενημερώθηκε!")
                    time.sleep(1)
                    st.rerun()

    # --------------------------------------------------
    # 6. ΒΟΗΘΕΙΑ & ΥΠΟΣΤΗΡΙΞΗ
    # --------------------------------------------------
    elif menu_choice == "🆘 Βοήθεια & Υποστήριξη":
        st.header("🆘 Κέντρο Υποστήριξης")
        with st.form("support_form"):
            default_email = st.session_state.current_user.get('email', '')
            sender_email = st.text_input("Το Email σας (για να λάβετε απάντηση) *", value=default_email)
            subject = st.text_input("Θέμα Μηνύματος *")
            msg_body = st.text_area("Το μήνυμά σας *")
            
            if st.form_submit_button("📨 Αποστολή Μηνύματος"):
                if subject and msg_body and sender_email:
                    msg_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "user": st.session_state.current_user['name'],
                        "email": sender_email,
                        "subject": subject,
                        "message": msg_body
                    }
                    st.session_state.support_messages.append(msg_entry)
                    admin_email = "johnkrv1@gmail.com"
                    send_email_notification(admin_email, f"🔔 Support: {subject}", f"Νέο μήνυμα από {sender_email}:\n\n{msg_body}")
                    st.success("Το μήνυμά σας εστάλη!")
                else:
                    st.error("Συμπληρώστε όλα τα πεδία.")

    # --------------------------------------------------
    # 7. ΕΙΣΕΡΧΟΜΕΝΑ ΜΗΝΥΜΑΤΑ (OWNER & ADMIN)
    # --------------------------------------------------
    elif menu_choice == "📨 Εισερχόμενα Μηνύματα":
         if st.session_state.current_user['role'] not in ['owner', 'admin']:
             st.stop()
         st.header("📨 Εισερχόμενα Μηνύματα Χρηστών")
         if not st.session_state.support_messages:
             st.info("Δεν υπάρχουν νέα μηνύματα.")
         else:
             st.dataframe(pd.DataFrame(st.session_state.support_messages).iloc[::-1], use_container_width=True, hide_index=True)

    # --------------------------------------------------
    # 8. ΔΙΑΧΕΙΡΙΣΗ ΧΡΗΣΤΩΝ (OWNER ONLY)
    # --------------------------------------------------
    elif menu_choice == "👥 Διαχείριση Χρηστών":
        if st.session_state.current_user['role'] != 'owner':
             st.stop()
        st.header("👑 Πίνακας Ελέγχου Owner")
        
        with st.expander("➕ Προσθήκη Νέου Χρήστη", expanded=True):
            with st.form("create_user"):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Username")
                new_p = c2.text_input("Password")
                c3, c4 = st.columns(2)
                new_n = c3.text_input("Όνομα")
                new_e = c4.text_input("Email")
                c5, c6 = st.columns(2)
                new_ph = c5.text_input("Τηλέφωνο")
                new_role = c6.selectbox("Ρόλος", ["user", "admin"])
                
                if st.form_submit_button("Δημιουργία"):
                    st.session_state.users_db[new_u] = {
                        "password": new_p, 
                        "role": new_role, 
                        "name": new_n, 
                        "email": new_e,
                        "phone": new_ph
                    }
                    st.success("Δημιουργήθηκε!")
                    st.rerun()

        st.divider()
        st.subheader("📋 Λίστα Εγγεγραμμένων")
        
        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 2, 2, 1, 1])
        h1.markdown("**Username**")
        h2.markdown("**Όνομα**")
        h3.markdown("**Email**")
        h4.markdown("**Ρόλος (Edit)**")
        h5.markdown("**Κωδικός**")
        h6.markdown("**Προβολή**")
        st.divider()

        for uname, udata in st.session_state.users_db.items():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1, 1])
            c1.write(uname)
            c2.write(udata['name'])
            c3.write(udata.get('email', '-'))
            
            r = udata['role']
            if uname == "GiannisKrv": 
                c4.error("OWNER (Locked)")
            else:
                current_index = 0 if r == 'user' else 1
                new_role_sel = c4.selectbox(
                    "Change Role", 
                    ["user", "admin"], 
                    index=current_index, 
                    key=f"role_edit_{uname}",
                    label_visibility="collapsed"
                )
                
                if new_role_sel != r:
                    st.session_state.users_db[uname]['role'] = new_role_sel
                    st.toast(f"Ο ρόλος του {uname} άλλαξε σε {new_role_sel.upper()}!", icon="🔄")
                    time.sleep(0.5)
                    st.rerun()

            toggle_key = f"vis_{uname}"
            if toggle_key not in st.session_state: st.session_state[toggle_key] = False
            
            if st.session_state[toggle_key]:
                c5.warning(f"`{udata['password']}`")
                btn_icon = "🙈"
            else:
                c5.text("••••••••")
                btn_icon = "👁️"
                
            if c6.button(btn_icon, key=f"btn_{uname}"):
                st.session_state[toggle_key] = not st.session_state[toggle_key]
                st.rerun()
            st.markdown("---")
