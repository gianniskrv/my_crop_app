import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import date, datetime, timedelta
import time
import json
import os
from fpdf import FPDF
import base64

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# ==============================================================================
# 💾 DATABASE SYSTEM (ΜΟΝΙΜΗ ΑΠΟΘΗΚΕΥΣΗ)
# ==============================================================================
FILES = {
    "users": "users.json",
    "history": "history.json",
    "expenses": "expenses.json",
    "inventory": "inventory.json",   # 📦 ΝΕΟ: Αποθήκη
    "machinery": "machinery.json",   # 🚜 ΝΕΟ: Μηχανήματα
    "calendar": "calendar.json"      # 📅 ΝΕΟ: Ημερολόγιο
}

# --- ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---
def date_handler(obj):
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    return obj

def load_data():
    # 1. Users
    if os.path.exists(FILES["users"]):
        with open(FILES["users"], 'r', encoding='utf-8') as f: st.session_state.users_db = json.load(f)
    else:
        st.session_state.users_db = {"GiannisKrv": {"password": "21041414", "role": "owner", "name": "Γιάννης", "email": "johnkrv1@gmail.com", "phone": ""}}
        save_data("users")

    # 2. History & Expenses & Others
    for key, file_path in FILES.items():
        if key == "users": continue
        state_key = f"{key}_db" if key not in ["history", "expenses"] else f"{key}_log"
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Date parsing fix
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

# --- PDF GENERATOR (Βασική Υποστήριξη) ---
def create_pdf(dataframe, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    
    # Simple table dump (Note: Greek chars require special fonts in FPDF, using Latin for safety)
    col_width = pdf.w / 4.5
    row_height = 10
    
    # Headers
    headers = [str(c) for c in dataframe.columns]
    for h in headers:
        pdf.cell(col_width, row_height, h[:10], border=1) # Truncate long headers
    pdf.ln(row_height)
    
    # Rows
    for index, row in dataframe.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item)[:10], border=1)
        pdf.ln(row_height)
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

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

def login_user(username, password):
    if username in st.session_state.users_db:
        if st.session_state.users_db[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = st.session_state.users_db[username]
            st.success(f"Καλωσήρθες {st.session_state.current_user['name']}!")
            time.sleep(0.5)
            st.rerun()
        else: st.error("Λάθος κωδικός.")
    else: st.error("Ο χρήστης δεν βρέθηκε.")

def logout():
    st.session_state.authenticated = False
    st.rerun()

# ==================================================
# 🔐 LOGIN SCREEN
# ==================================================
if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #2e7d32;'>🌱 AgroManager Pro</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Είσοδος", use_container_width=True):
                login_user(username, password)
else:
    # ==================================================
    # 📱 MAIN APP
    # ==================================================
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        
        selected = option_menu(
            menu_title="Μενού",
            options=["Dashboard", "Οικονομικά", "Αποθήκη", "Μηχανήματα", "Ημερολόγιο", "Καιρός", "Logout"],
            icons=["speedometer2", "wallet2", "box-seam", "truck", "calendar-check", "cloud-sun", "box-arrow-right"],
            menu_icon="cast", default_index=0,
            styles={"nav-link-selected": {"background-color": "#2e7d32"}}
        )

    # --- 1. DASHBOARD & YEARLY COMPARISON ---
    if selected == "Dashboard":
        st.title("📊 Επισκόπηση & Στατιστικά")
        
        df_inc = pd.DataFrame(st.session_state.history_log)
        df_exp = pd.DataFrame(st.session_state.expenses_log)
        
        # Financials
        rev = df_inc['revenue'].sum() if not df_inc.empty else 0
        exp = df_exp['amount_total'].sum() if not df_exp.empty else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Ταμείο", f"{rev - exp:.2f} €")
        c2.metric("📈 Έσοδα", f"{rev:.2f} €")
        c3.metric("💸 Έξοδα", f"{exp:.2f} €")
        
        # Pending Tasks Count
        tasks = st.session_state.calendar_db
        pending = len([t for t in tasks if not t.get('done', False)])
        c4.metric("📅 Εκκρεμότητες", f"{pending}", delta="Εργασίες", delta_color="off")
        
        st.divider()
        
        # --- NEW: YEAR OVER YEAR COMPARISON ---
        st.subheader("📊 Σύγκριση Ετών (Year-over-Year)")
        if not df_inc.empty:
            df_inc['year'] = pd.to_datetime(df_inc['date']).dt.year
            yearly_inc = df_inc.groupby('year')['revenue'].sum().reset_index()
            
            fig_comp = px.bar(yearly_inc, x='year', y='revenue', title="Έσοδα ανά Έτος", color='revenue', color_continuous_scale='Greens')
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν αρκετά δεδομένα για σύγκριση.")

    # --- 2. ΟΙΚΟΝΟΜΙΚΑ (INCOME/EXPENSES/PDF) ---
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
                        st.session_state.history_log.append({
                            "date": date.today(), "type": "income", "name": name, "quantity": qty, "price": price, "revenue": qty*price
                        })
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
                        st.session_state.expenses_log.append({
                            "date": date.today(), "type": "expense", "category": cat, "description": desc, "amount_total": amount
                        })
                        save_data("expenses")
                        st.success("Αποθηκεύτηκε!")
                        st.rerun()

        with t3:
            st.subheader("🖨️ Εξαγωγή Αναφορών")
            col_p1, col_p2 = st.columns(2)
            if st.session_state.history_log:
                df = pd.DataFrame(st.session_state.history_log)
                col_p1.download_button("📥 Λήψη CSV Εσόδων", df.to_csv(index=False).encode('utf-8-sig'), "income.csv")
                # PDF Button (Basic)
                # pdf_bytes = create_pdf(df, "Income Report")
                # col_p1.download_button("📄 Λήψη PDF (Beta)", data=pdf_bytes, file_name="income_report.pdf", mime='application/pdf')
            
            if st.session_state.expenses_log:
                df2 = pd.DataFrame(st.session_state.expenses_log)
                col_p2.download_button("📥 Λήψη CSV Εξόδων", df2.to_csv(index=False).encode('utf-8-sig'), "expenses.csv")

    # --- 3. ΑΠΟΘΗΚΗ (NEW) ---
    elif selected == "Αποθήκη":
        st.title("📦 Διαχείριση Αποθήκης")
        
        with st.expander("➕ Προσθήκη / Ενημέρωση Stock", expanded=False):
            with st.form("stock_form"):
                item = st.text_input("Όνομα Προϊόντος (π.χ. Ουρία)")
                cat = st.selectbox("Κατηγορία", ["Λιπάσματα", "Σπόροι", "Φάρμακα", "Ανταλλακτικά"])
                qty = st.number_input("Ποσότητα (+ για αγορά, - για χρήση)", step=1.0)
                unit = st.selectbox("Μονάδα", ["kg", "lt", "τεμάχια"])
                
                if st.form_submit_button("Ενημέρωση"):
                    # Logic: Find if exists and update, else create
                    found = False
                    for p in st.session_state.inventory_db:
                        if p['item'] == item:
                            p['quantity'] += qty
                            found = True
                            break
                    if not found:
                        st.session_state.inventory_db.append({"item": item, "category": cat, "quantity": qty, "unit": unit})
                    
                    save_data("inventory")
                    st.success(f"Το απόθεμα για '{item}' ενημερώθηκε!")
                    st.rerun()

        # Display Stock
        if st.session_state.inventory_db:
            df_inv = pd.DataFrame(st.session_state.inventory_db)
            st.dataframe(df_inv, use_container_width=True)
            
            # Low Stock Alert
            low_stock = df_inv[df_inv['quantity'] < 10]
            if not low_stock.empty:
                st.warning(f"⚠️ Χαμηλό απόθεμα σε: {', '.join(low_stock['item'].tolist())}")
        else:
            st.info("Η αποθήκη είναι άδεια.")

    # --- 4. ΜΗΧΑΝΗΜΑΤΑ (NEW) ---
    elif selected == "Μηχανήματα":
        st.title("🚜 Στόλος & Συντήρηση")
        
        with st.expander("➕ Προσθήκη Μηχανήματος", expanded=False):
            with st.form("mach_form"):
                m_name = st.text_input("Όνομα (π.χ. John Deere 6120)")
                m_hours = st.number_input("Ώρες Λειτουργίας", 0)
                last_serv = st.date_input("Τελευταίο Service")
                if st.form_submit_button("Προσθήκη"):
                    st.session_state.machinery_db.append({
                        "name": m_name, "hours": m_hours, "last_service": last_serv
                    })
                    save_data("machinery")
                    st.success("Προστέθηκε!")
                    st.rerun()
        
        if st.session_state.machinery_db:
            for machine in st.session_state.machinery_db:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.subheader(f"🚜 {machine['name']}")
                    c2.write(f"⏱️ **{machine['hours']}** ώρες")
                    
                    # Service Logic
                    last_s = machine['last_service']
                    if isinstance(last_s, str): last_s = datetime.strptime(last_s, "%Y-%m-%d").date()
                    days_diff = (date.today() - last_s).days
                    
                    c3.write(f"📅 Service: {last_s}")
                    if days_diff > 365:
                        st.error(f"⚠️ Service overdue ({days_diff} μέρες)!")
                    else:
                        st.success("✅ Κατάσταση OK")
        else:
            st.info("Δεν έχετε καταχωρήσει μηχανήματα.")

    # --- 5. ΗΜΕΡΟΛΟΓΙΟ (NEW) ---
    elif selected == "Ημερολόγιο":
        st.title("📅 Ημερολόγιο Εργασιών")
        
        c_in, c_view = st.columns([1, 2])
        
        with c_in:
            with st.form("task_form"):
                st.subheader("Νέα Εργασία")
                task_title = st.text_input("Τίτλος (π.χ. Ράντισμα)")
                task_date = st.date_input("Ημερομηνία")
                task_prio = st.selectbox("Προτεραιότητα", ["Normal", "High"])
                if st.form_submit_button("Προσθήκη"):
                    st.session_state.calendar_db.append({
                        "title": task_title, "date": task_date, "priority": task_prio, "done": False
                    })
                    save_data("calendar")
                    st.success("Προστέθηκε!")
                    st.rerun()

        with c_view:
            st.subheader("Προσεχείς Εργασίες")
            tasks = st.session_state.calendar_db
            # Sort by date
            tasks.sort(key=lambda x: str(x['date']))
            
            for i, task in enumerate(tasks):
                # Checkbox to mark as done
                cols = st.columns([0.1, 0.7, 0.2])
                is_done = cols[0].checkbox("", value=task.get('done', False), key=f"task_{i}")
                
                # Style logic
                title_style = f"~~{task['title']}~~" if is_done else f"**{task['title']}**"
                color = "red" if task['priority'] == "High" and not is_done else "black"
                
                cols[1].markdown(f":{color}[{title_style}]")
                cols[2].caption(f"{task['date']}")
                
                # Update state if changed
                if is_done != task.get('done', False):
                    task['done'] = is_done
                    save_data("calendar")
                    time.sleep(0.5)
                    st.rerun()

    # --- 6. WEATHER ---
    elif selected == "Καιρός":
        st.title("🌦️ Καιρός & GDD")
        st.info("Δεδομένα από Open-Meteo API")
        
        col1, col2 = st.columns(2)
        lat = col1.number_input("Latitude", value=39.6390)
        lon = col2.number_input("Longitude", value=22.4191)
        
        if st.button("Ανανέωση"):
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&daily=temperature_2m_max,temperature_2m_min&past_days=10"
                res = requests.get(url).json()
                st.metric("Θερμοκρασία Τώρα", f"{res['current']['temperature_2m']} °C")
                
                # Simple GDD Chart
                daily = res['daily']
                df_w = pd.DataFrame({"Date": daily['time'], "Max Temp": daily['temperature_2m_max']})
                st.line_chart(df_w.set_index("Date"))
            except:
                st.error("Σφάλμα σύνδεσης.")

    elif selected == "Logout":
        logout()
