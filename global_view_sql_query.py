import psycopg2

def execute_query(query):
    """
    Execute a SQL query and return results.
    
    Args:
        query (str): SQL query to execute
    
    Returns:
        list: Query results as list of tuples, or None if error
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
        
        # Execute query
        cursor.execute(query)
        
        # Fetch results
        results = cursor.fetchall()
        
        return results
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
        
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Example usage
if __name__ == "__main__":
    # Test the function
    query = "SELECT * FROM information_schema.tables LIMIT 5;"
    results = execute_query(query)
    
    if results:
        print(f"Query executed successfully. Found {len(results)} rows.")
        for i, row in enumerate(results, 1):
            print(f"Row {i}: {row}")
    else:
        print("No results or error occurred")