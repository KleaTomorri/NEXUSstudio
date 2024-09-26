from flask_app.config.mysqlconnection import connectToMySQL
from datetime import datetime

class Report:
    DB = "interviews"  

    def __init__(self, data):
        self.id = data['id']
        self.user_id = data['user_id']
        self.report_content = data['report_content']
        self.file_path = data['file_path']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

    @classmethod
    def save(cls, data):
        query = """
        INSERT INTO reports (user_id, report_content, file_path, created_at, updated_at)
        VALUES (%(user_id)s, %(report_content)s, %(file_path)s, NOW(), NOW());
        """
        return connectToMySQL(cls.DB).query_db(query, data)

    @classmethod
    def get_report_by_id(cls, data):
        query = "SELECT * FROM reports WHERE id = %(id)s;"
        result = connectToMySQL(cls.DB).query_db(query, data)
        if result:
            return cls(result[0])
        return None

    @classmethod
    def get_all_reports_by_user(cls, data):
        query = "SELECT * FROM reports WHERE user_id = %(user_id)s;"
        results = connectToMySQL(cls.DB).query_db(query, data)
        reports = []
        for row in results:
            reports.append(cls(row))
        return reports

    @classmethod
    def delete_report(cls, data):
        query = "DELETE FROM reports WHERE id = %(id)s;"
        return connectToMySQL(cls.DB).query_db(query, data)
