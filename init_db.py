from core.storage import initialiser_stockage, get_connection

print("🔧 Création de la base de données...")
initialiser_stockage()

# On vérifie que les tables ont bien été créées
conn = get_connection()
cursor = conn.cursor()

# Cette requête liste toutes les tables existantes dans la base.
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

conn.close()

print("✅ Base de données créée avec succès !")
print("📋 Tables créées :")
for table in tables:
    print(f"   - {table['name']}")