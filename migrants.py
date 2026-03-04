import sqlite3

OLD_DB_PATH = "/Users/parsahome/Desktop/filebase/filebase.db"
NEW_DB_PATH = "/Users/parsahome/Desktop/archbase_data/archbase.db"

def migrate():
    # Connect to both databases
    old_conn = sqlite3.connect(OLD_DB_PATH)
    new_conn = sqlite3.connect(NEW_DB_PATH)
    
    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    # Dictionaries to map old IDs to new auto-generated IDs
    col_map = {}
    file_map = {}
    label_map = {}

    print("Migrating Labels -> Tags...")
    old_labels = old_cur.execute("SELECT id, name, description, inserted_ts FROM labels").fetchall()
    for old_id, name, desc, ins_ts in old_labels:
        new_cur.execute("INSERT INTO tags (name, description, inserted_ts) VALUES (?, ?, ?)", (name, desc, ins_ts))
        label_map[old_id] = new_cur.lastrowid

    print("Migrating Collections -> Bundles...")
    # Step 1: Insert all bundles and map their IDs (ignoring parent_id for a moment)
    old_cols = old_cur.execute("SELECT id, name, parent_id, description, inserted_ts FROM collections").fetchall()
    col_parents = {} # Track old parent relationships
    
    for old_id, name, parent_id, desc, ins_ts in old_cols:
        new_cur.execute("INSERT INTO bundles (name, description, inserted_ts) VALUES (?, ?, ?)", (name, desc, ins_ts))
        col_map[old_id] = new_cur.lastrowid
        col_parents[old_id] = parent_id

    # Step 2: Update parent_ids using the new mapped IDs
    for old_id, old_parent in col_parents.items():
        if old_parent is not None and old_parent in col_map:
            new_parent_id = col_map[old_parent]
            new_bundle_id = col_map[old_id]
            new_cur.execute("UPDATE bundles SET parent_id = ? WHERE id = ?", (new_parent_id, new_bundle_id))

    print("Migrating Files and creating File_Bundles...")
    old_files = old_cur.execute("SELECT id, name, sha256_hash, extension, size, created_ts, inserted_ts, collection_id, description FROM files").fetchall()
    
    for old_id, name, sha256, ext, size, cr_ts, ins_ts, col_id, desc in old_files:
        # Precision hardcoded to 5. Will throw IntegrityError on duplicate hash.
        new_cur.execute("""
            INSERT INTO files (name, extension, sha256_hash, size, created_ts, description, inserted_ts, created_ts_percision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, ext, sha256, size, cr_ts, desc, ins_ts, 5))
        
        new_file_id = new_cur.lastrowid
        file_map[old_id] = new_file_id
        
        # Link the file to its bundle if it was in a collection
        if col_id is not None and col_id in col_map:
            new_bundle_id = col_map[col_id]
            new_cur.execute("INSERT INTO file_bundles (file_id, bundle_id, inserted_ts) VALUES (?, ?, ?)", 
                            (new_file_id, new_bundle_id, ins_ts))

    print("Migrating File_Labels -> File_Tags...")
    old_file_labels = old_cur.execute("SELECT file_id, label_id, inserted_ts FROM file_labels").fetchall()
    for f_id, l_id, ins_ts in old_file_labels:
        if f_id in file_map and l_id in label_map:
            new_cur.execute("INSERT INTO file_tags (file_id, tag_id, inserted_ts) VALUES (?, ?, ?)",
                            (file_map[f_id], label_map[l_id], ins_ts))

    # Save changes and close
    new_conn.commit()
    print("Migration complete!")

    old_conn.close()
    new_conn.close()

if __name__ == "__main__":
    migrate()