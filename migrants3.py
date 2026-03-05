import sqlite3

# Connect to databases
old_db = sqlite3.connect('/Users/parsahome/Desktop/archive_program/archive.db')
new_db = sqlite3.connect('/Users/parsahome/Desktop/archbase_data/archbase.db')
old_cur = old_db.cursor()
new_cur = new_db.cursor()

# 1. Migrate Collections to Bundles
col_mapping = {}  # Maps old collection_id to new bundle_id

old_cur.execute("SELECT id, inserted_ts, description FROM collections")
for old_id, inserted_ts, desc in old_cur.fetchall():
    name = f"AP_C_{old_id}"
    new_cur.execute(
        "INSERT INTO bundles (name, parent_id, description, inserted_ts) VALUES (?, NULL, ?, ?)",
        (name, desc, inserted_ts)
    )
    col_mapping[old_id] = new_cur.lastrowid

# 2. Migrate Files, File-Bundle mappings, and File-Tag mappings
old_cur.execute("""
    SELECT id, inserted_ts, sha256_hash, extension, created_ts, collection_id, description 
    FROM files
""")

for old_file_id, inserted_ts, sha256, ext, created_ts, col_id, desc in old_cur.fetchall():
    name = f"AP_F_{old_file_id}"
    
    # Insert File
    new_cur.execute("""
        INSERT INTO files (name, extension, sha256_hash, size, created_ts, description, inserted_ts, created_ts_percision)
        VALUES (?, ?, ?, -1, ?, ?, ?, 5)
    """, (name, ext, sha256, created_ts, desc, inserted_ts))
    
    new_file_id = new_cur.lastrowid
    
    # Tag the migrated file with Tag ID 1
    new_cur.execute("""
        INSERT INTO file_tags (file_id, tag_id, inserted_ts)
        VALUES (?, 1, ?)
    """, (new_file_id, inserted_ts))
    
    # Insert File-Bundle Join Table entry (if not an orphan)
    if col_id is not None and col_id in col_mapping:
        new_cur.execute("""
            INSERT INTO file_bundles (file_id, bundle_id, inserted_ts)
            VALUES (?, ?, ?)
        """, (new_file_id, col_mapping[col_id], inserted_ts))

# Commit and close
new_db.commit()
old_db.close()
new_db.close()

print("Migration completed successfully with tags applied.")