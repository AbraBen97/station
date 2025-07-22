import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
from typing import Dict, List
from io import BytesIO

# Configuration de la page
st.set_page_config(
    page_title="Gestion Stations-Service",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .alert-red {
        background-color: #ff4b4b;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    .alert-green {
        background-color: #00d4aa;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    .alert-orange {
        background-color: #ff8c00;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .justify-button {
        background-color: #ffa500 !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data_from_excel():
    """Charger les données depuis les fichiers Excel"""
    try:
        # Charger les utilisateurs
        if os.path.exists('users.xlsx'):
            users_df = pd.read_excel('users.xlsx')
            st.session_state.users = users_df.set_index('username').to_dict('index')
        
        # Charger les enregistrements quotidiens
        if os.path.exists('daily_records.xlsx'):
            records_df = pd.read_excel('daily_records.xlsx')
            st.session_state.daily_records = records_df.to_dict('records')
        
        # Charger l'inventaire
        if os.path.exists('inventory.xlsx'):
            inventory_df = pd.read_excel('inventory.xlsx')
            inventory_dict = {}
            for _, row in inventory_df.iterrows():
                inventory_dict[row['station']] = {
                    'gazoil': float(row['gazoil']),
                    'super': float(row['super'])
                }
            st.session_state.inventory = inventory_dict
        
        # Charger les alertes justifiées
        if os.path.exists('justified_alerts.xlsx'):
            alerts_df = pd.read_excel('justified_alerts.xlsx')
            st.session_state.justified_alerts = alerts_df.to_dict('records')
        
        # Charger les prix
        if os.path.exists('prices.xlsx'):
            prices_df = pd.read_excel('prices.xlsx')
            st.session_state.prices = prices_df.set_index('fuel_type')['price'].astype(float).to_dict()
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")

def save_data_to_excel():
    """Sauvegarder toutes les données dans des fichiers Excel"""
    try:
        # Sauvegarder les utilisateurs
        users_df = pd.DataFrame.from_dict(st.session_state.users, orient='index')
        users_df.index.name = 'username'
        users_df.reset_index().to_excel('users.xlsx', index=False)
        
        # Sauvegarder les enregistrements quotidiens
        if st.session_state.daily_records:
            records_df = pd.DataFrame(st.session_state.daily_records)
            records_df.to_excel('daily_records.xlsx', index=False)
        
        # Sauvegarder l'inventaire
        inventory_data = []
        for station, stock in st.session_state.inventory.items():
            inventory_data.append({
                'station': station,
                'gazoil': float(stock['gazoil']),
                'super': float(stock['super'])
            })
        inventory_df = pd.DataFrame(inventory_data)
        inventory_df.to_excel('inventory.xlsx', index=False)
        
        # Sauvegarder les alertes justifiées
        if 'justified_alerts' in st.session_state and st.session_state.justified_alerts:
            alerts_df = pd.DataFrame(st.session_state.justified_alerts)
            alerts_df.to_excel('justified_alerts.xlsx', index=False)
        
        # Sauvegarder les prix
        prices_data = [{'fuel_type': k, 'price': float(v)} for k, v in st.session_state.prices.items()]
        prices_df = pd.DataFrame(prices_data)
        prices_df.to_excel('prices.xlsx', index=False)
        
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {e}")

def init_data():
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'jean_dupont': {'password': 'pass123', 'role': 'worker', 'nom': 'Jean Dupont', 'station': 'Station A', 'telephone': '0123456789'},
            'marie_martin': {'password': 'pass456', 'role': 'worker', 'nom': 'Marie Martin', 'station': 'Station B', 'telephone': '0987654321'},
            'paul_bernard': {'password': 'pass789', 'role': 'worker', 'nom': 'Paul Bernard', 'station': 'Station C', 'telephone': '0147258369'},
        }
    
    if 'prices' not in st.session_state:
        st.session_state.prices = {
            'gazoil': 600.0,  # Use float
            'super': 700.0    # Use float
        }
    
    if 'stations' not in st.session_state:
        st.session_state.stations = ['Station A', 'Station B', 'Station C']
    
    if 'pumps' not in st.session_state:
        st.session_state.pumps = ['Pompe A', 'Pompe B', 'Pompe C']
    
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            'Station A': {'gazoil': 5000.0, 'super': 3000.0},
            'Station B': {'gazoil': 4500.0, 'super': 3500.0},
            'Station C': {'gazoil': 6000.0, 'super': 2800.0}
        }
    
    if 'daily_records' not in st.session_state:
        st.session_state.daily_records = []
    
    if 'justified_alerts' not in st.session_state:
        st.session_state.justified_alerts = []
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    # Charger les données depuis Excel si elles existent
    load_data_from_excel()

def login_page():
    st.title("🔐 Connexion - Gestion Stations-Service")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 👥 Connexion Employé")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter", key="employee_login"):
            if username in st.session_state.users and st.session_state.users[username]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.user_role = st.session_state.users[username]['role']
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect")
        
        st.markdown("---")
        st.markdown("### 👨‍💼 Accès Administrateur")
        admin_password = st.text_input("Mot de passe Admin", type="password", key="admin_pass")
        
        if st.button("Accès Admin", key="admin_login"):
            if admin_password == "admin123":
                st.session_state.logged_in = True
                st.session_state.current_user = "admin"
                st.session_state.user_role = "admin"
                st.rerun()
            else:
                st.error("Mot de passe administrateur incorrect")

def worker_dashboard():
    user_info = st.session_state.users[st.session_state.current_user]
    station = user_info['station']
    
    st.title(f"👋 Bonjour {user_info['nom']}")
    st.subheader(f"📍 {station}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Prix Gazoil", f"{st.session_state.prices['gazoil']:.2f} Franc CFA/L")
    with col2:
        st.metric("Prix Super", f"{st.session_state.prices['super']:.2f} Franc CFA/L")
    
    # Sélection de pompe
    st.markdown("### 🔧 Sélection de pompe")
    selected_pump = st.selectbox("Choisir votre pompe", st.session_state.pumps)
    
    today = date.today()
    
    # Vérifier s'il y a déjà un enregistrement aujourd'hui
    today_record = None
    for record in st.session_state.daily_records:
        if (record['date'] == today.strftime('%Y-%m-%d') and 
            record['station'] == station and 
            record['pump'] == selected_pump and
            record['user'] == st.session_state.current_user):
            today_record = record
            break
    
    if today_record is None:
        # Première connexion de la journée - Montée
        st.markdown("### ⬆️ Montée de service")
        
        col1, col2 = st.columns(2)
        
        # Récupérer les quantités de la veille
        yesterday = today - timedelta(days=1)
        yesterday_record = None
        for record in st.session_state.daily_records:
            if (record['date'] == yesterday.strftime('%Y-%m-%d') and 
                record['station'] == station and 
                record['pump'] == selected_pump):
                yesterday_record = record
                break
        
        if yesterday_record:
            initial_gazoil = yesterday_record['gazoil_end']
            initial_super = yesterday_record['super_end']
            st.info(f"Quantités de la veille: Gazoil {initial_gazoil}L, Super {initial_super}L")
        else:
            initial_gazoil = st.session_state.inventory[station]['gazoil'] // 3
            initial_super = st.session_state.inventory[station]['super'] // 3
        
        with col1:
            gazoil_start = st.number_input("Quantité Gazoil (L)", value=float(initial_gazoil), disabled=yesterday_record is not None)
        
        with col2:
            super_start = st.number_input("Quantité Super (L)", value=float(initial_super), disabled=yesterday_record is not None)
        
        if st.button("🔼 Enregistrer Montée"):
            new_record = {
                'date': today.strftime('%Y-%m-%d'),
                'station': station,
                'pump': selected_pump,
                'user': st.session_state.current_user,
                'time_start': datetime.now().strftime('%H:%M'),
                'gazoil_start': gazoil_start,
                'super_start': super_start,
                'gazoil_end': None,
                'super_end': None,
                'gazoil_amount': None,
                'super_amount': None,
                'total_declared_amount': None,
                'total_calculated_amount': None,
                'difference': None,
                'status': 'in_progress'
            }
            st.session_state.daily_records.append(new_record)
            save_data_to_excel()
            st.success("Montée enregistrée avec succès!")
            st.rerun()
    
    elif today_record['status'] == 'in_progress':
        # Descente
        st.markdown("### ⬇️ Descente de service")
        st.info(f"Service commencé à {today_record['time_start']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Gazoil début", f"{today_record['gazoil_start']} L")
            gazoil_end = st.number_input("Quantité Gazoil restante (L)", min_value=0.0, max_value=float(today_record['gazoil_start']))
        
        with col2:
            st.metric("Super début", f"{today_record['super_start']} L")
            super_end = st.number_input("Quantité Super restante (L)", min_value=0.0, max_value=float(today_record['super_start']))
        
        # Montants séparés pour gazoil et super
        st.markdown("### 💰 Montants vendus")
        col1, col2 = st.columns(2)
        
        with col1:
            gazoil_amount = st.number_input("Montant Gazoil vendu (Franc CFA)", min_value=0.0, step=0.01)
        
        with col2:
            super_amount = st.number_input("Montant Super vendu (Franc CFA)", min_value=0.0, step=0.01)
        
        total_declared_amount = gazoil_amount + super_amount
        
        # Calculs
        gazoil_sold = today_record['gazoil_start'] - gazoil_end
        super_sold = today_record['super_start'] - super_end
        gazoil_calculated = gazoil_sold * st.session_state.prices['gazoil']
        super_calculated = super_sold * st.session_state.prices['super']
        total_calculated_amount = gazoil_calculated + super_calculated
        difference = total_declared_amount - total_calculated_amount
        
        # Affichage des résultats
        st.markdown("### 📊 Résumé des ventes")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gazoil vendu", f"{gazoil_sold:.1f} L")
            st.metric("Calculé Gazoil", f"{gazoil_calculated:.2f} CFA")
        
        with col2:
            st.metric("Super vendu", f"{super_sold:.1f} L")
            st.metric("Calculé Super", f"{super_calculated:.2f} CFA")
        
        with col3:
            st.metric("Total calculé", f"{total_calculated_amount:.2f} CFA")
        
        with col4:
            st.metric("Total déclaré", f"{total_declared_amount:.2f} CFA")
            if difference < 0:
                st.markdown(f'<div class="alert-red">Différence: {difference:.2f} CFA</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-green">Différence: +{difference:.2f} CFA</div>', unsafe_allow_html=True)
        
        if st.button("🔽 Enregistrer Descente"):
            # Mettre à jour l'enregistrement
            for i, record in enumerate(st.session_state.daily_records):
                if (record['date'] == today.strftime('%Y-%m-%d') and 
                    record['station'] == station and 
                    record['pump'] == selected_pump and
                    record['user'] == st.session_state.current_user):
                    st.session_state.daily_records[i].update({
                        'time_end': datetime.now().strftime('%H:%M'),
                        'gazoil_end': gazoil_end,
                        'super_end': super_end,
                        'gazoil_amount': gazoil_amount,
                        'super_amount': super_amount,
                        'total_declared_amount': total_declared_amount,
                        'total_calculated_amount': total_calculated_amount,
                        'difference': difference,
                        'status': 'completed'
                    })
                    break
            
            save_data_to_excel()
            st.success("Descente enregistrée avec succès!")
            st.rerun()
    
    else:
        # Service terminé
        st.markdown("### ✅ Service terminé")
        st.success(f"Votre service est terminé. Montée: {today_record['time_start']}, Descente: {today_record['time_end']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Gazoil vendu", f"{today_record['gazoil_start'] - today_record['gazoil_end']} L")
            if 'gazoil_amount' in today_record:
                st.metric("Montant Gazoil", f"{today_record['gazoil_amount']:.2f} CFA")
        
        with col2:
            st.metric("Super vendu", f"{today_record['super_start'] - today_record['super_end']} L")
            if 'super_amount' in today_record:
                st.metric("Montant Super", f"{today_record['super_amount']:.2f} CFA")
        
        with col3:
            if today_record['difference'] < 0:
                st.markdown(f'<div class="alert-red">Différence: {today_record["difference"]:.2f} CFA</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-green">Différence: +{today_record["difference"]:.2f} CFA</div>', unsafe_allow_html=True)

def admin_dashboard():
    st.title("👨‍💼 Tableau de Bord Administrateur")
    
    tabs = st.tabs(["📊 Vue d'ensemble", "🏪 Suivi par station", "⚠️ Alertes", "🚚 Livraisons", "💰 Bilan comptable", "👥 Gestion utilisateurs", "⚙️ Paramètres"])
    
    with tabs[0]:  # Vue d'ensemble
        st.subheader("Résumé général")
        
        # Métriques générales
        today = date.today()
        today_records = [r for r in st.session_state.daily_records if r['date'] == today.strftime('%Y-%m-%d')]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = sum([r.get('total_declared_amount', 0) for r in today_records if r.get('total_declared_amount')])
            st.metric("Chiffre d'affaires (aujourd'hui)", f"{total_revenue:.2f} CFA")
        
        with col2:
            active_pumps = len([r for r in today_records if r.get('status') in ['in_progress', 'completed']])
            st.metric("Pompes actives", active_pumps)
        
        with col3:
            total_alerts = len([r for r in today_records if r.get('difference', 0) < -10])
            st.metric("Alertes", total_alerts)
        
        with col4:
            total_inventory = sum([sum(inv.values()) for inv in st.session_state.inventory.values()])
            st.metric("Stock total (L)", f"{total_inventory:,.0f}")
        
        # Graphique évolution des ventes
        if st.session_state.daily_records:
            df = pd.DataFrame(st.session_state.daily_records)
            df = df[df['total_declared_amount'].notna()]
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                daily_sales = df.groupby('date')['total_declared_amount'].sum().reset_index()
                
                fig = px.line(daily_sales, x='date', y='total_declared_amount', 
                             title="Évolution du chiffre d'affaires",
                             labels={'total_declared_amount': 'Chiffre d\'affaires (CFA)', 'date': 'Date'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:  # Suivi par station
        st.subheader("Suivi détaillé par station")
        
        selected_station = st.selectbox("Sélectionner une station", st.session_state.stations)
        
        station_records = [r for r in st.session_state.daily_records if r['station'] == selected_station]
        
        if station_records:
            df = pd.DataFrame(station_records)
            df = df[df['total_declared_amount'].notna()]
            
            if not df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Ventes par pompe
                    pump_sales = df.groupby('pump')['total_declared_amount'].sum()
                    fig_pie = px.pie(values=pump_sales.values, names=pump_sales.index, 
                                    title="Répartition des ventes par pompe")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Évolution des stocks
                    inventory = st.session_state.inventory[selected_station]
                    fig_bar = px.bar(x=list(inventory.keys()), y=list(inventory.values()),
                                    title="Stock actuel", labels={'x': 'Type', 'y': 'Quantité (L)'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Tableau détaillé
                display_columns = ['date', 'pump', 'user', 'gazoil_amount', 'super_amount', 'total_declared_amount', 'total_calculated_amount', 'difference']
                available_columns = [col for col in display_columns if col in df.columns]
                st.dataframe(df[available_columns])
        else:
            st.info("Aucune donnée disponible pour cette station.")
    
    with tabs[2]:  # Alertes
        st.subheader("⚠️ Alertes et anomalies")
        
        alerts = []
        for record in st.session_state.daily_records:
            if record.get('difference') and record['difference'] < -5:
                # Vérifier si l'alerte n'a pas été justifiée
                alert_id = f"{record['date']}_{record['station']}_{record['pump']}_{record['user']}"
                if not any(ja['alert_id'] == alert_id for ja in st.session_state.justified_alerts):
                    alerts.append(record)
        
        if alerts:
            for i, alert in enumerate(alerts):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="alert-red">
                        🚨 <strong>{alert['station']} - {alert['pump']}</strong><br>
                        Date: {alert['date']} | Employé: {st.session_state.users.get(alert['user'], {}).get('nom', alert['user'])}<br>
                        Différence: {alert['difference']:.2f} CFA | Déclaré: {alert.get('total_declared_amount', 0):.2f} CFA | Calculé: {alert.get('total_calculated_amount', 0):.2f} CFA
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    justification = st.text_input(f"Justification", key=f"just_{i}", placeholder="Raison de la différence")
                    if st.button("✅ Justifier", key=f"justify_{i}"):
                        if justification:
                            alert_id = f"{alert['date']}_{alert['station']}_{alert['pump']}_{alert['user']}"
                            justified_alert = {
                                'alert_id': alert_id,
                                'date': alert['date'],
                                'station': alert['station'],
                                'pump': alert['pump'],
                                'user': alert['user'],
                                'difference': alert['difference'],
                                'justification': justification,
                                'justified_by': st.session_state.current_user,
                                'justified_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                            }
                            st.session_state.justified_alerts.append(justified_alert)
                            save_data_to_excel()
                            st.success("Alerte justifiée et supprimée!")
                            st.rerun()
                        else:
                            st.error("Veuillez fournir une justification")
        else:
            st.success("Aucune alerte en cours ✅")
        
        # Afficher les alertes justifiées
        if st.session_state.justified_alerts:
            st.markdown("### 📋 Alertes justifiées")
            justified_df = pd.DataFrame(st.session_state.justified_alerts)
            st.dataframe(justified_df)
    
    with tabs[3]:  # Livraisons
        st.subheader("🚚 Gestion des livraisons")
        
        col1, col2 = st.columns(2)
        
        with col1:
            delivery_station = st.selectbox("Station", st.session_state.stations, key="delivery_station")
            fuel_type = st.selectbox("Type de carburant", ["gazoil", "super"])
            quantity = st.number_input("Quantité livrée (L)", min_value=0, step=100)
            
            if st.button("Ajouter livraison"):
                st.session_state.inventory[delivery_station][fuel_type] += quantity
                
                # Enregistrer la livraison
                delivery_record = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'time': datetime.now().strftime('%H:%M'),
                    'station': delivery_station,
                    'fuel_type': fuel_type,
                    'quantity': quantity,
                    'action': 'delivery',
                    'user': st.session_state.current_user
                }
                
                # Ajouter aux enregistrements
                if 'delivery_records' not in st.session_state:
                    st.session_state.delivery_records = []
                st.session_state.delivery_records.append(delivery_record)
                
                save_data_to_excel()
                st.success(f"Livraison ajoutée: {quantity}L de {fuel_type} à {delivery_station}")
                st.rerun()
        
        with col2:
            st.markdown("### Stock actuel")
            for station, stock in st.session_state.inventory.items():
                st.markdown(f"**{station}:**")
                st.markdown(f"- Gazoil: {stock['gazoil']:,} L")
                st.markdown(f"- Super: {stock['super']:,} L")
    
    with tabs[4]:  # Bilan comptable
        st.subheader("💰 Bilan comptable")
        
        if st.session_state.daily_records:
            df = pd.DataFrame(st.session_state.daily_records)
            completed_records = df[df['total_declared_amount'].notna()]
            
            if not completed_records.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_declared = completed_records['total_declared_amount'].sum()
                    st.metric("Total déclaré", f"{total_declared:.2f} CFA")
                
                with col2:
                    total_calculated = completed_records['total_calculated_amount'].sum()
                    st.metric("Total calculé", f"{total_calculated:.2f} CFA")
                
                with col3:
                    total_difference = completed_records['difference'].sum()
                    if total_difference < 0:
                        st.markdown(f'<div class="alert-red">Écart total: {total_difference:.2f} CFA</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="alert-green">Écart total: +{total_difference:.2f} CFA</div>', unsafe_allow_html=True)
                
                # Export Excel
                if st.button("📊 Exporter le rapport Excel"):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Feuille principale des ventes
                        completed_records.to_excel(writer, sheet_name='Ventes', index=False)
                        
                        # Feuille des alertes justifiées
                        if st.session_state.justified_alerts:
                            justified_df = pd.DataFrame(st.session_state.justified_alerts)
                            justified_df.to_excel(writer, sheet_name='Alertes_justifiees', index=False)
                        
                        # Feuille de l'inventaire
                        inventory_data = []
                        for station, stock in st.session_state.inventory.items():
                            inventory_data.append({
                                'Station': station,
                                'Gazoil': stock['gazoil'],
                                'Super': stock['super'],
                                'Total': stock['gazoil'] + stock['super']
                            })
                        inventory_df = pd.DataFrame(inventory_data)
                        inventory_df.to_excel(writer, sheet_name='Inventaire', index=False)
                        
                        # Feuille des livraisons si elles existent
                        if 'delivery_records' in st.session_state and st.session_state.delivery_records:
                            delivery_df = pd.DataFrame(st.session_state.delivery_records)
                            delivery_df.to_excel(writer, sheet_name='Livraisons', index=False)
                    
                    output.seek(0)
                    st.download_button(
                        label="📥 Télécharger le rapport Excel",
                        data=output.getvalue(),
                        file_name=f"rapport_station_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Graphique évolution mensuelle
                completed_records['date'] = pd.to_datetime(completed_records['date'])
                completed_records['month'] = completed_records['date'].dt.to_period('M')
                monthly_sales = completed_records.groupby('month')[['total_declared_amount', 'total_calculated_amount']].sum()
                
                if not monthly_sales.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='Déclaré', x=monthly_sales.index.astype(str), y=monthly_sales['total_declared_amount']))
                    fig.add_trace(go.Bar(name='Calculé', x=monthly_sales.index.astype(str), y=monthly_sales['total_calculated_amount']))
                    fig.update_layout(title='Comparaison mensuelle: Déclaré vs Calculé', barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée comptable disponible.")
    
    with tabs[5]:  # Gestion utilisateurs
        st.subheader("👥 Gestion des utilisateurs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ➕ Ajouter un nouveau travailleur")
            
            new_username = st.text_input("Nom d'utilisateur")
            new_password = st.text_input("Mot de passe", type="password")
            new_name = st.text_input("Nom complet")
            new_station = st.selectbox("Station assignée", st.session_state.stations, key="new_station")
            new_phone = st.text_input("Numéro de téléphone")
            
            if st.button("➕ Ajouter le travailleur"):
                if new_username and new_password and new_name and new_phone:
                    if new_username not in st.session_state.users:
                        st.session_state.users[new_username] = {
                            'password': new_password,
                            'role': 'worker',
                            'nom': new_name,
                            'station': new_station,
                            'telephone': new_phone
                        }
                        save_data_to_excel()
                        st.success(f"Travailleur {new_name} ajouté avec succès!")
                        st.rerun()
                    else:
                        st.error("Ce nom d'utilisateur existe déjà!")
                else:
                    st.error("Veuillez remplir tous les champs!")
        
        with col2:
            st.markdown("### 👥 Liste des travailleurs")
            
            workers = {k: v for k, v in st.session_state.users.items() if v['role'] == 'worker'}
            
            for username, info in workers.items():
                with st.expander(f"{info['nom']} - {info['station']}"):
                    st.write(f"**Nom d'utilisateur:** {username}")
                    st.write(f"**Station:** {info['station']}")
                    st.write(f"**Téléphone:** {info['telephone']}")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button(f"✏️ Modifier", key=f"edit_{username}"):
                            st.session_state[f'edit_mode_{username}'] = True
                            st.rerun()
                    
                    with col_delete:
                        if st.button(f"🗑️ Supprimer", key=f"delete_{username}"):
                            if st.session_state.get(f'confirm_delete_{username}', False):
                                del st.session_state.users[username]
                                save_data_to_excel()
                                st.success(f"Travailleur {info['nom']} supprimé!")
                                st.rerun()
                            else:
                                st.session_state[f'confirm_delete_{username}'] = True
                                st.warning("Cliquez à nouveau pour confirmer la suppression")
                    
                    # Mode édition
                    if st.session_state.get(f'edit_mode_{username}', False):
                        st.markdown("---")
                        edit_name = st.text_input("Nouveau nom", value=info['nom'], key=f"edit_name_{username}")
                        edit_station = st.selectbox("Nouvelle station", st.session_state.stations, 
                                                   index=st.session_state.stations.index(info['station']), 
                                                   key=f"edit_station_{username}")
                        edit_phone = st.text_input("Nouveau téléphone", value=info['telephone'], key=f"edit_phone_{username}")
                        edit_password = st.text_input("Nouveau mot de passe (optionnel)", type="password", key=f"edit_pass_{username}")
                        
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.button("💾 Sauvegarder", key=f"save_{username}"):
                                st.session_state.users[username]['nom'] = edit_name
                                st.session_state.users[username]['station'] = edit_station
                                st.session_state.users[username]['telephone'] = edit_phone
                                if edit_password:
                                    st.session_state.users[username]['password'] = edit_password
                                
                                del st.session_state[f'edit_mode_{username}']
                                save_data_to_excel()
                                st.success("Modifications sauvegardées!")
                                st.rerun()
                        
                        with col_cancel:
                            if st.button("❌ Annuler", key=f"cancel_{username}"):
                                del st.session_state[f'edit_mode_{username}']
                                st.rerun()
    
    with tabs[6]:  # Paramètres
        st.subheader("⚙️ Paramètres")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Prix des carburants")
            new_gazoil_price = st.number_input("Prix Gazoil (CFA/L)", value=float(st.session_state.prices['gazoil']), step=0.01)
            new_super_price = st.number_input("Prix Super (CFA/L)", value=float(st.session_state.prices['super']), step=0.01)
            
            if st.button("Mettre à jour les prix"):
                st.session_state.prices['gazoil'] = new_gazoil_price
                st.session_state.prices['super'] = new_super_price
                save_data_to_excel()
                st.success("Prix mis à jour!")
            
            st.markdown("### Gestion des stations")
            new_station_name = st.text_input("Nom de la nouvelle station")
            if st.button("➕ Ajouter une station"):
                if new_station_name and new_station_name not in st.session_state.stations:
                    st.session_state.stations.append(new_station_name)
                    st.session_state.inventory[new_station_name] = {'gazoil': 0.0, 'super': 0.0}
                    save_data_to_excel()
                    st.success(f"Station {new_station_name} ajoutée!")
                    st.rerun()
                else:
                    st.error("Nom invalide ou station déjà existante!")
            
            st.markdown("### Gestion des pompes")
            new_pump_name = st.text_input("Nom de la nouvelle pompe")
            if st.button("➕ Ajouter une pompe"):
                if new_pump_name and new_pump_name not in st.session_state.pumps:
                    st.session_state.pumps.append(new_pump_name)
                    save_data_to_excel()
                    st.success(f"Pompe {new_pump_name} ajoutée!")
                    st.rerun()
                else:
                    st.error("Nom invalide ou pompe déjà existante!")
        
        with col2:
            st.markdown("### Sauvegarde et restauration")
            
            if st.button("💾 Sauvegarder manuellement"):
                save_data_to_excel()
                st.success("Données sauvegardées!")
            
            st.markdown("### Statistiques système")
            st.metric("Nombre d'utilisateurs", len(st.session_state.users))
            st.metric("Nombre de stations", len(st.session_state.stations))
            st.metric("Nombre de pompes", len(st.session_state.pumps))
            st.metric("Nombre d'enregistrements", len(st.session_state.daily_records))
            
            if st.session_state.justified_alerts:
                st.metric("Alertes justifiées", len(st.session_state.justified_alerts))
            
            # Informations sur les fichiers Excel
            st.markdown("### Fichiers de données")
            excel_files = ['users.xlsx', 'daily_records.xlsx', 'inventory.xlsx', 'justified_alerts.xlsx', 'prices.xlsx']
            for file in excel_files:
                if os.path.exists(file):
                    file_size = os.path.getsize(file)
                    st.text(f"✅ {file} ({file_size} bytes)")
                else:
                    st.text(f"❌ {file} (non créé)")
            
            # Export complet des données
            if st.button("📊 Exporter toutes les données"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Utilisateurs
                    users_df = pd.DataFrame.from_dict(st.session_state.users, orient='index')
                    users_df.index.name = 'username'
                    users_df.reset_index().to_excel(writer, sheet_name='Utilisateurs', index=False)
                    
                    # Enregistrements quotidiens
                    if st.session_state.daily_records:
                        records_df = pd.DataFrame(st.session_state.daily_records)
                        records_df.to_excel(writer, sheet_name='Enregistrements', index=False)
                    
                    # Inventaire
                    inventory_data = []
                    for station, stock in st.session_state.inventory.items():
                        inventory_data.append({
                            'Station': station,
                            'Gazoil': stock['gazoil'],
                            'Super': stock['super']
                        })
                    inventory_df = pd.DataFrame(inventory_data)
                    inventory_df.to_excel(writer, sheet_name='Inventaire', index=False)
                    
                    # Prix
                    prices_data = [{'Carburant': k, 'Prix': float(v)} for k, v in st.session_state.prices.items()]
                    prices_df = pd.DataFrame(prices_data)
                    prices_df.to_excel(writer, sheet_name='Prix', index=False)
                    
                    # Alertes justifiées
                    if st.session_state.justified_alerts:
                        justified_df = pd.DataFrame(st.session_state.justified_alerts)
                        justified_df.to_excel(writer, sheet_name='Alertes_justifiees', index=False)
                    
                    # Livraisons si elles existent
                    if 'delivery_records' in st.session_state and st.session_state.delivery_records:
                        delivery_df = pd.DataFrame(st.session_state.delivery_records)
                        delivery_df.to_excel(writer, sheet_name='Livraisons', index=False)
                
                output.seek(0)
                st.download_button(
                    label="📥 Télécharger l'export complet",
                    data=output.getvalue(),
                    file_name=f"export_complet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def main():
    init_data()
    
    # Sidebar pour déconnexion
    if st.session_state.logged_in:
        with st.sidebar:
            st.write(f"Connecté en tant que: **{st.session_state.current_user}**")
            if st.button("🚪 Déconnexion"):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.session_state.user_role = None
                st.rerun()
    
    # Navigation principale
    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.user_role == 'admin':
        admin_dashboard()
    else:
        worker_dashboard()

if __name__ == "__main__":
    main()