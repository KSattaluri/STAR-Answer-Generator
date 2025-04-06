import sqlite3
import os

# Connect to the database
db_path = os.path.join("generated_answers", "processing_state.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("DATABASE STATE")
print("=" * 80)

# Check sub_prompt stage entries
print("\nSUB-PROMPT STAGE ENTRIES:")
cursor.execute("SELECT file_path, status, processed_file_path FROM processing_state WHERE stage = 'sub_prompt'")
results = cursor.fetchall()
for row in results:
    print(f"File: {row[0]}")
    print(f"  Status: {row[1]}")
    print(f"  Processed Path: {row[2]}")
    print("-" * 40)

# Check star_answer stage entries
print("\nSTAR ANSWER STAGE ENTRIES:")
cursor.execute("SELECT file_path, status, processed_file_path FROM processing_state WHERE stage = 'star_answer'")
results = cursor.fetchall()
for row in results:
    print(f"File: {row[0]}")
    print(f"  Status: {row[1]}")
    print(f"  Processed Path: {row[2]}")
    print("-" * 40)

# Count entries by stage and status
print("\nSUMMARY COUNTS:")
cursor.execute("""
    SELECT stage, status, COUNT(*) 
    FROM processing_state 
    GROUP BY stage, status
    ORDER BY stage, status
""")
results = cursor.fetchall()
for row in results:
    print(f"Stage: {row[0]}, Status: {row[1]}, Count: {row[2]}")

# Check if there are any files with star_answer stage and complete status
print("\nCOMPLETED STAR ANSWERS:")
cursor.execute("""
    SELECT file_path 
    FROM processing_state 
    WHERE stage = 'star_answer' AND status = 'complete'
""")
results = cursor.fetchall()
for row in results:
    print(f"Completed: {row[0]}")

# Close the database connection
conn.close()
