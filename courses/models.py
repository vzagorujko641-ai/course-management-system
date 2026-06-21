from django.db import models
from users.models import User


class Category(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name='Назва категорії'
    )

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

    def __str__(self):
        return self.name


class Tag(models.Model):

    name = models.CharField(
        max_length=60,
        unique=True,
        verbose_name='Назва тегу'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Course(models.Model):

    STATUS_CHOICES = (
        ('published', 'Опубліковано'),
        ('hidden', 'Приховано'),
        ('archived', 'Архівовано'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Назва курсу'
    )

    description = models.TextField(
        verbose_name='Опис курсу'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Категорія'
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Викладач'
    )

    co_teachers = models.ManyToManyField(
        User,
        related_name='assisted_courses',
        blank=True,
        verbose_name='Додаткові викладачі'
    )

    students = models.ManyToManyField(
        User,
        related_name='enrolled_courses',
        blank=True,
        verbose_name='Студенти'
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='courses',
        blank=True,
        verbose_name='Теги'
    )

    is_visible = models.BooleanField(
        default=True,
        verbose_name='Показувати курс'
    )

    enrollment_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Пароль для запису на курс'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='published',
        verbose_name='Статус курсу'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курси'

    def __str__(self):
        return self.title

    def is_teacher(self, user):
        return (
            user.is_authenticated
            and (
                user == self.teacher
                or user.is_superuser
                or self.co_teachers.filter(id=user.id).exists()
            )
        )


class CourseModule(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Курс'
    )

    title = models.CharField(
        max_length=180,
        verbose_name='Назва модуля'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Опис модуля'
    )

    order = models.PositiveIntegerField(
        default=1,
        verbose_name='Порядок'
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Модуль курсу'
        verbose_name_plural = 'Модулі курсу'

    def __str__(self):
        return f'{self.course.title} - {self.title}'


class StudentGroup(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='student_groups',
        verbose_name='Курс'
    )

    name = models.CharField(
        max_length=120,
        verbose_name='Назва групи'
    )

    enrollment_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Пароль групи'
    )

    students = models.ManyToManyField(
        User,
        related_name='course_groups',
        blank=True,
        verbose_name='Студенти групи'
    )

    class Meta:
        verbose_name = 'Група студентів'
        verbose_name_plural = 'Групи студентів'

    def __str__(self):
        return f'{self.course.title} - {self.name}'


class Lesson(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.SET_NULL,
        related_name='lessons',
        null=True,
        blank=True,
        verbose_name='Модуль'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Назва уроку'
    )

    content = models.TextField(
        verbose_name='Матеріал уроку'
    )

    category = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Категорія уроку'
    )

    order = models.PositiveIntegerField(
        default=1,
        verbose_name='Номер уроку'
    )

    banner_image = models.ImageField(
        upload_to='lesson_banners/',
        null=True,
        blank=True,
        verbose_name='Банер уроку'
    )

    video = models.FileField(
        upload_to='lesson_videos/',
        null=True,
        blank=True,
        verbose_name='Відеоурок'
    )

    pdf_material = models.FileField(
        upload_to='lesson_materials/',
        null=True,
        blank=True,
        verbose_name='PDF-матеріал'
    )

    presentation = models.FileField(
        upload_to='lesson_presentations/',
        null=True,
        blank=True,
        verbose_name='Презентація'
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title


class LessonImage(models.Model):

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Урок'
    )

    image = models.FileField(
        upload_to='lesson_images/',
        verbose_name='Зображення'
    )

    caption = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Підпис'
    )

    class Meta:
        verbose_name = 'Зображення уроку'
        verbose_name_plural = 'Галерея уроку'

    def __str__(self):
        return self.caption or self.image.name


class LessonProgress(models.Model):

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name='Урок'
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='Студент'
    )

    completed = models.BooleanField(
        default=True,
        verbose_name='Пройдено'
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата проходження'
    )

    class Meta:
        verbose_name = 'Прогрес уроку'
        verbose_name_plural = 'Прогрес уроків'

    def __str__(self):
        return f'{self.student.username} - {self.lesson.title}'


class Assignment(models.Model):

    ASSIGNMENT_TYPES = (
        ('homework', 'Домашнє завдання'),
        ('practice', 'Практична робота'),
        ('lab', 'Лабораторна робота'),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Курс'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Назва завдання'
    )

    description = models.TextField(
        verbose_name='Опис завдання'
    )

    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPES,
        default='homework',
        verbose_name='Тип роботи'
    )

    deadline = models.DateField(
        verbose_name='Дедлайн',
        null=True,
        blank=True
    )

    allow_late_submissions = models.BooleanField(
        default=True,
        verbose_name='Дозволити здачу після дедлайну'
    )

    class Meta:
        verbose_name = 'Завдання'
        verbose_name_plural = 'Завдання'

    def __str__(self):
        return self.title


class Submission(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Очікує перевірки'),
        ('checked', 'Перевірено'),
    )

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Завдання'
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Студент'
    )

    answer = models.TextField(
        verbose_name='Відповідь студента'
    )

    file = models.FileField(
        upload_to='submissions/',
        verbose_name='Файл',
        null=True,
        blank=True
    )

    grade = models.IntegerField(
        verbose_name='Оцінка',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    teacher_comment = models.TextField(
        verbose_name='Коментар викладача',
        blank=True
    )

    is_late = models.BooleanField(
        default=False,
        verbose_name='Здано після дедлайну'
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата відправлення'
    )

    class Meta:
        verbose_name = 'Відповідь студента'
        verbose_name_plural = 'Відповіді студентів'

    def __str__(self):
        return f'{self.student.username} - {self.assignment.title}'


class Message(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Курс'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Автор'
    )

    text = models.TextField(
        verbose_name='Повідомлення'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    file = models.FileField(
        upload_to='chat_files/',
        null=True,
        blank=True,
        verbose_name='Файл'
    )

    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Відповідь на'
    )

    likes = models.ManyToManyField(
        User,
        related_name='liked_messages',
        blank=True,
        verbose_name='Лайки'
    )

    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Закріплено'
    )

    class Meta:
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

    def __str__(self):
        return f'{self.author.username}: {self.text[:30]}'


class FavoriteCourse(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_courses',
        verbose_name='Студент'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='favorite_marks',
        verbose_name='Курс'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата додавання'
    )

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = 'Обраний курс'
        verbose_name_plural = 'Обрані курси'

    def __str__(self):
        return f'{self.student.username} - {self.course.title}'


class Quiz(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name='Курс'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Назва тесту'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Опис тесту'
    )

    time_limit = models.PositiveIntegerField(
        default=10,
        verbose_name='Час на виконання, хв'
    )

    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name='Максимальна кількість спроб'
    )

    show_correct_answers = models.BooleanField(
        default=True,
        verbose_name='Показувати правильні відповіді після тесту'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тести'

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Тест'
    )

    text = models.TextField(
        verbose_name='Питання'
    )

    order = models.PositiveIntegerField(
        default=1,
        verbose_name='Номер питання'
    )

    option_1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Варіант 1'
    )

    option_2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Варіант 2'
    )

    option_3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Варіант 3'
    )

    option_4 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Варіант 4'
    )

    correct_option = models.PositiveIntegerField(
        default=1,
        verbose_name='Номер правильної відповіді'
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Питання тесту'
        verbose_name_plural = 'Питання тесту'

    def __str__(self):
        return self.text[:80]


class QuizAnswerOption(models.Model):

    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Питання'
    )

    text = models.CharField(
        max_length=255,
        verbose_name='Варіант відповіді'
    )

    is_correct = models.BooleanField(
        default=False,
        verbose_name='Правильна відповідь'
    )

    class Meta:
        verbose_name = 'Варіант відповіді'
        verbose_name_plural = 'Варіанти відповідей'

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Тест'
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name='Студент'
    )

    score = models.PositiveIntegerField(
        default=0,
        verbose_name='Правильних відповідей'
    )

    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name='Усього питань'
    )

    percent = models.PositiveIntegerField(
        default=0,
        verbose_name='Результат, %'
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Початок'
    )

    finished_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Завершення'
    )

    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name='Витрачено секунд'
    )

    class Meta:
        ordering = ['-finished_at']
        verbose_name = 'Спроба тесту'
        verbose_name_plural = 'Спроби тестів'

    def __str__(self):
        return f'{self.student.username} - {self.quiz.title} - {self.percent}%'


class LibraryItem(models.Model):

    MATERIAL_TYPES = (
        ('book', 'Книга'),
        ('article', 'Стаття'),
        ('video', 'Відео'),
        ('link', 'Посилання'),
        ('file', 'Файл'),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='library_items',
        verbose_name='Курс'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Назва матеріалу'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )

    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPES,
        default='file',
        verbose_name='Тип матеріалу'
    )

    file = models.FileField(
        upload_to='library/',
        null=True,
        blank=True,
        verbose_name='Файл'
    )

    url = models.URLField(
        blank=True,
        verbose_name='Посилання'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата додавання'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Матеріал бібліотеки'
        verbose_name_plural = 'Електронна бібліотека'

    def __str__(self):
        return self.title


class ScheduleEvent(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='schedule_events',
        verbose_name='Курс'
    )

    title = models.CharField(
        max_length=180,
        verbose_name='Назва заняття'
    )

    starts_at = models.DateTimeField(
        verbose_name='Початок'
    )

    location = models.CharField(
        max_length=180,
        blank=True,
        verbose_name='Місце або посилання'
    )

    class Meta:
        ordering = ['starts_at']
        verbose_name = 'Заняття'
        verbose_name_plural = 'Розклад занять'

    def __str__(self):
        return f'{self.course.title} - {self.title}'


class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ('info', 'Інформація'),
        ('assignment', 'Завдання'),
        ('grade', 'Оцінка'),
        ('message', 'Повідомлення'),
        ('course', 'Курс'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Користувач'
    )

    title = models.CharField(
        max_length=160,
        verbose_name='Заголовок'
    )

    text = models.TextField(
        verbose_name='Текст'
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name='Тип'
    )

    url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Посилання'
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

    def __str__(self):
        return f'{self.user.username} - {self.title}'