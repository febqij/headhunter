## Шаг 1: Настройка базы данных PostgreSQL

### Создание файла с переменными окружения

Файл `.env` в корне проекта должен содержать следующие значения:

```
DB_NAME=headhunter_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
```

### Развертывание базы данных

Запустить контейнер (`docker-compose.yml`) PostgreSQL командой:

```
docker compose up -d
```

Проверить рабочий статус (`Up...`) контейнера:

```
docker compose ps
```
Ниже моя шпаргалка, чтобы не забыть компанды:
- **Перезагрузка контейнера:**
```
docker compose restart
```
- **Удалить контейнер вместе с данными:**
```
docker compose down -v
```
