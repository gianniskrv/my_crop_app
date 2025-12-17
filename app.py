import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import date

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# --- 2. ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ (GREEK CROPS) ---
# Προστέθηκε το 'wiki_term' για σωστή αναζήτηση στη Wikipedia
default_crops = [
    {"name": "Βαμβάκι", "category": "Βιομηχανικά", "scientific_name": "Gossypium hirsutum", "wiki_term": "Βαμβάκι (φυτό)"},
    {"name": "Σιτάρι Σκληρό", "category": "Σιτηρά", "scientific_name": "Triticum durum", "wiki_term": "Σίτος"},
    {"name": "Καλαμπόκι", "category": "Σιτηρά", "scientific_name": "Zea mays", "wiki_term": "Αραβόσιτος"},
    {"name": "Ηλίανθος", "category": "Βιομηχανικά", "scientific_name": "Helianthus annuus", "wiki_term": "Ηλίανθος"},
    {"name": "Ελιά (Λαδοελιά)", "category": "Δέντρα", "scientific_name": "Olea europaea", "wiki_term": "Ελιά"},
    {"name": "Ελιά (Βρώσιμη)", "category": "Δέντρα", "scientific_name": "Olea europaea", "wiki_term": "Ελιά"},
    {"name": "Πορτοκαλιά", "category": "Εσπεριδοειδή", "scientific_name": "Citrus sinensis", "wiki_term": "Πορτοκαλιά"},
    {"name": "Ροδακινιά", "category": "Πυρηνόκαρπα", "scientific_name": "Prunus persica", "wiki_term": "Ροδακινιά"},
    {"name": "Τομάτα", "category": "Κηπευτικά", "scientific_name": "Solanum lycopersicum", "wiki_term": "Τομάτα"},
    {"name": "Πατάτα", "category": "Κηπευτικά", "scientific_name": "Solanum tuberosum", "wiki_term": "Πατάτα"},
    {"name": "Αμπέλι (Οινοποιήσιμο)", "category": "Αμπέλι", "scientific_name": "Vitis vinifera", "wiki_term": "Άμπελος"},
]

# --- 3. INITIALIZE SESSION STATE (Μνήμη) ---
if 'history_log' not in st.session_state:
    st.session_state.history_log = []

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("Μενού")
menu_choice = st.sidebar.radio("Πλοήγηση", ["📝 Νέα Καταγραφή", "🗂️ Βιβλιοθήκη & Ιστορικό", "☁️ Καιρός & EffiSpray"])

# --- 5. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
st.title("🌱 Agricultural Management System")

# ==================================================
# ΣΕΛΙΔΑ 1: ΝΕΑ ΚΑΤΑΓΡΑΦΗ (ΕΙΣΑΓΩΓΗ)
# ==================================================
if menu_choice == "📝 Νέα Καταγραφή":
    st.header("Εισαγωγή Δεδομένων Παραγωγής")
    
    # Επιλογή Καλλιέργειας
    crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
    selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
    
    current_name = ""
    current_category = ""
    
    # Λογική: Νέα ή Υπάρχουσα;
    if selected_option == "➕ Προσθήκη Νέας...":
        col_new1, col_new2 = st.columns(2)
        current_name = col_new1.text_input("Όνομα Καλλιέργειας (π.χ. Καρυδιά)")
        current_category = col_new2.text_input("Κατηγορία (π.χ. Δέντρα)")
    else:
        # Ανάκτηση στοιχείων από τη λίστα αναφοράς
        crop_data = next((item for item in default_crops if item["name"] == selected_option), None)
        if crop_data:
            current_name = crop_data['name']
            current_category = crop_data['category']
            st.info(f"Κατηγορία: **{current_category}**")
            
            # Wikipedia Info (Διορθωμένο)
            if st.checkbox("🔍 Πληροφορίες από Wikipedia"):
                try:
                    with st.spinner('Αναζήτηση...'):
                        wikipedia.set_lang("el")
                        # Χρήση του ειδικού όρου (wiki_term) αν υπάρχει, αλλιώς του ονόματος
                        search_term = crop_data.get('wiki_term', current_name)
                        summary = wikipedia.summary(search_term, sentences=2)
                        st.caption(f"📚 **{search_term}:** {summary}")
                except:
                    st.warning(f"Δεν βρέθηκαν πληροφορίες για '{current_name}'.")

    st.divider()
    
    # Φόρμα Καταγραφής με Ημερομηνία
    with st.form("entry_form"):
        st.subheader("Στοιχεία Εγγραφής")
        
        # Ημερομηνία & Ποικιλία
        c1, c2 = st.columns(2)
        rec_date = c1.date_input("Ημερομηνία Καταγραφής", date.today())
        rec_variety = c2.text_input("Ποικιλία", placeholder="π.χ. Κορωνέικη")
        
        # Ποσότητα & Υγρασία
        c3, c4 = st.columns(2)
        rec_qty = c3.number_input("Ποσότητα (kg)", min_value=0, step=10)
        rec_moisture = c4.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, step=0.1)
        
        notes = st.text_area("Σημειώσεις / Παρατηρήσεις", placeholder="π.χ. Χαμηλή παραγωγή λόγω καύσωνα...")
        
        submitted = st.form_submit_button("💾 Αποθήκευση στη Βιβλιοθήκη")
        
        if submitted:
            if not current_name:
                st.error("Πρέπει να επιλέξεις ή να γράψεις όνομα καλλιέργειας!")
            else:
                new_entry = {
                    "date": rec_date,
                    "year": rec_date.year,
                    "name": current_name,
                    "category": current_category,
                    "variety": rec_variety,
                    "quantity": rec_qty,
                    "moisture": rec_moisture,
                    "notes": notes
                }
                st.session_state.history_log.append(new_entry)
                st.success(f"Η εγγραφή για '{current_name}' αποθηκεύτηκε επιτυχώς!")

# ==================================================
# ΣΕΛΙΔΑ 2: ΒΙΒΛΙΟΘΗΚΗ & ΙΣΤΟΡΙΚΟ (ΤΑΞΙΝΟΜΗΣΗ)
# ==================================================
elif menu_choice == "🗂️ Βιβλιοθήκη & Ιστορικό":
    st.header("🗂️ Αρχείο Καλλιεργειών")

    if not st.session_state.history_log:
        st.info("Η βιβλιοθήκη είναι άδεια. Πήγαινε στο 'Νέα Καταγραφή' για να προσθέσεις δεδομένα.")
    else:
        df = pd.DataFrame(st.session_state.history_log)
        
        # --- ΦΙΛΤΡΑ ---
        with st.expander("🔍 Αναζήτηση & Φίλτρα", expanded=True):
            col_f1, col_f2 = st.columns(2)
            
            # Φίλτρο Έτους
            available_years = sorted(df['year'].unique(), reverse=True)
            selected_year = col_f1.selectbox("Επίλεξε Έτος", available_years)
            
            # Φίλτρο Καλλιέργειας (με βάση το έτος)
            df_year = df[df['year'] == selected_year]
            available_crops = sorted(df_year['name'].unique())
            selected_crops = col_f2.multiselect("Επίλεξε Καλλιέργειες (κενό για όλες)", available_crops)

        st.divider()

        # --- ΕΜΦΑΝΙΣΗ ΔΕΔΟΜΕΝΩΝ ---
        if selected_crops:
            df_final = df_year[df_year['name'].isin(selected_crops)]
        else:
            df_final = df_year

        if df_final.empty:
            st.warning("Δεν βρέθηκαν εγγραφές με αυτά τα κριτήρια.")
        else:
            st.subheader(f"Αποτελέσματα για το {selected_year}")
            
            # 1. Συγκεντρωτικός Πίνακας
            st.write("📊 **Σύνολα Έτους ανά Είδος**")
            summary = df_final.groupby(['name', 'category'])[['quantity']].sum().reset_index()
            st.dataframe(summary, use_container_width=True)

            # 2. Αναλυτικό Ιστορικό
            st.write("📝 **Αναλυτικές Εγγραφές**")
            df_final = df_final.sort_values(by='date', ascending=False)
            
            for index, row in df_final.iterrows():
                with st.container():
                    c_txt, c_vals = st.columns([3, 1])
                    c_txt.markdown(f"**{row['name']}** ({row['category']}) - *{row['variety']}*")
                    c_txt.caption(f"📅 {row['date']} | 📝 {row['notes']}")
                    
                    c_vals.metric("Ποσότητα", f"{row['quantity']} kg", f"Υγρ: {row['moisture']}%")
                    st.markdown("---")

# ==================================================
# ΣΕΛΙΔΑ 3: ΚΑΙΡΟΣ & EFFISPRAY
# ==================================================
elif menu_choice == "☁️ Καιρός & EffiSpray":
    
    st.header("🌦️ Καιρικές Συνθήκες")
    user_location = st.text_input("📍 Περιοχή:", value="Larissa")
    
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={user_location}&count=1&language=el&format=json"
        geo_response = requests.get(geo_url).json()
        
        if "results" in geo_response:
            loc_data = geo_response['results'][0]
            lat, lon = loc_data['latitude'], loc_data['longitude']
            
            weather_url = (
                f
