import mysql.connector
from mysql.connector import Error
import os

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ledimo2003%',
            database='quiz'
        )
        if connection.is_connected():
            print("[INFO] Connected to MySQL database!")
            return connection
    except Error as e:
        print(f"[ERROR] Error connecting to MySQL: {e}")
        return None

def create_database(cursor):
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS quiz")
        print("[INFO] Database 'quiz' created successfully!")
    except Error as e:
        print(f"[ERROR] Error creating database: {e}")

def execute_schema(cursor):
    try:
        with open('schema.sql', 'r', encoding='utf-8') as file:
            schema = file.read()
            statements = schema.split(';')
            
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            print("[INFO] Database schema created successfully!")
    except Error as e:
        print(f"[ERROR] Error executing schema: {e}")

def main():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        create_database(cursor)
        
        # Reconnect with the database
        connection.close()
        connection = create_connection()
        cursor = connection.cursor()
        
        # Execute the schema
        execute_schema(cursor)
        
        # Commit changes and close connection
        connection.commit()
        cursor.close()
        connection.close()
        print("[INFO] Database initialization completed!")

if __name__ == '__main__':
    main()
