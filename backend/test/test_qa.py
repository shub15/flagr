"""
Test script for Contract Q&A endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token after login

# Sample review ID (use one from your database)
REVIEW_ID = "rev_be2841098e6b"  # Replace with actual review ID

# Test questions
test_questions = [
    "What is the notice period?",
    "Can I work remotely?",
    "Is the vendor liable for delays?",
    "What is the stipend amount?",
    "What are the working hours?",
    "Can I terminate the contract early?",
]

def test_qa_endpoint():
    """Test the Q&A endpoint with various questions."""
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("=" * 80)
    print("CONTRACT Q&A ENDPOINT TEST")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Question {i}: {question}")
        print("-" * 80)
        
        # Make request
        response = requests.post(
            f"{BASE_URL}/api/reviews/{REVIEW_ID}/ask",
            headers=headers,
            json={"question": question}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Answerable: {data['answerable']}")
            print(f"📊 Confidence: {data['confidence']:.2f}")
            print(f"\n💡 Answer:\n{data['answer']}\n")
            
            if data['supporting_quotes']:
                print("📑 Supporting Quotes:")
                for idx, quote in enumerate(data['supporting_quotes'], 1):
                    print(f"  {idx}. \"{quote['text']}\"")
                    print(f"     Confidence: {quote['confidence']:.2f}")
            else:
                print("📑 No supporting quotes (likely not answerable)")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
        
        print()
    
    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    print("\n⚠️  SETUP REQUIRED:")
    print("1. Make sure backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("2. Login to get JWT token")
    print("3. Update REVIEW_ID with an actual review from your database")
    print("4. Update TOKEN with your JWT token")
    print("\nPress Enter to continue...")
    input()
    
    test_qa_endpoint()
