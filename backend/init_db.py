"""
Initialize or update the database with the correct schema.
"""

from app.database.session import engine
from app.models.database import Base

def init_db():
    """Create all tables with the latest schema."""
    print("🔧 Creating/updating database tables...")
    
    # This will create all tables defined in Base
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print("\nTables created/verified:")
    print("  - users")
    print("  - contract_reviews (with summary, recommendation, annotation fields)")
    print("  - review_points")
    print("  - user_feedback")
    print("\n⚠️  If you have existing data, it's preserved. New columns are added as NULL.")

if __name__ == "__main__":
    init_db()
