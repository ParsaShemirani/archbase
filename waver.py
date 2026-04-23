import sqlite3
from datetime import datetime, timedelta, timezone

# Configuration
DB_FILE = '/Users/parsahome/Desktop/archbase_data/archbase.db'
TARGET_TAG_ID = 2
TARGET_EXTENSION = 'wav'

def tag_recent_wav_files():
    # Calculate timestamps in UTC to match the DB format
    now_utc = datetime.now(timezone.utc)
    one_hour_ago_utc = now_utc - timedelta(hours=1)
    
    # Format timestamps to match 'YYYY-MM-DDTHH:MM:SS+0000'
    now_str = now_utc.strftime('%Y-%m-%dT%H:%M:%S+0000')
    one_hour_ago_str = one_hour_ago_utc.strftime('%Y-%m-%dT%H:%M:%S+0000')

    # Connect to the database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Find .wav files inserted in the last hour
        cursor.execute('''
            SELECT id 
            FROM files 
            WHERE (extension = ? OR extension = ?)
              AND inserted_ts >= ?
        ''', (TARGET_EXTENSION, TARGET_EXTENSION.upper(), one_hour_ago_str))
        
        wav_files = cursor.fetchall()
        
        if not wav_files:
            print("No .wav files added in the last hour.")
            return

        added_count = 0
        
        # Link each found file to the tag
        for (file_id,) in wav_files:
            # Check if this file is already associated with tag 2
            cursor.execute('''
                SELECT 1 
                FROM file_tags 
                WHERE file_id = ? AND tag_id = ?
            ''', (file_id, TARGET_TAG_ID))
            
            # If no association exists, create one
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO file_tags (file_id, tag_id, inserted_ts)
                    VALUES (?, ?, ?)
                ''', (file_id, TARGET_TAG_ID, now_str))
                added_count += 1
                
        # Commit the transaction
        conn.commit()
        print(f"Successfully tagged {added_count} .wav file(s) with Tag ID {TARGET_TAG_ID} (Journal).")
        
    except sqlite3.Error as e:
        print(f"An SQLite error occurred: {e}")
        conn.rollback() # Roll back any partial changes on error
    finally:
        # Always close the connection
        conn.close()

if __name__ == '__main__':
    tag_recent_wav_files()