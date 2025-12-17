import streamlit as st

# Ορισμός της κλάσης Crop
class Crop:
    def __init__(self, name, quantity, soil_moisture):
        self.name = name
        self.quantity = quantity
        self.soil_moisture = soil_moisture

    def update_quantity(self, quantity):
        self.quantity = quantity

    def update_soil_moisture(self, moisture):
        self.soil_moisture = moisture

# Αρχικοποίηση λίστας (Session State) για να μην χάνονται τα δεδομένα
if 'crops' not in st.session_state:
    st.session_state.crops = []

def main():
    st.title("🌱 Agricultural Management System")
    
    # Μενού στην πλαϊνή μπάρα
    menu = ["View Crops", "Add Crop", "Update Crop"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- 1. VIEW CROPS ---
    if choice == "View Crops":
        st.header("Current Crops")
        if not st.session_state.crops:
            st.info("No crops in the system yet.")
        else:
            # Εμφάνιση ως λίστα
            for crop in st.session_state.crops:
                st.success(f"**{crop.name}** | Qty: {crop.quantity} | Moisture: {crop.soil_moisture}%")

    # --- 2. ADD CROP ---
    elif choice == "Add Crop":
        st.header("Add New Crop")
        
        # Φόρμα εισαγωγής
        with st.form("add_crop_form"):
            name = st.text_input("Crop Name")
            quantity = st.number_input("Quantity", min_value=0, step=1)
            moisture = st.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, step=0.1)
            
            submitted = st.form_submit_button("Add Crop")
            
            if submitted:
                if name:
                    new_crop = Crop(name, quantity, moisture)
                    st.session_state.crops.append(new_crop)
                    st.success(f"Crop '{name}' added successfully!")
                else:
                    st.error("Please enter a crop name.")

    # --- 3. UPDATE CROP ---
    elif choice == "Update Crop":
        st.header("Update Existing Crop")
        
        if not st.session_state.crops:
            st.warning("No crops available to update.")
        else:
            # Λίστα με τα ονόματα των καλλιεργειών
            crop_names = [crop.name for crop in st.session_state.crops]
            selected_crop_name = st.selectbox("Select Crop to Update", crop_names)
            
            # Βρίσκουμε το αντικείμενο crop που επιλέχθηκε
            selected_crop = next((c for c in st.session_state.crops if c.name == selected_crop_name), None)
            
            if selected_crop:
                st.write(f"Current Quantity: {selected_crop.quantity}")
                st.write(f"Current Moisture: {selected_crop.soil_moisture}%")
                
                new_qty = st.number_input("New Quantity", value=selected_crop.quantity, min_value=0)
                new_moist = st.number_input("New Moisture (%)", value=selected_crop.soil_moisture, min_value=0.0, max_value=100.0)
                
                if st.button("Update Crop Details"):
                    selected_crop.update_quantity(new_qty)
                    selected_crop.update_soil_moisture(new_moist)
                    st.success(f"Updated {selected_crop_name} successfully!")

if __name__ == "__main__":
    main()
import streamlit as st
import wikipedia  # Χρειάζεται εγκατάσταση: pip install wikipedia

# 1. Η ΛΙΣΤΑ ΜΑΣ (Μπορείς να την έχεις και σε άλλο αρχείο)
greek_crops = [
    {"name": "Βαμβάκι", "scientific_name": "Gossypium hirsutum", "category": "Βιομηχανικά"},
    {"name": "Σιτάρι Σκληρό", "scientific_name": "Triticum durum", "category": "Σιτηρά"},
    {"name": "Καλαμπόκι", "scientific_name": "Zea mays", "category": "Σιτηρά"},
    {"name": "Ελιά (Λαδοελιά)", "scientific_name": "Olea europaea", "category": "Δέντρα"},
    # ... πρόσθεσε τα υπόλοιπα εδώ ...
]

st.title("Προσθήκη / Ενημέρωση Καλλιέργειας")

# 2. DROPDOWN ΑΠΟ ΤΗ ΛΙΣΤΑ
# Φτιάχνουμε μια λίστα μόνο με τα ονόματα για το dropdown
crop_names = [crop['name'] for crop in greek_crops]

selected_crop_name = st.selectbox(
    "Επίλεξε Καλλιέργεια (από τη βάση δεδομένων):",
    options=crop_names
)

# 3. ΑΥΤΟΜΑΤΗ ΑΝΑΚΤΗΣΗ ΣΤΟΙΧΕΙΩΝ
# Βρίσκουμε ολόκληρο το αντικείμενο με βάση το όνομα που επέλεξε ο χρήστης
selected_crop_data = next((item for item in greek_crops if item["name"] == selected_crop_name), None)

if selected_crop_data:
    st.markdown("### Στοιχεία Καλλιέργειας")
    
    # Εμφάνισε τα στοιχεία που έχουμε ήδη
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Επιστημονικό Όνομα", value=selected_crop_data['scientific_name'], disabled=True)
    with col2:
        st.text_input("Κατηγορία", value=selected_crop_data['category'], disabled=True)

    # 4. (ΠΡΟΑΙΡΕΤΙΚΑ) ΤΡΑΒΗΓΜΑ ΑΠΟ ΤΟ INTERNET (WIKIPEDIA)
    # Αν θες να φέρεις κάτι live από το internet:
    if st.button("🔍 Λήψη πληροφοριών από Wikipedia"):
        try:
            with st.spinner('Αναζήτηση στο διαδίκτυο...'):
                wikipedia.set_lang("el") # Ορίζουμε Ελληνικά
                # Ψάχνουμε τη σελίδα
                page = wikipedia.page(selected_crop_name)
                st.info(f"**Περιγραφή από Wikipedia:** {page.summary[0:300]}...") # Πρώτοι 300 χαρακτήρες
                st.write(f"[Διάβασε περισσότερα]({page.url})")
        except:
            st.error("Δεν βρέθηκαν πληροφορίες στο διαδίκτυο για αυτή την καλλιέργεια.")

# Εδώ συνεχίζει η φόρμα σου για Quantity / Moisture κλπ
st.divider()
st.subheader("Ενημέρωση Παραγωγής")
new_qty = st.number_input("Ποσότητα (kg)", min_value=0)
new_moisture = st.number_input("Υγρασία (%)", min_value=0.0, format="%.2f")

if st.button("Save Crop"):
    st.success(f"Αποθηκεύτηκε: {selected_crop_name} - {new_qty}kg")
import pandas as pd # Βεβαιώσου ότι έχεις το import pandas στην αρχή

st.divider()
st.subheader("📊 Στατιστικά Καλλιεργειών")

# Έλεγχος αν υπάρχουν δεδομένα
if 'crops' in st.session_state and st.session_state.crops:
    # Μετατροπή της λίστας σε DataFrame (Πίνακα) για εύκολη διαχείριση
    df = pd.DataFrame(st.session_state.crops)
      # Δημιουργία στηλών για να μπουν τα γραφήματα δίπλα-δίπλα
    col1, col2 = st.columns(2)

    with col1:
        st.caption("Ποσότητα (kg) ανά Καλλιέργεια")
        # Μπαρο-διάγραμμα με τις ποσότητες
        st.bar_chart(df, x="name", y="quantity")

    with col2:
        st.caption("Επίπεδα Υγρασίας (%)")
        # Γράφημα γραμμής για την υγρασία
        st.line_chart(df, x="name", y="moisture")

    # Ένα γρήγορο "Σύνολο"
    total_qty = df['quantity'].sum()
    st.metric(label="Συνολική Παραγωγή (kg)", value=f"{total_qty} kg")

else:
    st.info("Πρόσθεσε μερικές καλλιέργειες για να δεις τα διαγράμματα!")
import requests # Βεβαιώσου ότι είναι πάνω-πάνω στα imports
import streamlit.components.v1 as components # Για να βάλουμε το EffiSpray

st.divider()
st.subheader("🌦️ Καιρικές Συνθήκες & Ψεκασμοί")

# Συντεταγμένες
LAT = 39.639
LON = 22.419

try:
    # Προσοχή: Όλα εδώ μέσα είναι στοιχισμένα (έχουν ένα Tab μπροστά)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&hourly=relativehumidity_2m,windspeed_10m"
    response = requests.get(url)
    data = response.json()
    
    current = data['current_weather']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Θερμοκρασία", f"{current['temperature']} °C")
    col2.metric("Ταχύτητα Ανέμου", f"{current['windspeed']} km/h")
    col3.info("Δεδομένα από Open-Meteo") 

except Exception as e:
    # Το except πρέπει να είναι στην ίδια ευθεία με το try (τέρμα αριστερά)
    st.error("Δεν ήταν δυνατή η λήψη καιρικών δεδομένων.")

# Το iframe είναι εκτός try/except, τέρμα αριστερά
st.write("### 🚜 Εργαλείο Ψεκασμού (EffiSpray)")
components.iframe("https://www.effispray.com/el", height=600, scrolling=True)
