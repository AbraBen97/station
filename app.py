import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
from typing import Dict, List

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
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

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
            'gazoil': 600,
            'super': 700
        }
    
    if 'stations' not in st.session_state:
        st.session_state.stations = ['Station A', 'Station B', 'Station C']
    
    if 'pumps' not in st.session_state:
        st.session_state.pumps = ['Pompe A', 'Pompe B', 'Pompe C']
    
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            'Station A': {'gazoil': 5000, 'super': 3000},
            'Station B': {'gazoil': 4500, 'super': 3500},
            'Station C': {'gazoil': 6000, 'super': 2800}
        }
    
    if 'daily_records' not in st.session_state:
        st.session_state.daily_records = []
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

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
        st.metric("Prix Gazoil", f"{st.session_state.prices['gazoil']:.2f} Franc Cfa/L")
    with col2:
        st.metric("Prix Super", f"{st.session_state.prices['super']:.2f} Franc Cfa/L")
    
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
        
        # Récupérer les quantités de la veille ou les quantités initiales
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
            gazoil_start = st.number_input("Quantité Gazoil (L)", value=initial_gazoil, disabled=yesterday_record is not None)
        
        with col2:
            super_start = st.number_input("Quantité Super (L)", value=initial_super, disabled=yesterday_record is not None)
        
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
                'declared_amount': None,
                'calculated_amount': None,
                'difference': None,
                'status': 'in_progress'
            }
            st.session_state.daily_records.append(new_record)
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
        
        declared_amount = st.number_input("Montant total vendu (Franc Cfa)", min_value=0.0, step=0.01)
        
        # Calculs
        gazoil_sold = today_record['gazoil_start'] - gazoil_end
        super_sold = today_record['super_start'] - super_end
        calculated_amount = (gazoil_sold * st.session_state.prices['gazoil'] + 
                           super_sold * st.session_state.prices['super'])
        difference = declared_amount - calculated_amount
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Montant calculé", f"{calculated_amount:.2f} Franc Cfa")
        with col2:
            st.metric("Montant déclaré", f"{declared_amount:.2f} Franc Cfa")
        with col3:
            if difference < 0:
                st.markdown(f'<div class="alert-red">Différence: {difference:.2f} Franc Cfa</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-green">Différence: +{difference:.2f} Franc Cfa</div>', unsafe_allow_html=True)
        
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
                        'declared_amount': declared_amount,
                        'calculated_amount': calculated_amount,
                        'difference': difference,
                        'status': 'completed'
                    })
                    break
            
            st.success("Descente enregistrée avec succès!")
            st.rerun()
    
    else:
        # Service terminé
        st.markdown("### ✅ Service terminé")
        st.success(f"Votre service est terminé. Montée: {today_record['time_start']}, Descente: {today_record['time_end']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Gazoil vendu", f"{today_record['gazoil_start'] - today_record['gazoil_end']} L")
        with col2:
            st.metric("Super vendu", f"{today_record['super_start'] - today_record['super_end']} L")
        with col3:
            if today_record['difference'] < 0:
                st.markdown(f'<div class="alert-red">Différence: {today_record["difference"]:.2f} Franc Cfa</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-green">Différence: +{today_record["difference"]:.2f} Franc Cfa</div>', unsafe_allow_html=True)

def admin_dashboard():
    st.title("👨‍💼 Tableau de Bord Administrateur")
    
    tabs = st.tabs(["📊 Vue d'ensemble", "🏪 Suivi par station", "⚠️ Alertes", "🚚 Livraisons", "💰 Bilan comptable", "⚙️ Paramètres"])
    
    with tabs[0]:  # Vue d'ensemble
        st.subheader("Résumé général")
        
        # Métriques générales
        today = date.today()
        today_records = [r for r in st.session_state.daily_records if r['date'] == today.strftime('%Y-%m-%d')]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = sum([r.get('declared_amount', 0) for r in today_records if r.get('declared_amount')])
            st.metric("Chiffre d'affaires (aujourd'hui)", f"{total_revenue:.2f} Franc Cfa")
        
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
            df = df[df['declared_amount'].notna()]
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                daily_sales = df.groupby('date')['declared_amount'].sum().reset_index()
                
                fig = px.line(daily_sales, x='date', y='declared_amount', 
                             title="Évolution du chiffre d'affaires",
                             labels={'declared_amount': 'Chiffre d\'affaires (Franc Cfa)', 'date': 'Date'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:  # Suivi par station
        st.subheader("Suivi détaillé par station")
        
        selected_station = st.selectbox("Sélectionner une station", st.session_state.stations)
        
        station_records = [r for r in st.session_state.daily_records if r['station'] == selected_station]
        
        if station_records:
            df = pd.DataFrame(station_records)
            df = df[df['declared_amount'].notna()]
            
            if not df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Ventes par pompe
                    pump_sales = df.groupby('pump')['declared_amount'].sum()
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
                st.dataframe(df[['date', 'pump', 'user', 'declared_amount', 'calculated_amount', 'difference']])
        else:
            st.info("Aucune donnée disponible pour cette station.")
    
    with tabs[2]:  # Alertes
        st.subheader("⚠️ Alertes et anomalies")
        
        alerts = []
        for record in st.session_state.daily_records:
            if record.get('difference') and record['difference'] < -5:
                alerts.append(record)
        
        if alerts:
            for alert in alerts:
                st.markdown(f"""
                <div class="alert-red">
                    🚨 <strong>{alert['station']} - {alert['pump']}</strong><br>
                    Date: {alert['date']} | Employé: {st.session_state.users.get(alert['user'], {}).get('nom', alert['user'])}<br>
                    Différence: {alert['difference']:.2f} Franc Cfa | Déclaré: {alert['declared_amount']:.2f} Franc Cfa | Calculé: {alert['calculated_amount']:.2f} Franc Cfa
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Aucune alerte en cours ✅")
    
    with tabs[3]:  # Livraisons
        st.subheader("🚚 Gestion des livraisons")
        
        col1, col2 = st.columns(2)
        
        with col1:
            delivery_station = st.selectbox("Station", st.session_state.stations, key="delivery_station")
            fuel_type = st.selectbox("Type de carburant", ["gazoil", "super"])
            quantity = st.number_input("Quantité livrée (L)", min_value=0, step=100)
            
            if st.button("Ajouter livraison"):
                st.session_state.inventory[delivery_station][fuel_type] += quantity
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
            completed_records = df[df['declared_amount'].notna()]
            
            if not completed_records.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_declared = completed_records['declared_amount'].sum()
                    st.metric("Total déclaré", f"{total_declared:.2f} Franc Cfa")
                
                with col2:
                    total_calculated = completed_records['calculated_amount'].sum()
                    st.metric("Total calculé", f"{total_calculated:.2f} Franc Cfa")
                
                with col3:
                    total_difference = completed_records['difference'].sum()
                    if total_difference < 0:
                        st.markdown(f'<div class="alert-red">Écart total: {total_difference:.2f} Franc Cfa</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="alert-green">Écart total: +{total_difference:.2f} Franc Cfa</div>', unsafe_allow_html=True)
                
                # Graphique évolution mensuelle
                completed_records['date'] = pd.to_datetime(completed_records['date'])
                completed_records['month'] = completed_records['date'].dt.to_period('M')
                monthly_sales = completed_records.groupby('month')[['declared_amount', 'calculated_amount']].sum()
                
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Déclaré', x=monthly_sales.index.astype(str), y=monthly_sales['declared_amount']))
                fig.add_trace(go.Bar(name='Calculé', x=monthly_sales.index.astype(str), y=monthly_sales['calculated_amount']))
                fig.update_layout(title='Comparaison mensuelle: Déclaré vs Calculé', barmode='group')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée comptable disponible.")
    
    with tabs[5]:  # Paramètres
        st.subheader("⚙️ Paramètres")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Prix des carburants")
            new_gazoil_price = st.number_input("Prix Gazoil (Franc Cfa/L)", value=st.session_state.prices['gazoil'], step=0.01)
            new_super_price = st.number_input("Prix Super (Franc Cfa/L)", value=st.session_state.prices['super'], step=0.01)
            
            if st.button("Mettre à jour les prix"):
                st.session_state.prices['gazoil'] = new_gazoil_price
                st.session_state.prices['super'] = new_super_price
                st.success("Prix mis à jour!")
        
        with col2:
            st.markdown("### Gestion des utilisateurs")
            
            # Affichage des utilisateurs
            for username, info in st.session_state.users.items():
                if info['role'] == 'worker':
                    st.markdown(f"**{info['nom']}** - {info['station']} ({info['telephone']})")
            
            # Exporter les données
            if st.button("Exporter les données (JSON)"):
                export_data = {
                    'daily_records': st.session_state.daily_records,
                    'inventory': st.session_state.inventory,
                    'prices': st.session_state.prices
                }
                st.download_button(
                    label="Télécharger",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"station_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
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