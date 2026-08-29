import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


load_dotenv()


class DatabaseUtil:

    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = None

    def connect(self):
        """Create a new database connection."""
        try:
            self.connection = psycopg2.connect(self.database_url)
            return self.connection

        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None

    def schema_details(self, schema_name):
        """Get tables, columns, data types and sample data."""

        connection = self.connect()

        if connection is None:
            return "Failed to connect to database."

        cursor = None

        try:
            cursor = connection.cursor()

            schema_info_context = f"Database Schema: {schema_name}\n"

            # Get tables
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE';
                """,
                (schema_name,)
            )

            tables_list = cursor.fetchall()

            for table in tables_list:

                table_name = table[0]

                schema_info_context += (
                    f"\nTable: {table_name}\n"
                )

                # Get columns
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (schema_name, table_name)
                )

                columns_list = cursor.fetchall()

                for column_name, data_type in columns_list:

                    schema_info_context += (
                        f"  Column: {column_name}, "
                        f"Data Type: {data_type}\n"
                    )
                # Get sample data
                query = sql.SQL(
                    "SELECT * FROM {}.{} LIMIT 5"
                ).format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )

                cursor.execute(query)

                sample_data = cursor.fetchall()

                schema_info_context += "  Sample Data:\n"

                for row in sample_data:
                    schema_info_context += f"    {row}\n"

            return schema_info_context

        except Exception as e:

            return f"Error fetching schema details: {e}"

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    def execute_sql(self, query):
        """Execute SQL query and return the result."""

        connection = self.connect()

        if connection is None:
            return "Failed to connect to database."

        cursor = None

        try:

            cursor = connection.cursor()

            cursor.execute(query)

            # SELECT queries have results
            if cursor.description:
                result = cursor.fetchall()
            else:
                result = "Query executed successfully."

            connection.commit()

            return str(result)

        except Exception as e:

            connection.rollback()

            return f"Error executing query: {e}"

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


if __name__ == "__main__":

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not set in .env")

    db = DatabaseUtil(database_url)

    result = db.schema_details("public")

    print(result)

    # with open("test_schema_details.txt", "w", encoding="utf-8") as f:
    #     f.write(result)