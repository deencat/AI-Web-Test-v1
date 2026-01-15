import sqlite3

conn = sqlite3.connect('aiwebtest.db')
cursor = conn.cursor()

# Update to a working free model
cursor.execute('UPDATE user_settings SET generation_model=? WHERE user_id=1', ('meta-llama/llama-3.3-70b-instruct:free',))
conn.commit()

# Verify
cursor.execute('SELECT generation_provider, generation_model FROM user_settings WHERE user_id=1')
result = cursor.fetchone()
print(f'✅ Updated settings:')
print(f'   Provider: {result[0]}')
print(f'   Model: {result[1]}')

conn.close()
