from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import RegisterUserForm, ProfileForm
from courses.forms import (
    AssignmentForm,
    CourseForm,
    CourseModuleForm,
    LessonForm,
    LibraryItemForm,
    QuizForm,
    QuizQuestionForm,
    ScheduleEventForm,
    StudentGroupForm,
)
from courses.models import (
    Course,
    Assignment,
    CourseModule,
    LibraryItem,
    Submission,
    Message,
    FavoriteCourse,
    LessonProgress,
    Notification,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    ScheduleEvent,
    StudentGroup,
)
from courses.views import calculate_course_progress
from users.models import User
from datetime import date, timedelta
from reportlab.pdfgen import canvas
import csv



def home(request):

    upcoming_deadlines = 0
    late_deadlines = 0
    total_messages = 0

    if request.user.is_authenticated:

        my_courses = request.user.enrolled_courses.all()

        today = date.today()
        week_later = today + timedelta(days=7)

        upcoming_deadlines = Assignment.objects.filter(
            course__in=my_courses,
            deadline__gte=today,
            deadline__lte=week_later
        ).count()

        late_deadlines = Assignment.objects.filter(
            course__in=my_courses,
            deadline__lt=today
        ).count()

        total_messages = Message.objects.filter(
            course__in=my_courses
        ).count()

    return render(request, 'users/home.html', {
        'upcoming_deadlines': upcoming_deadlines,
        'late_deadlines': late_deadlines,
        'total_messages': total_messages
    })


def register(request):
    form = RegisterUserForm()

    if request.method == 'POST':
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')

    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    error = 'Неправильний логін або пароль'

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error = 'Неправильний логін або пароль'

    return render(request, 'users/login.html', {'error': error})


def user_logout(request):
    logout(request)
    return redirect('/')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    profile_form = ProfileForm(instance=request.user)

    if request.method == 'POST':
        profile_form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if profile_form.is_valid():
            profile_form.save()
            return redirect('/dashboard/')

    my_courses = request.user.enrolled_courses.all()
    my_submissions = request.user.submissions.all()
    favorite_courses = Course.objects.filter(
        favorite_marks__student=request.user
    )
    notifications = Notification.objects.filter(user=request.user)[:6]
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    today = date.today()
    week_later = today + timedelta(days=7)

    upcoming_deadlines = Assignment.objects.filter(
        course__in=my_courses,
        deadline__gte=today,
        deadline__lte=week_later
    ).count()

    late_deadlines = Assignment.objects.filter(
        course__in=my_courses,
        deadline__lt=today
    ).count()

    new_grades = my_submissions.exclude(grade__isnull=True).count()

    graded_submissions = my_submissions.exclude(grade__isnull=True)

    grade_labels = []
    grade_values = []

    for submission in graded_submissions:
        grade_labels.append(submission.assignment.title)
        grade_values.append(submission.grade)

    return render(request, 'users/dashboard.html', {
        'my_courses': my_courses,
        'my_submissions': my_submissions,
        'upcoming_deadlines': upcoming_deadlines,
        'late_deadlines': late_deadlines,
        'new_grades': new_grades,
        'grade_labels': grade_labels,
        'grade_values': grade_values,
        'profile_form': profile_form,
        'favorite_courses': favorite_courses,
        'notifications': notifications,
        'unread_notifications': unread_notifications
    })


def my_progress(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    course_rows = []

    for course in request.user.enrolled_courses.all():
        progress = calculate_course_progress(request.user, course)
        total_lessons = course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course
        ).count()
        submissions_count = Submission.objects.filter(
            student=request.user,
            assignment__course=course
        ).count()
        quiz_attempts = QuizAttempt.objects.filter(
            student=request.user,
            quiz__course=course
        )
        best_quiz = 0

        if quiz_attempts.exists():
            best_quiz = max(attempt.percent for attempt in quiz_attempts)

        course_rows.append({
            'course': course,
            'progress': progress,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'submissions_count': submissions_count,
            'best_quiz': best_quiz,
            'certificate_available': progress == 100,
        })

    return render(request, 'users/my_progress.html', {
        'course_rows': course_rows
    })

def statistics(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.user.role != 'teacher' and not request.user.is_superuser:
        return redirect('/dashboard/')

    total_courses = Course.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_assignments = Assignment.objects.count()
    total_submissions = Submission.objects.count()

    grades = Submission.objects.exclude(grade__isnull=True)

    if grades.exists():
        average_grade = sum(item.grade for item in grades) / grades.count()
    else:
        average_grade = 0

    grade_0_59 = grades.filter(grade__lt=60).count()
    grade_60_74 = grades.filter(grade__gte=60, grade__lte=74).count()
    grade_75_89 = grades.filter(grade__gte=75, grade__lte=89).count()
    grade_90_100 = grades.filter(grade__gte=90, grade__lte=100).count()

    return render(request, 'users/statistics.html', {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'average_grade': round(average_grade, 2),

        'grade_0_59': grade_0_59,
        'grade_60_74': grade_60_74,
        'grade_75_89': grade_75_89,
        'grade_90_100': grade_90_100,
    })

from datetime import date

def calendar_view(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    assignments = Assignment.objects.exclude(deadline__isnull=True)

    if request.user.role == 'teacher' or request.user.is_superuser:
        assignments = assignments.filter(course__teacher=request.user)
    else:
        assignments = assignments.filter(course__students=request.user)

    assignments = assignments.order_by('deadline')

    today = date.today()

    for assignment in assignments:
        days_left = (assignment.deadline - today).days
        assignment.days_left = days_left

        if days_left < 0:
            assignment.status = 'Прострочено'
            assignment.status_class = 'late'
        elif days_left == 0:
            assignment.status = 'Дедлайн сьогодні'
            assignment.status_class = 'today'
        elif days_left <= 2:
            assignment.status = f'Залишилось {days_left} дн.'
            assignment.status_class = 'soon'
        else:
            assignment.status = f'Залишилось {days_left} дн.'
            assignment.status_class = 'normal'

    return render(request, 'users/calendar.html', {
        'assignments': assignments
    })

def _teacher_access_denied(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.user.role != 'teacher' and not request.user.is_superuser:
        return redirect('/dashboard/')

    return None


def _teacher_context(user):
    teacher_courses = (Course.objects.filter(teacher=user) | Course.objects.filter(co_teachers=user)).distinct()
    teacher_assignments = Assignment.objects.filter(course__in=teacher_courses)
    teacher_submissions = Submission.objects.filter(assignment__in=teacher_assignments)
    pending_submissions = teacher_submissions.filter(status='pending')
    teacher_groups = StudentGroup.objects.filter(course__in=teacher_courses)
    teacher_modules = CourseModule.objects.filter(course__in=teacher_courses)
    library_items = LibraryItem.objects.filter(course__in=teacher_courses)
    schedule_events = ScheduleEvent.objects.filter(course__in=teacher_courses)
    quiz_attempts = QuizAttempt.objects.filter(
        quiz__course__in=teacher_courses
    ).select_related('quiz', 'student', 'quiz__course')[:20]

    return {
        'teacher_courses': teacher_courses,
        'teacher_assignments': teacher_assignments,
        'teacher_submissions': teacher_submissions,
        'pending_submissions': pending_submissions,
        'pending_submissions_count': pending_submissions.count(),
        'teacher_groups': teacher_groups,
        'teacher_modules': teacher_modules,
        'library_items': library_items,
        'schedule_events': schedule_events,
        'quiz_attempts': quiz_attempts,
    }


def _teacher_forms(user):
    return {
        'course_form': CourseForm(teacher=user),
        'module_form': CourseModuleForm(teacher=user),
        'lesson_form': LessonForm(teacher=user),
        'assignment_form': AssignmentForm(teacher=user),
        'group_form': StudentGroupForm(teacher=user),
        'quiz_form': QuizForm(teacher=user),
        'question_form': QuizQuestionForm(teacher=user),
        'library_form': LibraryItemForm(teacher=user),
        'schedule_form': ScheduleEventForm(teacher=user),
    }


def _handle_teacher_post(request, success_url, context):
    forms = _teacher_forms(request.user)
    action = request.POST.get('action')

    if action == 'course':
        forms['course_form'] = CourseForm(request.POST, teacher=request.user)

        if forms['course_form'].is_valid():
            course = forms['course_form'].save(commit=False)
            course.teacher = request.user
            course.save()
            forms['course_form'].save_m2m()
            return redirect(success_url)

    elif action == 'module':
        forms['module_form'] = CourseModuleForm(request.POST, teacher=request.user)

        if forms['module_form'].is_valid():
            forms['module_form'].save()
            return redirect(success_url)

    elif action == 'lesson':
        forms['lesson_form'] = LessonForm(
            request.POST,
            request.FILES,
            teacher=request.user
        )

        if forms['lesson_form'].is_valid():
            lesson = forms['lesson_form'].save()

            for student in lesson.course.students.all():
                Notification.objects.create(
                    user=student,
                    title='Новий урок',
                    text=f'У курсі "{lesson.course.title}" додано урок: {lesson.title}',
                    notification_type='course',
                    url=f'/courses/{lesson.course.id}/'
                )

            return redirect(success_url)

    elif action == 'assignment':
        forms['assignment_form'] = AssignmentForm(request.POST, teacher=request.user)

        if forms['assignment_form'].is_valid():
            assignment = forms['assignment_form'].save()

            for student in assignment.course.students.all():
                Notification.objects.create(
                    user=student,
                    title='Нове завдання',
                    text=f'У курсі "{assignment.course.title}" додано завдання: {assignment.title}',
                    notification_type='assignment',
                    url=f'/courses/assignment/{assignment.id}/submit/'
                )

            return redirect(success_url)

    elif action == 'group':
        forms['group_form'] = StudentGroupForm(request.POST, teacher=request.user)

        if forms['group_form'].is_valid():
            group = forms['group_form'].save()
            group.course.students.add(*group.students.all())
            return redirect(success_url)

    elif action == 'library':
        forms['library_form'] = LibraryItemForm(
            request.POST,
            request.FILES,
            teacher=request.user
        )

        if forms['library_form'].is_valid():
            forms['library_form'].save()
            return redirect(success_url)

    elif action == 'schedule':
        forms['schedule_form'] = ScheduleEventForm(request.POST, teacher=request.user)

        if forms['schedule_form'].is_valid():
            forms['schedule_form'].save()
            return redirect(success_url)

    elif action == 'quiz':
        forms['quiz_form'] = QuizForm(request.POST, teacher=request.user)

        if forms['quiz_form'].is_valid():
            forms['quiz_form'].save()
            return redirect(success_url)

    elif action == 'question':
        forms['question_form'] = QuizQuestionForm(request.POST, teacher=request.user)

        if forms['question_form'].is_valid():
            forms['question_form'].save()
            return redirect(success_url)

    elif action == 'review':
        submission_id = request.POST.get('submission_id')
        submission = Submission.objects.filter(
            id=submission_id,
            assignment__in=context['teacher_assignments']
        ).first()

        if submission:
            grade = request.POST.get('grade')
            teacher_comment = request.POST.get('teacher_comment', '')
            status = request.POST.get('status', 'pending')

            if grade:
                submission.grade = max(0, min(100, int(grade)))
                status = 'checked'
            else:
                submission.grade = None

            if status in ['pending', 'checked']:
                submission.status = status

            submission.teacher_comment = teacher_comment
            submission.save()

            Notification.objects.create(
                user=submission.student,
                title='Роботу перевірено',
                text=f'Виставлено оцінку за завдання: {submission.assignment.title}',
                notification_type='grade',
                url='/dashboard/'
            )

            return redirect(success_url)

    context.update(forms)
    return None


def teacher_dashboard(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)

    return render(request, 'users/teacher_dashboard.html', context)


def teacher_create_course(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-course/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_course.html', context)


def teacher_create_lesson(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-lesson/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_lesson.html', context)


def teacher_create_module(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-module/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_module.html', context)


def teacher_create_assignment(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-assignment/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_assignment.html', context)


def teacher_create_practice(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-practice/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_practice.html', context)


def teacher_create_group(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/create-group/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_create_group.html', context)


def teacher_library_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/library/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_library.html', context)


def teacher_schedule_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/schedule/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_schedule.html', context)


def teacher_create_test(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    context.update(_teacher_forms(request.user))

    if request.method == 'POST':
        course_id = request.POST.get('course')
        course = Course.objects.filter(
            id=course_id,
            teacher=request.user
        ).first() or Course.objects.filter(
            id=course_id,
            co_teachers=request.user
        ).first()

        if course:
            quiz = Quiz.objects.create(
                course=course,
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', '').strip(),
                time_limit=int(request.POST.get('time_limit') or 10),
                max_attempts=int(request.POST.get('max_attempts') or 3),
                show_correct_answers=bool(request.POST.get('show_correct_answers'))
            )

            question_numbers = request.POST.getlist('question_number')

            for number in question_numbers:
                text = request.POST.get(f'question_text_{number}', '').strip()

                if not text:
                    continue

                QuizQuestion.objects.create(
                    quiz=quiz,
                    text=text,
                    order=int(request.POST.get(f'question_order_{number}') or number),
                    option_1=request.POST.get(f'option_1_{number}', '').strip(),
                    option_2=request.POST.get(f'option_2_{number}', '').strip(),
                    option_3=request.POST.get(f'option_3_{number}', '').strip(),
                    option_4=request.POST.get(f'option_4_{number}', '').strip(),
                    correct_option=int(request.POST.get(f'correct_option_{number}') or 1)
                )

            for student in course.students.all():
                Notification.objects.create(
                    user=student,
                    title='Новий тест',
                    text=f'У курсі "{course.title}" додано тест: {quiz.title}',
                    notification_type='assignment',
                    url=f'/courses/quiz/{quiz.id}/take/'
                )

            return redirect('/teacher-dashboard/tests/')

    return render(request, 'users/teacher_create_test.html', context)


def teacher_courses_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    return render(
        request,
        'users/teacher_courses.html',
        _teacher_context(request.user)
    )


def teacher_groups_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    return render(
        request,
        'users/teacher_groups.html',
        _teacher_context(request.user)
    )


def teacher_reviews_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)

    if request.method == 'POST':
        response = _handle_teacher_post(
            request,
            '/teacher-dashboard/reviews/',
            context
        )

        if response:
            return response

    return render(request, 'users/teacher_reviews.html', context)


def teacher_tests_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    return render(
        request,
        'users/teacher_tests.html',
        _teacher_context(request.user)
    )


def teacher_analytics_page(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    rows = []

    for course in context['teacher_courses']:
        students_count = course.students.count()
        submissions = Submission.objects.filter(assignment__course=course)
        checked = submissions.filter(status='checked')
        quiz_attempts = QuizAttempt.objects.filter(quiz__course=course)
        grades = [item.grade for item in checked if item.grade is not None]
        grades += [item.percent for item in quiz_attempts]

        rows.append({
            'course': course,
            'students_count': students_count,
            'lessons_count': course.lessons.count(),
            'assignments_count': course.assignments.count(),
            'submissions_count': submissions.count(),
            'checked_count': checked.count(),
            'average_grade': round(sum(grades) / len(grades), 2) if grades else 0,
        })

    context['analytics_rows'] = rows

    return render(request, 'users/teacher_analytics.html', context)


def export_grades_csv(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    teacher_courses = (Course.objects.filter(teacher=request.user) | Course.objects.filter(co_teachers=request.user)).distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="grades.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Курс', 'Студент', 'Робота/тест', 'Тип', 'Оцінка', 'Статус'])

    for submission in Submission.objects.filter(assignment__course__in=teacher_courses).select_related('assignment', 'assignment__course', 'student'):
        writer.writerow([
            submission.assignment.course.title,
            submission.student.username,
            submission.assignment.title,
            submission.assignment.get_assignment_type_display(),
            submission.grade if submission.grade is not None else '',
            submission.get_status_display(),
        ])

    for attempt in QuizAttempt.objects.filter(quiz__course__in=teacher_courses).select_related('quiz', 'quiz__course', 'student'):
        writer.writerow([
            attempt.quiz.course.title,
            attempt.student.username,
            attempt.quiz.title,
            'Тест',
            attempt.percent,
            'Автоматично перевірено',
        ])

    return response


def import_students(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    context = _teacher_context(request.user)
    imported_count = 0
    error = ''

    if request.method == 'POST':
        course = Course.objects.filter(
            id=request.POST.get('course'),
            teacher=request.user
        ).first() or Course.objects.filter(
            id=request.POST.get('course'),
            co_teachers=request.user
        ).first()
        uploaded_file = request.FILES.get('students_file')

        if course and uploaded_file:
            rows = uploaded_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(rows)

            for row in reader:
                username = (row.get('username') or row.get('login') or '').strip()
                email = (row.get('email') or '').strip()

                if not username:
                    continue

                student, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'role': 'student',
                    }
                )

                if created:
                    student.set_unusable_password()
                    student.save()

                course.students.add(student)
                imported_count += 1
        else:
            error = 'Оберіть курс і CSV-файл з колонками username,email.'

    context['imported_count'] = imported_count
    context['error'] = error

    return render(request, 'users/import_students.html', context)


def course_report_pdf(request):
    denied = _teacher_access_denied(request)

    if denied:
        return denied

    teacher_courses = (Course.objects.filter(teacher=request.user) | Course.objects.filter(co_teachers=request.user)).distinct()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="course_report.pdf"'

    p = canvas.Canvas(response)
    y = 800
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, y, 'LMS Course Report')
    y -= 35
    p.setFont('Helvetica', 11)

    for course in teacher_courses:
        if y < 90:
            p.showPage()
            y = 800
            p.setFont('Helvetica', 11)

        submissions = Submission.objects.filter(assignment__course=course)
        attempts = QuizAttempt.objects.filter(quiz__course=course)
        p.drawString(40, y, f'Course: {course.title}')
        y -= 18
        p.drawString(60, y, f'Students: {course.students.count()} | Lessons: {course.lessons.count()} | Assignments: {course.assignments.count()}')
        y -= 18
        p.drawString(60, y, f'Submissions: {submissions.count()} | Quiz attempts: {attempts.count()}')
        y -= 26

    p.save()
    return response


def gradebook(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.user.role == 'teacher' or request.user.is_superuser:
        courses = (Course.objects.filter(teacher=request.user) | Course.objects.filter(co_teachers=request.user)).distinct()
        submissions = Submission.objects.filter(
            assignment__course__in=courses
        ).select_related('assignment', 'assignment__course', 'student')
        attempts = QuizAttempt.objects.filter(
            quiz__course__in=courses
        ).select_related('quiz', 'quiz__course', 'student')
    else:
        submissions = Submission.objects.filter(
            student=request.user
        ).select_related('assignment', 'assignment__course')
        attempts = QuizAttempt.objects.filter(
            student=request.user
        ).select_related('quiz', 'quiz__course')

    grades = [item.grade for item in submissions if item.grade is not None]
    grades += [item.percent for item in attempts]
    average_grade = round(sum(grades) / len(grades), 2) if grades else 0

    return render(request, 'users/gradebook.html', {
        'submissions': submissions,
        'attempts': attempts,
        'average_grade': average_grade
    })


def notifications(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    items = Notification.objects.filter(user=request.user)

    return render(request, 'users/notifications.html', {
        'notifications': items
    })


@require_POST
def mark_notification_read(request, notification_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()

    if notification.url:
        return redirect(notification.url)

    return redirect('/notifications/')


def group_detail(request, group_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    group = get_object_or_404(
        StudentGroup,
        id=group_id,
    )

    if not group.course.is_teacher(request.user):
        return redirect('/teacher-dashboard/groups/')

    student_rows = []

    for student in group.students.all():
        student_rows.append({
            'student': student,
            'progress': calculate_course_progress(student, group.course),
            'submissions': Submission.objects.filter(
                student=student,
                assignment__course=group.course
            ).count(),
            'lessons': LessonProgress.objects.filter(
                student=student,
                lesson__course=group.course
            ).count(),
        })

    return render(request, 'users/group_detail.html', {
        'group': group,
        'student_rows': student_rows
    })

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='mukovoz073@gmail.com',
        password='admin12345'
    )