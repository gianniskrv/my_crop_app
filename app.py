import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import date, datetime
import time
import smtplib
import ssl
from email.message import EmailMessage

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 👤 ΔΙΑΧΕΙΡΙΣΗ ΧΡΗΣΤΩΝ & SESSION STATE
# ==============================================================================

if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "user": {"password": "123", "role": "user", "name": "Επισκέπτης", "email": "user@example.com"}
    }

# ΕΠΙΒΟΛΗ ΔΙΚΑΙΩΜΑΤΩΝ OWNER
st.session_state.users_db["GiannisKrv"] = {
    "password": "21041414", 
    "role": "owner", 
    "name": "Γιάννης", 
    "email": "johnkrv1@gmail.com" 
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# --- ΑΡΧΙΚΟΠΟΙΗΣΗ DB ---
if 'history_log' not in st.session_state:
    st.session_state.history_log = [] # ΕΣΟΔΑ (Παραγωγή)

if 'expenses_log' not in st.session_state:
    st.session_state.expenses_log = [] # ΕΞΟΔΑ (ΝΕΟ!)

if 'support_messages' not in st.session_state:
    st.session_state.support_messages = []

# ==============================================================================
# 🎨 ΑΣΦΑΛΕΙΑ & ΑΠΟΚΡΥΨΗ MENU
# ==============================================================================
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """

if not st.session_state.authenticated:
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
else:
    if st.session_state.current_user['role'] != 'owner':
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==============================================================================
# 📧 ΡΥΘΜΙΣΕΙΣ EMAIL
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
    except Exception as e:
        st.error(f"Απέτυχε η αποστολή email. Error: {e}")

# --- LOGIN FUNCTIONS ---
def login_user(username, password):
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Λάθος κωδικός πρόσβασης.")
    else:
        st.error("Ο χρήστης δεν βρέθηκε.")

def register_user(new_user, new_pass, new_name, new_email):
    if new_user in st.session_state.users_db:
        st.warning("Το όνομα χρήστη υπάρχει ήδη.")
    else:
        st.session_state.users_db[new_user] = {
            "password": new_pass, 
            "role": "user", 
            "name": new_name,
            "email": new_email 
        }
        st.success("Ο λογαριασμός δημιουργήθηκε! Τώρα μπορείτε να συνδεθείτε.")
        
        body = f"Γεια σου {new_name},\n\nΚαλωσήρθες στο AgroManager Pro!\nΟ λογαριασμός σου ενεργοποιήθηκε επιτυχώς."
        send_email_notification(new_email, "Καλωσήρισες στο AgroManager", body)

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

# ==================================================
# 🔐 ΟΘΟΝΗ ΕΙΣΟΔΟΥ
# ==================================================
if not st.session_state.authenticated:
    st.title("🔐 AgroManager Login")
    tab1, tab2 = st.tabs(["🔑 Σύνδεση", "📝 Εγγραφή"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Είσοδος"):
            login_user(username, password)
            
    with tab2:
        st.write("Δημιουργήστε νέο λογαριασμό:")
        c1, c2 = st.columns(2)
        new_user = c1.text_input("Επιθυμητό Username")
        new_pass = c2.text_input("Επιθυμητό Password", type="password")
        c3, c4 = st.columns(2)
        new_name = c3.text_input("Ονοματεπώνυμο")
        new_email = c4.text_input("Email (για ειδοποιήσεις)")
        
        if st.button("Δημιουργία Λογαριασμού"):
            if new_user and new_pass and new_name and new_email:
                register_user(new_user, new_pass, new_name, new_email)
            else:
                st.warning("Συμπληρώστε όλα τα πεδία.")

else:
    # ==================================================
    # 📱 ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ
    # ==================================================
    with st.sidebar:
        user_role = st.session_state.current_user['role']
        st.info(f"👤 **{st.session_state.current_user['name']}**\nRole: {user_role.upper()}")
        
        # --- ΜΕΝΟΥ ---
        menu_options = [
            "📝 Νέα Καταγραφή (Έσοδα)", # Μετονομάστηκε για σαφήνεια
            "💸 Έξοδα & Ταμείο",          # <--- ΝΕΟ!
            "🗂️ Βιβλιοθήκη & Οικονομικά", 
            "☁️ Καιρός & EffiSpray",
            "🆘 Βοήθεια & Υποστήριξη"
        ]
        
        if user_role in ['owner', 'admin']:
            menu_options.append("📨 Εισερχόμενα Μηνύματα")
        
        if user_role == 'owner':
            st.warning("👑 Owner Mode")
            menu_options.append("👥 Διαχείριση Χρηστών")
        elif user_role == 'admin':
            st.info("🔧 Admin Mode")
            
        if st.button("🚪 Αποσύνδεση"):
            logout()
        st.divider()
        st.title("Μενού")
        menu_choice = st.radio("Πλοήγηση", menu_options)

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

    st.title("🌱 Agricultural Management System")

    # --------------------------------------------------
    # 1. ΚΑΤΑΓΡΑΦΗ ΕΣΟΔΩΝ (ΠΑΡΑΓΩΓΗ)
    # --------------------------------------------------
    if menu_choice == "📝 Νέα Καταγραφή (Έσοδα)":
        st.header("Εισαγωγή Παραγωγής & Πωλήσεων")
        
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
                st.info(f"💵 Έσοδο: **{total_revenue:.2f} €**")

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
                        "type": "income", # Τύπος Εγγραφής
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
    # 2. ΚΑΤΑΓΡΑΦΗ ΕΞΟΔΩΝ (ΝΕΟ!)
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
            vat_rate = c2.selectbox("ΦΠΑ (%)", [0, 6, 13, 24], index=2) # Default 13%
            
            # Υπολογισμός ΦΠΑ
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
    # 3. ΒΙΒΛΙΟΘΗΚΗ & ΟΙΚΟΝΟΜΙΚΑ (ΕΝΗΜΕΡΩΜΕΝΟ)
    # --------------------------------------------------
    elif menu_choice == "🗂️ Βιβλιοθήκη & Οικονομικά":
        st.header("🗂️ Οικονομική Εικόνα & Αρχείο")
        
        # Merge lists just for visualization logic separation
        df_income = pd.DataFrame(st.session_state.history_log)
        df_expense = pd.DataFrame(st.session_state.expenses_log)

        # ΦΙΛΤΡΑ
        all_years = []
        if not df_income.empty: all_years.extend(df_income['year'].unique())
        if not df_expense.empty: all_years.extend(df_expense['year'].unique())
        unique_years = sorted(list(set(all_years)), reverse=True)
        
        if not unique_years:
            st.info("Δεν υπάρχουν εγγραφές ακόμα.")
        else:
            sel_year = st.selectbox("Επιλέξτε Έτος Οικονομικών", unique_years)
            st.divider()
            
            # Υπολογισμοί για το επιλεγμένο έτος
            inc_year = pd.DataFrame()
            exp_year = pd.DataFrame()
            
            if not df_income.empty: 
                inc_year = df_income[df_income['year'] == sel_year]
            if not df_expense.empty: 
                exp_year = df_expense[df_expense['year'] == sel_year]

            total_rev = inc_year['revenue'].sum() if not inc_year.empty else 0.0
            total_exp = exp_year['amount_total'].sum() if not exp_year.empty else 0.0
            net_profit = total_rev - total_exp
            
            # --- DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Έσοδα (Πωλήσεις)", f"{total_rev:.2f} €", delta_color="normal")
            col2.metric("💸 Έξοδα (με ΦΠΑ)", f"{total_exp:.2f} €", delta_color="inverse")
            col3.metric("📉 ΚΑΘΑΡΟ ΚΕΡΔΟΣ", f"{net_profit:.2f} €", delta=f"{net_profit:.2f} €")
            
            st.markdown("---")
            
            tab_inc, tab_exp = st.tabs(["📈 Ανάλυση Εσόδων", "📉 Ανάλυση Εξόδων"])
            
            with tab_inc:
                if inc_year.empty:
                    st.info("Κανένα έσοδο για αυτό το έτος.")
                else:
                    st.dataframe(inc_year[['date', 'name', 'quantity', 'price', 'revenue']], use_container_width=True)
            
            with tab_exp:
                if exp_year.empty:
                    st.info("Κανένα έξοδο για αυτό το έτος.")
                else:
                    # Group by Category
                    st.write("**Έξοδα ανά Κατηγορία**")
                    exp_summary = exp_year.groupby('category')[['amount_net', 'vat_amount', 'amount_total']].sum().reset_index()
                    st.dataframe(exp_summary, use_container_width=True)
                    
                    st.write("**Αναλυτική Λίστα**")
                    st.dataframe(exp_year[['date', 'category', 'description', 'amount_total']], use_container_width=True)

    # --------------------------------------------------
    # 4. ΚΑΙΡΟΣ
    # --------------------------------------------------
    elif menu_choice == "☁️ Καιρός & EffiSpray":
        st.header("🌦️ Πρόγνωση Καιρού")
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

                    st.success(f"📍 Βρέθηκε: **{name}, {country}**")

                    weather_url = (
                        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                        "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
                        "&timezone=auto"
                    )
                    w_res = requests.get(weather_url).json()
                    curr = w_res['current']

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🌡️ Θερμοκρασία", f"{curr['temperature_2m']} °C")
                    c2.metric("💧 Υγρασία", f"{curr['relative_humidity_2m']} %")
                    c3.metric("☔ Βροχή", f"{curr['precipitation']} mm")
                    c4.metric("💨 Άνεμος", f"{curr['wind_speed_10m']} km/h")
                    
                    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
                else:
                    st.warning("Η πόλη δεν βρέθηκε.")
            except:
                st.error("Υπήρξε πρόβλημα με τη σύνδεση.")

        st.divider()
        st.write("### 🚜 Εργαλείο Ψεκασμού (EffiSpray)")
        components.iframe("https://www.effispray.com/el", height=600, scrolling=True)

    # --------------------------------------------------
    # 5. ΒΟΗΘΕΙΑ & ΥΠΟΣΤΗΡΙΞΗ
    # --------------------------------------------------
    elif menu_choice == "🆘 Βοήθεια & Υποστήριξη":
        st.header("🆘 Κέντρο Υποστήριξης")
        st.write("Συμπληρώστε την παρακάτω φόρμα για να επικοινωνήσετε απευθείας με τον διαχειριστή.")
        
        with st.form("support_form"):
            default_email = st.session_state.current_user.get('email', '')
            sender_email = st.text_input("Το Email σας (για να λάβετε απάντηση) *", value=default_email)
            subject = st.text_input("Θέμα Μηνύματος *", placeholder="π.χ. Πρόβλημα με την εγγραφή...")
            msg_body = st.text_area("Το μήνυμά σας *", placeholder="Γράψτε εδώ λεπτομέρειες...")
            
            submit_support = st.form_submit_button("📨 Αποστολή Μηνύματος")
            
            if submit_support:
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
                    email_subj_formatted = f"🔔 AgroManager Support: {subject}"
                    email_body_formatted = (
                        f"Νέο μήνυμα υποστήριξης από: {st.session_state.current_user['name']}\n"
                        f"Email Επικοινωνίας: {sender_email}\n\n"
                        f"Θέμα: {subject}\n"
                        f"------------------------------------------------\n"
                        f"{msg_body}\n"
                        f"------------------------------------------------\n"
                    )
                    send_email_notification(admin_email, email_subj_formatted, email_body_formatted)
                    
                    st.success("Το μήνυμά σας εστάλη επιτυχώς!")
                else:
                    st.error("⚠️ Παρακαλώ συμπληρώστε όλα τα πεδία.")

    # --------------------------------------------------
    # 6. ΕΙΣΕΡΧΟΜΕΝΑ ΜΗΝΥΜΑΤΑ (OWNER & ADMIN)
    # --------------------------------------------------
    elif menu_choice == "📨 Εισερχόμενα Μηνύματα":
         if st.session_state.current_user['role'] not in ['owner', 'admin']:
             st.stop()
             
         st.header("📨 Εισερχόμενα Μηνύματα Χρηστών")
         
         if not st.session_state.support_messages:
             st.info("Δεν υπάρχουν νέα μηνύματα.")
         else:
             msg_df = pd.DataFrame(st.session_state.support_messages)
             msg_df = msg_df.iloc[::-1]
             
             st.dataframe(
                 msg_df,
                 column_config={
                     "timestamp": "Ημερομηνία",
                     "user": "Χρήστης",
                     "email": "Email Απάντησης",
                     "subject": "Θέμα",
                     "message": "Μήνυμα"
                 },
                 use_container_width=True,
                 hide_index=True
             )

    # --------------------------------------------------
    # 7. ΔΙΑΧΕΙΡΙΣΗ ΧΡΗΣΤΩΝ (OWNER ONLY)
    # --------------------------------------------------
    elif menu_choice == "👥 Διαχείριση Χρηστών":
        if st.session_state.current_user['role'] != 'owner':
             st.error("⛔ ΑΠΑΓΟΡΕΥΕΤΑΙ Η ΠΡΟΣΒΑΣΗ.")
             st.stop()
        
        st.header("👑 Πίνακας Ελέγχου Owner")
        
        with st.expander("➕ Προσθήκη Νέου Χρήστη", expanded=True):
            with st.form("create_user_admin_form"):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Username")
                new_p = c2.text_input("Password")
                c3, c4 = st.columns(2)
                new_n = c3.text_input("Όνομα")
                new_e = c4.text_input("Email")
                new_role = st.selectbox("Ρόλος", ["user", "admin"])
                
                if st.form_submit_button("Δημιουργία"):
                    if new_u and new_p and new_n:
                        st.session_state.users_db[new_u] = {
                            "password": new_p,
                            "role": new_role,
                            "name": new_n,
                            "email": new_e
                        }
                        st.success("Δημιουργήθηκε!")
                        st.rerun()

        st.divider()
        st.subheader("📋 Λίστα Εγγεγραμμένων")

        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 2, 1, 2, 1])
        h1.markdown("**Username**")
        h2.markdown("**Όνομα**")
        h3.markdown("**Email**")
        h4.markdown("**Ρόλος**")
        h5.markdown("**Κωδικός**")
        h6.markdown("**Προβολή**")
        st.divider()

        for uname, udata in st.session_state.users_db.items():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 1, 2, 1])
            c1.write(uname)
            c2.write(udata['name'])
            c3.write(udata.get('email', '-'))
            r = udata['role']
            if r == 'owner': c4.error("OWNER")
            elif r == 'admin': c4.warning("ADMIN")
            else: c4.success("USER")
            
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
