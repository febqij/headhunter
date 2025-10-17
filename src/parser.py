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
            'User-Agent': 'HH Parser/1.0 (febqij@gmail.com)',
            'HH-User-Agent': 'HHParser/1.0 (febqij@gmail.com)'
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
            elif response.status_code == 400:
                logger.error(f"HTTP 400 Bad Request: {response.text}")
                logger.error(f"Request URL: {response.url}")
                logger.error(f"Request params: {params}\n")
                return None
            else:
                logger.error(f"\nHTTP ошибка {response.status_code}: {e}\n")
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
        """Получает список всех регионов с дополнительными данными"""
        logger.info("Загрузка списка регионов...")
        data = self._make_request('/areas')
        
        if not data:
            logger.error("Не удалось загрузить регионы")
            return []
        
        areas = []
        
        def parse_areas(areas_list):
            """Рекурсивная функция для обработки вложенных регионов"""
            for area in areas_list:
                areas.append({
                    'id': int(area['id']),
                    'name': area['name'],
                    'parent_id': int(area['parent_id']) if area.get('parent_id') else None,
                    'url': f"{self.base_url}/areas/{area['id']}",
                    'utc_offset': area.get('utc_offset'),  # Новое поле
                    'lat': area.get('lat'),                # Новое поле
                    'lng': area.get('lng')                 # Новое поле
                })
                
                if 'areas' in area and area['areas']:
                    parse_areas(area['areas'])
        
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
            'per_page': HH_API_CONFIG['per_page']
        }
        
        # Обработка множественных регионов
        areas = PARSER_CONFIG['area']
        if isinstance(areas, list):
            # Для множественных регионов используем каждый отдельно
            for area in areas:
                area = area.strip()
                if area:
                    # HH API принимает несколько area параметров
                    if 'area' not in params:
                        params['area'] = []
                    params['area'].append(area)
        else:
            params['area'] = areas

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
        
        logger.info(f"Загрузка страницы {page} с параметрами: {params}")
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
        
        def process_salary(salary_data):
            """
            Обрабатывает зарплату с логикой:
            - Если один из показателей null, используем другой
            - Если оба null, возвращаем None
            """
            if not salary_data:
                return None, None, None, None
            
            salary_from = salary_data.get('from')
            salary_to = salary_data.get('to')
            
            # Если один из показателей null, копируем другой
            if salary_from is None and salary_to is not None:
                salary_from = salary_to
            elif salary_to is None and salary_from is not None:
                salary_to = salary_from
            # Если оба None, оставляем None
            
            return (
                salary_from,
                salary_to,
                salary_data.get('currency'),
                salary_data.get('gross')
            )
        
        # Обработка работодателя
        employer = vacancy.get('employer', {}) or {}  # На случай если employer = null
        employer_data = {
            'id': int(employer['id']) if employer.get('id') else None,
            'name': employer.get('name'),
            'url': employer.get('url'),
            'alternate_url': employer.get('alternate_url'),
            'logo_original': employer.get('logo_urls', {}).get('original') if employer.get('logo_urls') else None,
            'logo_90': employer.get('logo_urls', {}).get('90') if employer.get('logo_urls') else None,
            'logo_240': employer.get('logo_urls', {}).get('240') if employer.get('logo_urls') else None,
            'vacancies_url': employer.get('vacancies_url'),
            'country_id': employer.get('country_id'),
            'accredited_it_employer': employer.get('accredited_it_employer', False),
            'trusted': employer.get('trusted', False)
        }
        
        # Обработка зарплаты (приоритет salary_range, затем salary)
        salary_data = vacancy.get('salary_range') or vacancy.get('salary')
        salary_from, salary_to, salary_currency, salary_gross = process_salary(salary_data)
        
        # Обработка адреса
        address = vacancy.get('address', {}) or {}
        
        # Обработка snippet
        snippet = vacancy.get('snippet', {}) or {}
        
        # Профессиональные роли
        professional_roles = [
            int(role['id']) for role in vacancy.get('professional_roles', [])
            if role and role.get('id')
        ]
        
        # Обработка типов (могут быть None)
        vacancy_type = vacancy.get('type', {}) or {}
        schedule = vacancy.get('schedule', {}) or {}
        experience = vacancy.get('experience', {}) or {}
        employment = vacancy.get('employment', {}) or {}
        employment_form = vacancy.get('employment_form', {}) or {}
        area = vacancy.get('area', {}) or {}
        
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
            'area_id': int(area['id']) if area.get('id') else None,
            'employer_id': employer_data['id'],
            'salary_from': salary_from,
            'salary_to': salary_to,
            'salary_currency': salary_currency,
            'salary_gross': salary_gross,
            'vacancy_type': vacancy_type.get('id'),
            'vacancy_type_name': vacancy_type.get('name'),
            'schedule_id': schedule.get('id'),
            'schedule_name': schedule.get('name'),
            'experience_id': experience.get('id'),
            'experience_name': experience.get('name'),
            'employment_id': employment.get('id'),
            'employment_name': employment.get('name'),
            'employment_form_id': employment_form.get('id'),
            'employment_form_name': employment_form.get('name'),
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
