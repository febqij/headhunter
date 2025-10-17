-- Убедитесь, что схема существует
CREATE SCHEMA IF NOT EXISTS headhunter;

-- Устанавливаем search_path для текущей сессии
SET search_path TO headhunter, public;

-- Таблица категорий профессиональных ролей
CREATE TABLE IF NOT EXISTS headhunter.professional_role_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица профессиональных ролей
CREATE TABLE IF NOT EXISTS headhunter.professional_roles (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES headhunter.professional_role_categories(id),
    accept_incomplete_resumes BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица регионов (areas)
CREATE TABLE IF NOT EXISTS headhunter.areas (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES headhunter.areas(id),
    url TEXT,
    utc_offset VARCHAR(10),
    lat DECIMAL(10, 7),
    lng DECIMAL(10, 7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица работодателей
CREATE TABLE IF NOT EXISTS headhunter.employers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    url TEXT,
    alternate_url TEXT,
    logo_original TEXT,
    logo_90 TEXT,
    logo_240 TEXT,
    vacancies_url TEXT,
    country_id INTEGER,
    accredited_it_employer BOOLEAN DEFAULT FALSE,
    trusted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Основная таблица вакансий
CREATE TABLE IF NOT EXISTS headhunter.vacancies (
    id BIGINT,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    parsed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    name VARCHAR(1000) NOT NULL,
    premium BOOLEAN DEFAULT FALSE,
    has_test BOOLEAN DEFAULT FALSE,
    response_letter_required BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    
    area_id INTEGER REFERENCES headhunter.areas(id),
    employer_id INTEGER REFERENCES headhunter.employers(id),
    
    salary_from INTEGER,
    salary_to INTEGER,
    salary_currency VARCHAR(10),
    salary_gross BOOLEAN,
    
    vacancy_type VARCHAR(50),
    vacancy_type_name VARCHAR(255),
    schedule_id VARCHAR(50),
    schedule_name VARCHAR(255),
    experience_id VARCHAR(50),
    experience_name VARCHAR(255),
    employment_id VARCHAR(50),
    employment_name VARCHAR(255),
    employment_form_id VARCHAR(50),
    employment_form_name VARCHAR(255),
    
    address_city VARCHAR(255),
    address_street VARCHAR(500),
    address_building VARCHAR(100),
    address_lat DECIMAL(10, 7),
    address_lng DECIMAL(10, 7),
    address_raw TEXT,
    address_id BIGINT,
    
    url TEXT,
    alternate_url TEXT,
    apply_alternate_url TEXT,
    response_url TEXT,
    
    snippet_requirement TEXT,
    snippet_responsibility TEXT,
    
    accept_temporary BOOLEAN DEFAULT FALSE,
    accept_incomplete_resumes BOOLEAN DEFAULT FALSE,
    show_logo_in_search BOOLEAN,
    show_contacts BOOLEAN DEFAULT FALSE,
    is_adv_vacancy BOOLEAN DEFAULT FALSE,
    internship BOOLEAN DEFAULT FALSE,
    night_shifts BOOLEAN DEFAULT FALSE,
    
    working_days TEXT,
    working_time_intervals TEXT,
    working_time_modes TEXT,
    working_hours TEXT,
    work_schedule_by_days TEXT,
    fly_in_fly_out_duration TEXT,
    work_format TEXT,
    
    PRIMARY KEY (id, published_at, created_at, parsed_at)
);

-- Связующая таблица для professional_roles (many-to-many)
CREATE TABLE IF NOT EXISTS headhunter.vacancy_professional_roles (
    vacancy_id BIGINT,
    vacancy_published_at TIMESTAMP,
    vacancy_created_at TIMESTAMP,
    vacancy_parsed_at TIMESTAMP,
    professional_role_id INTEGER REFERENCES headhunter.professional_roles(id),
    PRIMARY KEY (vacancy_id, vacancy_published_at, vacancy_created_at, vacancy_parsed_at, professional_role_id),
    FOREIGN KEY (vacancy_id, vacancy_published_at, vacancy_created_at, vacancy_parsed_at) 
        REFERENCES headhunter.vacancies(id, published_at, created_at, parsed_at) ON DELETE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_vacancies_area ON headhunter.vacancies(area_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_employer ON headhunter.vacancies(employer_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_archived ON headhunter.vacancies(archived);
CREATE INDEX IF NOT EXISTS idx_vacancies_published ON headhunter.vacancies(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_vacancies_parsed ON headhunter.vacancies(parsed_at DESC);
CREATE INDEX IF NOT EXISTS idx_vacancies_salary_from ON headhunter.vacancies(salary_from) WHERE salary_from IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_employers_name ON headhunter.employers(name);
CREATE INDEX IF NOT EXISTS idx_areas_name ON headhunter.areas(name);
CREATE INDEX IF NOT EXISTS idx_areas_parent ON headhunter.areas(parent_id);
CREATE INDEX IF NOT EXISTS idx_areas_coordinates ON headhunter.areas(lat, lng) WHERE lat IS NOT NULL AND lng IS NOT NULL;
