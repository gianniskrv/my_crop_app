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
from email.message import EmailMessage

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 📧 ΡΥΘΜΙΣΕΙΣ EMAIL
# ==============================================================================
EMAIL_SENDER = "johnkrv1@gmail.com"
EMAIL_PASSWORD = "bcgb tdmn sjwe ajnt"

def send_email(receiver, subject, body):
    """Στέλνει email ειδοποίησης"""
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
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# ==============================================================================
# 💾 DATABASE SYSTEM
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "inventory": "inventory.json",
    "machinery": "machinery.json",
    "calendar": "calendar.json"
}

def date_handler(obj):
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    return obj

def load_data():
    # Φόρτωση Χρηστών
    if os.path.exists(FILES["users"]):
        with open(FILES["users"], 'r', encoding='utf-8') as f: st.session_state.users_db = json.load(f)
    else:
        st.session_state.users_db = {}

    # --- SECURITY ENFORCEMENT ---
    # Εξασφαλίζουμε ότι ο λογαριασμός GiannisKrv υπάρχει και είναι ΠΑΝΤΑ owner
    if "GiannisKrv" not in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"] = {
            "password": "change_me", # Θα κρατήσει τον παλιό αν υπάρχει στο json, αυτό είναι για init
            "role": "owner",
            "name": "Γιάννης",
            "email": "johnkrv1@gmail.com",
            "phone": ""
        }
    
    # ΚΛΕΙΔΩΜΑ: Επιβάλουμε τον ρόλο owner στον GiannisKrv ό,τι και να γίνει
    if "GiannisKrv" in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"]["role"] = "owner"
        # Αν δεν υπάρχει ήδη αρχείο, το σώζουμε τώρα
        if not os.path.exists(FILES["users"]):
            save_data("users")

    # Φόρτωση υπόλοιπων δεδομένων
    for key, file_path in FILES.items():
        if key == "users": continue
        state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for d in data:
                    if 'date' in d and isinstance(d['date'], str):
                        d['date'] = datetime.strptime(d['date'][:10], "%Y-%m-%d").date()
                st.session_state[state_key] = data
        else:
            st.session_state[state_key] = []

def save_data(key):
    target_file = FILES.get(key)
    state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
    if target_file and state_key in st.session_state:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state[state_key], f, default=date_handler, indent=4, ensure_ascii=False)

# ==============================================================================
# 🎨 DESIGN & CSS
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 👤 AUTH & SESSION
# ==============================================================================
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'weather_data' not in st.session_state: st.session_state.weather_data = None
if 'weather_loc_name' not in st.session_state: st.session_state.weather_loc_name = ""
if 'current_username' not in st.session_state: st.session_state.current_username = None

# --- Μεταβλητές για Ανάκτηση Κωδικού ---
if 'reset_mode' not in st.session_state: st.session_state.reset_mode = False
if 'reset_step' not in st.session_state: st.session_state.reset_step = 1 
if 'reset_otp' not in st.session_state: st.session_state.reset_otp = None
if 'reset_email_target' not in st.session_state: st.session_state.reset_email_target = None
if 'reset_username_target' not in st.session_state: st.session_state.reset_username_target = None


def login_user(username, password):
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.session_state.current_username = username
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(0.5)
            st.rerun()
        else: st.error("Λάθος κωδικός.")
    else: st.error("Ο χρήστης δεν βρέθηκε.")

def register_user(new_user, new_pass, new_name, new_email):
    if new_user in st.session_state.users_db:
        st.warning("Το όνομα χρήστη υπάρχει ήδη.")
    else:
        # Ολοι οι νέοι χρήστες είναι αυστηρά 'user'
        st.session_state.users_db[new_user] = {
            "password": new_pass, "role": "user", "name": new_name, "email": new_email, "phone": ""
        }
        save_data("users")
        
        user_subject = "🌱 Καλωσήρθες στο AgroManager Pro"
        user_body = f"Γεια σου {new_name},\n\nΟ λογαριασμός σου δημιουργήθηκε!\nUsername: {new_user}\nPassword: {new_pass}"
        send_email(new_email, user_subject, user_body)

        admin_subject = "🔔 Νέα Εγγραφή Χρήστη"
        admin_body = f"Νέος χρήστης:\nΌνομα: {new_name}\nUsername: {new_user}\nEmail: {new_email}"
        send_email(EMAIL_SENDER, admin_subject, admin_body)

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
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)
        
        if st.session_state.reset_mode:
            with st.container(border=True):
                st.markdown("### 🔄 Ανάκτηση Κωδικού")
                if st.session_state.reset_step == 1:
                    st.info("Εισάγετε το Email που δηλώσατε κατά την εγγραφή.")
                    email_input = st.text_input("Email")
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
                            sent = send_email(email_input, "🔑 Κωδικός Επαναφοράς", f"Κωδικός: {otp}")
                            if sent:
                                st.session_state.reset_step = 2
                                st.toast("Εστάλη!", icon="📧")
                                time.sleep(1)
                                st.rerun()
                            else: st.error("Σφάλμα Email.")
                        else: st.error("Άγνωστο Email.")
                    if col_r2.button("Πίσω", use_container_width=True):
                        st.session_state.reset_mode = False
                        st.rerun()
                elif st.session_state.reset_step == 2:
                    st.success(f"Κωδικός εστάλη στο: {st.session_state.reset_email_target}")
                    code_input = st.text_input("6ψήφιος κωδικός:")
                    new_password = st.text_input("Νέος Κωδικός:", type="password")
                    if st.button("💾 Αλλαγή", use_container_width=True):
                        if code_input == st.session_state.reset_otp:
                            if new_password:
                                uname = st.session_state.reset_username_target
                                st.session_state.users_db[uname]['password'] = new_password
                                save_data("users")
                                st.success("Επιτυχία!")
                                st.session_state.reset_mode = False
                                st.session_state.reset_step = 1
                                time.sleep(2)
                                st.rerun()
                            else: st.warning("Βάλτε κωδικό.")
                        else: st.error("Λάθος κωδικός.")
                    if st.button("Ακύρωση"):
                        st.session_state.reset_mode = False
                        st.rerun()
        else:
            with st.container(border=True):
                tab_login, tab_register = st.tabs(["🔑 Σύνδεση", "📝 Νέα Εγγραφή"])
                with tab_login:
                    username = st.text_input("Username", key="login_user")
                    password = st.text_input("Password", type="password", key="login_pass")
                    if st.button("Είσοδος", use_container_width=True):
                        login_user(username, password)
                    st.markdown("---")
                    if st.button("🆘 Ξέχασα τον κωδικό μου", type="secondary", use_container_width=True):
                        st.session_state.reset_mode = True
                        st.rerun()
                with tab_register:
                    st.markdown("##### Δημιουργία Νέου Λογαριασμού")
                    new_user = st.text_input("Επιθυμητό Username", key="reg_user")
                    new_pass = st.text_input("Κωδικός Πρόσβασης", type="password", key="reg_pass")
                    new_name = st.text_input("Ονοματεπώνυμο", key="reg_name")
                    new_email = st.text_input("Email (Υποχρεωτικό)", key="reg_email")
                    if st.button("Δημιουργία Λογαριασμού", use_container_width=True):
                        if new_user and new_pass and new_name and new_email:
                            with st.spinner("Δημιουργία..."):
                                register_user(new_user, new_pass, new_name, new_email)
                        else: st.error("Συμπληρώστε όλα τα πεδία.")

else:
    # ==================================================
    # 📱 MAIN APP (LOGGED IN)
    # ==================================================
    
    # ΡΥΘΜΙΣΗ ΜΕΝΟΥ: Το Admin panel εμφανίζεται ΜΟΝΟ στον GiannisKrv
    menu_options = ["Dashboard", "Οικονομικά", "Αποθήκη", "Μηχανήματα", "Ημερολόγιο", "Καιρός", "Το Προφίλ μου"]
    menu_icons = ["speedometer2", "wallet2", "box-seam", "truck", "calendar-check", "cloud-sun", "person-circle"]
    
    # --- SECURITY CHECK ΓΙΑ ΤΟ MENU ---
    # Εμφανίζεται ΜΟΝΟ αν το username είναι ακριβώς 'GiannisKrv'
    is_owner_account = st.session_state.current_username == "GiannisKrv"
    
    if is_owner_account:
        menu_options.insert(6, "Διαχείριση Χρηστών")
        menu_icons.insert(6, "people-fill")
    
    menu_options.append("Logout")
    menu_icons.append("box-arrow-right")

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        if is_owner_account:
            st.caption("🔒 OWNER ACCESS")
        
        selected = option_menu(
            menu_title="Μενού",
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast", default_index=0,
            styles={"nav-link-selected": {"background-color": "#2e7d32"}}
        )

    # --- 1. DASHBOARD ---
    if selected == "Dashboard":
        st.title("📊 Επισκόπηση & Στατιστικά")
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        rev = df_inc['revenue'].sum() if not df_inc.empty else 0
        exp = df_exp['amount_total'].sum() if not df_exp.empty else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Ταμείο", f"{rev - exp:.2f} €")
        c2.metric("📈 Έσοδα", f"{rev:.2f} €")
        c3.metric("💸 Έξοδα", f"{exp:.2f} €")
        tasks = st.session_state.calendar_db
        pending = len([t for t in tasks if not t.get('done', False)])
        c4.metric("📅 Εκκρεμότητες", f"{pending}", delta="Εργασίες", delta_color="off")
        st.divider()
        if not df_inc.empty:
            df_inc['year'] = pd.to_datetime(df_inc['date']).dt.year
            yearly_inc = df_inc.groupby('year')['revenue'].sum().reset_index()
            fig = px.bar(yearly_inc, x='year', y='revenue', title="Έσοδα ανά Έτος", color='revenue', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

    # --- 2. ΟΙΚΟΝΟΜΙΚΑ ---
    elif selected == "Οικονομικά":
        st.title("📝 Διαχείριση Οικονομικών")
        t1, t2, t3 = st.tabs(["💵 Έσοδα", "💸 Έξοδα", "🖨️ Αναφορές PDF"])
        with t1:
            with st.expander("➕ Νέα Καταγραφή Παραγωγής", expanded=True):
                with st.form("inc_form"):
                    c1, c2 = st.columns(2)
                    name = c1.selectbox("Καλλιέργεια", ["Βαμβάκι", "Σιτάρι", "Καλαμπόκι", "Ελιά", "Άλλο"])
                    qty = c2.number_input("Ποσότητα (kg)", 0.0)
                    price = st.number_input("Τιμή (€/kg)", 0.0)
                    if st.form_submit_button("💾 Αποθήκευση"):
                        st.session_state.history_log.append({"date": date.today(), "type": "income", "name": name, "quantity": qty, "price": price, "revenue": qty*price})
                        save_data("history")
                        st.success("Αποθηκεύτηκε!")
                        st.rerun()
        with t2:
            with st.expander("➕ Νέο Έξοδο", expanded=True):
                with st.form("exp_form"):
                    cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο", "Εργατικά"])
                    amount = st.number_input("Ποσό (€)", 0.0)
                    desc = st.text_input("Περιγραφή")
                    if st.form_submit_button("💾 Αποθήκευση"):
                        st.session_state.expenses_log.append({"date": date.today(), "type": "expense", "category": cat, "description": desc, "amount_total": amount})
                        save_data("expenses")
                        st.success("Αποθηκεύτηκε!")
                        st.rerun()
        with t3:
            st.subheader("🖨️ Εξαγωγή Αναφορών")
            c1, c2 = st.columns(2)
            if st.session_state.history_log:
                df = pd.DataFrame(st.session_state.history_log)
                c1.download_button("📥 CSV Εσόδων", df.to_csv(index=False).encode('utf-8-sig'), "income.csv")
            if st.session_state.expenses_log:
                df2 = pd.DataFrame(st.session_state.expenses_log)
                c2.download_button("📥 CSV Εξόδων", df2.to_csv(index=False).encode('utf-8-sig'), "expenses.csv")

    # --- 3. ΑΠΟΘΗΚΗ ---
    elif selected == "Αποθήκη":
        st.title("📦 Διαχείριση Αποθήκης")
        with st.expander("➕ Προσθήκη / Ενημέρωση Stock", expanded=False):
            with st.form("stock_form"):
                item = st.text_input("Όνομα Προϊόντος")
                cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Σπόροι", "Φάρμακα", "Ανταλλακτικά"])
                qty = st.number_input("Ποσότητα (+/-)", step=1.0)
                unit = st.selectbox("Μονάδα", ["kg", "lt", "τεμάχια"])
                if st.form_submit_button("Ενημέρωση"):
                    found = False
                    for p in st.session_state.inventory_db:
                        if p['item'] == item:
                            p['quantity'] += qty
                            found = True; break
                    if not found: st.session_state.inventory_db.append({"item": item, "category": cat, "quantity": qty, "unit": unit})
                    save_data("inventory")
                    st.success("Ενημερώθηκε!")
                    st.rerun()
        if st.session_state.inventory_db:
            st.dataframe(pd.DataFrame(st.session_state.inventory_db), use_container_width=True)

    # --- 4. ΜΗΧΑΝΗΜΑΤΑ ---
    elif selected == "Μηχανήματα":
        st.title("🚜 Στόλος")
        with st.expander("➕ Προσθήκη", expanded=False):
            with st.form("mach_form"):
                m_name = st.text_input("Όνομα")
                m_hours = st.number_input("Ώρες", 0)
                last_serv = st.date_input("Service")
                if st.form_submit_button("Προσθήκη"):
                    st.session_state.machinery_db.append({"name": m_name, "hours": m_hours, "last_service": last_serv})
                    save_data("machinery")
                    st.rerun()
        if st.session_state.machinery_db:
            for m in st.session_state.machinery_db:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.subheader(f"🚜 {m['name']}")
                    c1.write(f"⏱️ {m['hours']} ώρες")
                    c2.caption(f"Service: {m['last_service']}")

    # --- 5. ΗΜΕΡΟΛΟΓΙΟ ---
    elif selected == "Ημερολόγιο":
        st.title("📅 Εργασίες")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("task_form"):
                tt = st.text_input("Τίτλος")
                td = st.date_input("Ημερομηνία")
                tp = st.selectbox("Προτεραιότητα", ["Normal", "High"])
                if st.form_submit_button("Προσθήκη"):
                    st.session_state.calendar_db.append({"title": tt, "date": td, "priority": tp, "done": False})
                    save_data("calendar")
                    st.rerun()
        with c2:
            tasks = st.session_state.calendar_db
            tasks.sort(key=lambda x: str(x['date']))
            for i, t in enumerate(tasks):
                cc1, cc2 = st.columns([0.1, 0.9])
                done = cc1.checkbox("", t.get('done', False), key=f"t_{i}")
                if done != t.get('done', False):
                    t['done'] = done
                    save_data("calendar")
                    st.rerun()
                style = f"~~{t['title']}~~" if done else f"**{t['title']}**"
                cc2.markdown(style)

    # --- 6. WEATHER ---
    elif selected == "Καιρός":
        st.title("🌦️ Καιρός & GDD")
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

        st.divider()
        c_crop, c_var, c_base = st.columns(3)
        crop_name = c_crop.text_input("Καλλιέργεια", "Σιτάρι (Demo)")
        crop_var = c_var.text_input("Ποικιλία", "Skelio")
        tbase = c_base.number_input("Tbase", 0.0)

        if st.button("🔄 Λήψη Δεδομένων", type="primary"):
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation&daily=temperature_2m_max,temperature_2m_min&past_days=15"
            st.session_state.weather_data = requests.get(url).json()
            st.session_state.weather_loc_name = display_name
            st.rerun()

        if st.session_state.weather_data:
            d = st.session_state.weather_data
            curr = d['current']
            c1, c2 = st.columns(2)
            c1.metric("Θερμοκρασία", f"{curr['temperature_2m']} °C")
            c2.metric("Βροχή", f"{curr['precipitation']} mm")
            
            daily = d['daily']
            dates = daily['time']
            gdd_cum, acc = [], 0
            for i in range(len(dates)):
                avg = (daily['temperature_2m_max'][i] + daily['temperature_2m_min'][i]) / 2
                acc += max(avg - tbase, 0)
                gdd_cum.append(acc)
            
            st.subheader(f"📈 {crop_name} ({crop_var})")
            st.area_chart(pd.DataFrame({"Date": dates, "GDD": gdd_cum}).set_index("Date"), color="#2e7d32")

        st.divider()
        st.subheader("🛠️ Εργαλεία")
        st.link_button("🚜 EffiSpray", "https://www.effispray.com/el")
        with st.expander("📺 Προβολή"):
            components.iframe("https://www.effispray.com/el", height=600)

    # --- 7. ΠΡΟΦΙΛ (NEW) ---
    elif selected == "Το Προφίλ μου":
        st.title("👤 Το Προφίλ μου")
        curr_u = st.session_state.current_user
        curr_uname = st.session_state.current_username
        
        with st.form("edit_profile"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("Ονοματεπώνυμο", value=curr_u['name'])
            new_email = c2.text_input("Email", value=curr_u['email'])
            new_phone = st.text_input("Τηλέφωνο", value=curr_u.get('phone', ''))
            st.markdown("---")
            new_pass = st.text_input("Νέος Κωδικός (προαιρετικό)", type="password")
            
            if st.form_submit_button("💾 Αποθήκευση"):
                st.session_state.users_db[curr_uname]['name'] = new_name
                st.session_state.users_db[curr_uname]['email'] = new_email
                st.session_state.users_db[curr_uname]['phone'] = new_phone
                if new_pass: st.session_state.users_db[curr_uname]['password'] = new_pass
                save_data("users")
                st.session_state.current_user = st.session_state.users_db[curr_uname]
                st.success("Ενημερώθηκε!")
                time.sleep(1)
                st.rerun()

    # --- 8. ΔΙΑΧΕΙΡΙΣΗ ΧΡΗΣΤΩΝ (ADMIN ONLY - LOCKED TO GiannisKrv) ---
    elif selected == "Διαχείριση Χρηστών":
        # Διπλός έλεγχος ασφαλείας
        if st.session_state.current_username != "GiannisKrv":
            st.error("⛔ Δεν έχετε δικαίωμα πρόσβασης.")
        else:
            st.title("👥 Διαχείριση Εγγεγραμμένων Χρηστών")
            st.info("Λίστα όλων των χρηστών της εφαρμογής.")

            c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 2, 1])
            c1.markdown("**Username**")
            c2.markdown("**Όνομα**")
            c3.markdown("**Email**")
            c4.markdown("**Κωδικός**")
            c5.markdown("**Show**")
            st.divider()
            
            for uname, udata in st.session_state.users_db.items():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 2, 1])
                c1.write(uname)
                c2.write(udata['name'])
                c3.write(udata['email'])
                
                # Logic για εμφάνιση/απόκρυψη κωδικού
                key_vis = f"pass_vis_{uname}"
                if key_vis not in st.session_state: st.session_state[key_vis] = False
                
                if st.session_state[key_vis]:
                    c4.warning(udata['password'])
                    icon = "🙈"
                else:
                    c4.text("••••••••")
                    icon = "👁️"
                
                if c5.button(icon, key=f"btn_{uname}"):
                    st.session_state[key_vis] = not st.session_state[key_vis]
                    st.rerun()
                st.markdown("---")

    elif selected == "Logout":
        logout()
