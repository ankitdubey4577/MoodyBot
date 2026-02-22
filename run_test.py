#!/usr/bin/env python3
"""Start server, run tests, report results."""
import subprocess
import sys
import time
import requests

BASE = "http://127.0.0.1:8000"
results = []

def test(name, fn):
    try:
        fn()
        results.append(("PASS", name))
        print(f"  [PASS] {name}")
    except Exception as e:
        results.append(("FAIL", name, str(e)))
        print(f"  [FAIL] {name}: {e}")

def main():
    print("Starting MoodyBot API server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=".",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for i in range(20):
            try:
                requests.get(BASE + "/", timeout=2)
                print("Server ready.")
                break
            except Exception:
                time.sleep(0.5)
        else:
            print("Server failed to start within 10s")
            return 1

        print("\nMoodyBot API Tests")
        print("-" * 40)
        test("GET /", lambda: requests.get(BASE + "/", timeout=5))
        test("GET /tasks", lambda: requests.get(BASE + "/tasks", timeout=5))
        test("POST /tasks", lambda: requests.post(BASE + "/tasks", json={"description": "Test task", "user_priority": "medium", "mode": "work"}, timeout=10))
        test("GET /schedule", lambda: requests.get(BASE + "/schedule", timeout=5))
        test("GET /gamification", lambda: requests.get(BASE + "/gamification", timeout=5))
        test("GET /dashboard", lambda: requests.get(BASE + "/dashboard", timeout=5))
        test("POST /analyze", lambda: requests.post(BASE + "/analyze", json={"input": "I feel tired and need to finish a report"}, timeout=30))
        test("POST /ai/chat", lambda: requests.post(BASE + "/ai/chat", json={"text": "Add task: review PR tomorrow", "auto_add": False, "auto_schedule": False}, timeout=90))

        passed = sum(1 for r in results if r[0] == "PASS")
        total = len(results)
        print("-" * 40)
        print(f"Result: {passed}/{total} tests passed")
        return 0 if passed == total else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    sys.exit(main())
