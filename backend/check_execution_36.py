import requests

r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin123'})
token = r.json()['access_token']

for exec_id in [35, 36]:
    r2 = requests.get(f'http://localhost:8000/api/v1/executions/{exec_id}', headers={'Authorization': f'Bearer {token}'})
    data = r2.json()
    
    print(f"\n=== Execution {exec_id} ===")
    print(f"Status: {data.get('status')}")
    print(f"Result: {data.get('result')}")
    print(f"Started: {data.get('started_at')}")
    print(f"Completed: {data.get('completed_at')}")
    print(f"Duration: {data.get('duration_seconds')}s")
    print(f"Passed: {data.get('passed_steps')}, Failed: {data.get('failed_steps')}")
    
    if data.get('status') == 'completed':
        print("✅ COMPLETE!")

