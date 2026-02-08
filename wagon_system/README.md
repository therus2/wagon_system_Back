# Система учёта вагонов - Django Backend

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
```

2. Активируйте виртуальное окружение:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Настройка базы данных

1. Установите PostgreSQL
2. Создайте базу данных:
```sql
CREATE DATABASE wagon_db;
```

3. Создайте файл `.env` на основе `.env.example` и заполните настройки

## Миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

## Создание суперпользователя

```bash
python manage.py createsuperuser
```

## Запуск сервера

```bash
python manage.py runserver
```

## API Endpoints

- `/api/auth/login/` - Вход в систему
- `/api/auth/me/` - Информация о текущем пользователе
- `/api/wagons/` - Список вагонов
- `/api/wagons/bulk/` - Массовое создание вагонов
- `/api/compose/` - Подбор составов
- `/api/wagon-types/` - Типы вагонов
- `/api/cargo-types/` - Типы грузов
- `/api/firms/` - Фирмы
- `/api/station-config/` - Конфигурация станции
