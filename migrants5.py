import sqlite3

# Connect to the new database
db = sqlite3.connect('/Users/parsahome/Desktop/archbase_data/archbase.db')
cur = db.cursor()

# Fetch only the migrated files
cur.execute("SELECT id, name, extension FROM files WHERE name LIKE 'AP_F_%'")

for file_id, name, ext in cur.fetchall():
    # Strip any leading dot from the extension just in case
    clean_ext = ext.lstrip('.')
    
    # Check to prevent appending if it somehow already has the extension
    if not name.endswith(f".{clean_ext}"):
        new_name = f"{name}.{clean_ext}"
        
        # Update the name in the database
        cur.execute("UPDATE files SET name = ? WHERE id = ?", (new_name, file_id))

# Commit and close
db.commit()
db.close()

print("File names successfully updated with extensions.")