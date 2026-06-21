# Публікація EduCourse в інтернет

Найпростіший варіант для цього Django-проєкту: Render + PostgreSQL.

## 1. Завантажити код на GitHub

1. Створи репозиторій на GitHub.
2. Завантаж туди папку `course_system`.
3. Не завантажуй `.env`, `db.sqlite3`, `venv`, `media`, `staticfiles`.

## 2. Створити базу даних PostgreSQL

На Render створи PostgreSQL database і скопіюй `Internal Database URL`.

## 3. Створити Web Service

На Render створи `New Web Service` з GitHub-репозиторію.

Build Command:

```bash
./build.sh
```

Start Command:

```bash
gunicorn course_system.wsgi:application
```

## 4. Додати Environment Variables

```text
DJANGO_SECRET_KEY=довгий-випадковий-секретний-ключ
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=назва-сайту.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://назва-сайту.onrender.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DATABASE_URL=Internal Database URL з Render PostgreSQL
REGISTRATION_ACCESS_PASSWORD=пароль-для-реєстрації-студентів
```

## 5. Створити адміністратора

Після першого деплою відкрий Render Shell і виконай:

```bash
python manage.py createsuperuser
```

## Важливо про файли

Завантажені аватари, відео, PDF і роботи студентів у папці `media` на Render можуть зникати після перезапуску сервера. Для реального сайту потрібне окреме сховище файлів, наприклад S3-compatible storage. Для дипломної демонстрації можна показувати локально або без великих завантажень.
