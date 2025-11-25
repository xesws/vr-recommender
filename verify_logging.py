import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_logging():
    print("🧪 Testing Interaction Logging...")
    
    # 1. Simulate User 1 (New User)
    print("\n[User 1] Sending 'Hello'...")
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/chat", json={"message": "Hello"})
    print(f"   Status: {resp.status_code}")
    
    user_id_1 = resp.cookies.get('user_id')
    print(f"   Assigned User ID: {user_id_1}")
    assert user_id_1 is not None
    
    # 2. Simulate User 1 (Follow-up)
    print("\n[User 1] Sending 'Help'...")
    resp = session.post(f"{BASE_URL}/chat", json={"message": "Help"})
    print(f"   Status: {resp.status_code}")
    
    user_id_check = resp.cookies.get('user_id')
    assert user_id_check == user_id_1
    print("   ✓ User ID persisted via cookie")

    # 3. Simulate User 2 (Different User)
    print("\n[User 2] Sending 'Python'...")
    session2 = requests.Session()
    resp = session2.post(f"{BASE_URL}/chat", json={"message": "I want to learn Python"})
    print(f"   Status: {resp.status_code}")
    
    user_id_2 = resp.cookies.get('user_id')
    print(f"   Assigned User ID: {user_id_2}")
    assert user_id_2 != user_id_1
    print("   ✓ Different User ID assigned")

    # 4. Check Admin Stats
    time.sleep(1) # Allow DB write
    print("\n🔍 Checking Admin Stats...")
    resp = requests.get(f"{BASE_URL}/api/admin/stats")
    stats = resp.json()
    print(f"   Stats: {json.dumps(stats, indent=2)}")
    
    assert stats['total_interactions'] >= 3
    assert stats['unique_users'] >= 2
    print("   ✓ Stats look correct")

    # 5. Check Admin Logs
    print("\n🔍 Checking Admin Logs...")
    resp = requests.get(f"{BASE_URL}/api/admin/logs?limit=5")
    logs = resp.json()['logs']
    print(f"   Retrieved {len(logs)} logs")
    print(f"   Latest Log: {logs[0]['query_text']} -> {logs[0]['intent']}")

if __name__ == "__main__":
    test_logging()
