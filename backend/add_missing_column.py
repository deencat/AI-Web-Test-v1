import sqlite3

conn = sqlite3.connect('aiwebtest.db')
cursor = conn.cursor()

try:
    # Add missing column from Sprint 5
    cursor.execute('ALTER TABLE user_settings ADD COLUMN stagehand_provider VARCHAR(20) DEFAULT "python"')
    conn.commit()
    print('✅ Successfully added stagehand_provider column')
except Exception as e:
    if 'duplicate column name' in str(e).lower():
        print('ℹ️  Column already exists, no change needed')
    else:
        print(f'❌ Error: {e}')

# Verify the column was added
cursor.execute('PRAGMA table_info(user_settings)')
cols = cursor.fetchall()
print('\nCurrent user_settings columns:')
for col in cols:
    print(f'  - {col[1]} ({col[2]})')

conn.close()
