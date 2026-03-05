import sqlite3
import os

# Paths
storage_dir = '/Users/parsahome/Desktop/archive_program/archive_storage'
db_path = '/Users/parsahome/Desktop/archive_program/archive.db'

# Connect to the old database
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Fetch file ID, extension, and SHA256 hash
cur.execute("SELECT id, extension, sha256_hash FROM files")

for old_id, ext, sha256 in cur.fetchall():
    # Clean the extension just in case it was saved with a leading dot
    clean_ext = ext.lstrip('.') 
    
    old_filename = f"{old_id}.{clean_ext}"
    new_filename = sha256
    
    old_path = os.path.join(storage_dir, old_filename)
    new_path = os.path.join(storage_dir, new_filename)
    
    # Rename the file physically
    os.rename(old_path, new_path)

conn.close()

print("Files renamed successfully to their SHA256 hashes.")