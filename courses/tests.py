from django.test import TestCase

from courses.models import Assignment, Course, Lesson, LessonProgress
from users.models import User


class CourseAccessTests(TestCase):

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
        self.other_student = User.objects.create_user(
            username='other',
            password='pass12345',
            role='student'
        )
        self.course = Course.objects.create(
            title='Django',
            description='Course description',
            teacher=self.teacher
        )
        self.course.students.add(self.student)
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Intro',
            content='Lesson content'
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='Homework',
            description='Task'
        )

    def test_complete_lesson_requires_post(self):
        self.client.login(username='student', password='pass12345')

        response = self.client.get(f'/courses/lesson/{self.lesson.id}/complete/')

        self.assertEqual(response.status_code, 405)
        self.assertFalse(LessonProgress.objects.exists())

    def test_only_enrolled_student_can_complete_lesson(self):
        self.client.login(username='other', password='pass12345')

        response = self.client.post(f'/courses/lesson/{self.lesson.id}/complete/')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(LessonProgress.objects.exists())

    def test_only_enrolled_student_can_submit_assignment(self):
        self.client.login(username='other', password='pass12345')

        response = self.client.post(
            f'/courses/assignment/{self.assignment.id}/submit/',
            {'answer': 'My answer'}
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.assignment.submissions.exists())
