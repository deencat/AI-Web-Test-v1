import requests

r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin123'})
token = r.json()['access_token']

r2 = requests.get('http://localhost:8000/api/v1/executions/33', headers={'Authorization': f'Bearer {token}'})
data = r2.json()

print(f"Execution ID: 33")
print(f"Status: {data.get('status')}")
print(f"Result: {data.get('result')}")
print(f"Started: {data.get('started_at')}")
print(f"Completed: {data.get('completed_at')}")
print(f"Duration: {data.get('duration_seconds')}s")
print(f"Passed Steps: {data.get('passed_steps')}")
print(f"Failed Steps: {data.get('failed_steps')}")
print(f"Total Steps: {data.get('passed_steps', 0) + data.get('failed_steps', 0)}")

if data.get('status') == 'completed':
    print("\n✅ DATABASE UPDATES ARE WORKING!")
else:
    print(f"\n⚠️ Status is still: {data.get('status')}")

