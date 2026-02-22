#!/usr/bin/env python3
"""Quick API test script for MoodyBot."""
import requests
import sys

BASE = "http://127.0.0.1:8000"
results = []

def test(name, fn):
    try:
        fn()
        results.append((name, "PASS"))
        print(f"  [PASS] {name}")
        return True
    except Exception as e:
        results.append((name, f"FAIL: {e}"))
        print(f"  [FAIL] {name}: {e}")
        return False

def main():
    print("MoodyBot API Tests")
    print("-" * 40)
    
    # Health / root
    test("GET / (docs available)", lambda: requests.get(f"{BASE}/", timeout=5))
    
    # Tasks
    test("GET /tasks", lambda: requests.get(f"{BASE}/tasks", timeout=5))
    
    # Create task
    def create_task():
        r = requests.post(f"{BASE}/tasks", json={
            "description": "Test task from automation",
            "user_priority": "medium",
            "mode": "work"
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    
    test("POST /tasks", create_task)
    
    # Schedule
    test("GET /schedule", lambda: requests.get(f"{BASE}/schedule", timeout=5))
    
    # Gamification
    test("GET /gamification", lambda: requests.get(f"{BASE}/gamification", timeout=5))
    
    # Dashboard
    test("GET /dashboard", lambda: requests.get(f"{BASE}/dashboard", timeout=5))
    
    # Analyze (LangGraph)
    def analyze():
        r = requests.post(f"{BASE}/analyze", json={"input": "I feel tired and need to finish a report"}, timeout=30)
        r.raise_for_status()
        return r.json()
    
    test("POST /analyze", analyze)
    
    # AI Chat (main endpoint)
    def ai_chat():
        r = requests.post(f"{BASE}/ai/chat", json={
            "text": "Add task: review PR tomorrow",
            "auto_add": False,
            "auto_schedule": False
        }, timeout=60)
        r.raise_for_status()
        return r.json()
    
    test("POST /ai/chat", ai_chat)
    
    print("-" * 40)
    passed = sum(1 for _, s in results if s == "PASS")
    total = len(results)
    print(f"Result: {passed}/{total} tests passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
