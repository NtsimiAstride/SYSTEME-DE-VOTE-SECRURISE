import sqlite3

conn = sqlite3.connect('Vote_Projet_Tuto.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print(f"{'ID':<4} | {'MATRICULE':<15} | {'NOM DU VOTANT':<20} | {'STATUT'}")
print("-" * 55)

utilisateurs = cursor.execute("SELECT * FROM tokens").fetchall()

for user in utilisateurs:
    statut = "✅ Déjà voté" if user['is_used'] == 1 else "⏳ En attente"
    print(f"{user['id']:<4} | {user['token_code']:<15} | {user['voter_name']:<20} | {statut}")

conn.close()
