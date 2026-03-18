from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/company/', views.company_dashboard, name='company_dashboard'),

    path('tasks/', views.task_list, name='task_list'),
    path('tasks/post/', views.post_task, name='post_task'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/submit/', views.submit_task, name='submit_task'),
    path('tasks/<int:pk>/close/', views.close_task, name='close_task'),
    path('tasks/<int:pk>/submissions/', views.task_submissions, name='task_submissions'),

    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),

    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
