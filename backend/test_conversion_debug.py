import requests

# Login
login = requests.post('http://127.0.0.1:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin123'})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get user
me = requests.get('http://127.0.0.1:8000/api/v1/auth/me', headers=headers)
user_id = me.json()['id']
print(f'User ID: {user_id}')

# Generate scenario
gen = requests.post('http://127.0.0.1:8000/api/v1/scenarios/generate', headers=headers, json={
    'template_id': 1,
    'context_variables': {
        'method': 'GET',
        'endpoint': '/api/test',
        'headers': {},
        'request_body': None,
        'expected_status': 200,
        'schema': {'type': 'array'},
        'validation_rule': 'length > 0'
    },
    'use_faker_data': True
})
print(f'Generate status: {gen.status_code}')
scenario_id = gen.json()['id']
print(f'Scenario ID: {scenario_id}')

# Validate
val = requests.post(f'http://127.0.0.1:8000/api/v1/scenarios/{scenario_id}/validate', headers=headers)
print(f'Validate status: {val.status_code}')
print(f'Valid: {val.json().get("is_valid")}')

# Convert
conv = requests.post(f'http://127.0.0.1:8000/api/v1/scenarios/{scenario_id}/convert-to-test', headers=headers)
print(f'Convert status: {conv.status_code}')
print(f'Response: {conv.text}')
