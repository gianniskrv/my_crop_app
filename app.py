import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager", page_icon="🌱", layout="wide")

# --- 2. ΔΕΔΟΜΕΝΑ (GREEK CROPS DATABASE) ---
greek_crops = [
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

# --- 3. INITIALIZE SESSION STATE (Μνήμη Εφαρμογής) ---
# Εδώ αποθηκεύουμε τις καλλιέργειες που προσθέτει ο χρήστης
if 'my_crops' not in st.session_state:
    st.session_state.my_crops = []

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ (SIDEBAR) ---
st.sidebar.title("Menu")
menu_choice = st.sidebar.selectbox("Πλοήγηση", ["Διαχείριση Καλλιεργειών", "Προβολή & Καιρός"])

# --- 5. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
st.title("🌱 Agricultural Management System")

# ==================================================
# ΣΕΛΙΔΑ 1: ΔΙΑΧΕΙΡΙΣΗ (ADD/UPDATE)
# ==================================================
if menu_choice == "Διαχείριση Καλλιεργειών":
    st.header("Ενημέρωση Παραγωγής")
    
    # Επιλογή από τη βάση δεδομένων
    crop_names = [c['name'] for c in greek_crops]
    selected_name = st.selectbox("Επίλεξε Καλλιέργεια:", crop_names)
    
    # Βρίσκουμε τα info της επιλογής
    crop_info = next((item for item in greek_crops if item["name"] == selected_name), None)
    
    if crop_info:
        # Εμφάνιση σταθερών πληροφοριών
        col1, col2 = st.columns(2)
        col1.text_input("Επιστημονικό Όνομα", crop_info['scientific_name'], disabled=True)
        col2.text_input("Κατηγορία", crop_info['category'], disabled=True)
        
        # Wikipedia Search
        if st.checkbox("🔍 Πληροφορίες από Wikipedia"):
            try:
                with st.spinner('Αναζήτηση...'):
                    wikipedia.set_lang("el")
                    # Παίρνουμε μια σύνοψη 2 προτάσεων
                    summary = wikipedia.summary(selected_name, sentences=2)
                    st.info(f"📚 {summary}")
            except:
                st.warning("Δεν βρέθηκαν πληροφορίες στη Wikipedia για αυτό το φυτό.")

    st.divider()
    st.subheader("Καταχώρηση Δεδομένων")
    
    # Φόρμα εισαγωγής τιμών
    with st.form("crop_form"):
        # Προεπιλεγμένες τιμές αν υπάρχει ήδη η καλλιέργεια
        existing = next((item for item in st.session_state.my_crops if item['name'] == selected_name), None)
        default_qty = existing['quantity'] if existing else 0
        default_moist = existing['moisture'] if existing else 0.0

        new_qty = st.number_input("Ποσότητα Παραγωγής (kg)", min_value=0, value=default_qty, step=10)
        new_moisture = st.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, value=float(default_moist), step=0.1)
        
        submitted = st.form_submit_button("💾 Αποθήκευση / Ενημέρωση")
        
        if submitted:
            # Λογική αποθήκευσης
            if existing:
                existing['quantity'] = new_qty
                existing['moisture'] = new_moisture
                st.success(f"Ενημερώθηκε επιτυχώς: {selected_name}")
            else:
                new_entry = {
                    "name": selected_name,
                    "quantity": new_qty,
                    "moisture": new_moisture,
                    "category": crop_info['category']
                }
                st.session_state.my_crops.append(new_entry)
                st.success(f"Προστέθηκε επιτυχώς: {selected_name}")

# ==================================================
# ΣΕΛΙΔΑ 2: ΠΡΟΒΟΛΗ & ΚΑΙΡΟΣ
# ==================================================
elif menu_choice == "Προβολή & Καιρός":
    
    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: ΣΤΑΤΙΣΤΙΚΑ ---
    st.header("📊 Στατιστικά Καλλιεργειών")
    
    if st.session_state.my_crops:
        # Μετατροπή σε DataFrame για τα γραφήματα
        df = pd.DataFrame(st.session_state.my_crops)
        
        # Προβολή πίνακα δεδομένων (προαιρετικό)
        with st.expander("Προβολή Πίνακα Δεδομένων"):
            st.dataframe(df)

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
        st.info("Δεν υπάρχουν καταχωρημένες καλλιέργειες ακόμα. Πήγαινε στο μενού 'Διαχείριση' για να προσθέσεις.")

    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: ΚΑΙΡΟΣ ---
    st.divider()
    st.header("🌦️ Καιρικές Συνθήκες (Live)")
    
    # Συντεταγμένες (Λάρισα)
    LAT = 39.639
    LON = 22.419
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&hourly=relativehumidity_2m,windspeed_10m"
        response = requests.get(url)
        data = response.json()
        current = data['current_weather']
        
        w1, w2, w3 = st.columns(3)
        w1.metric("Θερμοκρασία", f"{current['temperature']} °C")
        w2.metric("Άνεμος", f"{current['windspeed']} km/h")
        w3.success("✅ Δεδομένα ΟΚ")
        
    except Exception as e:
        st.error("Δεν φορτώθηκαν τα καιρικά δεδομένα (Ελέγξτε τη σύνδεση).")

    # --- ΥΠΟ-ΕΝΟΤΗΤΑ: EFFISPRAY ---
    st.divider()
    st.header("🚜 Εργαλείο Ψεκασμού (EffiSpray)")
    st.caption("Δείτε τις ιδανικές ώρες για ψεκασμό:")
    components.iframe("https://www.effispray.com/el", height=600, scrolling=True)
