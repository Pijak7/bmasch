import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from ics import Calendar, Event

# --- DATENBANK SETUP ---
conn = sqlite3.connect('baumaschinen.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS maschinen 
             (id INTEGER PRIMARY KEY, name TEXT, typ TEXT, tuev DATE, wartung DATE)''')
conn.commit()

# --- FUNKTIONEN ---
def add_machine(name, typ, tuev, wartung):
    c.execute('INSERT INTO maschinen (name, typ, tuev, wartung) VALUES (?,?,?,?)', 
              (name, typ, tuev, wartung))
    conn.commit()

def get_data():
    return pd.read_sql_query("SELECT * FROM maschinen", conn)

def create_ics(df):
    cal = Calendar()
    for index, row in df.iterrows():
        # TÜV Event
        e_tuev = Event()
        e_tuev.name = f"TÜV: {row['name']}"
        e_tuev.begin = row['tuev']
        e_tuev.make_all_day()
        cal.events.add(e_tuev)
        # Wartung Event
        e_wart = Event()
        e_wart.name = f"Wartung: {row['name']}"
        e_wart.begin = row['wartung']
        e_wart.make_all_day()
        cal.events.add(e_wart)
    return cal.serialize()

# --- UI DESIGN ---
st.set_page_config(page_title="Maschinen-Manager", layout="wide")
st.title("🚜 Baumaschinen-Verwaltung")

menu = ["Übersicht", "Neues Gerät anlegen", "Kalender-Sync"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Übersicht":
    st.subheader("Aktueller Bestand")
    df = get_data()
    
    if not df.empty:
        # Farblich markieren, wenn Termine in den nächsten 30 Tagen liegen
        today = datetime.now().date()
        warn_limit = today + timedelta(days=30)
        
        def highlight_urgent(val):
            try:
                date_val = datetime.strptime(val, '%Y-%m-%d').date()
                if date_val < today: return 'background-color: #ff4b4b; color: white' # Überfällig
                if date_val < warn_limit: return 'background-color: #ffa500' # Bald fällig
            except:
                return ''
            return ''

        st.dataframe(df.style.applymap(highlight_urgent, subset=['tuev', 'wartung']))
    else:
        st.info("Noch keine Geräte erfasst.")

elif choice == "Neues Gerät anlegen":
    st.subheader("Gerät hinzufügen")
    with st.form("add_form"):
        name = st.text_input("Name des Geräts (z.B. Bagger Liebherr A914)")
        typ = st.selectbox("Kategorie", ["Großgerät", "Kleingerät", "Fahrzeug", "Anbauteil"])
        tuev = st.date_input("Nächster TÜV")
        wartung = st.date_input("Nächste Wartung")
        submit = st.form_submit_button("Speichern")
        
        if submit:
            add_machine(name, typ, tuev, wartung)
            st.success(f"{name} wurde gespeichert!")

elif choice == "Kalender-Sync":
    st.subheader("Export für Google/Outlook")
    df = get_data()
    if not df.empty:
        ics_data = create_ics(df)
        st.download_button(label="📅 Termine als .ics herunterladen",
                           data=ics_data,
                           file_name="baumaschinen_termine.ics",
                           mime="text/calendar")
        st.write("Anleitung: Lade die Datei herunter und öffne sie mit Outlook oder importiere sie in deinen Google Kalender.")
