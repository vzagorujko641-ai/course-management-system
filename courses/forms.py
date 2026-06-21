from django import forms
from users.forms import validate_uploaded_file

from .models import (
    Assignment,
    Course,
    CourseModule,
    Lesson,
    LibraryItem,
    Quiz,
    QuizQuestion,
    ScheduleEvent,
    StudentGroup,
    Submission,
)


def teacher_courses_for(user):
    return (Course.objects.filter(teacher=user) | Course.objects.filter(co_teachers=user)).distinct()


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'category',
            'tags',
            'co_teachers',
            'is_visible',
            'status',
            'enrollment_password',
        ]
        labels = {
            'title': 'Назва курсу',
            'description': 'Опис курсу',
            'category': 'Категорія',
            'tags': 'Теги',
            'co_teachers': 'Додаткові викладачі',
            'is_visible': 'Показувати студентам',
            'status': 'Статус курсу',
            'enrollment_password': 'Пароль для запису',
        }
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
            'co_teachers': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['co_teachers'].queryset = self.fields['co_teachers'].queryset.filter(
                role='teacher'
            ).exclude(id=teacher.id)


class CourseModuleForm(forms.ModelForm):

    class Meta:
        model = CourseModule
        fields = ['course', 'title', 'description', 'order']
        labels = {
            'course': 'Курс',
            'title': 'Назва модуля',
            'description': 'Опис модуля',
            'order': 'Порядок',
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)


class LessonForm(forms.ModelForm):

    class Meta:
        model = Lesson
        fields = [
            'course',
            'module',
            'title',
            'content',
            'category',
            'order',
            'banner_image',
            'video',
            'pdf_material',
            'presentation',
        ]
        labels = {
            'course': 'Курс',
            'module': 'Модуль',
            'title': 'Назва уроку',
            'content': 'Матеріал уроку',
            'category': 'Категорія уроку',
            'order': 'Номер уроку',
            'banner_image': 'Банер уроку',
            'video': 'Відеоурок',
            'pdf_material': 'PDF-матеріал',
            'presentation': 'Презентація',
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            teacher_courses = teacher_courses_for(teacher)
            self.fields['course'].queryset = teacher_courses
            self.fields['module'].queryset = CourseModule.objects.filter(
                course__in=teacher_courses
            ).distinct()

    def clean_banner_image(self):
        banner_image = self.cleaned_data.get('banner_image')
        validate_uploaded_file(
            banner_image,
            {'jpg', 'jpeg', 'png', 'webp'}
        )
        return banner_image

    def clean_video(self):
        video = self.cleaned_data.get('video')
        validate_uploaded_file(video, {'mp4', 'mov', 'webm', 'avi'})
        return video

    def clean_pdf_material(self):
        pdf_material = self.cleaned_data.get('pdf_material')
        validate_uploaded_file(pdf_material, {'pdf'})
        return pdf_material

    def clean_presentation(self):
        presentation = self.cleaned_data.get('presentation')
        validate_uploaded_file(presentation, {'pdf', 'ppt', 'pptx'})
        return presentation


class AssignmentForm(forms.ModelForm):

    class Meta:
        model = Assignment
        fields = [
            'course',
            'title',
            'description',
            'assignment_type',
            'deadline',
            'allow_late_submissions',
        ]
        labels = {
            'course': 'Курс',
            'title': 'Назва завдання',
            'description': 'Опис завдання',
            'assignment_type': 'Тип роботи',
            'deadline': 'Дедлайн',
            'allow_late_submissions': 'Дозволити здачу після дедлайну',
        }
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)


class StudentGroupForm(forms.ModelForm):

    class Meta:
        model = StudentGroup
        fields = ['course', 'name', 'enrollment_password', 'students']
        labels = {
            'course': 'Курс',
            'name': 'Назва групи',
            'enrollment_password': 'Пароль групи',
            'students': 'Студенти',
        }
        widgets = {
            'students': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)
            self.fields['students'].queryset = self.fields['students'].queryset.filter(role='student')


class QuizForm(forms.ModelForm):

    class Meta:
        model = Quiz
        fields = [
            'course',
            'title',
            'description',
            'time_limit',
            'max_attempts',
            'show_correct_answers',
        ]
        labels = {
            'course': 'Курс',
            'title': 'Назва тесту',
            'description': 'Опис тесту',
            'time_limit': 'Час на виконання, хв',
            'max_attempts': 'Кількість спроб',
            'show_correct_answers': 'Показувати правильні відповіді',
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)


class QuizQuestionForm(forms.ModelForm):

    class Meta:
        model = QuizQuestion
        fields = [
            'quiz',
            'text',
            'order',
            'option_1',
            'option_2',
            'option_3',
            'option_4',
            'correct_option',
        ]
        labels = {
            'quiz': 'Тест',
            'text': 'Питання',
            'order': 'Номер питання',
            'option_1': 'Варіант 1',
            'option_2': 'Варіант 2',
            'option_3': 'Варіант 3',
            'option_4': 'Варіант 4',
            'correct_option': 'Номер правильної відповіді',
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['quiz'].queryset = (
                Quiz.objects.filter(course__teacher=teacher)
                | Quiz.objects.filter(course__co_teachers=teacher)
            ).distinct()


class LibraryItemForm(forms.ModelForm):

    class Meta:
        model = LibraryItem
        fields = ['course', 'title', 'description', 'material_type', 'file', 'url']
        labels = {
            'course': 'Курс',
            'title': 'Назва матеріалу',
            'description': 'Опис',
            'material_type': 'Тип матеріалу',
            'file': 'Файл',
            'url': 'Посилання',
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)

    def clean_file(self):
        file = self.cleaned_data.get('file')
        validate_uploaded_file(file, {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'zip'})
        return file


class ScheduleEventForm(forms.ModelForm):

    class Meta:
        model = ScheduleEvent
        fields = ['course', 'title', 'starts_at', 'location']
        labels = {
            'course': 'Курс',
            'title': 'Назва заняття',
            'starts_at': 'Дата і час',
            'location': 'Місце або посилання',
        }
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields['course'].queryset = teacher_courses_for(teacher)


class SubmissionReviewForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ['grade', 'status', 'teacher_comment']
        labels = {
            'grade': 'Оцінка',
            'status': 'Статус',
            'teacher_comment': 'Коментар викладача',
        }
