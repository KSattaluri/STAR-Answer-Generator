import sqlite3
import os

# Connect to the database
db_path = os.path.join("generated_answers", "processing_state.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("DATABASE STATE")
print("=" * 80)

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"\nTables in the database: {[table[0] for table in tables]}")

# Check schema of processing_state table
cursor.execute("PRAGMA table_info(processing_state);")
schema = cursor.fetchall()
print("\nSchema of processing_state table:")
for col in schema:
    print(f"  {col}")

# Check all entries
print("\nALL ENTRIES:")
cursor.execute("SELECT id, file_path, stage, status, processed_file_path, attempts, created_at, updated_at FROM processing_state")
entries = cursor.fetchall()
for entry in entries:
    print(f"ID: {entry[0]}")
    print(f"  File Path: {entry[1]}")
    print(f"  Stage: {entry[2]}")
    print(f"  Status: {entry[3]}")
    print(f"  Processed File Path: {entry[4]}")
    print(f"  Attempts: {entry[5]}")
    print(f"  Created: {entry[6]}")
    print(f"  Updated: {entry[7]}")
    print("-" * 40)

# Count by stage and status
print("\nCOUNTS BY STAGE AND STATUS:")
cursor.execute("SELECT stage, status, COUNT(*) FROM processing_state GROUP BY stage, status")
counts = cursor.fetchall()
for count in counts:
    print(f"  {count[0]} - {count[1]}: {count[2]}")

# Close connection
conn.close()
print("\nDatabase check complete")
