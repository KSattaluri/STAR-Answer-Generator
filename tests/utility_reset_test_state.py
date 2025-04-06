"""
Reset Test State Script

This script cleans up generated files and resets the state database
to allow for fresh test runs.
"""

import os
import shutil
import sqlite3
from pathlib import Path

def main():
    print("\n" + "=" * 80)
    print("RESETTING TEST STATE")
    print("=" * 80 + "\n")
    
    # Define directories to clean
    base_dir = "generated_answers"
    subprompts_dir = os.path.join(base_dir, "sub_prompts")
    
    # Clean up generated sub-prompts
    if os.path.exists(subprompts_dir):
        print(f"Cleaning directory: {subprompts_dir}")
        for file_path in Path(subprompts_dir).glob('*.json'):
            if file_path.is_file():
                os.remove(file_path)
                print(f"  Removed file: {file_path}")
    
    # Reset state database
    db_path = os.path.join(base_dir, "processing_state.db")
    test_db_path = os.path.join(base_dir, "test_processing_state.db")
    
    for path in [db_path, test_db_path]:
        if os.path.exists(path):
            print(f"Resetting state database: {path}")
            try:
                # Connect to the database
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                # Delete all rows from each table
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"DELETE FROM {table_name};")
                    print(f"  Deleted all rows from table: {table_name}")
                
                # Commit changes
                conn.commit()
                conn.close()
                print(f"  Database reset successfully: {path}")
                
            except Exception as e:
                print(f"  Error resetting database {path}: {e}")
    
    print("\nCleanup completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
