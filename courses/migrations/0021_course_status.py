from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0020_delete_studentbadge'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='status',
            field=models.CharField(
                choices=[
                    ('published', 'Опубліковано'),
                    ('hidden', 'Приховано'),
                    ('archived', 'Архівовано'),
                ],
                default='published',
                max_length=20,
                verbose_name='Статус курсу',
            ),
        ),
    ]
