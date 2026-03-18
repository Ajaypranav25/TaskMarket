from django.contrib import admin
from .models import Level, UserProfile, Task, Submission


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level_number', 'name', 'min_avg_score', 'min_submissions', 'reward_multiplier']
    ordering = ['level_number']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'level', 'avg_score', 'total_submissions', 'total_earnings']
    list_filter = ['role', 'level']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'category', 'reward', 'status', 'submission_count', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['title', 'description']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['worker', 'task', 'ai_score', 'status', 'earnings', 'submitted_at']
    list_filter = ['status']
