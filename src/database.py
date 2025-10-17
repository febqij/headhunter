"""
Предварительно необходимо подготовить таблицы для хранения данных вакансий.
Базовая структура должна включать:
- vacancies (id, name, salary_from, salary_to, area_id, area_name, employer_id, employer_name, published_at, created_at, url, archived)
- employers (id, name, area_id)
- reas (id, name, parent_id)
"""
import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

class Database:
    """
    Класс для работы с БД через psycopg2
    """
    def __init__(self):
        self.connection = None
    
    def connect(self):
        self.connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
