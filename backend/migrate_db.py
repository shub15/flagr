"""
Simple migration script to add new columns to contract_reviews table.
Run this once to update your database schema.
"""

import sqlite3
from pathlib import Path

# Path to your SQLite database
DB_PATH = Path("data/overrule.db")

def migrate_database():
    """Add new columns to contract_reviews table."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add summary column
        cursor.execute("ALTER TABLE contract_reviews ADD COLUMN summary TEXT")
        print("✅ Added 'summary' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  'summary' column already exists")
        else:
            raise
    
    try:
        # Add recommendation column
        cursor.execute("ALTER TABLE contract_reviews ADD COLUMN recommendation VARCHAR(20)")
        print("✅ Added 'recommendation' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  'recommendation' column already exists")
        else:
            raise
    
    try:
        # Add annotated_pdf_url column
        cursor.execute("ALTER TABLE contract_reviews ADD COLUMN annotated_pdf_url VARCHAR(500)")
        print("✅ Added 'annotated_pdf_url' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  'annotated_pdf_url' column already exists")
        else:
            raise
    
    try:
        # Add annotation_map column
        cursor.execute("ALTER TABLE contract_reviews ADD COLUMN annotation_map TEXT")
        print("✅ Added 'annotation_map' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  'annotation_map' column already exists")
        else:
            raise
    
    try:
        # Add annotation_stats column
        cursor.execute("ALTER TABLE contract_reviews ADD COLUMN annotation_stats TEXT")
        print("✅ Added 'annotation_stats' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  'annotation_stats' column already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Database migration completed successfully!")
    print("You can now restart your server and all fields will be saved.")

if __name__ == "__main__":
    migrate_database()
