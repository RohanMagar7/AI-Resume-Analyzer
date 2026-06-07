from django.contrib import admin
from .models import Resume, SkillDatabase, JobRole


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'status', 'ats_score', 'candidate_name', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['original_filename', 'candidate_name', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(SkillDatabase)
class SkillDatabaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ['title', 'min_experience']
    search_fields = ['title']