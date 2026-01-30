"""
Helper script to create initial migration
Run: python scripts/create_migration.py
"""
import subprocess
import sys

if __name__ == "__main__":
    try:
        # Create initial migration
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
            check=True
        )
        print("Migration created successfully!")
        print("Run 'alembic upgrade head' to apply the migration")
    except subprocess.CalledProcessError as e:
        print(f"Error creating migration: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: alembic not found. Make sure you're in the backend directory and have installed dependencies.")
        sys.exit(1)

