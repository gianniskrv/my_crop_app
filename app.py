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
# 💾 DATABASE SYSTEM
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

def date_handler(obj):
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    return obj

def load_data():
    if os.path.exists(FILES["users"]):
        with open(FILES["users"], 'r', encoding='utf-8') as f: st.session_state.users_db = json.load(f)
    else: st.session_state.users_db = {}

    if "GiannisKrv" not in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"] = {"password": "change_me", "role": "owner", "name": "Γιάννης", "email": "johnkrv1@gmail.com", "phone": ""}
    if "GiannisKrv" in st.session_state.users_db:
        st.session_state.users_db["GiannisKrv"]["role"] = "owner"
        if not os.path.exists(FILES["users"]): save_data("users")

    for key, file_path in FILES.items():
        if key == "users": continue
        state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for d in data:
                        if 'date' in d and isinstance(d['date'], str):
                            try: d['date'] = datetime.strptime(d['date'][:10], "%Y-%m-%d").date()
                            except: pass
                st.session_state[state_key] = data
        else: st.session_state[state_key] = []

def save_data(key):
    target_file = FILES.get(key)
    state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
    if target_file and state_key in st.session_state:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state[state_key], f, default=date_handler, indent=4, ensure_ascii=False)

def image_to_base64(uploaded_file):
    if uploaded_file is None: return None
    try: return base64.b64encode(uploaded_file.getvalue()).decode()
    except: return None

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
    div[data-testid="stExpander"] details summary p { font-weight: bold; font-size: 1.05rem; color: #2e7d32; }
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
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.session_state.current_username = username
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(0.5); st.rerun()
        else: st.error("Λάθος κωδικός.")
    else: st.error("Ο χρήστης δεν βρέθηκε.")

def register_user(new_user, new_pass, new_name, new_email):
    if new_user in st.session_state.users_db: st.warning("Το όνομα χρήστη υπάρχει ήδη.")
    else:
        st.session_state.users_db[new_user] = {"password": new_pass, "role": "user", "name": new_name, "email": new_email, "phone": ""}
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
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)
        if st.session_state.reset_mode:
            with st.container(border=True):
                st.markdown("### 🔄 Ανάκτηση Κωδικού")
                if st.session_state.reset_step == 1:
                    email_input = st.text_input("Email")
                    if st.button("Αποστολή Κωδικού", use_container_width=True):
                        found_user = None
                        for uname, udata in st.session_state.users_db.items():
                            if udata.get('email') == email_input: found_user = uname; break
                        if found_user:
                            otp = str(random.randint(100000, 999999))
                            st.session_state.reset_otp = otp
                            st.session_state.reset_email_target = email_input
                            st.session_state.reset_username_target = found_user
                            if send_email(email_input, "🔑 Κωδικός Επαναφοράς", f"Κωδικός: {otp}"):
                                st.session_state.reset_step = 2; st.toast("Εστάλη!", icon="📧"); time.sleep(1); st.rerun()
                            else: st.error("Σφάλμα Email.")
                        else: st.error("Άγνωστο Email.")
                    if st.button("Πίσω"): st.session_state.reset_mode = False; st.rerun()
                elif st.session_state.reset_step == 2:
                    code_input = st.text_input("6ψήφιος κωδικός:")
                    new_password = st.text_input("Νέος Κωδικός:", type="password")
                    if st.button("💾 Αλλαγή", use_container_width=True):
                        if code_input == st.session_state.reset_otp:
                            st.session_state.users_db[st.session_state.reset_username_target]['password'] = new_password
                            save_data("users")
                            st.success("Επιτυχία!"); st.session_state.reset_mode = False; st.session_state.reset_step = 1; time.sleep(2); st.rerun()
                        else: st.error("Λάθος κωδικός.")
        else:
            with st.container(border=True):
                tab_login, tab_register = st.tabs(["🔑 Σύνδεση", "📝 Νέα Εγγραφή"])
                with tab_login:
                    username = st.text_input("Username", key="login_user")
                    password = st.text_input("Password", type="password", key="login_pass")
                    if st.button("Είσοδος", use_container_width=True): login_user(username, password)
                    if st.button("🆘 Ξέχασα τον κωδικό μου", type="secondary", use_container_width=True): st.session_state.reset_mode = True; st.rerun()
                with tab_register:
                    new_user = st.text_input("Username", key="reg_user")
                    new_pass = st.text_input("Password", type="password", key="reg_pass")
                    new_name = st.text_input("Όνομα", key="reg_name")
                    new_email = st.text_input("Email", key="reg_email")
                    if st.button("Δημιουργία", use_container_width=True):
                        if new_user and new_pass and new_name and new_email:
                            with st.spinner("Δημιουργία..."): register_user(new_user, new_pass, new_name, new_email)
                        else: st.error("Συμπληρώστε όλα τα πεδία.")

else:
    # ==================================================
    # 📱 MAIN APP (LOGGED IN)
    # ==================================================
    current_role = st.session_state.current_user.get('role', 'user')
    is_owner = (current_role == 'owner')
    is_admin = (current_role == 'admin')

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        if is_owner: st.caption("🔒 OWNER ACCESS")
        elif is_admin: st.caption("🛡️ ADMIN ACCESS")
        else: st.caption("MEMBER")
        st.divider()

        # 1. ΔΙΑΧΕΙΡΙΣΗ
        with st.expander("🚜 Διαχείριση & Οργάνωση", expanded=True):
            opt_mng = option_menu(None, ["Dashboard", "Οικονομικά", "Αποθήκη", "Μηχανήματα", "Ημερολόγιο"], 
                icons=["speedometer2", "wallet2", "box-seam", "truck", "calendar-check"], default_index=0, key="nav_mng")

        # 2. ΓΕΩΡΓΙΑ & ΚΑΙΡΟΣ (ΔΙΑΧΩΡΙΣΜΟΣ)
        with st.expander("🌦️ Γεωργία & Καιρός", expanded=True):
            opt_agro = option_menu(None, ["Καιρός", "GDD & Ανάπτυξη"], 
                icons=["cloud-sun", "graph-up-arrow"], default_index=0, key="nav_agro")

        # 3. ΓΕΝΙΚΑ
        with st.expander("⚙️ Γενικά & Προφίλ", expanded=True):
            gen_options = ["Μηνύματα", "Βοήθεια", "Το Προφίλ μου"]
            gen_icons = ["chat-text", "life-preserver", "person-circle"]
            if is_owner or is_admin:
                gen_options.append("Διαχείριση Χρηστών")
                gen_icons.append("people-fill")
            gen_options.append("Logout")
            gen_icons.append("box-arrow-right")
            opt_gen = option_menu(None, gen_options, icons=gen_icons, default_index=0, key="nav_gen")

    # SYNC MENU LOGIC
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
        st.title("📊 Επισκόπηση")
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        rev = df_inc['revenue'].sum() if not df_inc.empty else 0
        exp = df_exp['amount_total'].sum() if not df_exp.empty else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Ταμείο", f"{rev - exp:.2f} €")
        c2.metric("📈 Έσοδα", f"{rev:.2f} €")
        c3.metric("💸 Έξοδα", f"{exp:.2f} €")
        st.divider()
        if not df_inc.empty:
            df_inc['year'] = pd.to_datetime(df_inc['date']).dt.year
            yearly_inc = df_inc.groupby('year')['revenue'].sum().reset_index()
            fig = px.bar(yearly_inc, x='year', y='revenue', title="Έσοδα ανά Έτος", color='revenue', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

    elif selected == "Οικονομικά":
        st.title("📝 Οικονομικά")
        t1, t2 = st.tabs(["Έσοδα", "Έξοδα"])
        with t1:
            with st.form("inc_form"):
                c1, c2 = st.columns(2)
                name = c1.selectbox("Καλλιέργεια", ["Βαμβάκι", "Σιτάρι", "Καλαμπόκι", "Ελιά"])
                qty = c2.number_input("Ποσότητα (kg)", 0.0)
                price = st.number_input("Τιμή (€/kg)", 0.0)
                if st.form_submit_button("💾 Αποθήκευση"):
                    st.session_state.history_log.append({"date": date.today(), "type": "income", "name": name, "quantity": qty, "price": price, "revenue": qty*price})
                    save_data("history")
                    st.success("ΟΚ!")
                    st.rerun()
        with t2:
            with st.form("exp_form"):
                cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Φάρμακα", "Πετρέλαιο"])
                amount = st.number_input("Ποσό (€)", 0.0)
                desc = st.text_input("Περιγραφή")
                if st.form_submit_button("💾 Αποθήκευση"):
                    st.session_state.expenses_log.append({"date": date.today(), "type": "expense", "category": cat, "description": desc, "amount_total": amount})
                    save_data("expenses")
                    st.success("ΟΚ!")
                    st.rerun()

    elif selected == "Αποθήκη":
        st.title("📦 Αποθήκη")
        with st.form("stock_form"):
            item = st.text_input("Προϊόν")
            qty = st.number_input("Ποσότητα", step=1.0)
            if st.form_submit_button("Ενημέρωση"):
                st.session_state.inventory_db.append({"item": item, "quantity": qty})
                save_data("inventory")
                st.success("ΟΚ!")
                st.rerun()
        if st.session_state.inventory_db: st.dataframe(pd.DataFrame(st.session_state.inventory_db), use_container_width=True)

    elif selected == "Μηχανήματα":
        st.title("🚜 Στόλος")
        with st.form("mach_form"):
            m_name = st.text_input("Όνομα")
            m_hours = st.number_input("Ώρες", 0)
            if st.form_submit_button("Προσθήκη"):
                st.session_state.machinery_db.append({"name": m_name, "hours": m_hours})
                save_data("machinery")
                st.rerun()
        if st.session_state.machinery_db: st.dataframe(pd.DataFrame(st.session_state.machinery_db), use_container_width=True)

    elif selected == "Ημερολόγιο":
        st.title("📅 Εργασίες")
        with st.form("task_form"):
            tt = st.text_input("Τίτλος")
            td = st.date_input("Ημερομηνία")
            if st.form_submit_button("Προσθήκη"):
                st.session_state.calendar_db.append({"title": tt, "date": td, "done": False})
                save_data("calendar")
                st.rerun()
        for i, t in enumerate(st.session_state.calendar_db):
            c1, c2 = st.columns([0.1, 0.9])
            done = c1.checkbox("", t.get('done', False), key=f"t_{i}")
            if done != t.get('done', False): t['done'] = done; save_data("calendar"); st.rerun()
            c2.write(f"~~{t['title']}~~" if done else f"**{t['title']}**")

    # --- ΚΑΙΡΟΣ (ΑΠΛΟΠΟΙΗΜΕΝΟ) ---
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
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
                st.session_state.weather_data = requests.get(url).json()
                st.session_state.weather_loc_name = display_name
                st.rerun()
            except: st.error("Σφάλμα σύνδεσης.")

        if st.session_state.weather_data:
            d = st.session_state.weather_data
            curr = d.get('current', {})
            st.success(f"📍 {st.session_state.weather_loc_name}")
            c1, c2 = st.columns(2)
            c1.metric("Θερμοκρασία", f"{curr.get('temperature_2m', '-')} °C")
            c2.metric("Βροχή", f"{curr.get('precipitation', '-')} mm")
            
            # Simple Chart
            daily = d.get('daily', {})
            if daily:
                chart_df = pd.DataFrame({"Date": daily['time'], "Max Temp": daily['temperature_2m_max']})
                st.line_chart(chart_df.set_index("Date"))

    # --- GDD & TOOLS (ΧΩΡΙΣ DEMO) ---
    elif selected == "GDD & Ανάπτυξη":
        st.title("📈 Ανάπτυξη Φυτών & Εργαλεία")
        
        # Πρέπει να υπάρχει καιρός
        if not st.session_state.weather_data:
            st.warning("⚠️ Πηγαίνετε στην καρτέλα 'Καιρός' και πατήστε 'Λήψη Καιρού' πρώτα!")
        else:
            d = st.session_state.weather_data
            daily = d.get('daily', {})
            
            c_crop, c_var, c_base = st.columns(3)
            # Αφαίρεση του (Demo)
            crop_name = c_crop.text_input("Καλλιέργεια", "Σιτάρι") 
            crop_var = c_var.text_input("Ποικιλία", "Skelio")
            tbase = c_base.number_input("Tbase", 0.0)
            
            dates = daily['time']
            gdd_cum, acc = [], 0
            for i in range(len(dates)):
                avg = (daily['temperature_2m_max'][i] + daily['temperature_2m_min'][i]) / 2
                acc += max(avg - tbase, 0)
                gdd_cum.append(acc)
            
            st.subheader(f"GDD: {crop_name} ({crop_var})")
            st.area_chart(pd.DataFrame({"Date": dates, "GDD": gdd_cum}).set_index("Date"), color="#2e7d32")
            
            st.divider()
            st.subheader("🛠️ Εργαλεία")
            st.link_button("🚜 EffiSpray", "https://www.effispray.com/el")
            with st.expander("📺 Προβολή"):
                components.iframe("https://www.effispray.com/el", height=600, scrolling=True)

    elif selected == "Μηνύματα":
        st.title("💬 Μηνύματα")
        with st.expander("✉️ Νέο Μήνυμα"):
            with st.form("msg_form"):
                to = st.text_input("Προς (Username)")
                body = st.text_area("Μήνυμα")
                if st.form_submit_button("Αποστολή"):
                    st.session_state.messages_db.append({"from": st.session_state.current_username, "to": to, "body": body, "time": str(datetime.now())})
                    save_data("messages")
                    st.success("Εστάλη!")
        
        # Inbox
        msgs = [m for m in st.session_state.messages_db if m.get('to') == st.session_state.current_username or (is_owner and m.get('to') == "Support")]
        for m in reversed(msgs):
            st.info(f"Από: {m.get('from')} | {m.get('time')}\n\n{m.get('body')}")

    elif selected == "Βοήθεια":
        st.title("🆘 Help Desk")
        with st.form("help"):
            sub = st.text_input("Θέμα")
            desc = st.text_area("Περιγραφή")
            if st.form_submit_button("Αποστολή"):
                st.session_state.messages_db.append({"from": st.session_state.current_username, "to": "Support", "body": f"Subject: {sub}\n{desc}", "time": str(datetime.now())})
                save_data("messages")
                send_email(EMAIL_SENDER, "Support Ticket", f"{sub}\n{desc}")
                st.success("OK")

    elif selected == "Το Προφίλ μου":
        st.title("👤 Προφίλ")
        with st.form("prof"):
            new_pass = st.text_input("Νέος Κωδικός", type="password")
            if st.form_submit_button("Αλλαγή"):
                st.session_state.users_db[st.session_state.current_username]['password'] = new_pass
                save_data("users")
                st.success("OK")

    elif selected == "Διαχείριση Χρηστών":
        if is_owner or is_admin:
            st.title("👥 Users")
            st.dataframe(pd.DataFrame(st.session_state.users_db).T)
        else: st.error("No Access")

    elif selected == "Logout":
        logout()
