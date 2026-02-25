import os
import streamlit as st
import sqlite3
import csv
from datetime import datetime
from flask import Flask, request, render_template_string, session, redirect, url_for, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cle_secrete_keyce_2026"
ADMIN_PASSWORD = "KeyceAdmin2026"

# Configuration des fichiers
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- CONNEXION BDD ---
def get_db():
    conn = sqlite3.connect('Vote_Projet_Tuto.db')
    conn.row_factory = sqlite3.Row
    # Mise à jour de la table settings pour inclure les nouveaux modes
    try:
        conn.execute("ALTER TABLE settings ADD COLUMN is_sealed INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE settings ADD COLUMN hide_results INTEGER DEFAULT 0")
    except: pass
    return conn

# --- TEMPLATE CSS ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; color: #333; }
        nav { background: #2c3e50; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        nav a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .container { max-width: 900px; margin: 30px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }
        .section { border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: left; }
        h2 { border-bottom: 2px solid #27ae60; padding-bottom: 5px; color: #2c3e50; margin-top: 0; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .btn { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: bold; transition: 0.3s; display: inline-block; text-decoration: none; text-align: center;}
        .btn-blue { background: #3498db; } .btn-green { background: #27ae60; } .btn-red { background: #e74c3c; } .btn-gold { background: #f1c40f; color: #333; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .result-bar { background: #eee; border-radius: 10px; height: 15px; width: 100%; margin: 10px 0; overflow: hidden; }
        .result-fill { background: #27ae60; height: 100%; transition: width 0.5s; }
        .candidate-card { border: 1px solid #eee; padding: 15px; border-radius: 10px; text-align: center; background: #fafafa; }
        .stats-box { background: #2c3e50; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .help-text { font-size: 0.85em; color: #666; margin-top: -5px; margin-bottom: 10px; }
        .alert-sealed { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    </style>
</head>
<body>
    <nav><a href="/">🗳️ VOTANT</a><a href="/admin">🔧 ADMIN</a></nav>
    <div class="container">{{ content | safe }}</div>
</body>
</html>
"""

def save_image(file):
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filename = f"{int(datetime.now().timestamp())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f"/static/uploads/{filename}"
    return None

@app.route('/export')
def export_csv():
    if not session.get('admin_logged_in'): return redirect(url_for('admin'))
    db = get_db()
    tokens = db.execute("SELECT token_code, voter_name, is_used FROM tokens WHERE is_used = 1").fetchall()
    
    def generate():
        data = csv.writer(csv.StringIO())
        yield 'Matricule,Nom du Votant,Statut\\n'
        for row in tokens:
            yield f"{row['token_code']},{row['voter_name']},A VOTE\\n"
    
    return Response(generate(), mimetype='text/csv', headers={"Content-disposition":"attachment; filename=emargement_keyce_2026.csv"})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    db = get_db()
    if not session.get('admin_logged_in'):
        if request.method == 'POST' and request.form.get('admin_pass') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return render_template_string(BASE_HTML, content='<h2>🔐 Accès Admin</h2><form method="post"><input type="password" name="admin_pass" placeholder="Mot de passe"><button class="btn btn-blue">Connexion</button></form>')

    if request.method == 'POST':
        if 'logout' in request.form:
            session.pop('admin_logged_in', None)
            return redirect(url_for('admin'))
        
        if 'set_competition' in request.form:
            # Gestion des checkbox pour scellement et masquage
            sealed = 1 if 'is_sealed' in request.form else 0
            hide = 1 if 'hide_results' in request.form else 0
            db.execute("DELETE FROM settings")
            db.execute("INSERT INTO settings (title, start_date, end_date, is_sealed, hide_results) VALUES (?,?,?,?,?)", 
                       (request.form['title'], request.form['start'], request.form['end'], sealed, hide))
            db.commit()
        
        if 'add_candidate' in request.form:
            photo = save_image(request.files.get('photo_file'))
            db.execute("INSERT INTO candidates (name, description, photo_url) VALUES (?,?,?)", (request.form['name'], request.form['desc'], photo))
            db.commit()

        if 'gen_matricules' in request.form:
            prefix, count = request.form['prefix'], int(request.form['count'])
            for i in range(1, count + 1):
                m_code = f"{prefix}{str(i).zfill(3)}"
                db.execute("INSERT OR IGNORE INTO tokens (token_code) VALUES (?)", (m_code,))
            db.commit()

        if 'import_list' in request.form:
            raw_data = request.form['matricule_list']
            matricules = [m.strip() for m in raw_data.replace('\\n', ',').split(',') if m.strip()]
            for m in matricules:
                db.execute("INSERT OR IGNORE INTO tokens (token_code) VALUES (?)", (m,))
            db.commit()

    config = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    candidates = db.execute("SELECT * FROM candidates ORDER BY votes DESC").fetchall()
    tokens = db.execute("SELECT * FROM tokens").fetchall()
    
    total_tokens = len(tokens)
    used_tokens = len([t for t in tokens if t['is_used'] == 1])
    remaining_tokens = total_tokens - used_tokens
    participation_rate = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0
    total_v = sum([c['votes'] for c in candidates])

    content = "<h1>Tableau de Bord Administratif</h1>"
    content += '<div style="display:flex; justify-content:center; gap:10px;"><form method="post"><button name="logout" class="btn btn-red">Déconnexion</button></form>'
    content += '<a href="/export" class="btn btn-blue">📥 Télécharger l\'Émargement (CSV)</a></div><br>'
    
    if config and config['is_sealed']:
        content += "<div class='alert-sealed'>🔒 L'URNE EST SCELLÉE. Aucun nouveau vote n'est possible.</div>"

    content += f"""<div class='stats-box'>
        <h2>📊 Participation Globale</h2>
        <div class='grid'>
            <div style='text-align:center;'><strong>{used_tokens}</strong><br><small>Votes exprimés</small></div>
            <div style='text-align:center;'><strong>{remaining_tokens}</strong><br><small>Inscrits restants</small></div>
        </div>
        <div class='result-bar' style='background: #444; margin-top:15px;'><div class='result-fill' style='width:{participation_rate}%; background: #f1c40f;'></div></div>
        <p style='text-align:center; margin-bottom:0;'>Taux de participation : {participation_rate:.1f}%</p>
    </div>"""

    content += f"""<div class='section'><h2>🏆 Paramètres et Sécurité du Scrutin</h2>
    <form method='post'>
        <input type='text' name='title' placeholder='Titre' value='{config['title'] if config else ""}' required>
        <div class='grid'>
            <div>Début: <input type='datetime-local' name='start' value='{config['start_date'] if config else ""}' required></div>
            <div>Fin: <input type='datetime-local' name='end' value='{config['end_date'] if config else ""}' required></div>
        </div>
        <div style="margin-top:10px; background:#f9f9f9; padding:10px; border-radius:5px;">
            <label><input type="checkbox" name="is_sealed" {'checked' if config and config['is_sealed'] else ""}> <b>Sceller l'urne</b> (Bloque tous les votes immédiatement)</label><br>
            <label><input type="checkbox" name="hide_results" {'checked' if config and config['hide_results'] else ""}> <b>Masquer les scores</b> (Suspense pour l'admin)</label>
        </div>
        <button name='set_competition' class='btn btn-blue' style="margin-top:10px;">Sauvegarder les paramètres</button>
    </form></div>"""

    content += """<div class='section'><h2>👤 Gestion des Candidats</h2>
    <form method='post' enctype="multipart/form-data">
        <input type='text' name='name' placeholder='Nom complet' required>
        <textarea name='desc' placeholder='Profession de foi' rows='3' required></textarea>
        <input type='file' name='photo_file' accept="image/*" required>
        <button name='add_candidate' class='btn btn-blue'>Ajouter à la liste</button>
    </form></div>"""

    content += f"""<div class='section'><h2>🎫 Liste Électorale</h2>
    <form method='post'>
        <textarea name='matricule_list' placeholder='Collez les identifiants ici...' rows='4'></textarea>
        <button name='import_list' class='btn btn-gold'>Importer la liste officielle</button>
    </form>
    <p>Électeurs inscrits : <b>{total_tokens}</b></p></div>"""

    content += "<div class='section'><h2>📊 Résultats détaillés</h2>"
    if config and config['hide_results'] and not config['is_sealed']:
        content += "<p style='text-align:center; font-style:italic; color:orange;'>Les scores sont masqués car le scrutin est en cours.</p>"
    else:
        for c in candidates:
            p = (c['votes']/total_v*100) if total_v > 0 else 0
            content += f"<strong>{c['name']}</strong> ({c['votes']} voix)<div class='result-bar'><div class='result-fill' style='width:{p}%'></div></div>"
    content += "</div>"
    
    return render_template_string(BASE_HTML, content=content)

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    config = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    if not config: return render_template_string(BASE_HTML, content="<h2>En attente de configuration...</h2>")

    now = datetime.now().isoformat()
    # Le vote est ouvert si la date est OK ET que l'urne n'est pas scellée
    is_open = (config['start_date'] <= now <= config['end_date']) and not config['is_sealed']

    if 'login' in request.form:
        if not is_open:
            return render_template_string(BASE_HTML, content="<h3 style='color:red;'>Scrutin fermé.</h3>")
        
        # Récupération des saisies du formulaire
        nom_saisi = request.form['voter_name'].strip()
        matricule_saisi = request.form['token_code'].strip()

        # VERIFICATION STRICTE : Nom + Matricule + Pas encore utilisé
        token = db.execute(
            "SELECT * FROM tokens WHERE token_code = ? AND voter_name = ? AND is_used = 0", 
            (matricule_saisi, nom_saisi)
        ).fetchone()

        if token:
            # Si le duo existe, on ouvre la session
            session['voter'], session['token'] = nom_saisi, matricule_saisi
        else:
            # Si ça ne correspond pas, on bloque l'accès
            return render_template_string(BASE_HTML, content="""
                <div style='color:red; border:2px solid red; padding:15px;'>
                    <h3>❌ Accès Refusé</h3>
                    <p>Le nom et le matricule ne correspondent pas ou vous avez déjà voté.</p>
                </div>
                <a href='/' class='btn btn-blue'>Réessayer</a>
            """)

    if 'cast_vote' in request.form and 'token' in session:
        if config['is_sealed']: return redirect(url_for('index'))
        db.execute("UPDATE candidates SET votes = votes + 1 WHERE id = ?", (request.form['candidate_id'],))
        db.execute("UPDATE tokens SET is_used = 1, voter_name = ? WHERE token_code = ?", (session['voter'], session['token']))
        db.commit()
        session.clear()
        return render_template_string(BASE_HTML, content="<h2>✅ Bulletin enregistré.</h2><p>Merci pour votre participation.</p><a href='/' class='btn btn-blue'>Sortir</a>")

    content = f"<h1>{config['title']}</h1>"
    if config['is_sealed']:
        content += "<div class='alert-sealed'>🔒 SCRUTIN TERMINÉ. L'urne a été scellée officiellement.</div>"
    elif not is_open:
        content += f"<p style='color:red;'><b>Bureau fermé.</b><br>Ouverture le : {config['start_date']}</p>"
    
    if 'token' not in session:
        if is_open:
            content += '<form method="post"><input type="text" name="voter_name" placeholder="Nom et Prénom" required><input type="text" name="token_code" placeholder="N° Matricule ou CNI" required><button class="btn btn-green" name="login">Accéder au vote</button></form>'
    else:
        cands = db.execute("SELECT * FROM candidates").fetchall()
        content += f"<h3>Électeur : {session['voter']}</h3><div class='grid'>"
        for c in cands:
            content += f'<div class="candidate-card"><img src="{c["photo_url"]}" width="100%" style="border-radius:8px; height:180px; object-fit:cover;"><p><b>{c["name"]}</b></p><small style="display:block; height:60px; overflow:hidden;">{c["description"]}</small><form method="post"><input type="hidden" name="candidate_id" value="{c["id"]}"><button name="cast_vote" class="btn btn-blue" style="width:100%">Choisir ce candidat</button></form></div>'
        content += "</div>"
    
    return render_template_string(BASE_HTML, content=content)

if __name__ == '__main__':
    app.run(debug=True)
