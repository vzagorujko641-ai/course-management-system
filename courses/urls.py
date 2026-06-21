from django.urls import path
from . import views


urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course),
    path('<int:course_id>/favorite/', views.toggle_favorite_course, name='toggle_favorite_course'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment),
    path('<int:course_id>/send-message/', views.send_message),
    path('<int:course_id>/get-messages/', views.get_messages),
    path('message/<int:message_id>/like/', views.toggle_message_like, name='toggle_message_like'),
    path('message/<int:message_id>/pin/', views.toggle_message_pin, name='toggle_message_pin'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
   path('<int:course_id>/generate-certificate/', views.generate_certificate, name='generate_certificate'),
   path('lesson/<int:lesson_id>/complete/', views.complete_lesson),
]
