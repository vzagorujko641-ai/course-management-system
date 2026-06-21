# Публікація EduCourse на Render

Проєкт підготовлено до запуску як Render Blueprint разом із PostgreSQL.

## 1. Завантажити зміни на GitHub

Репозиторій уже має remote `origin`. Закоміть і відправ зміни:

```bash
git add course_system/settings.py render.yaml DEPLOY.md .gitignore
git commit -m "Configure Render deployment"
git push origin main
```

Якщо поточна гілка називається не `main`, у останній команді вкажи її назву.

## 2. Створити Blueprint на Render

1. У Render відкрий **New → Blueprint**.
2. Підключи GitHub-репозиторій `course-management-system`.
3. Render прочитає `render.yaml` і запропонує створити вебсервіс `educourse` та PostgreSQL `educourse-db`.
4. Для `REGISTRATION_ACCESS_PASSWORD` введи власний пароль.
5. Натисни **Deploy Blueprint**.

Якщо ім'я `educourse` вже зайняте, Render додасть до адреси суфікс або запропонує іншу назву. Django автоматично підхопить фактичний домен із `RENDER_EXTERNAL_HOSTNAME`.

## 3. Створити адміністратора

Після успішного деплою відкрий для вебсервісу **Shell** та виконай:

```bash
python manage.py createsuperuser
```

## Важливо про файли

PostgreSQL зберігає облікові записи, курси та оцінки. Завантажені аватари, відео, PDF та студентські роботи пишуться у локальну папку `media`, тому можуть зникнути після перезапуску або нового деплою Render. Для постійного зберігання потрібне зовнішнє сховище, наприклад Cloudinary або S3-сумісний сервіс.
