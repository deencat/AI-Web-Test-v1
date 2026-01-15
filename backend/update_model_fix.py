import sqlite3

# Connect to database
conn = sqlite3.connect('aiwebtest.db')
cursor = conn.cursor()

# Update execution_model to free Llama model
cursor.execute("""
    UPDATE user_settings 
    SET execution_model = 'meta-llama/llama-3.3-70b-instruct:free'
    WHERE user_id = 1
""")

conn.commit()

# Verify the update
result = cursor.execute("""
    SELECT generation_provider, generation_model, execution_provider, execution_model 
    FROM user_settings 
    WHERE user_id = 1
""").fetchone()

print("Current settings:")
print(f"  Generation: {result[0]} / {result[1]}")
print(f"  Execution: {result[2]} / {result[3]}")
print(f"\n✅ Updated execution_model to: {result[3]}")

conn.close()
