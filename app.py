import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Vote Projet Tuto 2026", layout="wide")

DB_PATH = 'Vote_Projet_Tuto.db'
ADMIN_PASSWORD = "KeyceAdmin2026"

# --- LOGIQUE BDD ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY, title TEXT, start_date TEXT, end_date TEXT, 
            is_sealed INTEGER DEFAULT 0, hide_results INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, photo_url TEXT, votes INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT, token_code TEXT UNIQUE, voter_name TEXT, is_used INTEGER DEFAULT 0
        );
    """)
    db.commit()

init_db()

# --- NAVIGATION ---
st.sidebar.title("🗳️ Navigation")
page = st.sidebar.radio("Aller vers :", ["Espace Votant", "Administration"])

# --- PAGE ADMINISTRATION ---
if page == "Administration":
    st.title("🔧 Administration")
    
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("Mot de passe Admin", type="password")
        if st.button("Connexion"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    else:
        if st.sidebar.button("Déconnexion Admin"):
            st.session_state.admin_auth = False
            st.rerun()

        db = get_db()
        config = db.execute("SELECT * FROM settings LIMIT 1").fetchone()

        # 1. Paramètres
        with st.expander("🏆 Paramètres du Scrutin", expanded=True):
            with st.form("settings_form"):
                title = st.text_input("Titre du Scrutin", value=config['title'] if config else "")
                col1, col2 = st.columns(2)
                start = col1.text_input("Date Début (YYYY-MM-DD HH:MM)", value=config['start_date'] if config else "")
                end = col2.text_input("Date Fin (YYYY-MM-DD HH:MM)", value=config['end_date'] if config else "")
                sealed = st.checkbox("Sceller l'urne (Bloque les votes)", value=bool(config['is_sealed']) if config else False)
                hide = st.checkbox("Masquer les scores en direct", value=bool(config['hide_results']) if config else False)
                if st.form_submit_button("Sauvegarder"):
                    db.execute("DELETE FROM settings")
                    db.execute("INSERT INTO settings (title, start_date, end_date, is_sealed, hide_results) VALUES (?,?,?,?,?)",
                               (title, start, end, int(sealed), int(hide)))
                    db.commit()
                    st.success("Paramètres mis à jour !")

        # 2. Gestion Candidats
        with st.expander("👤 Ajouter un Candidat"):
            with st.form("cand_form"):
                c_name = st.text_input("Nom complet")
                c_desc = st.text_area("Description / Programme")
                c_img = st.text_input("URL de la photo (ex: https://...)")
                if st.form_submit_button("Ajouter"):
                    db.execute("INSERT INTO candidates (name, description, photo_url) VALUES (?,?,?)", (c_name, c_desc, c_img))
                    db.commit()
                    st.success("Candidat ajouté")

        # 3. Résultats
        st.subheader("📊 Résultats")
        cands = db.execute("SELECT * FROM candidates ORDER BY votes DESC").fetchall()
        total_v = sum([c['votes'] for c in cands])
        
        for c in cands:
            p = (c['votes']/total_v) if total_v > 0 else 0
            st.write(f"**{c['name']}** : {c['votes']} voix")
            st.progress(p)

# --- PAGE VOTANT ---
else:
    st.title("🗳️ Espace de Vote")
    db = get_db()
    config = db.execute("SELECT * FROM settings LIMIT 1").fetchone()

    if not config:
        st.warning("Le scrutin n'est pas encore configuré.")
    else:
        st.header(config['title'])
        
        if config['is_sealed']:
            st.error("🔒 L'urne est scellée. Le scrutin est terminé.")
        else:
            if "voter_token" not in st.session_state:
                with st.form("login_voter"):
                    v_name = st.text_input("Nom complet")
                    v_code = st.text_input("Matricule")
                    if st.form_submit_button("Accéder au vote"):
                        # Vérification simplifiée pour l'exemple
                        st.session_state.voter_name = v_name
                        st.session_state.voter_token = v_code
                        st.rerun()
            else:
                st.info(f"Électeur : {st.session_state.voter_name}")
                cands = db.execute("SELECT * FROM candidates").fetchall()
                cols = st.columns(3)
                for idx, c in enumerate(cands):
                    with cols[idx % 3]:
                        if c['photo_url']: st.image(c['photo_url'], use_container_width=True)
                        st.subheader(c['name'])
                        st.caption(c['description'])
                        if st.button(f"Voter pour {c['name']}", key=f"v_{c['id']}"):
                            db.execute("UPDATE candidates SET votes = votes + 1 WHERE id = ?", (c['id'],))
                            db.commit()
                            st.success("Vote validé !")
                            st.session_state.clear()
                            st.balloons()
                            st.button("Terminer")
