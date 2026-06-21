# Generated manually for LMS feature extensions.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0017_course_password_studentgroup'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='allow_late_submissions',
            field=models.BooleanField(default=True, verbose_name='Дозволити здачу після дедлайну'),
        ),
        migrations.AddField(
            model_name='submission',
            name='is_late',
            field=models.BooleanField(default=False, verbose_name='Здано після дедлайну'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='max_attempts',
            field=models.PositiveIntegerField(default=3, verbose_name='Максимальна кількість спроб'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='show_correct_answers',
            field=models.BooleanField(default=True, verbose_name='Показувати правильні відповіді після тесту'),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160, verbose_name='Заголовок')),
                ('text', models.TextField(verbose_name='Текст')),
                ('notification_type', models.CharField(choices=[('info', 'Інформація'), ('assignment', 'Завдання'), ('grade', 'Оцінка'), ('message', 'Повідомлення'), ('course', 'Курс')], default='info', max_length=20, verbose_name='Тип')),
                ('url', models.CharField(blank=True, max_length=255, verbose_name='Посилання')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Повідомлення',
                'verbose_name_plural': 'Повідомлення',
                'ordering': ['-created_at'],
            },
        ),
    ]
