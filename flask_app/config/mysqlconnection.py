import pymysql.cursors
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MySQLConnection:
    def __init__(self, db):
        self.connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=db,
            charset=os.getenv('DB_CHARSET', 'utf8mb4'),  # default to utf8mb4
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

    def query_db(self, query: str, data: dict = None):
        with self.connection.cursor() as cursor:
            try:
                query = cursor.mogrify(query, data)
                print("Running Query:", query)

                cursor.execute(query)
                if query.lower().startswith("insert"):
                    self.connection.commit()
                    return cursor.lastrowid
                elif query.lower().startswith("select"):
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
            except Exception as e:
                print("Something went wrong", e)
                self.connection.rollback()
                return False

    def close(self):
        self.connection.close()

def connectToMySQL(db):
    return MySQLConnection(db)
