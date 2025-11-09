import psycopg2


def execute_query(query):
    """
    Execute a SQL query and return results as list of dictionaries.

    Args:
        query (str): SQL query to execute

    Returns:
        list[dict]: Query results, where each row is a dict with column names as keys.
                    Returns None if an error occurs.
    """
    # Database credentials
    HOST = "localhost"
    PORT = 8002
    DATABASE = "postgres"
    USER = "postgres"
    PASSWORD = "postgres"

    connection = None
    cursor = None

    try:
        # Connect to database
        connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD
        )

        # Create cursor
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch column names from cursor description
        column_names = [desc[0] for desc in cursor.description]

        # Fetch all rows and convert them into list of dicts
        rows = cursor.fetchall()
        results = [dict(zip(column_names, row)) for row in rows]

        return results

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        # Always close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# Example usage (for testing only)
if __name__ == "__main__":
    query = "SELECT table_schema, table_name FROM information_schema.tables LIMIT 5;"
    results = execute_query(query)

    if results:
        print(f"Query executed successfully. Found {len(results)} rows.")
        for row in results:
            print(row)
    else:
        print("No results or error occurred.")
