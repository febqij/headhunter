import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# HeadHunter API configuration
HH_API_CONFIG = {
    'base_url': 'https://api.hh.ru',
    'vacancies_endpoint': '/vacancies',
    'areas_endpoint': '/salary_statistics/dictionaries/salary_areas',
    'professional_roles_endpoint': '/professional_roles',
    'timeout': 10,
    'per_page': 100,  # Максимум 100
    'max_pages': 20,  # API ограничение: 2000 вакансий
    'delay_between_requests': 0.25  # Секунды между запросами
}

# Parser configuration
PARSER_CONFIG = {
    'area': os.getenv('HH_AREA', '113'),  # 113 = Россия
    'text': os.getenv('HH_SEARCH_TEXT', ''),  # Поисковый запрос
    'search_field': os.getenv('HH_SEARCH_FIELD', 'name'),  # name, description, company_name
    'experience': os.getenv('HH_EXPERIENCE', ''),  # noExperience, between1And3, between3And6, moreThan6
    'employment': os.getenv('HH_EMPLOYMENT', ''),  # full, part, project, volunteer, probation
    'schedule': os.getenv('HH_SCHEDULE', '')  # fullDay, shift, flexible, remote, flyInFlyOut
}

# Logging configuration
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'parser.log'
}
