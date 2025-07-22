import streamlit as st
import pandas as pd
import datetime
from datetime import date
import hashlib
import sqlite3
from PIL import Image
import plotly.express as px

# Configuration de base de l'application
st.set_page_config(page_title="Gestion Stations-Service", page_icon="⛽", layout="wide")

# Connexion à la base de données SQLite
conn = sqlite3.connect('stations_service.db')
c = conn.cursor()

# Création des tables si elles n'existent pas
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS utilisateurs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nom TEXT UNIQUE,
                 mot_de_passe TEXT,
                 role TEXT,
                 station TEXT,
                 prenom TEXT,
                 telephone TEXT,
                 date_embauche TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS activites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT,
                 utilisateur_id INTEGER,
                 station TEXT,
                 pompe TEXT,
                 monte_gazoil REAL,
                 monte_super REAL,
                 descente_gazoil REAL,
                 descente_super REAL,
                 montant_declare_gazoil REAL,
                 montant_declare_super REAL,
                 FOREIGN KEY(utilisateur_id) REFERENCES utilisateurs(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS stations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nom TEXT UNIQUE,
                 adresse TEXT,
                 gazoil_stock REAL,
                 super_stock REAL,
                 prix_gazoil REAL,
                 prix_super REAL)''')
    
    conn.commit()

init_db()

# Fonctions utilitaires
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verifier_utilisateur(nom, mot_de_passe):
    mot_de_passe_hash = hash_password(mot_de_passe)
    c.execute("SELECT * FROM utilisateurs WHERE nom=? AND mot_de_passe=?", (nom, mot_de_passe_hash))
    return c.fetchone()

def get_historique_station(station):
    c.execute("SELECT * FROM activites WHERE station=? ORDER BY date DESC", (station,))
    return c.fetchall()

def get_historique_utilisateur(utilisateur_id):
    c.execute("SELECT * FROM activites WHERE utilisateur_id=? ORDER BY date DESC", (utilisateur_id,))
    return c.fetchall()

def get_stock(station):
    c.execute("SELECT gazoil_stock, super_stock FROM stations WHERE nom=?", (station,))
    return c.fetchone()

def update_stock(station, gazoil, super_fuel):
    c.execute("UPDATE stations SET gazoil_stock=?, super_stock=? WHERE nom=?", 
              (gazoil, super_fuel, station))
    conn.commit()

# Interface de connexion
def page_connexion():
    st.title("⛽ Gestion des Stations-Service")
    st.write("Veuillez vous connecter pour accéder au système")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Connexion Employé")
        nom = st.text_input("Nom d'utilisateur")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter"):
            utilisateur = verifier_utilisateur(nom, mot_de_passe)
            if utilisateur:
                st.session_state['utilisateur'] = utilisateur
                st.session_state['role'] = utilisateur[3]
                st.session_state['page'] = 'employe' if utilisateur[3] == 'employe' else 'admin'
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect")
    
    with col2:
        st.subheader("Accès Admin")
        admin_pass = st.text_input("Mot de passe admin", type="password", key="admin_pass")
        
        if st.button("Accès Admin"):
            if admin_pass == "admin123":  # Mot de passe admin temporaire
                st.session_state['page'] = 'admin'
                st.session_state['role'] = 'admin'
                st.rerun()
            else:
                st.error("Mot de passe admin incorrect")

# Interface employé
def page_employe():
    utilisateur = st.session_state['utilisateur']
    station = utilisateur[4]
    
    st.title(f"⛽ Station {station}")
    st.sidebar.title(f"Profil")
    st.sidebar.write(f"Nom: {utilisateur[1]}")
    st.sidebar.write(f"Prénom: {utilisateur[5]}")
    st.sidebar.write(f"Téléphone: {utilisateur[6]}")
    st.sidebar.write(f"Date d'embauche: {utilisateur[7]}")
    
    if st.sidebar.button("Déconnexion"):
        del st.session_state['utilisateur']
        del st.session_state['role']
        del st.session_state['page']
        st.rerun()
    
    # Vérifier si une activité existe déjà pour aujourd'hui
    today = date.today().isoformat()
    c.execute("SELECT * FROM activites WHERE utilisateur_id=? AND date=?", (utilisateur[0], today))
    activite_existante = c.fetchone()
    
    if activite_existante:
        st.warning("Vous avez déjà enregistré une activité pour aujourd'hui.")
        afficher_activite(activite_existante)
        return
    
    # Sélection de la pompe
    pompe = st.selectbox("Sélectionnez votre pompe pour aujourd'hui", ["Pompe A", "Pompe B", "Pompe C"])
    
    # Section Montée
    st.subheader("Montée - Début de journée")
    
    # Récupérer les valeurs de descente de la veille si elles existent
    hier = (date.today() - datetime.timedelta(days=1)).isoformat()
    c.execute("SELECT descente_gazoil, descente_super FROM activites WHERE station=? AND pompe=? AND date=?",
              (station, pompe, hier))
    valeurs_veille = c.fetchone()
    
    gazoil_monte = st.number_input("Quantité de Gazoil dans la cuve (L)", 
                                  min_value=0.0, 
                                  max_value=10000.0,
                                  value=valeurs_veille[0] if valeurs_veille else 0.0,
                                  disabled=bool(valeurs_veille))
    
    super_monte = st.number_input("Quantité de Super dans la cuve (L)", 
                                 min_value=0.0, 
                                 max_value=10000.0,
                                 value=valeurs_veille[1] if valeurs_veille else 0.0,
                                 disabled=bool(valeurs_veille))
    
    # Section Descente
    st.subheader("Descente - Fin de journée")
    gazoil_descente = st.number_input("Quantité restante de Gazoil (L)", min_value=0.0, max_value=10000.0)
    super_descente = st.number_input("Quantité restante de Super (L)", min_value=0.0, max_value=10000.0)
    
    # Prix des carburants
    c.execute("SELECT prix_gazoil, prix_super FROM stations WHERE nom=?", (station,))
    prix_gazoil, prix_super = c.fetchone()
    
    st.subheader("Ventes déclarées")
    montant_gazoil = st.number_input("Montant vendu pour Gazoil (FCFA)", min_value=0.0)
    montant_super = st.number_input("Montant vendu pour Super (FCFA)", min_value=0.0)
    
    if st.button("Enregistrer la journée"):
        # Calcul des quantités vendues
        quantite_vendue_gazoil = gazoil_monte - gazoil_descente
        quantite_vendue_super = super_monte - super_descente
        
        # Calcul des montants théoriques
        montant_calcule_gazoil = quantite_vendue_gazoil * prix_gazoil
        montant_calcule_super = quantite_vendue_super * prix_super
        
        # Enregistrement dans la base de données
        c.execute('''INSERT INTO activites 
                    (date, utilisateur_id, station, pompe, monte_gazoil, monte_super, 
                     descente_gazoil, descente_super, montant_declare_gazoil, montant_declare_super)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (today, utilisateur[0], station, pompe, gazoil_monte, super_monte,
                   gazoil_descente, super_descente, montant_gazoil, montant_super))
        conn.commit()
        
        # Mise à jour du stock
        c.execute("SELECT gazoil_stock, super_stock FROM stations WHERE nom=?", (station,))
        current_gazoil, current_super = c.fetchone()
        new_gazoil = current_gazoil - quantite_vendue_gazoil
        new_super = current_super - quantite_vendue_super
        update_stock(station, new_gazoil, new_super)
        
        st.success("Journée enregistrée avec succès!")
        
        # Afficher le récapitulatif
        st.subheader("Récapitulatif de la journée")
        recap_data = {
            "Type": ["Gazoil", "Super"],
            "Quantité vendue (L)": [quantite_vendue_gazoil, quantite_vendue_super],
            "Montant déclaré (FCFA)": [montant_gazoil, montant_super],
            "Montant calculé (FCFA)": [montant_calcule_gazoil, montant_calcule_super],
            "Différence (FCFA)": [montant_gazoil - montant_calcule_gazoil, montant_super - montant_calcule_super]
        }
        recap_df = pd.DataFrame(recap_data)
        
        # Mise en forme conditionnelle
        def color_diff(val):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        
        st.dataframe(recap_df.style.applymap(color_diff, subset=['Différence (FCFA)']))

def afficher_activite(activite):
    st.subheader(f"Activité du {activite[1]}")
    
    # Récupérer les prix
    c.execute("SELECT prix_gazoil, prix_super FROM stations WHERE nom=?", (activite[3],))
    prix_gazoil, prix_super = c.fetchone()
    
    # Calculs
    quantite_vendue_gazoil = activite[5] - activite[7]
    quantite_vendue_super = activite[6] - activite[8]
    montant_calcule_gazoil = quantite_vendue_gazoil * prix_gazoil
    montant_calcule_super = quantite_vendue_super * prix_super
    
    # Création du tableau récapitulatif
    recap_data = {
        "Type": ["Gazoil", "Super"],
        "Montée (L)": [activite[5], activite[6]],
        "Descente (L)": [activite[7], activite[8]],
        "Quantité vendue (L)": [quantite_vendue_gazoil, quantite_vendue_super],
        "Montant déclaré (FCFA)": [activite[9], activite[10]],
        "Montant calculé (FCFA)": [montant_calcule_gazoil, montant_calcule_super],
        "Différence (FCFA)": [
            activite[9] - montant_calcule_gazoil,
            activite[10] - montant_calcule_super
        ]
    }
    recap_df = pd.DataFrame(recap_data)
    
    # Mise en forme conditionnelle
    def color_diff(val):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'
    
    st.dataframe(recap_df.style.applymap(color_diff, subset=['Différence (FCFA)']))

# Interface admin
def page_admin():
    st.title("⛽ Administration des Stations-Service")
    
    menu = st.sidebar.selectbox("Menu Admin", [
        "Tableau de bord", 
        "Gestion des Stations", 
        "Gestion des Employés",
        "Livraisons",
        "Bilan Comptable"
    ])
    
    if st.sidebar.button("Déconnexion"):
        del st.session_state['role']
        del st.session_state['page']
        st.rerun()
    
    if menu == "Tableau de bord":
        st.header("Tableau de bord global")
        
        # Récupérer toutes les stations
        c.execute("SELECT nom FROM stations")
        stations = [row[0] for row in c.fetchall()]
        
        selected_station = st.selectbox("Sélectionnez une station", ["Toutes"] + stations)
        
        if selected_station == "Toutes":
            # Afficher les données pour toutes les stations
            c.execute("SELECT * FROM activites ORDER BY date DESC")
            activites = c.fetchall()
        else:
            # Afficher les données pour une station spécifique
            c.execute("SELECT * FROM activites WHERE station=? ORDER BY date DESC", (selected_station,))
            activites = c.fetchall()
        
        if activites:
            # Convertir en DataFrame
            cols = ["ID", "Date", "UserID", "Station", "Pompe", "Monte Gazoil", "Monte Super",
                    "Descente Gazoil", "Descente Super", "Montant Gazoil", "Montant Super"]
            df = pd.DataFrame(activites, columns=cols)
            
            # Ajouter des calculs
            df['Quantité Gazoil Vendue'] = df['Monte Gazoil'] - df['Descente Gazoil']
            df['Quantité Super Vendue'] = df['Monte Super'] - df['Descente Super']
            
            # Récupérer les prix pour chaque station
            prix = {}
            for station in df['Station'].unique():
                c.execute("SELECT prix_gazoil, prix_super FROM stations WHERE nom=?", (station,))
                prix[station] = c.fetchone()
            
            df['Montant Calculé Gazoil'] = df.apply(
                lambda row: row['Quantité Gazoil Vendue'] * prix[row['Station']][0], axis=1)
            df['Montant Calculé Super'] = df.apply(
                lambda row: row['Quantité Super Vendue'] * prix[row['Station']][1], axis=1)
            df['Différence Gazoil'] = df['Montant Gazoil'] - df['Montant Calculé Gazoil']
            df['Différence Super'] = df['Montant Super'] - df['Montant Calculé Super']
            
            # Afficher le DataFrame avec mise en forme
            st.dataframe(df.style.applymap(
                lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                subset=['Différence Gazoil', 'Différence Super']
            ))
            
            # Graphiques d'évolution
            st.subheader("Évolution des ventes")
            
            fig = px.line(df, x='Date', y=['Quantité Gazoil Vendue', 'Quantité Super Vendue'],
                         title='Quantités vendues par jour')
            st.plotly_chart(fig)
            
            fig2 = px.line(df, x='Date', y=['Montant Gazoil', 'Montant Super'],
                          title='Montants vendus par jour')
            st.plotly_chart(fig2)
            
        else:
            st.warning("Aucune activité enregistrée pour cette sélection.")
    
    elif menu == "Gestion des Stations":
        st.header("Gestion des Stations")
        
        # Ajouter une nouvelle station
        with st.expander("Ajouter une nouvelle station"):
            with st.form("nouvelle_station"):
                nom = st.text_input("Nom de la station")
                adresse = st.text_input("Adresse")
                gazoil_stock = st.number_input("Stock initial Gazoil (L)", min_value=0.0)
                super_stock = st.number_input("Stock initial Super (L)", min_value=0.0)
                prix_gazoil = st.number_input("Prix du Gazoil (FCFA/L)", min_value=0.0)
                prix_super = st.number_input("Prix du Super (FCFA/L)", min_value=0.0)
                
                if st.form_submit_button("Enregistrer"):
                    try:
                        c.execute('''INSERT INTO stations 
                                    (nom, adresse, gazoil_stock, super_stock, prix_gazoil, prix_super)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                 (nom, adresse, gazoil_stock, super_stock, prix_gazoil, prix_super))
                        conn.commit()
                        st.success("Station enregistrée avec succès!")
                    except sqlite3.IntegrityError:
                        st.error("Une station avec ce nom existe déjà")
        
        # Liste des stations existantes
        st.subheader("Liste des stations")
        c.execute("SELECT * FROM stations")
        stations = c.fetchall()
        
        if stations:
            cols = ["ID", "Nom", "Adresse", "Gazoil (L)", "Super (L)", "Prix Gazoil", "Prix Super"]
            df = pd.DataFrame(stations, columns=cols)
            st.dataframe(df)
        else:
            st.info("Aucune station enregistrée")
    
    elif menu == "Gestion des Employés":
        st.header("Gestion des Employés")
        
        # Ajouter un nouvel employé
        with st.expander("Ajouter un nouvel employé"):
            with st.form("nouvel_employe"):
                nom = st.text_input("Nom d'utilisateur")
                mot_de_passe = st.text_input("Mot de passe", type="password")
                prenom = st.text_input("Prénom")
                telephone = st.text_input("Téléphone")
                date_embauche = st.date_input("Date d'embauche")
                c.execute("SELECT nom FROM stations")
                stations = [row[0] for row in c.fetchall()]
                station = st.selectbox("Station d'affectation", stations)
                
                if st.form_submit_button("Enregistrer"):
                    try:
                        mot_de_passe_hash = hash_password(mot_de_passe)
                        c.execute('''INSERT INTO utilisateurs 
                                    (nom, mot_de_passe, role, station, prenom, telephone, date_embauche)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                 (nom, mot_de_passe_hash, 'employe', station, 
                                  prenom, telephone, date_embauche.isoformat()))
                        conn.commit()
                        st.success("Employé enregistré avec succès!")
                    except sqlite3.IntegrityError:
                        st.error("Un utilisateur avec ce nom existe déjà")
        
        # Liste des employés
        st.subheader("Liste des employés")
        c.execute("SELECT id, nom, prenom, telephone, station, date_embauche FROM utilisateurs WHERE role='employe'")
        employes = c.fetchall()
        
        if employes:
            cols = ["ID", "Nom", "Prénom", "Téléphone", "Station", "Date d'embauche"]
            df = pd.DataFrame(employes, columns=cols)
            st.dataframe(df)
        else:
            st.info("Aucun employé enregistré")
    
    elif menu == "Livraisons":
        st.header("Gestion des Livraisons")
        
        c.execute("SELECT nom FROM stations")
        stations = [row[0] for row in c.fetchall()]
        selected_station = st.selectbox("Sélectionnez une station", stations)
        
        current_gazoil, current_super = get_stock(selected_station)
        st.write(f"Stock actuel - Gazoil: {current_gazoil} L | Super: {current_super} L")
        
        with st.form("livraison_form"):
            gazoil_livraison = st.number_input("Quantité de Gazoil livrée (L)", min_value=0.0)
            super_livraison = st.number_input("Quantité de Super livrée (L)", min_value=0.0)
            
            if st.form_submit_button("Enregistrer la livraison"):
                new_gazoil = current_gazoil + gazoil_livraison
                new_super = current_super + super_livraison
                update_stock(selected_station, new_gazoil, new_super)
                st.success(f"Stock mis à jour - Gazoil: {new_gazoil} L | Super: {new_super} L")
    
    elif menu == "Bilan Comptable":
        st.header("Bilan Comptable")
        
        # Sélection de la période
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date de début")
        with col2:
            date_fin = st.date_input("Date de fin")
        
        if st.button("Générer le bilan"):
            c.execute('''SELECT station, 
                         SUM(monte_gazoil - descente_gazoil) as total_gazoil,
                         SUM(monte_super - descente_super) as total_super,
                         SUM(montant_declare_gazoil) as total_montant_gazoil,
                         SUM(montant_declare_super) as total_montant_super
                         FROM activites
                         WHERE date BETWEEN ? AND ?
                         GROUP BY station''',
                      (date_debut.isoformat(), date_fin.isoformat()))
            resultats = c.fetchall()
            
            if resultats:
                cols = ["Station", "Gazoil vendu (L)", "Super vendu (L)", 
                       "Montant Gazoil (FCFA)", "Montant Super (FCFA)"]
                df = pd.DataFrame(resultats, columns=cols)
                
                # Calcul des totaux
                df.loc['Total'] = df.sum(numeric_only=True)
                
                # Calcul des montants théoriques
                for index, row in df.iterrows():
                    if index == 'Total':
                        continue
                    c.execute("SELECT prix_gazoil, prix_super FROM stations WHERE nom=?", (row['Station'],))
                    prix_gazoil, prix_super = c.fetchone()
                    df.at[index, 'Montant Calculé Gazoil'] = row['Gazoil vendu (L)'] * prix_gazoil
                    df.at[index, 'Montant Calculé Super'] = row['Super vendu (L)'] * prix_super
                    df.at[index, 'Différence Gazoil'] = row['Montant Gazoil (FCFA)'] - df.at[index, 'Montant Calculé Gazoil']
                    df.at[index, 'Différence Super'] = row['Montant Super (FCFA)'] - df.at[index, 'Montant Calculé Super']
                
                # Mise en forme
                st.dataframe(df.style.applymap(
                    lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                    subset=['Différence Gazoil', 'Différence Super']
                ))
                
                # Graphiques
                st.subheader("Répartition des ventes")
                
                fig = px.pie(df[:-1], values='Montant Gazoil (FCFA)', names='Station',
                            title='Répartition des ventes de Gazoil par station')
                st.plotly_chart(fig)
                
                fig2 = px.pie(df[:-1], values='Montant Super (FCFA)', names='Station',
                             title='Répartition des ventes de Super par station')
                st.plotly_chart(fig2)
            else:
                st.warning("Aucune activité enregistrée pour cette période")

# Page principale
def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'connexion'
    
    if st.session_state['page'] == 'connexion':
        page_connexion()
    elif st.session_state['page'] == 'employe':
        page_employe()
    elif st.session_state['page'] == 'admin':
        page_admin()

if __name__ == "__main__":
    main()