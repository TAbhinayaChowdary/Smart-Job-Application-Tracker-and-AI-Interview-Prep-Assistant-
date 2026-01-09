from backend.app.core.database import engine
from sqlalchemy import text

def add_columns():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE job_applications ADD COLUMN interview_date DATETIME"))
            print("Added interview_date column")
        except Exception as e:
            print(f"interview_date might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE job_applications ADD COLUMN deadline_date DATETIME"))
            print("Added deadline_date column")
        except Exception as e:
            print(f"deadline_date might already exist: {e}")

if __name__ == "__main__":
    add_columns()
