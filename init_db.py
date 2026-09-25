"""
MySQL Database Initialization and Seeder Script
Strictly MySQL only. Fails loudly if tables are not created.
Usage: python init_db.py
"""

import os
import re
import sys
import pymysql
from config import Config

REQUIRED_TABLES = {'users', 'admins', 'food_items', 'meal_entries'}

def parse_sql_file(file_path):
    """
    Parses a SQL script file into individual executable statements.
    Accurately removes block comments (/* ... */) and line comments (-- ...)
    so that statements following comments are never skipped.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SQL file not found at: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove multi-line comments
    cleaned = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    statements = []
    current_statement = []

    for line in cleaned.splitlines():
        trimmed = line.strip()
        # Skip pure comment lines
        if trimmed.startswith('--'):
            continue

        # Strip trailing inline comments: e.g. "..., CURDATE()), -- comment"
        line_no_comment = re.sub(r'--.*$', '', line).strip()
        if line_no_comment:
            current_statement.append(line_no_comment)

        if line_no_comment.endswith(';'):
            stmt = ' '.join(current_statement).strip()
            if stmt.endswith(';'):
                stmt = stmt[:-1].strip()
            if stmt:
                statements.append(stmt)
            current_statement = []

    if current_statement:
        stmt = ' '.join(current_statement).strip()
        if stmt.endswith(';'):
            stmt = stmt[:-1].strip()
        if stmt:
            statements.append(stmt)

    return statements

def init_database():
    print("=" * 65)
    print(" FOOD NUTRITION ANALYZER - MYSQL DATABASE INITIALIZATION ")
    print("=" * 65)
    print(f"Target Database: '{Config.DB_NAME}'")
    print(f"Connecting to MySQL server at {Config.DB_HOST}:{Config.DB_PORT} as '{Config.DB_USER}'...")

    try:
        # Step 1: Connect to MySQL server
        server_conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4',
            autocommit=True
        )
        print("[SUCCESS] Connected to MySQL Server!")

        with server_conn.cursor() as cursor:
            print(f"Ensuring database '{Config.DB_NAME}' exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"[SUCCESS] Database '{Config.DB_NAME}' verified!")
        server_conn.close()

        # Step 2: Connect directly to food_nutrition_db
        db_conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            autocommit=True
        )

        sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
        statements = parse_sql_file(sql_file_path)
        print(f"Parsed {len(statements)} executable SQL statements from {os.path.basename(sql_file_path)}.")

        executed_count = 0
        with db_conn.cursor() as cursor:
            for i, stmt in enumerate(statements, 1):
                # Skip standalone CREATE DATABASE / USE statements as we are already connected to the database
                upper_stmt = stmt.upper()
                if upper_stmt.startswith('CREATE DATABASE') or upper_stmt.startswith('USE '):
                    continue

                try:
                    cursor.execute(stmt)
                    executed_count += 1
                except Exception as e:
                    print(f"\n[FATAL ERROR] Failed executing statement #{i}:")
                    print(f"SQL Snippet: {stmt[:120]}...")
                    print(f"Error details: {e}")
                    db_conn.close()
                    raise RuntimeError(f"Database initialization aborted due to SQL error: {e}") from e

        # Step 3: Strictly verify all required tables exist
        print("\nVerifying database schema...")
        with db_conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables_result = cursor.fetchall()
            created_tables = {t[0] for t in tables_result}

            print(f"Discovered tables in '{Config.DB_NAME}': {sorted(list(created_tables))}")

            missing_tables = REQUIRED_TABLES - created_tables
            if missing_tables:
                db_conn.close()
                error_msg = f"[CRITICAL FAILURE] Missing required tables: {missing_tables}. Database initialization failed!"
                print(error_msg, file=sys.stderr)
                raise RuntimeError(error_msg)

            # Step 4: Verify record counts
            cursor.execute("SELECT COUNT(*) FROM food_items;")
            food_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM admins;")
            admin_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM meal_entries;")
            meal_count = cursor.fetchone()[0]

            if food_count < 40:
                db_conn.close()
                raise RuntimeError(f"[CRITICAL FAILURE] Expected at least 40 food items, found only {food_count}!")

            if admin_count < 1:
                db_conn.close()
                raise RuntimeError("[CRITICAL FAILURE] Default admin account was not inserted!")

            if user_count < 1:
                db_conn.close()
                raise RuntimeError("[CRITICAL FAILURE] Demo user account was not inserted!")

        db_conn.close()

        print("-" * 65)
        print("VERIFICATION PASSED: All tables and seed data created successfully!")
        print(f"  - Users table:        {user_count} record(s)")
        print(f"  - Admins table:       {admin_count} record(s)")
        print(f"  - Food Items table:   {food_count} record(s) across 9 categories")
        print(f"  - Meal Entries table: {meal_count} record(s)")
        print("-" * 65)
        print("Default Demo Accounts:")
        print("  - Admin: admin@nutrition.com / Admin@123")
        print("  - User:  john@example.com   / User@123")
        print("=" * 65)
        return True

    except pymysql.MySQLError as e:
        print("\n" + "!" * 65, file=sys.stderr)
        print(f"[FATAL MySQL ERROR]: {e}", file=sys.stderr)
        print("!" * 65, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR]: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    init_database()
