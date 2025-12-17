import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import datetime # ΝΕΟ: Για να βάζουμε ημερομηνίες

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
# 'my_crops': Κρατάει την ΤΡΕΧΟΥΣΑ κατάσταση (για τα γραφήματα)
if 'my_crops' not in st.session_state:
    st.session_state.my_crops = []

# 'history': Κρατάει ΟΛΕΣ τις εγγραφές (Βιβλιοθήκη)
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
# ΣΕΛΙΔΑ 1: ΔΙΑΧΕΙΡΙΣΗ (ADD/UPDATE)
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

            # Wikipedia check (μικρότερο κουμπί)
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
            # Βρες αν υπάρχει προηγούμενη εγγραφή για να γεμίσεις τα πεδία
            existing = next((item for item in st.session_state.my_crops if item['name'] == current_name), None)
            
            def_qty = existing['quantity'] if existing else 0
            def_moist = existing['moisture'] if existing else 0.0
            def_var = existing['variety'] if existing and 'variety' in existing else ""

            st.subheader("Στοιχεία Εγγραφής")
            col_f1, col_f2 = st.columns(2)
            new_qty = col_f1.number_input("Ποσότητα (kg)", min_value=0, value=def_qty, step=10)
            new_moisture = col_f2.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, value=float(def_moist), step=0.1)
            new_variety = st.text_input("Ποικιλία (π.χ. Κορωνέικη)", value=def_var)
            
            # Ημερομηνία Εγγραφής (Default: Σήμερα)
            date_entry = st.date_input("Ημερομηνία Καταχώρησης", datetime.now())

            submitted = st.form_submit_button("💾 Αποθήκευση στη Βιβλιοθήκη")
            
            if submitted:
                # 1. Ενημέρωση Τρέχουσας Κατάστασης (Για τα γραφήματα)
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
                
                # 2. Προσθήκη στο ΙΣΤΟΡΙΚΟ (Βιβλιοθήκη)
                # Κάθε φορά που πατάς save, φτιάχνεται μια νέα εγγραφή "ιστορίας"
                history_entry = {
                    "date": date_entry,          # Ημερομηνία
                    "year": date_entry.year,     # Έτος (για εύκολο φιλτράρισμα)
                    "name": current_name,
                    "variety": new_variety,
                    "category": current_category,
                    "quantity": new_qty,
                    "moisture": new_moisture
                }
                st.session_state.history.append(history_entry)
                
                st.success(f"Η εγγραφή για '{current_name}' αποθηκεύτηκε στη Βιβλιοθήκη ({date_entry})!")

# ==================================================
# ΣΕΛΙΔΑ 2: ΠΡΟΒΟΛΗ & ΣΤΑΤΙΣΤΙΚΑ (DASHBOARD)
# ==================================================
elif menu_choice == "Προβολή & Στατιστικά":
    st.header("📊 Τρέχουσα Εικόνα Παραγωγής")
    
    if st.session_state.my_crops:
        df = pd.DataFrame(st.session_state.my_crops)
        
        # Κάρτες συνόλων
        total_kg = df['quantity'].sum()
        avg_moist = df['moisture'].mean()
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Συνολική Παραγωγή", f"{total_kg} kg")
        col_m2.metric("Μέση Υγρασία", f"{avg_moist:.1f} %")

        # Γραφήματα
        tab1, tab2 = st.tabs(["Γράφημα Μπάρας", "Πίνακας"])
        with tab1:
            st.bar_chart(df, x="name", y="quantity")
        with tab2:
            st.dataframe(df, use_container_width=True)
            
    else:
        st.info("Δεν υπάρχουν δεδομένα. Πήγαινε στην 'Διαχείριση' για να προσθέσεις.")

# ==================================================
# ΣΕΛΙΔΑ 3: ΒΙΒΛΙΟΘΗΚΗ ΙΣΤΟΡΙΚΟΥ (ΝΕΟ!)
# ==================================================
elif menu_choice == "🗄️ Βιβλιοθήκη Ιστορικού":
    st.header("🗄️ Αρχείο Δεδομένων")
    st.caption("Εδώ βλέπετε όλες τις καταχωρήσεις που έχετε κάνει διαχρονικά.")

    if st.session_state.history:
        # Δημιουργία DataFrame από το ιστορικό
        df_hist = pd.DataFrame(st.session_state.history)
        
        # --- ΦΙΛΤΡΑ ---
        col_filter1, col_filter2 = st.columns(2)
        
        # Φίλτρο Έτους
        available_years = sorted(df_hist['year'].unique(), reverse=True)
        selected_year = col_filter1.selectbox("📅 Επιλογή Έτους", available_years)
        
        # Φίλτρο Είδους (Καλλιέργειας)
        available_crops = ["Όλα"] + sorted(df_hist['name'].unique().tolist())
        selected_crop = col_filter2.selectbox("🌱 Επιλογή Καλλιέργειας", available_crops)
        
        # Εφαρμογή Φίλτρων
        df_filtered = df_hist[df_hist['year'] == selected_year]
        
        if selected_crop != "Όλα":
            df_filtered = df_filtered[df_filtered['name'] == selected_crop]
            
        # Εμφάνιση αποτελεσμάτων
        st.divider()
        st.subheader(f"Αποτελέσματα για: {selected_year}")
        
        if not df_filtered.empty:
            # Μορφοποίηση ημερομηνίας για να φαίνεται ωραία
            df_display = df_filtered.copy()
            df_display['date'] = pd.to_datetime(df_display['date']).dt.strftime('%d/%m/%Y')
            
            # Επιλογή στηλών για εμφάνιση
            cols_to_show = ['date', 'name', 'variety', 'quantity', 'moisture', 'category']
            st.dataframe(df_display[cols_to_show], use_container_width=True)
            
            # Σύνολο φιλτραρισμένων
            sum_filtered = df_filtered['quantity'].sum()
            st.success(f"👉 Συνολική ποσότητα για την επιλογή σας: **{sum_filtered} kg**")
        else:
            st.warning("Δεν βρέθηκαν εγγραφές με αυτά τα κριτήρια.")
            
    else:
        st.info("Η βιβλιοθήκη είναι άδεια. Ξεκινήστε τις καταχωρήσεις!")

# ==================================================
# ΣΕΛΙΔΑ 4: ΚΑΙΡΟΣ
# ==================================================
elif menu_choice == "🌦️ Καιρός":
    st.header("🌦️ Καιρικές Συνθήκες")
    
    user_location = st.text_input("📍 Περιοχή:", value="Larissa")
    
    try:
        geo_url = f"https://geocoding-api.open-
