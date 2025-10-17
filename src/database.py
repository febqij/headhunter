import psycopg2
from psycopg2 import sql, extras
from psycopg2.extensions import connection
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from config import DB_CONFIG

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn: Optional[connection] = None
        
    def connect(self) -> None:
        """Устанавливает соединение с БД"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Успешное подключение к базе данных")
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    def disconnect(self) -> None:
        """Закрывает соединение с БД"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")
    
    def execute_script(self, script_path: str) -> None:
        """Выполняет SQL-скрипт из файла"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = f.read()
            
            with self.conn.cursor() as cur:
                cur.execute(script)
                self.conn.commit()
                logger.info(f"Скрипт {script_path} успешно выполнен")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка выполнения скрипта: {e}")
            raise
    
    def upsert_areas(self, areas_data: List[Dict]) -> None:
        """Вставка/обновление регионов"""
        insert_query = """
            INSERT INTO areas (id, name, parent_id, url)
            VALUES (%(id)s, %(name)s, %(parent_id)s, %(url)s)
            ON CONFLICT (id) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                url = EXCLUDED.url
        """
        try:
            with self.conn.cursor() as cur:
                extras.execute_batch(cur, insert_query, areas_data, page_size=1000)
                self.conn.commit()
                logger.info(f"Вставлено/обновлено {len(areas_data)} регионов")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при вставке регионов: {e}")
            raise
    
    def upsert_professional_roles(self, categories_data: List[Dict], roles_data: List[Dict]) -> None:
        """Вставка/обновление профессиональных ролей"""
        cat_query = """
            INSERT INTO professional_role_categories (id, name)
            VALUES (%(id)s, %(name)s)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """
        
        role_query = """
            INSERT INTO professional_roles (id, name, category_id, accept_incomplete_resumes)
            VALUES (%(id)s, %(name)s, %(category_id)s, %(accept_incomplete_resumes)s)
            ON CONFLICT (id) DO UPDATE SET 
                name = EXCLUDED.name,
                category_id = EXCLUDED.category_id,
                accept_incomplete_resumes = EXCLUDED.accept_incomplete_resumes
        """
        
        try:
            with self.conn.cursor() as cur:
                extras.execute_batch(cur, cat_query, categories_data, page_size=100)
                extras.execute_batch(cur, role_query, roles_data, page_size=1000)
                self.conn.commit()
                logger.info(f"Вставлено {len(categories_data)} категорий и {len(roles_data)} ролей")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при вставке профессиональных ролей: {e}")
            raise
    
    def upsert_employer(self, employer_data: Dict) -> None:
        """Вставка/обновление работодателя"""
        query = """
            INSERT INTO employers (
                id, name, url, alternate_url, logo_original, logo_90, logo_240,
                vacancies_url, country_id, accredited_it_employer, trusted, updated_at
            ) VALUES (
                %(id)s, %(name)s, %(url)s, %(alternate_url)s, %(logo_original)s, 
                %(logo_90)s, %(logo_240)s, %(vacancies_url)s, %(country_id)s,
                %(accredited_it_employer)s, %(trusted)s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                url = EXCLUDED.url,
                alternate_url = EXCLUDED.alternate_url,
                logo_original = EXCLUDED.logo_original,
                logo_90 = EXCLUDED.logo_90,
                logo_240 = EXCLUDED.logo_240,
                vacancies_url = EXCLUDED.vacancies_url,
                country_id = EXCLUDED.country_id,
                accredited_it_employer = EXCLUDED.accredited_it_employer,
                trusted = EXCLUDED.trusted,
                updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, employer_data)
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при вставке работодателя {employer_data.get('id')}: {e}")
            raise
    
    def upsert_vacancy(self, vacancy_data: Dict, professional_roles: List[int]) -> None:
        """Вставка/обновление вакансии с версионированием"""
        vacancy_query = """
            INSERT INTO vacancies (
                id, published_at, created_at, parsed_at, name, premium, has_test,
                response_letter_required, archived, area_id, employer_id,
                salary_from, salary_to, salary_currency, salary_gross,
                vacancy_type, vacancy_type_name, schedule_id, schedule_name,
                experience_id, experience_name, employment_id, employment_name,
                employment_form_id, employment_form_name,
                address_city, address_street, address_building, address_lat, address_lng,
                address_raw, address_id, url, alternate_url, apply_alternate_url, response_url,
                snippet_requirement, snippet_responsibility, accept_temporary,
                accept_incomplete_resumes, show_logo_in_search, show_contacts,
                is_adv_vacancy, internship, night_shifts,
                working_days, working_time_intervals, working_time_modes,
                working_hours, work_schedule_by_days, fly_in_fly_out_duration, work_format
            ) VALUES (
                %(id)s, %(published_at)s, %(created_at)s, %(parsed_at)s, %(name)s, %(premium)s, 
                %(has_test)s, %(response_letter_required)s, %(archived)s, %(area_id)s, %(employer_id)s,
                %(salary_from)s, %(salary_to)s, %(salary_currency)s, %(salary_gross)s,
                %(vacancy_type)s, %(vacancy_type_name)s, %(schedule_id)s, %(schedule_name)s,
                %(experience_id)s, %(experience_name)s, %(employment_id)s, %(employment_name)s,
                %(employment_form_id)s, %(employment_form_name)s,
                %(address_city)s, %(address_street)s, %(address_building)s, %(address_lat)s, 
                %(address_lng)s, %(address_raw)s, %(address_id)s, %(url)s, %(alternate_url)s,
                %(apply_alternate_url)s, %(response_url)s, %(snippet_requirement)s, 
                %(snippet_responsibility)s, %(accept_temporary)s, %(accept_incomplete_resumes)s,
                %(show_logo_in_search)s, %(show_contacts)s, %(is_adv_vacancy)s, %(internship)s, 
                %(night_shifts)s, %(working_days)s, %(working_time_intervals)s, %(working_time_modes)s,
                %(working_hours)s, %(work_schedule_by_days)s, %(fly_in_fly_out_duration)s, %(work_format)s
            )
            ON CONFLICT (id, published_at, created_at, parsed_at) DO NOTHING
        """
        
        roles_query = """
            INSERT INTO vacancy_professional_roles (
                vacancy_id, vacancy_published_at, vacancy_created_at, vacancy_parsed_at, professional_role_id
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(vacancy_query, vacancy_data)
                
                # Вставка связей с профессиональными ролями
                for role_id in professional_roles:
                    cur.execute(roles_query, (
                        vacancy_data['id'],
                        vacancy_data['published_at'],
                        vacancy_data['created_at'],
                        vacancy_data['parsed_at'],
                        role_id
                    ))
                
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при вставке вакансии {vacancy_data.get('id')}: {e}")
            raise
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
