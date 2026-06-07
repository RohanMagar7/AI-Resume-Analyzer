import logging
from collections import Counter

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from resume_parser.models import Resume
from resume_parser.parser_engine import analyze_resume
from .serializers import (
    ResumeUploadSerializer,
    ResumeListSerializer,
    ResumeDetailSerializer,
    ResumeAnalysisSerializer,
    DashboardStatsSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
def upload_resume(request):
    """
    Upload a resume file for analysis.
    Accepts PDF or DOCX files and returns analysis results.
    """
    serializer = ResumeUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    file = serializer.validated_data['file']
    target_role = serializer.validated_data.get('target_role', '')

    # Validate file type
    ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
    if ext not in ('pdf', 'docx'):
        return Response(
            {'error': 'Unsupported file type. Please upload a PDF or DOCX file.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        file_content = file.read()
        file_size = len(file_content)

        if file_size == 0:
            return Response(
                {'error': 'Uploaded file is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return Response(
                {'error': 'File size exceeds 10MB limit.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run analysis
        analysis_result = analyze_resume(file_content, ext)

        # Save to database
        resume = Resume.objects.create(
            original_filename=file.name,
            file_size=file_size,
            file_type=ext,
            parsed_text=analysis_result['parsed_text'],
            candidate_name=analysis_result['candidate_name'],
            email=analysis_result['email'],
            phone=analysis_result['phone'],
            extracted_skills=analysis_result['extracted_skills'],
            experience_years=analysis_result['experience_years'],
            education=analysis_result['education'],
            experience_list=analysis_result['experience_list'],
            ats_score=analysis_result['ats_score'],
            keyword_score=analysis_result['keyword_score'],
            format_score=analysis_result['format_score'],
            experience_score=analysis_result['experience_score'],
            education_score=analysis_result['education_score'],
            skills_match_score=analysis_result['skills_match_score'],
            content_distribution_score=analysis_result.get('content_distribution_score'),
            section_analysis=analysis_result.get('section_analysis', {}),
            projects_list=analysis_result.get('projects_list', []),
            improvement_suggestions=analysis_result.get('improvement_suggestions', []),
            suggested_roles=analysis_result['suggested_roles'],
            match_scores=analysis_result['match_scores'],
            status='completed',
        )

        # Save file to storage after analysis
        file.seek(0)
        resume.file.save(file.name, file, save=True)

        # Return results
        response_serializer = ResumeAnalysisSerializer({
            'id': resume.id,
            'candidate_name': resume.candidate_name,
            'email': resume.email,
            'phone': resume.phone,
            'extracted_skills': resume.extracted_skills,
            'experience_years': resume.experience_years,
            'education': resume.education,
            'experience_list': resume.experience_list,
            'ats_score': resume.ats_score,
            'keyword_score': resume.keyword_score,
            'format_score': resume.format_score,
            'experience_score': resume.experience_score,
            'education_score': resume.education_score,
            'skills_match_score': resume.skills_match_score,
            'content_distribution_score': resume.content_distribution_score,
            'section_analysis': resume.section_analysis,
            'suggested_roles': resume.suggested_roles,
            'match_scores': resume.match_scores,
            'status': resume.status,
            'created_at': resume.created_at,
        })

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    except ValueError as e:
        logger.error(f"Analysis error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during resume upload: {e}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred during analysis.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_resumes(request):
    """List all analyzed resumes with summary info. Uses pagination."""
    resumes = Resume.objects.all()
    status_filter = request.query_params.get('status', None)
    sort_by = request.query_params.get('sort', '-created_at')

    if status_filter:
        resumes = resumes.filter(status=status_filter)

    allowed_sort_fields = ['-created_at', 'created_at', '-ats_score', 'ats_score',
                           '-experience_years', 'experience_years', '-file_size']
    if sort_by in allowed_sort_fields:
        resumes = resumes.order_by(sort_by)

    # Use server-side pagination - only fetch one page from DB
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    page_size = min(page_size, 100)  # Cap page size to prevent abuse

    total = resumes.count()
    start = (page - 1) * page_size
    end = start + page_size
    page_resumes = resumes[start:end]

    serializer = ResumeListSerializer(page_resumes, many=True)
    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'results': serializer.data,
    })


@api_view(['GET'])
def get_resume_detail(request, pk):
    """Get detailed analysis results for a specific resume."""
    resume = get_object_or_404(Resume, pk=pk)
    serializer = ResumeDetailSerializer(resume)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_resume(request, pk):
    """Delete a resume record and its file."""
    resume = get_object_or_404(Resume, pk=pk)
    resume.file.delete(save=False)  # Delete the file from storage
    resume.delete()
    return Response({'message': 'Resume deleted successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def dashboard_stats(request):
    """Get aggregate statistics for the analytics dashboard."""
    resumes = Resume.objects.filter(status='completed')

    total = resumes.count()
    if total == 0:
        return Response({
            'total_resumes': 0,
            'avg_ats_score': 0,
            'avg_experience_years': 0,
            'top_skills': [],
            'score_distribution': {
                'excellent': 0, 'good': 0, 'average': 0, 'poor': 0,
            },
            'recent_analyses': [],
            'role_distribution': {},
        })

    # Use ORM aggregation instead of loading all records into memory
    agg = resumes.aggregate(
        avg_ats=Avg('ats_score'),
        avg_exp=Avg('experience_years')
    )
    avg_ats = agg['avg_ats'] or 0
    avg_exp = agg['avg_exp'] or 0

    # Top skills - use iterator to avoid loading all into memory at once
    # Still needs Python processing since skills are JSONField, but uses iterator
    all_skills = Counter()
    role_counter = Counter()
    distribution = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}

    resume_iterator = resumes.only(
        'extracted_skills', 'ats_score', 'suggested_roles'
    ).iterator()

    for resume in resume_iterator:
        all_skills.update(resume.extracted_skills)
        for role in resume.suggested_roles:
            role_counter[role] += 1
        score = resume.ats_score or 0
        if score >= 80:
            distribution['excellent'] += 1
        elif score >= 60:
            distribution['good'] += 1
        elif score >= 40:
            distribution['average'] += 1
        else:
            distribution['poor'] += 1

    top_skills = [skill for skill, _ in all_skills.most_common(15)]

    recent = resumes.order_by('-created_at')[:5]
    recent_serializer = ResumeListSerializer(recent, many=True)

    return Response({
        'total_resumes': total,
        'avg_ats_score': round(avg_ats, 2),
        'avg_experience_years': round(avg_exp, 1),
        'top_skills': top_skills,
        'score_distribution': distribution,
        'recent_analyses': recent_serializer.data,
        'role_distribution': dict(role_counter.most_common(10)),
    })


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint."""
    return Response({'status': 'healthy', 'service': 'AI Resume Analyzer API'})