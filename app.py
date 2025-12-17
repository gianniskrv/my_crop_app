import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager", page_icon="🌱", layout="wide")

# --- 2. ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ (GREEK CROPS) ---
default_crops = [
    {"name": "Βαμβάκι", "category": "Βιομηχανικά", "scientific_name": "Gossypium hirsutum"},
    {"name": "Σιτάρι Σκληρό", "category": "Σιτηρά", "scientific_name": "Triticum durum"},
    {"name": "Καλαμπόκι", "category": "Σιτηρά", "scientific_name": "Zea mays"},
    {"name": "Ηλίανθος", "category": "Βιομηχανικά", "scientific_name": "Helianthus annuus"},
    {"name": "Ελιά (Λαδοελιά)", "category": "Δέντρα", "scientific_name": "Olea europaea"},
    {"name": "Ελιά (Βρώσιμη)", "category": "Δέντρα", "scientific_name": "Olea europaea"},
    {"name": "Πορτοκαλιά", "category": "Εσπεριδοειδή", "scientific_name": "Citrus sinensis"},
    {"name": "Ροδακινιά", "category": "Πυρηνόκαρπα", "scientific_name": "Prunus persica"},
    {"name": "Τομάτα", "category": "Κηπευτικά", "scientific_name": "Solanum lycopersicum"},
    {"name": "Πατάτα", "category": "Κηπευτικά", "scientific_name": "Solanum tuberosum"},
    {"name": "Αμπέλι (Οινοποιήσιμο)", "category": "Αμπέλι", "scientific_name": "Vitis vinifera"},
]

# --- 3. INITIALIZE SESSION STATE ---
if 'my_crops' not in st.session_state:
    st.session_state.my_crops = []

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("Μενού")
menu_choice = st.sidebar.selectbox(
    "Πλοήγηση", 
    ["Διαχείριση & Εισαγωγή", "Προβολή & Στατιστικά", "🗄️ Βιβλιοθήκη Ιστορικού", "🌦️ Καιρός"]
)

# --- 5. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
st.title("🌱 Agricultural Management System")

# ==================================================
# ΣΕΛΙΔΑ 1: ΔΙΑΧΕΙΡΙΣΗ & ΕΙΣΑΓΩΓΗ
# ==================================================
if menu_choice == "Διαχείριση & Εισαγωγή":
    st.header("📝 Καταχώρηση Παραγωγής")
    
    # Επιλογή
    crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
    selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
    
    current_name = ""
    current_category = ""
    current_scientific = ""
    
    if selected_option == "➕ Προσθήκη Νέας...":
        st.info("Δημιουργία νέας καλλιέργειας.")
        col_new1, col_new2 = st.columns(2)
        current_name = col_new1.text_input("Όνομα Καλλιέργειας (π.χ. Καρυδιά)")
        current_category = col_new2.text_input("Κατηγορία (π.χ. Δέντρα)")
    else:
        crop_data = next((item for item in default_crops if item["name"] == selected_option), None)
        if crop_data:
            current_name = crop_data['name']
            current_category = crop_data['category']
            current_scientific = crop_data['scientific_name']
            
            col1, col2 = st.columns(2)
            col1.text_input("Επιστημονικό Όνομα", current_scientific, disabled=True)
            col2.text_input("Κατηγορία", current_category, disabled=True)

            if st.checkbox("Εμφάνιση πληροφοριών Wikipedia"):
                try:
                    with st.spinner('Loading...'):
                        wikipedia.set_lang("el")
                        summary = wikipedia.summary(current_name, sentences=2)
                        st.info(f"📚 {summary}")
                except:
                    st.warning("Δεν βρέθηκαν πληροφορίες.")

    st.divider()
    
    if selected_option == "➕ Προσθήκη Νέας..." and not current_name:
        st.warning("👈 Παρακαλώ συμπληρώστε το Όνομα της νέας καλλιέργειας.")
    else:
        with st.form("crop_form"):
            existing = next((item for item in st.session_state.my_crops if item['name'] == current_name), None)
            
            def_qty = existing['quantity'] if existing else 0
            def_moist = existing['moisture'] if existing else 0.0
            def_var = existing['variety'] if existing and 'variety' in existing else ""

            st.subheader("Στοιχεία Εγγραφής")
            col_f1, col_f2 = st.columns(2)
            new_qty = col_f1.number_input("Ποσότητα (kg)", min_value=0, value=def_qty, step=10)
            new_moisture = col_f2.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, value=float(def_moist), step=0.1)
            new_variety = st.text_input("Ποικιλία (π.χ. Κορωνέικη)", value=def_var)
            
            date_entry = st.date_input("Ημερομηνία Καταχώρησης", datetime.now())

            submitted = st.form_submit_button("💾 Αποθήκευση στη Βιβλιοθήκη")
            
            if submitted:
                # 1. Update Current State
                if existing:
                    existing['quantity'] = new_qty
                    existing['moisture'] = new_moisture
                    existing['variety'] = new_variety
                    existing['category'] = current_category
                else:
                    new_entry = {
                        "name": current_name,
                        "category": current_category,
                        "quantity": new_qty,
                        "moisture": new_moisture,
                        "variety": new_variety
                    }
                    st.session_state.my_crops.append(new_entry)
                
                # 2. Add to History
                history_entry = {
                    "date": date_entry,
                    "year": date_entry.year,
                    "name": current_name,
                    "variety": new_variety,
                    "category": current_category,
                    "quantity": new_qty,
                    "moisture": new_moisture
                }
                st.session_state.history.append(history_entry)
                
                st.success(f"Η εγγραφή για '{current_name}' αποθηκεύτηκε!")

# ==================================================
# ΣΕΛΙΔΑ 2: ΠΡΟΒΟΛΗ & ΣΤΑΤΙΣΤΙΚΑ
# ==================================================
elif menu_choice == "Προβολή & Στατιστικά":
    st.header("📊 Τρέχουσα Εικόνα Παραγωγής")
    
    if st.session_state.my_crops:
        df = pd.DataFrame(st.session_state.my_crops)
        
        total_kg = df['quantity'].sum()
        avg_moist = df['moisture'].mean()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Συνολική Παραγωγή", f"{total_kg} kg")
        col_m2.metric("Μέση Υγρασία", f"{avg_moist:.1f} %")

        tab1, tab2 = st.tabs(["Γράφημα Μπάρας", "Πίνακας"])
        with tab1:
            st.bar_chart(df, x="name", y="quantity")
