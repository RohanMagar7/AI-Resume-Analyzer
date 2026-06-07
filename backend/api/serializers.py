from rest_framework import serializers
from resume_parser.models import Resume


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer for uploading a resume file."""
    file = serializers.FileField(help_text="Resume file (PDF or DOCX)")
    target_role = serializers.CharField(required=False, allow_blank=True, max_length=200,
                                         help_text="Optional target job role for specific matching")


class ResumeListSerializer(serializers.ModelSerializer):
    """Serializer for listing resumes (summary view)."""

    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_size', 'file_type',
            'candidate_name', 'email', 'ats_score',
            'status', 'extracted_skills', 'experience_years',
            'created_at',
        ]


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed resume view including all analysis."""

    class Meta:
        model = Resume
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResumeAnalysisSerializer(serializers.Serializer):
    """Serializer for returning analysis results."""
    id = serializers.UUIDField()
    candidate_name = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    extracted_skills = serializers.ListField(child=serializers.CharField())
    experience_years = serializers.FloatField()
    education = serializers.ListField()
    experience_list = serializers.ListField()
    ats_score = serializers.FloatField()
    keyword_score = serializers.FloatField()
    format_score = serializers.FloatField()
    experience_score = serializers.FloatField()
    education_score = serializers.FloatField()
    skills_match_score = serializers.FloatField()
    content_distribution_score = serializers.FloatField(required=False, allow_null=True)
    section_analysis = serializers.DictField(required=False, default=dict)
    projects_list = serializers.ListField(required=False, default=list)
    improvement_suggestions = serializers.ListField(required=False, default=list)
    suggested_roles = serializers.ListField(child=serializers.CharField())
    match_scores = serializers.ListField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    total_resumes = serializers.IntegerField()
    avg_ats_score = serializers.FloatField()
    avg_experience_years = serializers.FloatField()
    top_skills = serializers.ListField()
    score_distribution = serializers.DictField()
    recent_analyses = ResumeListSerializer(many=True)
    role_distribution = serializers.DictField()