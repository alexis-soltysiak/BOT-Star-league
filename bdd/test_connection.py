from db_config import SessionLocal
from sqlalchemy import text  # Importer text depuis SQLAlchemy

def test_connection():
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))  # Utiliser text('SELECT 1')
        print("Connexion réussie à la base de données Supabase !")
    except Exception as e:
        print(f"Erreur de connexion : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
