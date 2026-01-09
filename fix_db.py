import sqlite3

try:
    conn = sqlite3.connect('sjtap.db')
    cursor = conn.cursor()
    # Check if column exists
    cursor.execute("PRAGMA table_info(job_applications)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'location' not in columns:
        print("Adding location column...")
        cursor.execute("ALTER TABLE job_applications ADD COLUMN location VARCHAR")
        conn.commit()
    else:
        print("Location column already exists.")
        
    conn.close()
    print("Database schema fixed.")
except Exception as e:
    print(f"Error: {e}")
