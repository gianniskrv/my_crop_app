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

# ΕΠΙΒΟΛΗ ΔΙΚΑΙΩΜΑΤΩΝ OWNER (Μόνο εσύ)
st.session_state.users_db["GiannisKrv"] = {
    "password": "21041414", 
    "role": "owner",  # <--- ΑΛΛΑΓΗ ΣΕ OWNER
    "name": "Γιάννης", 
    "email": "johnkrv1@gmail.com" 
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# --- ΑΡΧΙΚΟΠΟΙΗΣΗ ΙΣΤΟΡΙΚΟΥ & ΜΗΝΥΜΑΤΩΝ ---
if 'history_log' not in st.session_state:
    st.session_state.history_log = []

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

# ΛΟΓΙΚΗ: 
# Αν δεν είναι συνδεδεμένος -> ΚΡΥΨΕ ΤΑ ΠΑΝΤΑ
# Αν είναι συνδεδεμένος και ΔΕΝ είναι Owner -> ΚΡΥΨΕ ΤΑ ΠΑΝΤΑ
# Μόνο ο OWNER βλέπει τα εργαλεία προγραμματιστή (Manage app)
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

# Η δημόσια εγγραφή φτιάχνει πάντα 'user'
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
        st.write("Δημιουργήστε νέο λογαριασμό (Ρόλος: User):")
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
            "📝 Νέα Καταγραφή", 
            "🗂️ Βιβλιοθήκη & Οικονομικά", 
            "☁️ Καιρός & EffiSpray",
            "🆘 Βοήθεια & Υποστήριξη"
        ]
        
        # O OWNER και ο ADMIN βλέπουν τα μηνύματα
        if user_role in ['owner', 'admin']:
            menu_options.append("📨 Εισερχόμενα Μηνύματα")
        
        # ΜΟΝΟ O OWNER βλέπει τη διαχείριση χρηστών (για να φτιάχνει Admins)
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

    # --- DB ---
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
    # 1. ΝΕΑ ΚΑΤΑΓΡΑΦΗ
    # --------------------------------------------------
    if menu_choice == "📝 Νέα Καταγραφή":
        st.header("Εισαγωγή Παραγωγής & Οικονομικών")
        
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
                
                if st.checkbox("🔍 Πληροφορίες από Wikipedia"):
                    try:
                        with st.spinner('Αναζήτηση...'):
                            wikipedia.set_lang("el")
                            search_term = crop_data.get('wiki_term', current_name)
                            summary = wikipedia.summary(search_term, sentences=2)
                            st.caption(f"📚 **{search_term}:** {summary}")
                    except:
                        st.warning(f"Δεν βρέθηκαν πληροφορίες.")

        st.divider()
        
        with st.form("entry_form"):
            st.subheader("Στοιχεία Εγγραφής")
            c1, c2 = st.columns(2)
            rec_date = c1.date_input("Ημερομηνία", date.today())
            rec_variety = c2.text_input("Ποικιλία", placeholder="π.χ. Κορωνέικη")
            
            st.markdown("---")
            st.write("💰 **Οικονομικά & Ποσότητες**")
            
            c3, c4, c5 = st.columns(3)
            rec_qty = c3.number_input("Ποσότητα (kg)", min_value=0, step=10)
            rec_moisture = c4.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, step=0.1)
            rec_price = c5.number_input("Τιμή Πώλησης (€/kg)", min_value=0.0, step=0.01, format="%.2f")
            
            total_revenue = rec_qty * rec_price
            if rec_qty > 0 and rec_price > 0:
                st.info(f"💵 Εκτιμώμενο Έσοδο: **{total_revenue:.2f} €**")

            notes = st.text_area("Σημειώσεις", placeholder="Παρατηρήσεις...")
            submitted = st.form_submit_button("💾 Αποθήκευση")
            
            if submitted:
                if not current_name:
                    st.error("Συμπλήρωσε όνομα καλλιέργειας!")
                else:
                    new_entry = {
                        "user": st.session_state.current_user['name'],
                        "date": rec_date,
                        "year": rec_date.year,
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
                    st.success(f"Αποθηκεύτηκε: {current_name} ({total_revenue:.2f}€)")
                    
                    user_mail = st.session_state.current_user.get('email')
                    if user_mail and "@" in user_mail:
                        email_subject = f"Νέα Πώληση: {current_name}"
                        email_body = (
                            f"Γεια σου {st.session_state.current_user['name']},\n\n"
                            f"Καταχωρήθηκε νέα εγγραφή:\n"
                            f"- Καλλιέργεια: {current_name}\n"
                            f"- Ποσότητα: {rec_qty} kg\n"
                            f"- Τιμή: {rec_price} €/kg\n"
                            f"- ΣΥΝΟΛΟ ΕΣΟΔΩΝ: {total_revenue:.2f} €\n\n"
                            f"Ημερομηνία: {rec_date}"
                        )
                        send_email_notification(user_mail, email_subject, email_body)

    # --------------------------------------------------
    # 2. ΒΙΒΛΙΟΘΗΚΗ
    # --------------------------------------------------
    elif menu_choice == "🗂️ Βιβλιοθήκη & Οικονομικά":
        st.header("🗂️ Αρχείο & Οικονομικά Στοιχεία")

        if not st.session_state.history_log:
            st.info("Δεν υπάρχουν δεδομένα ακόμα.")
        else:
            df = pd.DataFrame(st.session_state.history_log)
            
            with st.expander("🔍 Αναζήτηση & Φίλτρα", expanded=True):
                col_f1, col_f2 = st.columns(2)
                years = sorted(df['year'].unique(), reverse=True)
                sel_year = col_f1.selectbox("Έτος", years)
                
                df_year = df[df['year'] == sel_year]
                crops = sorted(df_year['name'].unique())
                sel_crops = col_f2.multiselect("Καλλιέργειες", crops)

            st.divider()
            
            df_final = df_year[df_year['name'].isin(sel_crops)] if sel_crops else df_year

            if df_final.empty:
                st.warning("Κανένα αποτέλεσμα.")
            else:
                st.subheader(f"Οικονομικά Στοιχεία {sel_year}")
                
                total_income_year = df_final['revenue'].sum()
                total_kg_year = df_final['quantity'].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("💰 Συνολικά Έσοδα Έτους", f"{total_income_year:.2f} €")
                m2.metric("⚖️ Συνολική Παραγωγή", f"{total_kg_year} kg")
                
                st.write("📊 **Ανάλυση ανά Προϊόν**")
                summary = df_final.groupby(['name'])[['quantity', 'revenue']].sum().reset_index()
                st.dataframe(
                    summary.style.format({"revenue": "{:.2f} €"}), 
                    use_container_width=True
                )

                st.divider()
                st.write("📝 **Αναλυτικό Ιστορικό**")
                for i, row in df_final.sort_values(by='date', ascending=False).iterrows():
                    with st.container():
                        rev = row.get('revenue', 0)
                        prc = row.get('price', 0)
                        
                        c_txt, c_money = st.columns([3, 1])
                        c_txt.markdown(f"**{row['name']}** - {row['variety']} ({row['date']})")
                        c_txt.caption(f"Ποσότητα: {row['quantity']}kg | Τιμή: {prc} €/kg")
                        
                        c_money.metric("Έσοδο", f"{rev:.2f} €")
                        st.markdown("---")

    # --------------------------------------------------
    # 3. ΚΑΙΡΟΣ
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
    # 4. ΒΟΗΘΕΙΑ & ΥΠΟΣΤΗΡΙΞΗ
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
    # 5. ΕΙΣΕΡΧΟΜΕΝΑ ΜΗΝΥΜΑΤΑ (OWNER & ADMIN)
    # --------------------------------------------------
    elif menu_choice == "📨 Εισερχόμενα Μηνύματα":
         # Έλεγχος: Μόνο Owner και Admin μπαίνουν εδώ
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
    # 6. ΔΙΑΧΕΙΡΙΣΗ ΧΡΗΣΤΩΝ (OWNER ONLY)
    # --------------------------------------------------
    elif menu_choice == "👥 Διαχείριση Χρηστών":
        # ⚠️ ΑΠΟΚΛΕΙΣΤΙΚΑ ΓΙΑ OWNER ⚠️
        if st.session_state.current_user['role'] != 'owner':
             st.error("⛔ ΑΠΑΓΟΡΕΥΕΤΑΙ Η ΠΡΟΣΒΑΣΗ. Μόνο ο Ιδιοκτήτης έχει πρόσβαση εδώ.")
             st.stop()
        
        st.header("👑 Πίνακας Ελέγχου Owner")
        st.caption("Εδώ μπορείτε να δημιουργήσετε νέους χρήστες και να ορίσετε αν θα είναι Admin ή User.")
        
        # --- ΦΟΡΜΑ ΔΗΜΙΟΥΡΓΙΑΣ ΝΕΟΥ ΧΡΗΣΤΗ (ΜΕ ΕΠΙΛΟΓΗ ΡΟΛΟΥ) ---
        with st.expander("➕ Προσθήκη Νέου Χρήστη (Admin/User)", expanded=True):
            with st.form("create_user_admin_form"):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Username")
                new_p = c2.text_input("Password")
                
                c3, c4 = st.columns(2)
                new_n = c3.text_input("Όνομα")
                new_e = c4.text_input("Email")
                
                # ΕΠΙΛΟΓΗ ΡΟΛΟΥ
                new_role = st.selectbox("Ρόλος", ["user", "admin"])
                
                submit_create = st.form_submit_button("Δημιουργία Χρήστη")
                
                if submit_create:
                    if new_u and new_p and new_n:
                        if new_u in st.session_state.users_db:
                            st.warning("Το Username υπάρχει ήδη.")
                        else:
                            st.session_state.users_db[new_u] = {
                                "password": new_p,
                                "role": new_role, # Αποθηκεύουμε τον ρόλο που διάλεξες
                                "name": new_n,
                                "email": new_e
                            }
                            st.success(f"Ο χρήστης {new_u} δημιουργήθηκε ως {new_role.upper()}!")
                            st.rerun()
                    else:
                        st.warning("Συμπληρώστε τα βασικά πεδία.")

        st.divider()
        st.subheader("📋 Λίστα Εγγεγραμμένων")

        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 2, 1, 2, 1])
        h1.markdown("**Username**")
        h2.markdown("**Όνομα**")
        h3.markdown("**Email**")
        h4.markdown("**Ρόλος**") # Νέα στήλη για να βλέπεις ποιος είναι τι
        h5.markdown("**Κωδικός**")
        h6.markdown("**Προβολή**")
        st.divider()

        for uname, udata in st.session_state.users_db.items():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 1, 2, 1])
            
            c1.write(uname)
            c2.write(udata['name'])
            c3.write(udata.get('email', '-'))
            
            # Εμφάνιση Ρόλου με χρώμα
            r = udata['role']
            if r == 'owner':
                c4.error("OWNER")
            elif r == 'admin':
                c4.warning("ADMIN")
            else:
                c4.success("USER")
            
            toggle_key = f"vis_{uname}"
            if toggle_key not in st.session_state:
                st.session_state[toggle_key] = False
            
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
