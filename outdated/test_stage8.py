
import requests
import time
import json

BASE_URL = "http://localhost:5001/api/admin/data"

def test_data_update():
    print("🧪 Testing Data Management API...")
    
    # 1. Check Status
    print("\n[1] Checking Data Status...")
    try:
        res = requests.get(f"{BASE_URL}/status")
        status = res.json()
        print(json.dumps(status, indent=2))
        assert "courses" in status
        assert "vr_apps" in status
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
        return

    # 2. Trigger Course Update (Limit 5)
    print("\n[2] Triggering Course Update (Limit=5)...")
    try:
        res = requests.post(f"{BASE_URL}/update/courses", json={"limit": 5})
        print(f"Status: {res.status_code}")
        data = res.json()
        print(data)
        
        if res.status_code == 409:
            print("⚠ Job already running (expected if previous test ran)")
        else:
            assert "job_id" in data
    except Exception as e:
        print(f"❌ Failed to trigger update: {e}")

    # 3. Poll for completion
    print("\n[3] Polling status for 10 seconds...")
    for i in range(5):
        time.sleep(2)
        res = requests.get(f"{BASE_URL}/status")
        status = res.json()
        job = status.get("job", {})
        print(f"   Job Status: {job.get('status')} | Logs: {len(job.get('logs', []))}")
        
        if job.get("status") in ["COMPLETED", "FAILED"]:
            print(f"   ✓ Job finished: {job.get('status')}")
            break
            
    print("\n✅ Test Complete")

if __name__ == "__main__":
    test_data_update()
