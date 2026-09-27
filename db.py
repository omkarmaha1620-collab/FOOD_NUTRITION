"""
MySQL Database Connection and Query Execution Module
Strictly uses MySQL via PyMySQL. No SQLite.
"""

import pymysql
from pymysql.cursors import DictCursor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establish a connection directly to the MySQL database.
    Uses credentials loaded from environment variables in Config.
    """
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=True
        )
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"MySQL Connection Error on {Config.DB_HOST}:{Config.DB_PORT} ({Config.DB_NAME}): {e}")
        raise e

def execute_query(sql, params=None, fetch_one=False):
    """
    Execute a SELECT query on MySQL with safe parameterization (%s).
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def execute_insert(sql, params=None):
    """
    Execute an INSERT statement on MySQL and return the inserted row ID.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.lastrowid
    finally:
        if conn:
            conn.close()

def execute_update(sql, params=None):
    """
    Execute an UPDATE or DELETE statement on MySQL and return affected rows count.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.rowcount
    finally:
        if conn:
            conn.close()

def init_reset_table():
    """
    Ensure password_resets table exists in MySQL database without affecting other tables.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `password_resets` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `token_hash` VARCHAR(64) NOT NULL UNIQUE,
        `expires_at` DATETIME NOT NULL,
        `used` TINYINT(1) NOT NULL DEFAULT 0,
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `fk_password_reset_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """
    try:
        execute_update(create_table_sql)
    except Exception as e:
        logger.warning(f"Could not initialize password_resets table: {e}")
