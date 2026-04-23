import sqlite3

DB_PATH = "/Users/parsahome/Desktop/archbase_data/archbase.db"
OUTPUT_FILE = "preview.txt"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open(OUTPUT_FILE, "w") as f:
    # get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]

    for table in tables:
        f.write(f"\n=== TABLE: {table} ===\n")
        
        cur.execute(f"SELECT * FROM {table} LIMIT 5;")
        rows = cur.fetchall()

        for row in rows:
            f.write(str(row) + "\n")

conn.close()

print("Done. Output written to preview.txt")