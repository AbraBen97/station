import streamlit as st
import pandas as pd
import hashlib
import datetime
import json
import os
from pathlib import Path

# Initialisation des fichiers de données
DATA_DIR = "station_data"
Path(DATA_DIR).mkdir(exist_ok=True)
USERS_FILE = f"{DATA_DIR}/users.json"
DATA_FILE = f"{DATA_DIR}/station_data.json"
PRICES = {"gazoil": 1.2, "super": 1.5}  # Prix par litre en euros

# Fonction pour charger/enregistrer les données
def load_data(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return default_data

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Données initiales des utilisateurs
users = load_data(USERS_FILE, {
    "admin": {"password": hashlib.sha256("admin123".encode()).hexdigest(), "role": "admin"},
    "travailleur1": {
        "password": hashlib.sha256("pass123".encode()).hexdigest(),
        "role": "worker",
        "info": {"nom": "Jean Dupont", "station": "Station A", "tel": "0123456789"}
    },
    "travailleur2": {
        "password": hashlib.sha256("pass123".encode()).hexdigest(),
        "role": "worker",
        "info": {"nom": "Marie Dubois", "station": "Station B", "tel": "0987654321"}
    }
})

# Interface de connexion
def login_page():
    st.title("Connexion")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    admin_mode = st.checkbox("Mode Administrateur")
    admin_password = st.text_input("Mot de passe Admin (si mode admin)", type="password") if admin_mode else ""

    if st.button("Se connecter"):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in users and users[username]["password"] == hashed_password:
            if admin_mode:
                if admin_password == "admin123":  # Mot de passe admin
                    st.session_state["role"] = "admin"
                    st.session_state["user"] = username
                    st.success("Connexion admin réussie")
                else:
                    st.error("Mot de passe admin incorrect")
            else:
                st.session_state["role"] = users[username]["role"]
                st.session_state["user"] = username
                st.success("Connexion réussie")
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")

# Interface travailleur
def worker_page():
    st.title(f"Bienvenue {users[st.session_state['user']]['info']['nom']}")
    station = users[st.session_state['user']]['info']['station']
    data = load_data(DATA_FILE, {})
    
    # Sélection de la pompe
    pompe = st.selectbox("Choisir la pompe", ["Pompe A", "Pompe B", "Pompe C"])
    
    # Date actuelle
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    # Initialisation des données pour la station/pompe
    if station not in data:
        data[station] = {}
    if pompe not in data[station]:
        data[station][pompe] = {}
    if today not in data[station][pompe]:
        data[station][pompe][today] = {"montée": {}, "descente": {}}

    # Quantités de la veille (non modifiables)
    quantite_gazoil = 0
    quantite_super = 0
    if yesterday in data[station][pompe] and "descente" in data[station][pompe][yesterday]:
        quantite_gazoil = data[station][pompe][yesterday]["descente"].get("gazoil", 0)
        quantite_super = data[station][pompe][yesterday]["descente"].get("super", 0)

    st.subheader("Montée")
    if not data[station][pompe][today]["montée"]:
        with st.form("montée_form"):
            st.write(f"Quantité gazoil (fixe de la veille): {quantite_gazoil} L")
            st.write(f"Quantité super (fixe de la veille): {quantite_super} L")
            if st.form_submit_button("Confirmer Montée"):
                data[station][pompe][today]["montée"] = {
                    "gazoil": quantite_gazoil,
                    "super": quantite_super,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                save_data(DATA_FILE, data)
                st.success("Montée enregistrée")
    else:
        st.write("Montée déjà enregistrée pour aujourd'hui")
        st.write(f"Gazoil: {data[station][pompe][today]['montée']['gazoil']} L")
        st.write(f"Super: {data[station][pompe][today]['montée']['super']} L")

    st.subheader("Descente")
    with st.form("descente_form"):
        gazoil_restant = st.number_input("Quantité gazoil restant (L)", min_value=0.0)
        super_restant = st.number_input("Quantité super restant (L)", min_value=0.0)
        montant_decalre = st.number_input("Montant total déclaré (€)", min_value=0.0)
        if st.form_submit_button("Enregistrer Descente"):
            # Calcul du montant théorique
            gazoil_vendu = quantite_gazoil - gazoil_restant
            super_vendu = quantite_super - super_restant
            montant_calcule = (gazoil_vendu * PRICES["gazoil"]) + (super_vendu * PRICES["super"])
            
            data[station][pompe][today]["descente"] = {
                "gazoil": gazoil_restant,
                "super": super_restant,
                "montant_déclaré": montant_decalre,
                "montant_calculé": montant_calcule,
                "timestamp": datetime.datetime.now().isoformat()
            }
            save_data(DATA_FILE, data)
            st.success("Descente enregistrée")

            # Affichage comparaison
            st.subheader("Vérification")
            col1, col2, col3 = st.columns(3)
            col1.metric("Montant Déclaré", f"{montant_decalre:.2f} €")
            col2.metric("Montant Calculé", f"{montant_calcule:.2f} €")
            difference = montant_decalre - montant_calcule
            col3.metric("Différence", f"{difference:.2f} €", delta_color="inverse")

# Interface admin
def admin_page():
    st.title("Tableau de bord Administrateur")
    data = load_data(DATA_FILE, {})
    
    # Sélection de la station
    stations = list(data.keys())
    selected_station = st.selectbox("Choisir une station", ["Toutes"] + stations)
    
    # Vue générale
    if selected_station == "Toutes":
        st.subheader("Vue générale")
        for station in stations:
            st.write(f"### {station}")
            df = pd.DataFrame()
            for pompe in data[station]:
                for date in data[station][pompe]:
                    if "descente" in data[station][pompe][date]:
                        row = {
                            "Date": date,
                            "Pompe": pompe,
                            "Gazoil vendu (L)": data[station][pompe][date]["montée"]["gazoil"] - data[station][pompe][date]["descente"]["gazoil"],
                            "Super vendu (L)": data[station][pompe][date]["montée"]["super"] - data[station][pompe][date]["descente"]["super"],
                            "Montant déclaré (€)": data[station][pompe][date]["descente"]["montant_déclaré"],
                            "Montant calculé (€)": data[station][pompe][date]["descente"]["montant_calculé"],
                            "Différence (€)": data[station][pompe][date]["descente"]["montant_déclaré"] - data[station][pompe][date]["descente"]["montant_calculé"]
                        }
                        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            if not df.empty:
                df["Différence (€)"] = df["Différence (€)"].apply(lambda x: f'<span style="color:red">{x:.2f}</span>' if x < 0 else f'{x:.2f}')
                st.markdown(df.to_html(escape=False), unsafe_allow_html=True)
    
    # Vue par station
    else:
        st.subheader(f"Suivi de {selected_station}")
        df = pd.DataFrame()
        for pompe in data[selected_station]:
            for date in data[selected_station][pompe]:
                if "descente" in data[selected_station][pompe][date]:
                    row = {
                        "Date": date,
                        "Pompe": pompe,
                        "Gazoil vendu (L)": data[selected_station][pompe][date]["montée"]["gazoil"] - data[selected_station][pompe][date]["descente"]["gazoil"],
                        "Super vendu (L)": data[selected_station][pompe][date]["montée"]["super"] - data[selected_station][pompe][date]["descente"]["super"],
                        "Montant déclaré (€)": data[selected_station][pompe][date]["descente"]["montant_déclaré"],
                        "Montant calculé (€)": data[selected_station][pompe][date]["descente"]["montant_calculé"],
                        "Différence (€)": data[selected_station][pompe][date]["descente"]["montant_déclaré"] - data[selected_station][pompe][date]["descente"]["montant_calculé"]
                    }
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        if not df.empty:
            df["Différence (€)"] = df["Différence (€)"].apply(lambda x: f'<span style="color:red">{x:.2f}</span>' if x < 0 else f'{x:.2f}')
            st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

    # Ajout de livraison
    st.subheader("Ajouter une livraison")
    with st.form("livraison_form"):
        station_livraison = st.selectbox("Station", stations)
        pompe_livraison = st.selectbox("Pompe", ["Pompe A", "Pompe B", "Pompe C"])
        gazoil_livraison = st.number_input("Gazoil livré (L)", min_value=0.0)
        super_livraison = st.number_input("Super livré (L)", min_value=0.0)
        if st.form_submit_button("Enregistrer Livraison"):
            today = datetime.date.today().isoformat()
            if station_livraison not in data:
                data[station_livraison] = {}
            if pompe_livraison not in data[station_livraison]:
                data[station_livraison][pompe_livraison] = {}
            if today not in data[station_livraison][pompe_livraison]:
                data[station_livraison][pompe_livraison][today] = {"montée": {}, "descente": {}}
            
            current_gazoil = data[station_livraison][pompe_livraison][today]["montée"].get("gazoil", 0)
            current_super = data[station_livraison][pompe_livraison][today]["montée"].get("super", 0)
            
            data[station_livraison][pompe_livraison][today]["montée"]["gazoil"] = current_gazoil + gazoil_livraison
            data[station_livraison][pompe_livraison][today]["montée"]["super"] = current_super + super_livraison
            save_data(DATA_FILE, data)
            st.success("Livraison enregistrée")

    # Bilan comptable
    st.subheader("Bilan comptable")
    total_gazoil = 0
    total_super = 0
    total_montant = 0
    for station in data:
        for pompe in data[station]:
            for date in data[station][pompe]:
                if "descente" in data[station][pompe][date]:
                    total_gazoil += data[station][pompe][date]["montée"]["gazoil"] - data[station][pompe][date]["descente"]["gazoil"]
                    total_super += data[station][pompe][date]["montée"]["super"] - data[station][pompe][date]["descente"]["super"]
                    total_montant += data[station][pompe][date]["descente"]["montant_déclaré"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gazoil vendu", f"{total_gazoil:.2f} L")
    col2.metric("Total Super vendu", f"{total_super:.2f} L")
    col3.metric("Total Montant", f"{total_montant:.2f} €")

# Fonction principale
def main():
    if "user" not in st.session_state:
        login_page()
    elif st.session_state["role"] == "worker":
        worker_page()
    else:
        admin_page()

if __name__ == "__main__":
    main()