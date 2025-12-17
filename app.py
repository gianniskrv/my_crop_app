import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components

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

# --- 3. INITIALIZE SESSION STATE (Μνήμη) ---
if 'my_crops' not in st.session_state:
    st.session_state.my_crops = []

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("Μενού")
menu_choice = st.sidebar.selectbox("Πλοήγηση", ["Διαχείριση Καλλιεργειών", "Προβολή & Καιρός"])

# --- 5. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
st.title("🌱 Agricultural Management System")

# ==================================================
# ΣΕΛΙΔΑ 1: ΔΙΑΧΕΙΡΙΣΗ (ADD/UPDATE)
# ==================================================
if menu_choice == "Διαχείριση Καλλιεργειών":
    st.header("Ενημέρωση Παραγωγής")
    
    # Λίστα επιλογών + "Προσθήκη Νέας"
    crop_options = [c['name'] for c in default_crops] + ["➕ Προσθήκη Νέας..."]
    selected_option = st.selectbox("Επίλεξε Καλλιέργεια:", crop_options)
    
    current_name = ""
    current_category = ""
    current_scientific = ""
    
    # Λογική: Νέα ή Υπάρχουσα;
    if selected_option == "➕ Προσθήκη Νέας...":
        st.info("Δημιουργία νέας καλλιέργειας.")
        col_new1, col_new2 = st.columns(2)
        current_name = col_new1.text_input("Όνομα Καλλιέργειας (π.χ. Καρυδιά)")
        current_category = col_new2.text_input("Κατηγορία (π.χ. Δέντρα)")
    else:
        # Ανάκτηση στοιχείων από τη βάση
        crop_data = next((item for item in default_crops if item["name"] == selected_option), None)
        if crop_data:
            current_name = crop_data['name']
            current_category = crop_data['category']
            current_scientific = crop_data['scientific_name']
            
            # Εμφάνιση πληροφοριών (Read-only)
            col1, col2 = st.columns(2)
            col1.text_input("Επιστημονικό Όνομα", current_scientific, disabled=True)
            col2.text_input("Κατηγορία", current_category, disabled=True)
            
            # Wikipedia
            if st.checkbox("🔍 Πληροφορίες από Wikipedia"):
                try:
                    with st.spinner('Αναζήτηση...'):
                        wikipedia.set_lang("el")
                        summary = wikipedia.summary(current_name, sentences=2)
                        st.info(f"📚 {summary}")
                except:
                    st.warning("Δεν βρέθηκαν πληροφορίες.")

    st.divider()
    st.subheader("Στοιχεία Παραγωγής")
    
    # Έλεγχος αν λείπει το όνομα στη νέα προσθήκη
    if selected_option == "➕ Προσθήκη Νέας..." and not current_name:
        st.warning("👈 Παρακαλώ συμπληρώστε το Όνομα της νέας καλλιέργειας.")
    else:
        # Φόρμα Δεδομένων
        with st.form("crop_form"):
            # Αν υπάρχει ήδη στα δεδομένα μας, φέρε τις παλιές τιμές
            existing = next((item for item in st.session_state.my_crops if item['name'] == current_name), None)
            
            def_qty = existing['quantity'] if existing else 0
            def_moist = existing['moisture'] if existing else 0.0
            def_var = existing['variety'] if existing and 'variety' in existing else ""

            col_f1, col_f2 = st.columns(2)
            new_qty = col_f1.number_input("Ποσότητα (kg)", min_value=0, value=def_qty, step=10)
            new_moisture = col_f2.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, value=float(def_moist), step=0.1)
            
            # Πεδίο Ποικιλίας
            new_variety = st.text_input("Ποικιλία (π.χ. Κορωνέικη)", value=def_var, placeholder="Προαιρετικό")
            
            submitted = st.form_submit_button("💾 Αποθήκευση / Ενημέρωση")
            
            if submitted:
                if existing:
                    # Ενημέρωση
                    existing['quantity'] = new_qty
                    existing['moisture'] = new_moisture
                    existing['variety'] = new_variety
                    existing['category'] = current_category
                    st.success(f"Ενημερώθηκε: {current_name}")
                else:
                    # Νέα Εγγραφή
                    new_entry = {
                        "name": current_name,
                        "category": current_category,
                        "quantity": new_qty,
                        "moisture": new_moisture,
                        "variety": new_variety
                    }
                    st.session_state.my_crops.append(new_entry)
                    st.success(f"Προστέθηκε: {current_name}")

# ==================================================
# ΣΕΛΙΔΑ 2: ΠΡΟΒΟΛΗ & ΚΑΙΡΟΣ
# ==================================================
elif menu_choice == "Προβολή & Καιρός":
    
    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: ΣΤΑΤΙΣΤΙΚΑ ---
    st.header("📊 Στατιστικά Καλλιεργειών")
    
    if st.session_state.my_crops:
        df = pd.DataFrame(st.session_state.my_crops)
        
        # Πίνακας
        with st.expander("Προβολή Αναλυτικού Πίνακα", expanded=True):
            cols_order = ['name', 'variety', 'category', 'quantity', 'moisture']
            final_cols = [c for c in cols_order if c in df.columns]
            st.dataframe(df[final_cols], use_container_width=True)

        # Γραφήματα
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Παραγωγή (kg)")
            st.bar_chart(df, x="name", y="quantity")
        with col2:
            st.caption("Υγρασία (%)")
            st.line_chart(df, x="name", y="moisture")
        
        total_kg = df['quantity'].sum()
        st.metric("Συνολική Παραγωγή", f"{total_kg} kg")
    else:
        st.info("Δεν υπάρχουν δεδομένα. Πήγαινε στο μενού 'Διαχείριση' για προσθήκη.")

    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: ΚΑΙΡΟΣ (Advanced) ---
    st.divider()
    st.header("🌦️ Καιρικές Συνθήκες")
    
    user_location = st.text_input("📍 Πληκτρολόγησε την περιοχή σου (π.χ. Larissa, Athens):", value="Larissa")
    
    try:
        # 1. Geocoding (Βρίσκουμε συντεταγμένες από το όνομα)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={user_location}&count=1&language=el&format=json"
        geo_response = requests.get(geo_url).json()
        
        if "results" in geo_response:
            loc_data = geo_response['results'][0]
            lat = loc_data['latitude']
            lon = loc_data['longitude']
            country = loc_data.get('country', '')
            name_found = loc_data['name']
            
            st.caption(f"🗺️ Πρόγνωση για: **{name_found}, {country}**")
            
            # 2. Weather API (Ζητάμε πολλά δεδομένα)
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,wind_direction_10m"
                "&timezone=auto"
            )
            w_response = requests.get(weather_url).json()
            curr = w_response['current']
            
            # Εμφάνιση σε 2 σειρές
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Θερμοκρασία", f"{curr['temperature_2m']} °C")
            c2.metric("💧 Υγρασία", f"{curr['relative_humidity_2m']}%")
            c3.metric("🤒 Αίσθηση", f"{curr['apparent_temperature']} °C")
            
            c4, c5, c6 = st.columns(3)
            c4.metric("💨 Ταχ. Ανέμου", f"{curr['wind_speed_10m']} km/h")
            c5.metric("🧭 Κατεύθυνση", f"{curr['wind_direction_10m']}°")
            c6.metric("☔ Βροχή (Τώρα)", f"{curr['precipitation']} mm")
            
        else:
            st.error(f"Δεν βρέθηκε η πόλη '{user_location}'. Δοκίμασε στα Αγγλικά.")

    except Exception:
        st.error("Πρόβλημα σύνδεσης με τον καιρό.")

    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: EFFISPRAY ---
    st.divider()
    st.write("### 🚜 Εργαλείο Ψεκασμού (EffiSpray)")
    components.iframe("https://www.effispray.com/el", height=600, scrolling=True)
