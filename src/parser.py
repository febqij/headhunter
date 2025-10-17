import requests
import time
import logging
from typing import List, Dict, Optional, Generator
from datetime import datetime
from config import HH_API_CONFIG, PARSER_CONFIG

logger = logging.getLogger(__name__)

class HHParser:
    def __init__(self):
        self.base_url = HH_API_CONFIG['base_url']
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH Parser/1.0 (your_email@example.com)'
        })
        self.parsed_at = datetime.now()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Выполняет GET-запрос с обработкой ошибок"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=HH_API_CONFIG['timeout']
            )
            response.raise_for_status()
            
            # Соблюдение rate limit
            time.sleep(HH_API_CONFIG['delay_between_requests'])
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning("Rate limit превышен, ожидание 60 секунд...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP ошибка {response.status_code}: {e}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка подключения: {e}")
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут запроса к {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {e}")
            return None
    
    def fetch_areas(self) -> List[Dict]:
        """Получает список всех регионов"""
        logger.info("Загрузка списка регионов...")
        data = self._make_request(HH_API_CONFIG['areas_endpoint'])
        
        if not data:
            return []
        
        areas = []
        
        def parse_areas(areas_list, parent_id=None):
            for area in areas_list:
                areas.append({
                    'id': int(area['id']),
                    'name': area['name'],
                    'parent_id': parent_id,
                    'url': f"{self.base_url}/areas/{area['id']}"
                })
                
                if 'areas' in area and area['areas']:
                    parse_areas(area['areas'], int(area['id']))
        
        parse_areas(data)
        logger.info(f"Загружено {len(areas)} регионов")
        return areas
    
    def fetch_professional_roles(self) -> tuple[List[Dict], List[Dict]]:
        """Получает профессиональные роли и категории"""
        logger.info("Загрузка профессиональных ролей...")
        data = self._make_request(HH_API_CONFIG['professional_roles_endpoint'])
        
        if not data or 'categories' not in data:
            return [], []
        
        categories = []
        roles = []
        
        for category in data['categories']:
            categories.append({
                'id': int(category['id']),
                'name': category['name']
            })
            
            for role in category.get('roles', []):
                roles.append({
                    'id': int(role['id']),
                    'name': role['name'],
                    'category_id': int(category['id']),
                    'accept_incomplete_resumes': role.get('accept_incomplete_resumes', False)
                })
        
        logger.info(f"Загружено {len(categories)} категорий и {len(roles)} ролей")
        return categories, roles
    
    def fetch_vacancies(self, page: int = 0) -> Optional[Dict]:
        """Получает страницу вакансий"""
        params = {
            'page': page,
            'per_page': HH_API_CONFIG['per_page'],
            'area': PARSER_CONFIG['area']
        }
        
        # Добавление опциональных параметров
        if PARSER_CONFIG['text']:
            params['text'] = PARSER_CONFIG['text']
            params['search_field'] = PARSER_CONFIG['search_field']
        
        if PARSER_CONFIG['experience']:
            params['experience'] = PARSER_CONFIG['experience']
        
        if PARSER_CONFIG['employment']:
            params['employment'] = PARSER_CONFIG['employment']
        
        if PARSER_CONFIG['schedule']:
            params['schedule'] = PARSER_CONFIG['schedule']
        
        logger.info(f"Загрузка страницы {page}...")
        return self._make_request(HH_API_CONFIG['vacancies_endpoint'], params)
    
    def parse_all_vacancies(self) -> Generator[Dict, None, None]:
        """Парсит все вакансии постранично"""
        page = 0
        total_found = None
        total_parsed = 0
        
        while page < HH_API_CONFIG['max_pages']:
            data = self.fetch_vacancies(page)
            
            if not data or 'items' not in data:
                logger.warning(f"Нет данных на странице {page}")
                break
            
            if total_found is None:
                total_found = data.get('found', 0)
                logger.info(f"Всего найдено вакансий: {total_found}")
            
            items = data['items']
            if not items:
                logger.info("Больше нет вакансий")
                break
            
            for vacancy in items:
                yield self.normalize_vacancy(vacancy)
                total_parsed += 1
            
            logger.info(f"Обработано {total_parsed} из {min(total_found, 2000)} вакансий")
            page += 1
        
        logger.info(f"Парсинг завершен. Всего обработано: {total_parsed} вакансий")
    
    def normalize_vacancy(self, vacancy: Dict) -> Dict:
        """Нормализует данные вакансии для вставки в БД"""
        
        def join_list(items, key='name'):
            """Объединяет список словарей в строку через запятую"""
            if not items:
                return None
            return ', '.join([item.get(key, '') for item in items if item.get(key)])
        
        # Обработка работодателя
        employer = vacancy.get('employer', {})
        employer_data = {
            'id': int(employer['id']) if employer.get('id') else None,
            'name': employer.get('name'),
            'url': employer.get('url'),
            'alternate_url': employer.get('alternate_url'),
            'logo_original': employer.get('logo_urls', {}).get('original'),
            'logo_90': employer.get('logo_urls', {}).get('90'),
            'logo_240': employer.get('logo_urls', {}).get('240'),
            'vacancies_url': employer.get('vacancies_url'),
            'country_id': employer.get('country_id'),
            'accredited_it_employer': employer.get('accredited_it_employer', False),
            'trusted': employer.get('trusted', False)
        }
        
        # Обработка зарплаты
        salary = vacancy.get('salary') or vacancy.get('salary_range', {})
        
        # Обработка адреса
        address = vacancy.get('address', {})
        
        # Обработка snippet
        snippet = vacancy.get('snippet', {})
        
        # Профессиональные роли
        professional_roles = [
            int(role['id']) for role in vacancy.get('professional_roles', [])
            if role.get('id')
        ]
        
        # Формирование данных вакансии
        vacancy_data = {
            'id': int(vacancy['id']),
            'published_at': vacancy['published_at'],
            'created_at': vacancy['created_at'],
            'parsed_at': self.parsed_at,
            'name': vacancy['name'],
            'premium': vacancy.get('premium', False),
            'has_test': vacancy.get('has_test', False),
            'response_letter_required': vacancy.get('response_letter_required', False),
            'archived': vacancy.get('archived', False),
            'area_id': int(vacancy['area']['id']) if vacancy.get('area') else None,
            'employer_id': employer_data['id'],
            'salary_from': salary.get('from'),
            'salary_to': salary.get('to'),
            'salary_currency': salary.get('currency'),
            'salary_gross': salary.get('gross'),
            'vacancy_type': vacancy.get('type', {}).get('id'),
            'vacancy_type_name': vacancy.get('type', {}).get('name'),
            'schedule_id': vacancy.get('schedule', {}).get('id'),
            'schedule_name': vacancy.get('schedule', {}).get('name'),
            'experience_id': vacancy.get('experience', {}).get('id'),
            'experience_name': vacancy.get('experience', {}).get('name'),
            'employment_id': vacancy.get('employment', {}).get('id'),
            'employment_name': vacancy.get('employment', {}).get('name'),
            'employment_form_id': vacancy.get('employment_form', {}).get('id'),
            'employment_form_name': vacancy.get('employment_form', {}).get('name'),
            'address_city': address.get('city'),
            'address_street': address.get('street'),
            'address_building': address.get('building'),
            'address_lat': address.get('lat'),
            'address_lng': address.get('lng'),
            'address_raw': address.get('raw'),
            'address_id': address.get('id'),
            'url': vacancy.get('url'),
            'alternate_url': vacancy.get('alternate_url'),
            'apply_alternate_url': vacancy.get('apply_alternate_url'),
            'response_url': vacancy.get('response_url'),
            'snippet_requirement': snippet.get('requirement'),
            'snippet_responsibility': snippet.get('responsibility'),
            'accept_temporary': vacancy.get('accept_temporary', False),
            'accept_incomplete_resumes': vacancy.get('accept_incomplete_resumes', False),
            'show_logo_in_search': vacancy.get('show_logo_in_search'),
            'show_contacts': vacancy.get('show_contacts', False),
            'is_adv_vacancy': vacancy.get('is_adv_vacancy', False),
            'internship': vacancy.get('internship', False),
            'night_shifts': vacancy.get('night_shifts', False),
            'working_days': join_list(vacancy.get('working_days', [])),
            'working_time_intervals': join_list(vacancy.get('working_time_intervals', [])),
            'working_time_modes': join_list(vacancy.get('working_time_modes', [])),
            'working_hours': join_list(vacancy.get('working_hours', [])),
            'work_schedule_by_days': join_list(vacancy.get('work_schedule_by_days', [])),
            'fly_in_fly_out_duration': join_list(vacancy.get('fly_in_fly_out_duration', [])),
            'work_format': join_list(vacancy.get('work_format', []))
        }
        
        return {
            'vacancy': vacancy_data,
            'employer': employer_data,
            'professional_roles': professional_roles
        }
