import os
import shutil

# --- THIS SCRIPT CLEANS UP THE PROJECT ---

# 1. Find and delete all __pycache__ directories
project_root = os.path.dirname(os.path.abspath(__file__))
for root, dirs, files in os.walk(project_root):
    if "__pycache__" in dirs:
        pycache_path = os.path.join(root, "__pycache__")
        print(f"Deleting cache directory: {pycache_path}")
        shutil.rmtree(pycache_path)

# 2. Delete the old database file
db_path = os.path.join(project_root, "models", "database.db")
if os.path.exists(db_path):
    print(f"Deleting database file: {db_path}")
    os.remove(db_path)
else:
    print("Database file not found, which is good.")

print("\nCleanup complete! Your project is now clean.")
print("You can now safely restart the application.")