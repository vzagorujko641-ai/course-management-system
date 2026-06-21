from django.contrib import admin
from .models import (
    Category,
    Course,
    CourseModule,
    Lesson,
    LessonImage,
    LessonProgress,
    Assignment,
    Submission,
    Message,
    FavoriteCourse,
    StudentGroup,
    Quiz,
    QuizQuestion,
    QuizAnswerOption,
    QuizAttempt,
    Notification,
    LibraryItem,
    ScheduleEvent,
    Tag,
)

admin.site.site_header = 'EduCourse | Адміністрування'
admin.site.site_title = 'EduCourse Admin'
admin.site.index_title = 'Панель керування навчальним порталом'


class CasefoldSearchMixin:

    casefold_search_fields = ()

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request,
            queryset,
            search_term
        )

        if not search_term or not self.casefold_search_fields:
            return queryset, may_have_duplicates

        normalized_search = search_term.casefold()
        base_queryset = self.model.objects.all()
        matched_ids = []

        for item in base_queryset:
            values = []

            for field_path in self.casefold_search_fields:
                value = item

                for field_name in field_path.split('__'):
                    value = getattr(value, field_name, '')

                    if value is None:
                        value = ''
                        break

                values.append(str(value))

            if normalized_search in ' '.join(values).casefold():
                matched_ids.append(item.id)

        if matched_ids:
            queryset = queryset | self.model.objects.filter(id__in=matched_ids)

        return queryset.distinct(), may_have_duplicates


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'category')
    ordering = ('order', 'id')
    classes = ('collapse',)
    show_change_link = True


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    fields = ('title', 'deadline', 'allow_late_submissions')
    classes = ('collapse',)
    show_change_link = True


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0
    fields = ('title', 'time_limit', 'max_attempts', 'show_correct_answers')
    classes = ('collapse',)
    show_change_link = True


class StudentGroupInline(admin.TabularInline):
    model = StudentGroup
    extra = 0
    fields = ('name', 'enrollment_password', 'students')
    filter_horizontal = ('students',)
    classes = ('collapse',)
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(CasefoldSearchMixin, admin.ModelAdmin):
    search_fields = ('name',)
    casefold_search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(CasefoldSearchMixin, admin.ModelAdmin):
    search_fields = ('name',)
    casefold_search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(CasefoldSearchMixin, admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'status', 'is_visible', 'created_at')
    list_filter = ('status', 'is_visible', 'category', 'teacher')
    search_fields = ('title', 'description')
    casefold_search_fields = ('title', 'description', 'category__name', 'teacher__username')
    autocomplete_fields = ('category', 'teacher')
    filter_horizontal = ('students', 'co_teachers', 'tags')
    inlines = [StudentGroupInline, LessonInline, AssignmentInline, QuizInline]
    actions = ('hide_courses', 'show_courses')
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Викладачі та студенти', {
            'fields': ('teacher', 'co_teachers', 'students')
        }),
        ('Доступ до курсу', {
            'fields': ('status', 'is_visible', 'enrollment_password')
        }),
    )

    @admin.action(description='Сховати вибрані курси')
    def hide_courses(self, request, queryset):
        queryset.update(is_visible=False, status='hidden')

    @admin.action(description='Показати вибрані курси')
    def show_courses(self, request, queryset):
        queryset.update(is_visible=True, status='published')


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    fields = (
        'order',
        'text',
        'option_1',
        'option_2',
        'option_3',
        'option_4',
        'correct_option',
    )
    ordering = ('order', 'id')
    classes = ('collapse',)


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')


@admin.register(LessonImage)
class LessonImageAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'caption')
    search_fields = ('caption', 'lesson__title')


@admin.register(Quiz)
class QuizAdmin(CasefoldSearchMixin, admin.ModelAdmin):
    list_display = ('title', 'course', 'time_limit', 'max_attempts', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    casefold_search_fields = ('title', 'description', 'course__title')
    autocomplete_fields = ('course',)
    inlines = [QuizQuestionInline]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'assignment_type', 'deadline', 'allow_late_submissions')
    list_filter = ('assignment_type', 'course', 'allow_late_submissions')
    search_fields = ('title', 'description', 'course__title')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'module', 'order', 'category')
    list_filter = ('course', 'module', 'category')
    search_fields = ('title', 'content', 'course__title')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'grade', 'submitted_at')
    list_filter = ('status', 'assignment__course')
    search_fields = ('assignment__title', 'student__username', 'answer')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('course', 'author', 'is_pinned', 'created_at')
    list_filter = ('course', 'is_pinned')
    search_fields = ('text', 'author__username')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'score', 'total_questions', 'percent', 'finished_at')
    list_filter = ('quiz', 'student')
    search_fields = ('quiz__title', 'student__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'text', 'user__username')


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'material_type', 'created_at')
    list_filter = ('course', 'material_type')
    search_fields = ('title', 'description', 'course__title')


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'starts_at', 'location')
    list_filter = ('course', 'starts_at')
    search_fields = ('title', 'course__title', 'location')


# Category, lesson, assignment, lesson progress, favorite course,
# quiz question and answer option models are intentionally managed through
# course/test pages, not as separate sidebar sections in the admin.
