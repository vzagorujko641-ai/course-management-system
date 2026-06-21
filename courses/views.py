from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import (
    Course,
    Lesson,
    LessonProgress,
    Assignment,
    Submission,
    Category,
    Tag,
    Message,
    FavoriteCourse,
    StudentGroup,
    Quiz,
    QuizAttempt,
    Notification,
)
from .forms import SubmissionReviewForm
from users.forms import validate_uploaded_file

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

from datetime import datetime
import os
import csv


def user_can_open_course(user, course):
    if course.is_visible and getattr(course, 'status', 'published') == 'published':
        return True

    return (
        user.is_authenticated
        and course.is_teacher(user)
    )


def user_is_enrolled_or_owner(user, course):
    if not user.is_authenticated:
        return False

    return (
        course.students.filter(id=user.id).exists()
        or course.is_teacher(user)
    )


def user_is_enrolled_student(user, course):
    return (
        user.is_authenticated
        and user.role == 'student'
        and course.students.filter(id=user.id).exists()
    )


def redirect_to_safe_next(request, fallback_url):
    next_url = request.POST.get('next') or request.GET.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)

    return redirect(fallback_url)


def calculate_course_progress(user, course):
    total_assignments = course.assignments.count()
    total_lessons = course.lessons.count()
    total_items = total_assignments + total_lessons

    if total_items == 0 or not user.is_authenticated:
        return 0

    completed_assignments = Submission.objects.filter(
        student=user,
        assignment__course=course
    ).values('assignment').distinct().count()

    completed_lessons = LessonProgress.objects.filter(
        student=user,
        lesson__course=course
    ).values('lesson').distinct().count()

    return int(((completed_assignments + completed_lessons) / total_items) * 100)


def course_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    teacher_id = request.GET.get('teacher', '')
    tag_id = request.GET.get('tag', '')
    only_my = request.GET.get('my', '')
    only_favorite = request.GET.get('favorite', '')

    all_courses = Course.objects.all().order_by('category__name', 'title')

    if not request.user.is_authenticated or not request.user.is_superuser:
        all_courses = all_courses.filter(is_visible=True, status='published')

    if category_id:
        all_courses = all_courses.filter(category_id=category_id)

    if teacher_id:
        all_courses = all_courses.filter(teacher_id=teacher_id) | all_courses.filter(co_teachers__id=teacher_id)

    if tag_id:
        all_courses = all_courses.filter(tags__id=tag_id)

    if request.user.is_authenticated and only_my:
        all_courses = all_courses.filter(students=request.user)

    if request.user.is_authenticated and only_favorite:
        all_courses = all_courses.filter(favorite_marks__student=request.user)

    if query:
        normalized_query = query.casefold()
        courses = []

        for course in all_courses.prefetch_related('lessons', 'assignments'):
            searchable_text = ' '.join([
                course.title,
                course.description,
                ' '.join(lesson.title for lesson in course.lessons.all()),
                ' '.join(lesson.content for lesson in course.lessons.all()),
                ' '.join(assignment.title for assignment in course.assignments.all()),
                ' '.join(assignment.description for assignment in course.assignments.all()),
            ])

            if normalized_query in searchable_text.casefold():
                courses.append(course)
    else:
        courses = all_courses

    favorite_course_ids = []

    if request.user.is_authenticated:
        favorite_course_ids = FavoriteCourse.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)

    categories = Category.objects.all()
    tags = Tag.objects.all()
    teachers = Course.objects.values(
        'teacher_id',
        'teacher__username'
    ).distinct().order_by('teacher__username')

    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'query': query,
        'categories': categories,
        'category_id': category_id,
        'teacher_id': teacher_id,
        'tag_id': tag_id,
        'teachers': teachers,
        'tags': tags,
        'only_my': only_my,
        'only_favorite': only_favorite,
        'favorite_course_ids': favorite_course_ids
    })


def course_detail(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    if not user_can_open_course(request.user, course):
        return render(request, 'courses/access_denied.html', {
            'course': course,
            'reason': 'Курс зараз недоступний для перегляду.'
        }, status=403)

    modules = course.modules.prefetch_related('lessons').all()
    lessons = course.lessons.select_related('module').prefetch_related('images').all().order_by('order', 'id')
    quizzes = course.quizzes.all().order_by('created_at')
    library_items = course.library_items.all()
    schedule_events = course.schedule_events.all()[:8]
    total_lessons = course.lessons.count()
    total_assignments = course.assignments.count()
    total_quizzes = course.quizzes.count()
    students_count = course.students.count()

    is_enrolled = False
    can_chat = False
    enroll_error = ''

    if request.GET.get('enroll_error'):
        enroll_error = 'Неправильний пароль для запису на курс або групу.'

    if request.user.is_authenticated:

        is_enrolled = course.students.filter(
            id=request.user.id
        ).exists()

        if user_is_enrolled_or_owner(request.user, course):
            can_chat = True

    if request.method == 'POST' and can_chat:

        text = request.POST.get('text')
        uploaded_file = request.FILES.get('file')
        reply_to_id = request.POST.get('reply_to')
        reply_to = None

        if reply_to_id:
            reply_to = Message.objects.filter(
                id=reply_to_id,
                course=course
            ).first()

            if reply_to and reply_to.author == request.user:
                reply_to = None

        try:
            validate_uploaded_file(uploaded_file, {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'})
        except Exception as error:
            return HttpResponse(str(error), status=400)

        if text or uploaded_file:
            Message.objects.create(
                course=course,
                author=request.user,
                text=text,
                file=uploaded_file,
                reply_to=reply_to
            )

    if request.user.is_authenticated:

        if course.is_teacher(request.user):

            messages = course.messages.select_related('author', 'reply_to', 'reply_to__author').prefetch_related('likes').order_by(
                '-is_pinned',
                'created_at'
            )

        else:

            messages = course.messages.select_related('author', 'reply_to', 'reply_to__author').prefetch_related('likes').filter(
                author=request.user
            ).order_by('-is_pinned', 'created_at')

    else:

        messages = []

    progress = calculate_course_progress(request.user, course)
    certificate_available = progress == 100

    completed_lessons = []
    is_favorite = False

    if request.user.is_authenticated:

        completed_lessons = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course
        ).values_list('lesson_id', flat=True)

        is_favorite = FavoriteCourse.objects.filter(
            student=request.user,
            course=course
        ).exists()

    return render(request, 'courses/course_detail.html', {

        'course': course,
        'lessons': lessons,
        'modules': modules,
        'quizzes': quizzes,
        'library_items': library_items,
        'schedule_events': schedule_events,
        'total_lessons': total_lessons,
        'total_assignments': total_assignments,
        'total_quizzes': total_quizzes,
        'students_count': students_count,

        'is_enrolled': is_enrolled,
        'enroll_error': enroll_error,

        'can_chat': can_chat,

        'messages': messages,

        'progress': progress,

        'completed_lessons': completed_lessons,

        'certificate_available': certificate_available,
        'is_favorite': is_favorite

    })


@require_POST
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not request.user.is_authenticated:
        return redirect('/login/')

    if not user_can_open_course(request.user, course):
        return render(request, 'courses/access_denied.html', {
            'course': course,
            'reason': 'Курс приховано або архівовано.'
        }, status=403)

    access_password = request.POST.get('access_password', '')
    matched_group = None

    if course.enrollment_password and access_password == course.enrollment_password:
        course.students.add(request.user)
        Notification.objects.create(
            user=course.teacher,
            title='Новий студент на курсі',
            text=f'{request.user.username} записався/записалась на курс "{course.title}".',
            notification_type='course',
            url=f'/courses/{course.id}/'
        )
        return redirect(f'/courses/{course.id}/')

    matched_group = StudentGroup.objects.filter(
        course=course,
        enrollment_password=access_password
    ).first()

    if matched_group and matched_group.enrollment_password:
        course.students.add(request.user)
        matched_group.students.add(request.user)
        Notification.objects.create(
            user=course.teacher,
            title='Новий студент у групі',
            text=f'{request.user.username} приєднався/приєдналась до групи "{matched_group.name}".',
            notification_type='course',
            url=f'/groups/{matched_group.id}/'
        )
        return redirect(f'/courses/{course.id}/')

    if not course.enrollment_password and not course.student_groups.exclude(enrollment_password='').exists():
        course.students.add(request.user)
        Notification.objects.create(
            user=course.teacher,
            title='Новий студент на курсі',
            text=f'{request.user.username} записався/записалась на курс "{course.title}".',
            notification_type='course',
            url=f'/courses/{course.id}/'
        )
        return redirect(f'/courses/{course.id}/')

    return redirect(f'/courses/{course.id}/?enroll_error=1')


@require_POST
def toggle_favorite_course(request, course_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    course = get_object_or_404(Course, id=course_id)

    if not user_can_open_course(request.user, course):
        return HttpResponseForbidden('Курс недоступний.')

    favorite = FavoriteCourse.objects.filter(
        student=request.user,
        course=course
    ).first()

    if favorite:
        favorite.delete()
    else:
        FavoriteCourse.objects.create(
            student=request.user,
            course=course
        )

    return redirect_to_safe_next(request, f'/courses/{course.id}/')


@require_POST
def toggle_message_like(request, message_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    message = get_object_or_404(Message, id=message_id)

    if not user_is_enrolled_or_owner(request.user, message.course):
        return HttpResponseForbidden('Немає доступу до чату курсу.')

    if message.likes.filter(id=request.user.id).exists():
        message.likes.remove(request.user)
    else:
        message.likes.add(request.user)

    return redirect(f'/courses/{message.course.id}/')


@require_POST
def toggle_message_pin(request, message_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    message = get_object_or_404(Message, id=message_id)

    if (
        message.course.is_teacher(request.user)
    ):
        message.is_pinned = not message.is_pinned
        message.save()

    return redirect(f'/courses/{message.course.id}/')


def take_quiz(request, quiz_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    is_enrolled = course.students.filter(id=request.user.id).exists()

    if not is_enrolled and not course.is_teacher(request.user):
        return redirect(f'/courses/{course.id}/')

    questions = quiz.questions.prefetch_related('options').all()
    attempts_used = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user
    ).count()

    if attempts_used >= quiz.max_attempts and not course.is_teacher(request.user):
        return render(request, 'courses/quiz_result.html', {
            'quiz': quiz,
            'attempt': QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user
            ).first(),
            'attempt_limit_reached': True,
            'questions': questions
        })

    if request.method == 'POST':
        started_at_iso = request.session.get(f'quiz_started_at_{quiz.id}')
        time_spent_seconds = 0

        if started_at_iso:
            started_at = datetime.fromisoformat(started_at_iso)
            time_spent_seconds = int((timezone.now() - started_at).total_seconds())

            if time_spent_seconds > quiz.time_limit * 60 and not course.is_teacher(request.user):
                return HttpResponse(
                    'Час на виконання тесту вичерпано.',
                    status=403
                )

        total_questions = questions.count()
        score = 0
        selected_answers = {}

        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            selected_answers[question.id] = selected_option

            if selected_option and selected_option.isdigit() and int(selected_option) == question.correct_option:
                score += 1

        percent = 0

        if total_questions > 0:
            percent = int((score / total_questions) * 100)

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            score=score,
            total_questions=total_questions,
            percent=percent,
            time_spent_seconds=time_spent_seconds
        )

        request.session.pop(f'quiz_started_at_{quiz.id}', None)

        result_rows = []

        for question in questions:
            selected_option = selected_answers.get(question.id)
            result_rows.append({
                'question': question,
                'selected_option': selected_option,
                'is_correct': selected_option and selected_option.isdigit() and int(selected_option) == question.correct_option
            })

        return render(request, 'courses/quiz_result.html', {
            'quiz': quiz,
            'attempt': attempt,
            'result_rows': result_rows
        })

    request.session[f'quiz_started_at_{quiz.id}'] = timezone.now().isoformat()

    return render(request, 'courses/take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'attempts_used': attempts_used,
        'attempts_left': max(quiz.max_attempts - attempts_used, 0),
        'time_limit_seconds': quiz.time_limit * 60
    })


def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if not request.user.is_authenticated:
        return redirect('/login/')

    if not user_is_enrolled_student(request.user, assignment.course):
        return HttpResponseForbidden('Завдання доступне тільки студентам курсу.')

    today = timezone.localdate()

    if (
        assignment.deadline
        and assignment.deadline < today
        and not assignment.allow_late_submissions
    ):
        return HttpResponse(
            'Термін здачі завдання минув.',
            status=403
        )

    if request.method == 'POST':
        answer = request.POST.get('answer')
        uploaded_file = request.FILES.get('file')

        try:
            validate_uploaded_file(uploaded_file, {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'zip'})
        except Exception as error:
            return HttpResponse(str(error), status=400)

        Submission.objects.create(
            assignment=assignment,
            student=request.user,
            answer=answer,
            file=uploaded_file,
            is_late=bool(assignment.deadline and assignment.deadline < today)
        )

        Notification.objects.create(
            user=assignment.course.teacher,
            title='Нова відповідь на завдання',
            text=f'{request.user.username} відправив(ла) роботу: {assignment.title}',
            notification_type='assignment',
            url=f'/teacher-dashboard/'
        )

        return redirect(f'/courses/{assignment.course.id}/')

    return render(request, 'courses/submit_assignment.html', {
        'assignment': assignment
    })


def send_message(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if (
        request.method == 'POST'
        and request.user.is_authenticated
        and user_is_enrolled_or_owner(request.user, course)
    ):
        text = request.POST.get('text')
        uploaded_file = request.FILES.get('file')
        reply_to_id = request.POST.get('reply_to')
        reply_to = None

        if reply_to_id:
            reply_to = Message.objects.filter(
                id=reply_to_id,
                course=course
            ).first()

            if reply_to and reply_to.author == request.user:
                reply_to = None

        try:
            validate_uploaded_file(uploaded_file, {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'})
        except Exception as error:
            return JsonResponse({'error': str(error)}, status=400)

        if text or uploaded_file:
            message = Message.objects.create(
                course=course,
                author=request.user,
                text=text,
                file=uploaded_file,
                reply_to=reply_to
            )

            return JsonResponse({
                'author': message.author.username,
                'text': message.text,
                'created_at': message.created_at.strftime('%d.%m.%Y %H:%M')
            })

    return JsonResponse({'error': 'Помилка'}, status=400)


def get_messages(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not user_is_enrolled_or_owner(request.user, course):
        return JsonResponse({'messages': []})

    if request.user.is_authenticated:
        if request.user == course.teacher or request.user.is_superuser:
            messages = course.messages.all().order_by('created_at')
        else:
            messages = course.messages.filter(
                author=request.user
            ).order_by('created_at')
    else:
        messages = []

    data = []

    for message in messages:
        data.append({
            'author': message.author.username,
            'text': message.text,
            'file_url': message.file.url if message.file else '',
            'likes_count': message.likes.count(),
            'is_pinned': message.is_pinned,
            'created_at': message.created_at.strftime('%d.%m.%Y %H:%M')
        })

    return JsonResponse({'messages': data})


def generate_certificate(request, course_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    course = get_object_or_404(Course, id=course_id)

    if not user_is_enrolled_student(request.user, course):
        return render(request, 'courses/certificate_status.html', {
            'course': course,
            'progress': 0,
            'certificate_available': False,
            'message': 'Сертифікат доступний тільки студентам цього курсу.'
        }, status=403)

    progress = calculate_course_progress(request.user, course)

    if progress < 100:
        return render(request, 'courses/certificate_status.html', {
            'course': course,
            'progress': progress,
            'certificate_available': False,
            'message': 'Сертифікат відкриється після 100% проходження курсу.'
        }, status=403)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="certificate_{course.id}.pdf"'
    )

    page_size = landscape(A4)

    p = canvas.Canvas(response, pagesize=page_size)
    width, height = page_size

    template_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'images',
        'certificate_template.png'
    )

    p.drawImage(
        template_path,
        0,
        0,
        width=width,
        height=height,
        preserveAspectRatio=True,
        anchor='c'
    )

    pdfmetrics.registerFont(
        TTFont('Arial', 'C:/Windows/Fonts/arial.ttf')
    )

    pdfmetrics.registerFont(
        TTFont('ArialBold', 'C:/Windows/Fonts/arialbd.ttf')
    )

    p.setFillColorRGB(0.45, 0.12, 0.08)
    p.setFont("ArialBold", 33)

    p.drawCentredString(
        width / 2 - 120,
        305,
        request.user.username
    )

    p.setFillColorRGB(0.15, 0.15, 0.15)
    p.setFont("ArialBold", 24)

    p.drawCentredString(
        width / 2 - 120,
        178,
        course.title
    )

    p.setFont("Arial", 16)

    p.drawCentredString(
        width / 2 - 120,
        38,
        datetime.now().strftime('%d.%m.%Y')
    )

    certificate_number = f'LMS-{course.id}-{request.user.id}-{datetime.now().strftime("%Y%m%d")}'

    p.setFillColorRGB(0.25, 0.25, 0.25)
    p.setFont("Arial", 12)

    p.drawString(
        width - 250,
        38,
        f'№ {certificate_number}'
    )

    qr = QrCodeWidget(certificate_number)
    bounds = qr.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(
        76,
        76,
        transform=[76 / qr_width, 0, 0, 76 / qr_height, 0, 0]
    )
    drawing.add(qr)
    renderPDF.draw(drawing, p, width - 120, 68)

    p.showPage()
    p.save()

    return response


@require_POST
def complete_lesson(request, lesson_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    lesson = get_object_or_404(Lesson, id=lesson_id)

    if not user_is_enrolled_student(request.user, lesson.course):
        return HttpResponseForbidden('Урок доступний тільки студентам курсу.')

    LessonProgress.objects.get_or_create(
        lesson=lesson,
        student=request.user
    )

    return redirect(f'/courses/{lesson.course.id}/')


def review_submission(request, submission_id):
    if not request.user.is_authenticated:
        return redirect('/login/')

    submission = get_object_or_404(
        Submission,
        id=submission_id,
    )

    if not submission.assignment.course.is_teacher(request.user):
        return HttpResponseForbidden('Немає доступу до перевірки цієї роботи.')

    if request.method == 'POST':
        form = SubmissionReviewForm(request.POST, instance=submission)

        if form.is_valid():
            reviewed_submission = form.save(commit=False)

            if reviewed_submission.grade is not None:
                reviewed_submission.grade = max(0, min(100, reviewed_submission.grade))
                reviewed_submission.status = 'checked'

            reviewed_submission.save()

            Notification.objects.create(
                user=reviewed_submission.student,
                title='Роботу перевірено',
                text=f'Викладач перевірив завдання: {reviewed_submission.assignment.title}',
                notification_type='grade',
                url='/dashboard/'
            )

    return redirect('/teacher-dashboard/')
