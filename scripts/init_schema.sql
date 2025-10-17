-- scripts/init_schema.sql
-- Создание схемы для приложения
CREATE SCHEMA IF NOT EXISTS headhunter;

-- Установка прав для пользователя postgres
GRANT ALL PRIVILEGES ON SCHEMA headhunter TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA headhunter TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA headhunter TO postgres;

-- Установка search_path по умолчанию для базы данных
ALTER DATABASE headhunter_db SET search_path TO headhunter, public;

-- Установка search_path для пользователя postgres
ALTER ROLE postgres IN DATABASE headhunter_db SET search_path TO headhunter, public;

-- Информационное сообщение
DO $$
BEGIN
    RAISE NOTICE 'Schema "headhunter" created successfully';
    RAISE NOTICE 'Default search_path set to: headhunter, public';
END $$;
