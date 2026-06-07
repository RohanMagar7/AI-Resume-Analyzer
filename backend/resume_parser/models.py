import uuid
import os
from django.db import models
from django.utils import timezone


def resume_upload_path(instance, filename):
    """Generate upload path for resume files."""
    ext = filename.split('.')[-1] if '.' in filename else 'pdf'
    return f'resumes/{instance.id}/{instance.id}.{ext}'


class Resume(models.Model):
    """Model representing an uploaded resume and its analysis results."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=resume_upload_path, max_length=500)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    file_type = models.CharField(max_length=10, default='pdf')

    # Parsed content
    parsed_text = models.TextField(blank=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    # Analysis results
    extracted_skills = models.JSONField(default=list, blank=True)
    experience_years = models.FloatField(null=True, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience_list = models.JSONField(default=list, blank=True)

    # ATS Score components
    ats_score = models.FloatField(null=True, blank=True)
    keyword_score = models.FloatField(null=True, blank=True)
    format_score = models.FloatField(null=True, blank=True)
    experience_score = models.FloatField(null=True, blank=True)
    education_score = models.FloatField(null=True, blank=True)
    skills_match_score = models.FloatField(null=True, blank=True)
    content_distribution_score = models.FloatField(null=True, blank=True, help_text="Score for how well content is balanced across resume sections")

    # Section analysis (V2)
    section_analysis = models.JSONField(default=dict, blank=True, help_text="Detailed section detection and quality analysis data")

    # Projects
    projects_list = models.JSONField(default=list, blank=True, help_text="Extracted project entries from resume")

    # Improvement suggestions (V3)
    improvement_suggestions = models.JSONField(default=list, blank=True, help_text="Actionable suggestions to improve the resume")

    # Job role matching
    suggested_roles = models.JSONField(default=list, blank=True)
    match_scores = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} - ATS: {self.ats_score}"


class SkillDatabase(models.Model):
    """Database of known skills and their categories for matching."""

    CATEGORY_CHOICES = [
        ('programming', 'Programming Language'),
        ('framework', 'Framework / Library'),
        ('database', 'Database'),
        ('cloud', 'Cloud / DevOps'),
        ('tool', 'Tool / Platform'),
        ('soft_skill', 'Soft Skill'),
        ('domain', 'Domain Knowledge'),
        ('language', 'Language'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    aliases = models.JSONField(default=list, blank=True, help_text="Alternative names for this skill")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class JobRole(models.Model):
    """Predefined job roles with required skills for matching."""

    title = models.CharField(max_length=200, unique=True)
    required_skills = models.JSONField(default=list, help_text="List of skill names required for this role")
    preferred_skills = models.JSONField(default=list, blank=True, help_text="List of preferred skill names")
    min_experience = models.IntegerField(default=0, help_text="Minimum years of experience")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title