from django.conf import settings
from django.test import TestCase

from courses.models import Course, FavoriteCourse
from users.models import User


class RegistrationTests(TestCase):

    def test_public_registration_creates_student(self):
        response = self.client.post('/register/', {
            'username': 'new_user',
            'email': 'new@example.com',
            'access_password': settings.REGISTRATION_ACCESS_PASSWORD,
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.get(username='new_user').role, 'student')


class NotificationAndFavoriteTests(TestCase):

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher',
            password='pass12345',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student',
            password='pass12345',
            role='student'
        )
        self.course = Course.objects.create(
            title='Django',
            description='Course description',
            teacher=self.teacher
        )

    def test_favorite_toggle_requires_post(self):
        self.client.login(username='student', password='pass12345')

        response = self.client.get(f'/courses/{self.course.id}/favorite/')

        self.assertEqual(response.status_code, 405)
        self.assertFalse(FavoriteCourse.objects.exists())
