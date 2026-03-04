import sqlite3

DB_PATH = "/Users/parsahome/Desktop/archbase_data/archbase.db"

def fix_filenames():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # SQLite uses || for string concatenation
    cur.execute("UPDATE files SET name = name || '.' || extension WHERE id >= 11")
    
    print(f"Successfully updated {cur.rowcount} files.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_filenames()