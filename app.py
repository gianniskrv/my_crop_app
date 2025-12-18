import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import date, datetime, timedelta
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
# 💾 DATABASE SYSTEM (ΜΟΝΙΜΗ ΑΠΟΘΗΚΕΥΣΗ)
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "messages": "messages.json"
}

def date_handler(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

def load_data():
    if os.path.exists(FILES["users"]):
        with open(FILES["users"], 'r', encoding='utf-8') as f:
            st.session_state.users_db = json.load(f)
    else:
        st.session_state.users_db = {}

    if os.path.exists(FILES["history"]):
        with open(FILES["history"], 'r', encoding='utf-8') as f:
            data = json.load(f)
            for d in data:
                d['date'] = datetime.strptime(d['date'], "%Y-%m-%d").date()
            st.session_state.history_log = data
    else:
        st.session_state.history_log = []

    if os.path.exists(FILES["expenses"]):
        with open(FILES["expenses"], 'r', encoding='utf-8') as f:
            data = json.load(f)
            for d in data:
                d['date'] = datetime.strptime(d['date'], "%Y-%m-%d").date()
            st.session_state.expenses_log = data
    else:
        st.session_state.expenses_log = []

    if os.path.exists(FILES["messages"]):
        with open(FILES["messages"], 'r', encoding='utf-8') as f:
            st.session_state.support_messages = json.load(f)
    else:
        st.session_state.support_messages = []

    # Εξασφάλιση OWNER
    st.session_state.users_db["GiannisKrv"] = {
        "password": "21041414", 
        "role": "owner", 
        "name": "Γιάννης", 
        "email": "johnkrv1@gmail.com",
        "phone": "6912345678"
    }
    
    if "user" not in st.session_state.users_db:
        st.session_state.users_db["user"] = {
            "password": "123", "role": "user", "name": "Επισκέπτης", "email": "user@example.com", "phone": ""
        }

def save_all_data():
    with open(FILES["users"], 'w', encoding='utf-8') as f:
        json.dump(st.session_state.users_db, f, indent=4, ensure_ascii=False)
    with open(FILES["history"], 'w', encoding='utf-8') as f:
        json.dump(st.session_state.history_log, f, default=date_handler, indent=4, ensure_ascii=False)
    with open(FILES["expenses"], 'w', encoding='utf-8') as f:
        json.dump(st.session_state.expenses_log, f, default=date_handler, indent=4, ensure_ascii=False)
    with open(FILES["messages"], 'w', encoding='utf-8') as f:
        json.dump(st.session_state.support_messages, f, indent=4, ensure_ascii=False)

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
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 👤 SESSION STATE
# ==============================================================================
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'current_username' not in st.session_state: st.session_state.current_username = None

if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1 
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None
if 'reset_email_target' not in st.session_state: st.session_state.reset_email_target = None
if 'reset_username_target' not in st.session_state: st.session_state.reset_username_target = None

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
    except Exception as e:
        st.error(f"Απέτυχε η αποστολή email. Error: {e}")
        return False

def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- AUTH ---
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
            "password": new_pass, "role": "user", "name": new_name, "email": new_email, "phone": new_phone
        }
        save_all_data()
        st.success("Επιτυχία! Συνδεθείτε.")
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
                            save_all_data()
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
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Είσοδος", use_container_width=True):
                    login_user(username, password)
                st.markdown("---")
                if st.button("🆘 Ξέχασα τον κωδικό μου", type="secondary", use_container_width=True):
                    st.session_state.reset_mode = True
                    st.rerun()
            with tab2:
                st.write("Δημιουργήστε νέο λογαριασμό:")
                new_user = st.text_input("Επιθυμητό Username")
                new_pass = st.text_input("Επιθυμητό Password", type="password")
                new_name = st.text_input("Ονοματεπώνυμο")
                new_email = st.text_input("Email")
                new_phone = st.text_input("Κινητό Τηλέφωνο")
                if st.button("Δημιουργία Λογαριασμού", use_container_width=True):
                    if new_user and new_pass and new_name and new_email:
                        register_user(new_user, new_pass, new_name, new_email, new_phone)
                    else:
                        st.warning("Συμπληρώστε όλα τα πεδία.")

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
            "📝 Νέα Καταγραφή (Έσοδα)", "💸 Έξοδα & Ταμείο", "🗂️ Βιβλιοθήκη & Οικονομικά", 
            "☁️ Καιρός & Γεωργία Ακριβείας", "👤 Το Προφίλ μου", "🆘 Βοήθεια & Υποστήριξη"
        ]
        if user_role in ['owner', 'admin']: menu_options.append("📨 Εισερχόμενα Μηνύματα")
        if user_role == 'owner': menu_options.append("👥 Διαχείριση Χρηστών")
        menu_choice = st.radio("Πλοήγηση", menu_options)
        st.divider()
        if st.button("🚪 Αποσύνδεση"): logout()

    default_crops = [{"name": "Βαμβάκι", "category": "Βιομηχανικά"}, {"name": "Σιτάρι Σκληρό", "category": "Σιτηρά"}, {"name": "Καλαμπόκι", "category": "Σιτηρά"}, {"name": "Ηλίανθος", "category": "Βιομηχανικά"}, {"name": "Ελιά (Λαδοελιά)", "category": "Δέντρα"}, {"name": "Ελιά (Βρώσιμη)", "category": "Δέντρα"}, {"name": "Πορτοκαλιά", "category": "Εσπεριδοειδή"}, {"name": "Ροδακινιά", "category": "Πυρηνόκαρπα"}, {"name": "Τομάτα", "category": "Κηπευτικά"}, {"name": "Πατάτα", "category": "Κηπευτικά"}, {"name": "Αμπέλι (Οινοποιήσιμο)", "category": "Αμπέλι"}]
    st.markdown("<h1 style='color:#1b5e20;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)

    # --- 1. INCOME ---
    if menu_choice == "📝 Νέα Καταγραφή (Έσοδα)":
        st.header("Εισαγωγή Παραγωγής & Πωλήσεων")
        with st.container(border=True):
            crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
            selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
            current_name, current_category = "", ""
            if selected_option == "➕ Προσθήκη Νέας...":
                c1, c2 = st.columns(2)
                current_name = c1.text_input("Όνομα")
                current_category = c2.text_input("Κατηγορία")
            else:
                crop_data = next((i for i in default_crops if i["name"] == selected_option), None)
                current_name = crop_data['name']
                current_category = crop_data['category']
                st.info(f"Κατηγορία: **{current_category}**")
        st.divider()
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            rec_date = c1.date_input("Ημερομηνία", date.today())
            rec_variety = c2.text_input("Ποικιλία")
            c3, c4, c5 = st.columns(3)
            rec_qty = c3.number_input("Ποσότητα (kg)", 0, step=10)
            rec_moisture = c4.number_input("Υγρασία (%)", 0.0, 100.0, 0.1)
            rec_price = c5.number_input("Τιμή (€/kg)", 0.0, step=0.01)
            total_revenue = rec_qty * rec_price
            if total_revenue > 0: st.markdown(f"### 💵 Έσοδο: **{total_revenue:.2f} €**")
            notes = st.text_area("Σημειώσεις")
            if st.form_submit_button("💾 Αποθήκευση"):
                if not current_name: st.error("Συμπλήρωσε όνομα!")
                else:
                    new_entry = {"user": st.session_state.current_user['name'], "date": rec_date, "year": rec_date.year, "type": "income", "name": current_name, "category": current_category, "variety": rec_variety, "quantity": rec_qty, "moisture": rec_moisture, "price": rec_price, "revenue": total_revenue, "notes": notes}
                    st.session_state.history_log.append(new_entry)
                    save_all_data()
                    st.success("Αποθηκεύτηκε!")
                    u_email = st.session_state.current_user.get('email')
                    if u_email: send_email_notification(u_email, f"Πώληση: {current_name}", f"Έσοδο {total_revenue}€")

    # --- 2. EXPENSES ---
    elif menu_choice == "💸 Έξοδα & Ταμείο":
        st.header("💸 Διαχείριση Εξόδων")
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            exp_date = col1.date_input("Ημερομηνία", date.today())
            exp_cat = col2.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο", "Σπόροι", "Εργατικά", "Ρεύμα", "Μηχανήματα", "Άλλα"])
            desc = st.text_input("Περιγραφή")
            c1, c2, c3 = st.columns(3)
            amount_net = c1.number_input("Καθαρή Αξία (€)", 0.0, step=1.0)
            vat_rate = c2.selectbox("ΦΠΑ (%)", [0, 6, 13, 24], index=2)
            amount_total = amount_net * (1 + vat_rate/100)
            c3.metric("Σύνολο", f"{amount_total:.2f} €")
            if st.form_submit_button("💾 Αποθήκευση"):
                if amount_net > 0:
                    st.session_state.expenses_log.append({"user": st.session_state.current_user['name'], "date": exp_date, "year": exp_date.year, "type": "expense", "category": exp_cat, "description": desc, "amount_net": amount_net, "vat_rate": vat_rate, "vat_amount": amount_net*(vat_rate/100), "amount_total": amount_total})
                    save_all_data()
                    st.success("Αποθηκεύτηκε!")
                else: st.warning("Βάλε ποσό.")

    # --- 3. LIBRARY ---
    elif menu_choice == "🗂️ Βιβλιοθήκη & Οικονομικά":
        st.header("🗂️ Οικονομική Εικόνα")
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        years = sorted(list(set(list(df_inc['year'].unique() if not df_inc.empty else []) + list(df_exp['year'].unique() if not df_exp.empty else []))), reverse=True)
        
        if not years: st.info("Δεν υπάρχουν δεδομένα.")
        else:
            sel_year = st.selectbox("Έτος", years)
            df_inc_y = df_inc[df_inc['year'] == sel_year] if not df_inc.empty else pd.DataFrame()
            df_exp_y = df_exp[df_exp['year'] == sel_year] if not df_exp.empty else pd.DataFrame()
            rev = df_inc_y['revenue'].sum() if not df_inc_y.empty else 0
            exp = df_exp_y['amount_total'].sum() if not df_exp_y.empty else 0
            
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Έσοδα", f"{rev:.2f} €")
                c2.metric("Έξοδα", f"{exp:.2f} €")
                c3.metric("Κέρδος", f"{rev-exp:.2f} €", delta=f"{rev-exp:.2f} €")
            
            t1, t2, t3 = st.tabs(["Έσοδα", "Έξοδα", "Export"])
            with t1: st.dataframe(df_inc_y, use_container_width=True)
            with t2: st.dataframe(df_exp_y, use_container_width=True)
            with t3:
                c1, c2 = st.columns(2)
                if not df_inc_y.empty: c1.download_button("CSV Εσόδων", convert_df(df_inc_y), "income.csv", "text/csv")
                if not df_exp_y.empty: c2.download_button("CSV Εξόδων", convert_df(df_exp_y), "expenses.csv", "text/csv")

    # --- 4. WEATHER & PRECISION (CHART ADDED) ---
    elif menu_choice == "☁️ Καιρός & Γεωργία Ακριβείας":
        st.header("🌦️ Καιρός & Γεωργία Ακριβείας")
        
        st.caption("Επιλέξτε τρόπο αναζήτησης για μέγιστη ακρίβεια.")
        search_mode = st.radio("Τρόπος Αναζήτησης:", ["🏙️ Πόλη", "🌐 Συντεταγμένες (GPS)"], horizontal=True)
        
        lat, lon = None, None
        display_name = ""
        
        col_input, col_info = st.columns([2, 1])
        
        with col_input:
            if search_mode == "🏙️ Πόλη":
                user_city = st.text_input("🔍 Αναζήτηση Πόλης", value="Larissa")
                if user_city:
                    try:
                        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={user_city}&count=1&language=el&format=json"
                        geo_res = requests.get(geo_url).json()
                        if "results" in geo_res:
                            data = geo_res['results'][0]
                            lat, lon = data['latitude'], data['longitude']
                            display_name = f"{data['name']}, {data.get('country', '')}"
                        else:
                            st.warning("Η πόλη δεν βρέθηκε.")
                    except:
                        st.error("Σφάλμα σύνδεσης.")
            else:
                c_lat, c_lon = st.columns(2)
                lat = c_lat.number_input("Γεωγραφικό Πλάτος (Latitude)", value=39.6390, format="%.4f")
                lon = c_lon.number_input("Γεωγραφικό Μήκος (Longitude)", value=22.4191, format="%.4f")
                display_name = f"Στίγμα: {lat}, {lon}"

        if lat is not None and lon is not None:
            st.success(f"📍 Τοποθεσία: **{display_name}**")
            
            try:
                # API Call with Past Days for GDD Chart
                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                    "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
                    "&daily=temperature_2m_max,temperature_2m_min&timezone=auto&past_days=60&forecast_days=7"
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
                
                # --- GDD CALCULATOR WITH CHART ---
                st.subheader("🧬 Υπολογιστής Ημεροβαθμών Ανάπτυξης (GDD)")
                
                with st.container(border=True):
                    g1, g2 = st.columns(2)
                    crop_gdd = g1.selectbox("Καλλιέργεια", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "Τομάτα", "✏️ Custom"])
                    var_gdd = g2.text_input("Ποικιλία", "π.χ. ST-402")
                    tbase = 10.0
                    final_crop_name = crop_gdd
                    
                    if crop_gdd == "✏️ Custom":
                        final_crop_name = st.text_input("Όνομα Φυτού")
                        tbase = st.number_input("Tbase", 10.0)
                    else:
                        if crop_gdd == "Βαμβάκι": tbase=15.6
                        elif crop_gdd == "Καλαμπόκι": tbase=10.0
                        elif crop_gdd == "Σιτάρι": tbase=0.0
                        elif crop_gdd == "Τομάτα": tbase=10.0
                    
                    # Calculate GDD for all days (History + Forecast)
                    dates = daily['time']
                    tmax = daily['temperature_2m_max']
                    tmin = daily['temperature_2m_min']
                    
                    gdd_data = []
                    cumulative_gdd = 0
                    
                    for i in range(len(dates)):
                        day_gdd = max(((tmax[i] + tmin[i]) / 2) - tbase, 0)
                        cumulative_gdd += day_gdd
                        gdd_data.append(cumulative_gdd)
                    
                    # Current Day GDD (Usually index 60 if past_days=60)
                    today_idx = 60 # Default past_days index
                    gdd_today = 0
                    if len(gdd_data) > today_idx:
                        gdd_today = gdd_data[today_idx] - gdd_data[today_idx-1]
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Μέγιστη (Σήμερα)", f"{tmax[today_idx]}°C")
                    k2.metric("Ελάχιστη (Σήμερα)", f"{tmin[today_idx]}°C")
                    k3.metric("GDD Σήμερα", f"{gdd_today:.1f}")
                    
                    st.success(f"✅ Συνολική Ανάπτυξη (Συσσωρευμένοι GDD): **{cumulative_gdd:.1f}**")
                    
                    # CHART
                    st.write("**📈 Διάγραμμα Ανάπτυξης Φυτού (Συσσωρευμένοι Ημεροβαθμοί)**")
                    chart_df = pd.DataFrame({"Date": dates, "Cumulative GDD": gdd_data})
                    chart_df.set_index("Date", inplace=True)
                    st.area_chart(chart_df, color="#2e7d32") # Πράσινο χρώμα ανάπτυξης
                
                st.divider()
                
                # --- VRT CALCULATOR ---
                st.subheader("🧪 VRT Λίπανση")
                with st.container(border=True):
                    v1, v2 = st.columns(2)
                    crop_vrt = v1.selectbox("Φυτό", ["Βαμβάκι", "Καλαμπόκι", "Σιτάρι", "✏️ Custom"])
                    var_vrt = v2.text_input("Ποικιλία", "π.χ. P1570", key="vrt_var")
                    rem_coef = 4.5 if crop_vrt == "Βαμβάκι" else 3.0
                    if crop_vrt == "✏️ Custom": rem_coef = st.number_input("Μονάδες N/100kg", 3.0)
                    
                    yld = st.number_input("Στόχος (kg/στρ)", 400)
                    fert = st.selectbox("Λίπασμα", ["Ουρία (46-0-0)", "Νιτρική (34.5)", "Θειική (21)", "NPK (20)", "✏️ Custom"])
                    n_per = 0.46
                    if "34.5" in fert: n_per=0.345
                    elif "21" in fert: n_per=0.21
                    elif "20" in fert: n_per=0.20
                    elif "✏️" in fert: n_per = st.number_input("N %", 0.0, 100.0, 46.0)/100
                    
                    if n_per > 0:
                        dose = ((yld/100)*rem_coef) / n_per / 0.8
                        st.info(f"Στόχος: {yld} kg/στρ")
                        st.success(f"👉 Συνιστώμενη Δόση: **{dose:.1f} kg/στρ**")

                st.map(pd.DataFrame({'lat':[lat], 'lon':[lon]}))
            except Exception as e: 
                st.error(f"Error fetching weather: {e}")
        
        st.divider()
        components.iframe("https://www.effispray.com/el", height=600, scrolling=True)

    # --- 5. PROFILE ---
    elif menu_choice == "👤 Το Προφίλ μου":
        st.header("👤 Προφίλ")
        u = st.session_state.current_user
        with st.form("prof"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Όνομα", u['name'])
            e = c2.text_input("Email", u.get('email',''))
            c3, c4 = st.columns(2)
            p = c3.text_input("Τηλ", u.get('phone',''))
            pw = c4.text_input("Νέος Κωδικός", type="password")
            if st.form_submit_button("💾 Save"):
                un = st.session_state.current_username
                st.session_state.users_db[un].update({'name':n, 'email':e, 'phone':p})
                if pw: st.session_state.users_db[un]['password'] = pw
                st.session_state.current_user = st.session_state.users_db[un]
                save_all_data()
                st.success("Updated!")
                st.rerun()

    # --- 6. SUPPORT ---
    elif menu_choice == "🆘 Βοήθεια & Υποστήριξη":
        st.header("🆘 Support")
        with st.form("sup"):
            em = st.text_input("Email *", st.session_state.current_user.get('email',''))
            sub = st.text_input("Θέμα *")
            bod = st.text_area("Μήνυμα *")
            if st.form_submit_button("Αποστολή"):
                if em and sub and bod:
                    st.session_state.support_messages.append({"timestamp": str(datetime.now()), "user": st.session_state.current_user['name'], "email": em, "subject": sub, "message": bod})
                    save_all_data()
                    send_email_notification("johnkrv1@gmail.com", f"Support: {sub}", f"{bod}\nFrom: {em}")
                    st.success("Εστάλη!")

    # --- 7. INBOX ---
    elif menu_choice == "📨 Εισερχόμενα Μηνύματα":
        if user_role not in ['owner', 'admin']: st.stop()
        st.header("📨 Inbox")
        if st.session_state.support_messages:
            st.dataframe(pd.DataFrame(st.session_state.support_messages).iloc[::-1], use_container_width=True)
        else: st.info("Empty.")

    # --- 8. ADMIN USERS ---
    elif menu_choice == "👥 Διαχείριση Χρηστών":
        if user_role != 'owner': st.stop()
        st.header("👑 Users")
        with st.expander("➕ New User"):
            with st.form("new_u"):
                c1,c2 = st.columns(2)
                nu = c1.text_input("User")
                np = c2.text_input("Pass")
                c3,c4,c5 = st.columns(3)
                nn = c3.text_input("Name")
                ne = c4.text_input("Email")
                nr = c5.selectbox("Role", ["user", "admin"])
                if st.form_submit_button("Create"):
                    st.session_state.users_db[nu] = {'password':np, 'role':nr, 'name':nn, 'email':ne, 'phone':''}
                    save_all_data()
                    st.success("Created!")
                    st.rerun()
        
        st.divider()
        for un, ud in st.session_state.users_db.items():
            c1,c2,c3,c4,c5,c6 = st.columns([2,2,2,2,1,1])
            c1.write(un)
            c2.write(ud['name'])
            c3.write(ud.get('email','-'))
            if un == "GiannisKrv": c4.error("OWNER")
            else:
                idx = 0 if ud['role']=='user' else 1
                nr = c4.selectbox("Role", ["user", "admin"], index=idx, key=f"r_{un}", label_visibility="collapsed")
                if nr != ud['role']:
                    st.session_state.users_db[un]['role'] = nr
                    save_all_data()
                    st.rerun()
            
            k = f"v_{un}"
            if k not in st.session_state: st.session_state[k] = False
            if st.session_state[k]: c5.warning(f"`{ud['password']}`")
            else: c5.text("••••")
            if c6.button("👁️", key=f"b_{un}"):
                st.session_state[k] = not st.session_state[k]
                st.rerun()
            st.markdown("---")
