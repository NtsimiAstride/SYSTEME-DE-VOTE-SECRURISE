import sqlite3

def init_db():
    conn = sqlite3.connect('Vote_Projet_Tuto.db')
    cursor = conn.cursor()

    # Table des Paramètres avec TOUTES les colonnes nécessaires
    cursor.execute('DROP TABLE IF EXISTS settings') # On recrée proprement
    cursor.execute('''
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            title TEXT,
            start_date TEXT,
            end_date TEXT,
            is_sealed INTEGER DEFAULT 0,
            hide_results INTEGER DEFAULT 0
        )
    ''')

    # Table des Candidats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            photo_url TEXT,
            votes INTEGER DEFAULT 0
        )
    ''')

    # Table des Tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_code TEXT UNIQUE NOT NULL,
            voter_name TEXT DEFAULT NULL,
            is_used INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec les bonnes colonnes.")

if __name__ == "__main__":
    init_db()
