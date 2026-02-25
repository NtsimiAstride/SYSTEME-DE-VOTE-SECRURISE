import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from flask import Flask, request, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "cle_secrete_votant_keyce_2026"

# --- CONNEXION BDD ---
def get_db():
    conn = sqlite3.connect('Vote_Projet_Tuto.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fonction pour hacher le matricule (Sécurité Pilier 1)
def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

# --- MODÈLE CSS ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; color: #333; }
        header { background: #2c3e50; padding: 25px; text-align: center; color: white; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        .container { max-width: 800px; margin: 30px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }
        .candidate-card { border: 1px solid #eee; padding: 15px; border-radius: 12px; background: #fff; transition: 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .candidate-card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-top: 25px; }
        .candidate-img { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; }
        .btn { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: bold; width: 100%; transition: 0.3s; text-decoration: none; display: inline-block; font-size: 16px; }
        .btn-green { background: #27ae60; }
        .btn-blue { background: #3498db; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        .receipt-box { border: 2px dashed #27ae60; background: #ebf9f1; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .status-msg { padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; }
        .closed { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <header><h1>🗳️ Portail de Vote Officiel</h1></header>
    <div class="container">{{ content | safe }}</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    config = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    
    if not config:
        return render_template_string(BASE_HTML, content="<h2>Le scrutin n'est pas encore configuré.</h2>")

    # Vérification des conditions d'ouverture
    now = datetime.now().isoformat()
    is_time_ok = config['start_date'] <= now <= config['end_date']
    is_sealed = config.get('is_sealed', 0) == 1
    is_open = is_time_ok and not is_sealed

    # --- LOGIQUE DE CONNEXION ---
    if 'login' in request.form:
        if not is_open:
            msg = "Urne scellée officiellement." if is_sealed else "Le bureau est fermé."
            return render_template_string(BASE_HTML, content=f"<div class='status-msg closed'>{msg}</div><a href='/' class='btn btn-blue'>Retour</a>")
        
        token_input = request.form['token_code'].strip()
        voter_name = request.form['voter_name'].strip()
        
        # Vérification si le matricule existe et n'est pas utilisé
        token = db.execute("SELECT * FROM tokens WHERE token_code = ? AND is_used = 0", (token_input,)).fetchone()
        if token:
            session['voter'] = voter_name
            session['token_raw'] = token_input # Stocké temporairement pour le processus de vote
        else:
            return render_template_string(BASE_HTML, content="<div class='status-msg closed'>❌ Identifiant invalide ou déjà utilisé.</div><a href='/' class='btn btn-blue'>Réessayer</a>")

    # --- LOGIQUE DE VOTE SÉCURISÉ ---
    if 'cast_vote' in request.form and 'token_raw' in session:
        if is_sealed:
            session.clear()
            return redirect(url_for('index'))

        # Pilier 1 & 2 : Hachage et Empreinte numérique
        t_hash = hash_token(session['token_raw'])
        fingerprint = request.user_agent.string + request.remote_addr
        
        # Pilier 4 : Reçu de vote unique
        receipt = secrets.token_hex(4).upper()

        # Pilier 3 : Anonymisation (Séparation des tables)
        # On enregistre l'émargement
        db.execute("INSERT INTO signatures (token_hash, voter_name, timestamp, device_fingerprint) VALUES (?, ?, ?, ?)",
                   (t_hash, session['voter'], datetime.now().isoformat(), fingerprint))
        
        # On enregistre le bulletin dans l'urne anonyme
        db.execute("INSERT INTO ballots (candidate_id, confirmation_code) VALUES (?, ?)",
                   (request.form['candidate_id'], receipt))
        
        # On marque le matricule comme consommé
        db.execute("UPDATE tokens SET is_used = 1 WHERE token_code = ?", (session['token_raw'],))
        db.commit()
        
        v_name = session['voter']
        session.clear()
        
        return render_template_string(BASE_HTML, content=f"""
            <div class="receipt-box">
                <h2>✅ Vote confirmé, {v_name} !</h2>
                <p>Ton reçu de vote anonyme est : <br><b style="font-size: 24px; color: #27ae60;">{receipt}</b></p>
                <p style="font-size: 0.9em;">Ce code est ta preuve numérique. Il permet de vérifier que ton bulletin est dans l'urne sans jamais révéler pour qui tu as voté.</p>
            </div>
            <a href='/' class='btn btn-blue'>Quitter le portail</a>
        """)

    # --- AFFICHAGE ---
    content = f"<h1>{config['title']}</h1>"
    
    if is_sealed:
        content += "<div class='status-msg closed'>🔒 SCRUTIN TERMINÉ<br><small>L'urne a été scellée par l'administration.</small></div>"
    elif not is_time_ok:
        content += f"<div class='status-msg closed'>⏳ BUREAU FERMÉ<br><small>Ouverture prévue : {config['start_date']}</small></div>"
    
    if 'token_raw' not in session:
        if is_open:
            content += """
            <p>Connectez-vous pour accéder à votre bulletin de vote unique.</p>
            <form method="post">
                <input type="text" name="voter_name" placeholder="Nom et Prénom" required>
                <input type="text" name="token_code" placeholder="Votre Matricule Officiel" required>
                <button class="btn btn-green" name="login">Accéder aux candidats</button>
            </form>"""
    else:
        cands = db.execute("SELECT * FROM candidates").fetchall()
        content += f"<p>Bienvenue <b>{session['voter']}</b>, faites votre choix :</p><div class='grid'>"
        for c in cands:
            content += f'''
            <div class="candidate-card">
                <img src="{c['photo_url']}" class="candidate-img">
                <h4>{c['name']}</h4>
                <p style="font-size:0.85em; color:#666; height:45px; overflow:hidden;">{c['description']}</p>
                <form method="post">
                    <input type="hidden" name="candidate_id" value="{c['id']}">
                    <button name="cast_vote" class="btn btn-blue">Voter pour elle</button>
                </form>
            </div>'''
        content += "</div>"
    
    return render_template_string(BASE_HTML, content=content)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
