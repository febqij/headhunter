import logging
from database import Database
from parser import HHParser
from config import LOG_CONFIG, SCHEMA_FILE

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOG_CONFIG['file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_database(db: Database):
    """Инициализация БД и загрузка справочников"""
    logger.info("Инициализация базы данных...")
    
    # Выполнение schema.sql
    db.execute_script(SCHEMA_FILE)
    
    # Загрузка справочников
    parser = HHParser()
    
    # Загрузка регионов
    areas = parser.fetch_areas()
    if areas:
        db.upsert_areas(areas)
    
    # Загрузка профессиональных ролей
    categories, roles = parser.fetch_professional_roles()
    if categories and roles:
        db.upsert_professional_roles(categories, roles)
    
    logger.info("Инициализация завершена")

def parse_vacancies(db: Database):
    """Парсинг вакансий"""
    logger.info("Начало парсинга вакансий...")
    
    parser = HHParser()
    processed = 0
    errors = 0
    skipped = 0
    
    for data in parser.parse_all_vacancies():
        try:
            # Вставка работодателя (может быть None)
            if data['employer']['id']:
                db.upsert_employer(data['employer'])
            else:
                logger.warning(f"Вакансия {data['vacancy']['id']} без работодателя")
                skipped += 1
                continue
            
            # Вставка вакансии
            db.upsert_vacancy(data['vacancy'], data['professional_roles'])
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"Обработано {processed} вакансий (ошибок: {errors}, пропущено: {skipped})")
                
        except KeyError as e:
            errors += 1
            logger.error(f"Отсутствует обязательное поле в вакансии: {e}")
            logger.debug(f"Проблемная вакансия: {data.get('vacancy', {}).get('id', 'unknown')}")
            continue
            
        except Exception as e:
            errors += 1
            logger.error(f"Ошибка обработки вакансии {data.get('vacancy', {}).get('id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Парсинг завершен. Обработано: {processed}, ошибок: {errors}, пропущено: {skipped}")

def main():
    """Основная функция"""
    try:
        with Database() as db:
            # Раскомментируйте для первого запуска
            initialize_database(db)
            
            # Парсинг вакансий
            parse_vacancies(db)
            
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
