import requests
import json
import os

# --- PASTE YOUR CREDENTIALS HERE ---
API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
# -----------------------------------

def get_boards_and_lists():
    auth = {'key': API_KEY, 'token': TOKEN}
    
    # 1. Get all Boards
    print("Fetching Boards...")
    url = "https://api.trello.com/1/members/me/boards"
    response = requests.get(url, params=auth)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return

    boards = response.json()
    
    if not boards:
        print("No boards found. Check your permissions.")
        return

    for board in boards:
        print(f"\nBOARD: {board['name']} (ID: {board['id']})")
        
        # 2. Get Lists for this Board
        lists_url = f"https://api.trello.com/1/boards/{board['id']}/lists"
        lists_resp = requests.get(lists_url, params=auth)
        
        if lists_resp.status_code == 200:
            lists = lists_resp.json()
            for lst in lists:
                print(f"  └─ LIST: {lst['name']} -> ID: {lst['id']}")  # <--- COPY THIS ID
        else:
            print("  (Could not fetch lists for this board)")

if __name__ == "__main__":
    get_boards_and_lists()