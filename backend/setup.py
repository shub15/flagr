#!/usr/bin/env python
"""
Setup script for Legal Advisor backend.
Initializes database, verifies configuration, and checks dependencies.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Ensure Python 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print("✅ Python version OK")

def check_env_file():
    """Check if .env exists"""
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        print("📝 Creating .env from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env created - PLEASE EDIT WITH YOUR API KEYS")
        else:
            print("❌ .env.example not found")
        return False
    print("✅ .env file exists")
    return True

def check_directories():
    """Create required directories"""
    dirs = [
        "data/legal_docs",
        "data/reference_playbooks",
        "data/vectordb"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Data directories created")

def initialize_database():
    """Initialize database tables"""
    try:
        from app.database.session import init_db
        print("🔄 Initializing database...")
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    return True

def verify_config():
    """Verify configuration"""
    try:
        from app.config import settings
        print("\n📋 Configuration Check:")
        
        # Check API keys
        keys_to_check = {
            "OpenAI": settings.openai_api_key,
            "Google Gemini": settings.google_api_key,
            "Pinecone": settings.pinecone_api_key
        }
        
        for name, key in keys_to_check.items():
            if key and not key.startswith("your_"):
                print(f"  ✅ {name} API key configured")
            else:
                print(f"  ⚠️  {name} API key missing")
        
        # if settings.grok_api_key and not settings.grok_api_key.startswith("your_"):
        #     print(f"  ✅ Grok API key configured")
        # else:
        #     print(f"  ℹ️  Grok API key not set (optional)")
        
        print(f"\n  Database: {settings.database_url.split('://')[0]}")
        print(f"  Pinecone Index: {settings.pinecone_index_name}")
        
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        print("Please ensure .env is properly configured")
        return False
    
    return True

def main():
    """Main setup routine"""
    print("🚀 Legal Advisor Backend Setup\n")
    
    check_python_version()
    env_exists = check_env_file()
    check_directories()
    
    if not env_exists:
        print("\n⚠️  Please edit .env with your API keys before continuing")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    if not verify_config():
        print("\n⚠️  Configuration incomplete")
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\n📚 Next Steps:")
    print("  1. Ensure all API keys are set in .env")
    print("  2. Upload Indian Labour Law PDFs:")
    print("     - Use POST /api/legal-docs/upload")
    print("  3. Start the server:")
    print("     uvicorn app.main:app --reload")
    print("  4. Open API docs:")
    print("     http://localhost:8000/docs")
    print("\n🎯 Ready to review contracts!\n")

if __name__ == "__main__":
    main()
