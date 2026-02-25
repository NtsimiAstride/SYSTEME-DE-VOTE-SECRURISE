import sqlite3

def creer_liste_electorale():
    conn = sqlite3.connect('Vote_Projet_Tuto.db')
    cursor = conn.cursor()

    # On s'assure que la table existe avec les bonnes colonnes
    cursor.execute('DROP TABLE IF EXISTS tokens')
    cursor.execute('''
        CREATE TABLE tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_code TEXT UNIQUE NOT NULL,
            voter_name TEXT NOT NULL,
            is_used INTEGER DEFAULT 0
        )
    ''')

    # Ta liste fictive de votants autorisés
    liste_votants = [
        ('MAT-2026-001', 'NTSIMI ASTRIDE'),
        ('MAT-2026-002', 'KWEMO GABRIELLE'),
        ('MAT-2026-003', 'KAM RAISSA'),
        ('MAT-2026-004', 'KOUGANG SERENA'),
        ('MAT-2026-005', 'BOUGUIA JOSIANE')
    ]

    cursor.executemany("INSERT INTO tokens (token_code, voter_name) VALUES (?, ?)", liste_votants)
    
    conn.commit()
    conn.close()
    print("✅ Liste électorale fictive générée avec succès !")

if __name__ == "__main__":
    creer_liste_electorale()
