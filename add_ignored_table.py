from backend.app.core.database import engine
from sqlalchemy import text

def add_ignored_table():
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ignored_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created ignored_emails table")
            # Index
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_ignored_emails_message_id ON ignored_emails (message_id)"))
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    add_ignored_table()
