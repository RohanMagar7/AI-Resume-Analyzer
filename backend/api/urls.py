from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('upload/', views.upload_resume, name='upload-resume'),
    path('resumes/', views.list_resumes, name='list-resumes'),
    path('resumes/<uuid:pk>/', views.get_resume_detail, name='resume-detail'),
    path('resumes/<uuid:pk>/delete/', views.delete_resume, name='delete-resume'),
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),
]