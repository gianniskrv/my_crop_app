import streamlit as st
import pandas as pd
import requests
import wikipedia
import streamlit.components.v1 as components
from datetime import date

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="AgroManager Pro", page_icon="🌱", layout="wide")

# --- 2. ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ ---
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

# --- 3. INITIALIZE SESSION STATE ---
if 'history_log' not in st.session_state:
    st.session_state.history_log = []

# --- 4. ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ---
st.sidebar.title("Μενού")
menu_choice = st.sidebar.radio("Πλοήγηση", ["📝 Νέα Καταγραφή", "🗂️ Βιβλιοθήκη & Ιστορικό", "☁️ Καιρός & EffiSpray"])

# --- 5. ΚΥΡΙΟ ΠΡΟΓΡΑΜΜΑ ---
st.title("🌱 Agricultural Management System")

# ==================================================
# ΣΕΛΙΔΑ 1: ΝΕΑ ΚΑΤΑΓΡΑΦΗ
# ==================================================
if menu_choice == "📝 Νέα Καταγραφή":
    st.header("Εισαγωγή Δεδομένων Παραγωγής")
    
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
        
        c3, c4 = st.columns(2)
        rec_qty = c3.number_input("Ποσότητα (kg)", min_value=0, step=10)
        rec_moisture = c4.number_input("Υγρασία (%)", min_value=0.0, max_value=100.0, step=0.1)
        
        notes = st.text_area("Σημειώσεις", placeholder="Παρατηρήσεις...")
        submitted = st.form_submit_button("💾 Αποθήκευση")
        
        if submitted:
            if not current_name:
                st.error("Συμπλήρωσε όνομα καλλιέργειας!")
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
                st.success(f"Αποθηκεύτηκε: {current_name}")

# ==================================================
# ΣΕΛΙΔΑ 2: ΒΙΒΛΙΟΘΗΚΗ
# ==================================================
elif menu_choice == "🗂️ Βιβλιοθήκη & Ιστορικό":
    st.header("🗂️ Αρχείο Καλλιεργειών")

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
            st.subheader(f"Δεδομένα του {sel_year}")
            
            # Σύνολα
            st.write("📊 **Σύνολα (kg)**")
            summary = df_final.groupby(['name'])[['quantity']].sum().reset_index()
            st.dataframe(summary, use_container_width=True)

            # Λίστα
            st.write("📝 **Ιστορικό Εγγραφών**")
            for i, row in df_final.sort_values(by='date', ascending=False).iterrows():
                with st.container():
                    st.markdown(f"**{row['name']}** - {row['variety']} ({row['date']})")
                    st.caption(f"Ποσότητα: {row['quantity']}kg | Υγρασία: {row['moisture']}% | {row['notes']}")
                    st.markdown("---")

# ==================================================
# ΣΕΛΙΔΑ 3: ΚΑΙΡΟΣ (ΜΕ SEARCH BAR) & EFFISPRAY
# ==================================================
elif menu_choice == "☁️ Καιρός & EffiSpray":
    
    st.header("🌦️ Πρόγνωση Καιρού")
    
    # --- ΜΠΑΡΑ ΑΝΑΖΗΤΗΣΗΣ ---
    col_search, col_btn = st.columns([3, 1])
    # O χρήστης γράφει εδώ την πόλη
    user_city = col_search.text_input("🔍 Αναζήτηση Περιοχής (π.χ. Larissa, Karditsa, Athens)", value="Larissa")
    
    # Ξεκινάμε τη διαδικασία αναζήτησης
    if user_city:
        try:
            # Βήμα 1: Βρες τις συντεταγμένες (Geocoding)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={user_city}&count=1&language=el&format=json"
            geo_res = requests.get(geo_url).json()

            if "results" in geo_res:
                data = geo_res['results'][0]
                lat = data['latitude']
                lon = data['longitude']
                name = data['name']
                country = data.get("country", "")

                st.success(f"📍 Βρέθηκε: **{name}, {country}**")

                # Βήμα 2: Φέρε τον καιρό (Weather API)
                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                    "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
                    "&timezone=auto"
                )
                w_res = requests.get(weather_url).json()
                curr = w_res['current']

                # Εμφάνιση μετρήσεων
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🌡️ Θερμοκρασία", f"{curr['temperature_2m']} °C")
                c2.metric("💧 Υγρασία", f"{curr['relative_humidity_2m']} %")
                c3.metric("☔ Βροχή", f"{curr['precipitation']} mm")
                c4.metric("💨 Άνεμος", f"{curr['wind_speed_10m']} km/h")
                
                # Εμφάνιση χάρτη με πινέζα
                map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(map_data)
                
            else:
                st.warning("Η πόλη δεν βρέθηκε. Δοκίμασε με Λατινικούς χαρακτήρες (π.χ. Athens).")

        except Exception as e:
            st.error("Υπήρξε πρόβλημα με τη σύνδεση.")
            # st.write(e) # Ξεκλείδωσέ το αν θες να δεις το τεχνικό λάθος

    st.divider()
    st.write("### 🚜 Εργαλείο Ψεκασμού (EffiSpray)")
    components.iframe("https://www.effispray.com/el", height=600, scrolling=True)
