import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('instance/biblionest.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(Books)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'image_path' not in columns:
            print("Adding image_path column to Books table...")
            cursor.execute("ALTER TABLE Books ADD COLUMN image_path TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column image_path already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate()
