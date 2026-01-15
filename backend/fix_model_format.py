import sqlite3
import sys

# Connect to database
conn = sqlite3.connect('aiwebtest.db')
cursor = conn.cursor()

# Check current value
current = cursor.execute("""
    SELECT generation_model, execution_model 
    FROM user_settings 
    WHERE user_id = 1
""").fetchone()

print(f"BEFORE: generation_model = {current[0]}, execution_model = {current[1]}")

# Update both models to correct OpenRouter format
cursor.execute("""
    UPDATE user_settings 
    SET generation_model = 'openai/gpt-4o',
        execution_model = 'meta-llama/llama-3.3-70b-instruct:free'
    WHERE user_id = 1
""")

# Commit changes
conn.commit()

# Verify update
after = cursor.execute("""
    SELECT generation_model, execution_model 
    FROM user_settings 
    WHERE user_id = 1
""").fetchone()

print(f"AFTER:  generation_model = {after[0]}, execution_model = {after[1]}")

if after[0] == 'openai/gpt-4o':
    print("\n✅ SUCCESS: Models updated correctly!")
else:
    print(f"\n❌ ERROR: Update failed! Still shows: {after[0]}")
    sys.exit(1)

conn.close()
