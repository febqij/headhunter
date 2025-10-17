import os
from dotenv import load_dotenv

load_dotenv()

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
SCHEMA_FILE = os.path.join(SCRIPTS_DIR, 'schema.sql')

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'headhunter_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'options': f"-c search_path={os.getenv('DB_SCHEMA', 'headhunter')},public"  # Установка search_path
}

# Schema configuration
DB_SCHEMA = os.getenv('DB_SCHEMA', 'headhunter')

# HeadHunter API configuration
HH_API_CONFIG = {
    'base_url': 'https://api.hh.ru',
    'vacancies_endpoint': '/vacancies',
    'areas_endpoint': '/areas',
    'professional_roles_endpoint': '/professional_roles',
    'timeout': 10,
    'per_page': 100,
    'max_pages': 20,
    'delay_between_requests': 0.25
}

# Parser configuration
PARSER_CONFIG = {
    'area': os.getenv('HH_AREA', '113').split(','),
    'text': os.getenv('HH_SEARCH_TEXT', ''),
    'search_field': os.getenv('HH_SEARCH_FIELD', 'name'),
    'experience': os.getenv('HH_EXPERIENCE', ''),
    'employment': os.getenv('HH_EMPLOYMENT', ''),
    'schedule': os.getenv('HH_SCHEDULE', '')
}

# Logging configuration
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'parser.log'
}
