
import requests
import time
import json

BASE_URL = "http://localhost:5001/api/admin/data"

def test_filtered_update():
    print("🧪 Testing Filtered Course Update...")
    
    # Trigger Course Update with Filters
    print("\n[1] Triggering Update (CS Dept, Fall 2025, Limit 3)...")
    params = {
        "limit": 3,
        "department": "School of Computer Science",
        "semester": "f25"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/update/courses", json=params)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(data)
        
        if res.status_code == 409:
            print("⚠ Job already running")
            return
            
    except Exception as e:
        print(f"❌ Failed to trigger update: {e}")
        return

    # Poll for logs to confirm filters were applied
    print("\n[2] Polling for confirmation logs...")
    for i in range(10):
        time.sleep(2)
        res = requests.get(f"{BASE_URL}/status")
        status = res.json()
        job = status.get("job", {})
        logs = job.get("logs", [])
        
        # Print new logs
        if logs:
            print(f"   Last log: {logs[-1]}")
            
        # Check for confirmation in logs
        log_text = " ".join(logs)
        if "Filter: Department = 'School of Computer Science'" in log_text:
            print("   ✅ Confirmed Department Filter")
        if "Filter: Semester = 'f25'" in log_text:
            print("   ✅ Confirmed Semester Filter")
            
        if job.get("status") in ["COMPLETED", "FAILED"]:
            print(f"   ✓ Job finished: {job.get('status')}")
            break
            
    print("\nTest Complete")

if __name__ == "__main__":
    test_filtered_update()
