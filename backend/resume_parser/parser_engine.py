"""
Core resume parsing engine with NLP-based skill extraction, ATS scoring,
and job role matching capabilities.

Version 2.0 - Improved section detection and distribution analysis for
higher ATS accuracy.
"""
import re
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import PyPDF2
import docx
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Lazy NLTK data initialization - downloaded once when first needed, not at import time
_nltk_initialized = False

def _ensure_nltk_data():
    """Download NLTK data on first use rather than at import time."""
    global _nltk_initialized
    if _nltk_initialized:
        return
    for resource in ['tokenizers/punkt', 'corpora/stopwords']:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(resource.split('/')[-1], quiet=True)
    _nltk_initialized = True

# Comprehensive skill database with categories
SKILL_DATABASE = {
    # Programming Languages
    'python': 'programming', 'javascript': 'programming', 'java': 'programming',
    'c++': 'programming', 'c#': 'programming', 'ruby': 'programming',
    'go': 'programming', 'rust': 'programming', 'swift': 'programming',
    'kotlin': 'programming', 'typescript': 'programming', 'php': 'programming',
    'scala': 'programming', 'perl': 'programming', 'r': 'programming',
    'sql': 'programming', 'html': 'programming', 'css': 'programming',
    'bash': 'programming', 'shell': 'programming', 'powershell': 'programming',
    'dart': 'programming', 'lua': 'programming', 'haskell': 'programming',

    # Frameworks & Libraries
    'django': 'framework', 'flask': 'framework', 'fastapi': 'framework',
    'react': 'framework', 'angular': 'framework', 'vue': 'framework',
    'node.js': 'framework', 'express': 'framework', 'spring': 'framework',
    'spring boot': 'framework', 'rails': 'framework', 'laravel': 'framework',
    'asp.net': 'framework', '.net': 'framework', 'tensorflow': 'framework',
    'pytorch': 'framework', 'keras': 'framework', 'scikit-learn': 'framework',
    'pandas': 'framework', 'numpy': 'framework', 'jquery': 'framework',
    'bootstrap': 'framework', 'tailwind': 'framework', 'redux': 'framework',
    'next.js': 'framework', 'nuxt.js': 'framework', 'sass': 'framework',
    'less': 'framework', 'graphql': 'framework', 'rest': 'framework',
    'rest api': 'framework', 'apache spark': 'framework', 'hadoop': 'framework',
    'docker': 'framework', 'kubernetes': 'framework', 'jenkins': 'framework',
    'terraform': 'framework', 'ansible': 'framework',
    'opencv': 'framework', 'nltk': 'framework', 'spacy': 'framework',

    # Databases
    'postgresql': 'database', 'mysql': 'database', 'mongodb': 'database',
    'redis': 'database', 'sqlite': 'database', 'oracle': 'database',
    'sql server': 'database', 'mariadb': 'database', 'cassandra': 'database',
    'dynamodb': 'database', 'elasticsearch': 'database', 'firebase': 'database',
    'cosmos db': 'database', 'couchbase': 'database', 'neo4j': 'database',

    # Cloud & DevOps
    'aws': 'cloud', 'azure': 'cloud', 'gcp': 'cloud', 'google cloud': 'cloud',
    'amazon web services': 'cloud', 'heroku': 'cloud', 'digitalocean': 'cloud',
    'git': 'cloud', 'github': 'cloud', 'gitlab': 'cloud', 'bitbucket': 'cloud',
    'ci/cd': 'cloud', 'circleci': 'cloud', 'travis': 'cloud',
    'nginx': 'cloud', 'apache': 'cloud', 'linux': 'cloud',
    'unix': 'cloud', 'ubuntu': 'cloud', 'centos': 'cloud',

    # Tools & Platforms
    'jira': 'tool', 'confluence': 'tool', 'slack': 'tool', 'trello': 'tool',
    'asana': 'tool', 'notion': 'tool', 'monday.com': 'tool',
    'postman': 'tool', 'swagger': 'tool', 'figma': 'tool',
    'sketch': 'tool', 'adobe xd': 'tool', 'photoshop': 'tool',
    'illustrator': 'tool', 'tableau': 'tool', 'power bi': 'tool',
    'matlab': 'tool', 'jupyter': 'tool', 'vscode': 'tool',
    'intellij': 'tool', 'eclipse': 'tool', 'vim': 'tool',

    # Soft Skills
    'leadership': 'soft_skill', 'communication': 'soft_skill',
    'teamwork': 'soft_skill', 'problem solving': 'soft_skill',
    'critical thinking': 'soft_skill', 'time management': 'soft_skill',
    'project management': 'soft_skill', 'agile': 'soft_skill',
    'scrum': 'soft_skill', 'management': 'soft_skill',
    'mentoring': 'soft_skill', 'collaboration': 'soft_skill',
    'presentation': 'soft_skill', 'negotiation': 'soft_skill',
    'adaptability': 'soft_skill', 'creativity': 'soft_skill',
    'analytical': 'soft_skill', 'research': 'soft_skill',
}


# ============================================================
# SECTION: Text Extraction
# ============================================================

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    return text.strip()


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from a DOCX file."""
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise ValueError(f"Failed to parse DOCX: {str(e)}")
    return text.strip()


def extract_text(file_content: bytes, file_type: str) -> str:
    """Extract text from a resume file based on its type."""
    if file_type == 'pdf':
        return extract_text_from_pdf(file_content)
    elif file_type == 'docx':
        return extract_text_from_docx(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


# ============================================================
# SECTION: Candidate Information Extraction
# ============================================================

def extract_email(text: str) -> Optional[str]:
    """Extract email address from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    patterns = [
        r'\+?1?\d{10,13}',
        r'\+?1?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return None


def extract_candidate_name(text: str) -> Optional[str]:
    """Extract candidate name (usually the first line of resume)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        # Name is typically the first non-empty line, 2-4 words, capitalized
        words = line.split()
        if 1 <= len(words) <= 4 and all(w[0].isupper() if w else False for w in words if w):
            # Skip if it looks like a section header
            if any(w.upper() == w and len(w) > 2 for w in words):
                continue
            return line
    return None


# ============================================================
# SECTION: Advanced Section Detection
# ============================================================

# Comprehensive list of section headers commonly found in resumes
# Organized by category for detection and distribution analysis
SECTION_HEADERS = {
    'summary': [
        'summary', 'professional summary', 'profile', 'career objective',
        'objective', 'career summary', 'executive summary', 'qualifications summary',
        'professional profile', 'about me', 'personal statement',
    ],
    'experience': [
        'experience', 'work experience', 'professional experience', 'employment',
        'work history', 'employment history', 'relevant experience',
        'career history', 'professional background', 'work', 'job experience',
        'professional experience', 'business experience', 'internships',
    ],
    'education': [
        'education', 'academic background', 'educational background',
        'academic qualifications', 'education and training',
        'education & training', 'qualifications', 'academic history',
        'formal education', 'degrees',
    ],
    'skills': [
        'skills', 'technical skills', 'core competencies', 'expertise',
        'technologies', 'competencies', 'proficiencies', 'skill set',
        'technical expertise', 'key skills', 'professional skills',
        'areas of expertise', 'technical proficiencies',
    ],
    'projects': [
        'projects', 'project experience', 'academic projects',
        'personal projects', 'technical projects', 'key projects',
        'project work', 'open source', 'contributions',
    ],
    'certifications': [
        'certifications', 'certificates', 'professional certifications',
        'licenses', 'licenses and certifications', 'licenses & certifications',
        'professional development', 'training and certifications',
    ],
    'achievements': [
        'achievements', 'accomplishments', 'awards', 'honors',
        'awards and honors', 'awards & honors', 'recognition',
        'professional achievements', 'key achievements',
    ],
    'publications': [
        'publications', 'research', 'research experience',
        'papers', 'research papers', 'thesis', 'dissertation',
        'conferences', 'presentations',
    ],
    'languages': [
        'languages', 'language proficiency', 'language skills',
        'foreign languages', 'spoken languages',
    ],
    'interests': [
        'interests', 'hobbies', 'activities', 'extracurricular',
        'volunteer', 'volunteering', 'volunteer experience',
        'community service', 'leadership activities',
    ],
    'references': [
        'references', 'professional references', 'references available upon request',
    ],
    'technical': [
        'technical skills', 'technical expertise', 'technical qualifications',
        'technical proficiencies', 'technical background',
    ],
}

# Flatten into a lookup for detection
_ALL_SECTION_NAMES = {}
for category, headers in SECTION_HEADERS.items():
    for header in headers:
        _ALL_SECTION_NAMES[header] = category

# Also detect these as "other section" boundaries that terminate experience sections
_END_SECTION_TRIGGERS = [
    'education', 'skills', 'certifications', 'projects', 'publications',
    'awards', 'achievements', 'interests', 'hobbies', 'languages',
    'references', 'volunteer', 'training',
]

# Patterns that strongly indicate a section header line
_SECTION_HEADER_PATTERNS = [
    # All-caps header (e.g. "EXPERIENCE", "EDUCATION")
    re.compile(r'^[A-Z][A-Z\s/&]{2,30}$'),
    # Title case header (e.g. "Professional Experience", "Technical Skills")
    re.compile(r'^(?:Professional|Work|Technical|Relevant|Core|Key|Academic|'
               r'Educational|Professional|Career|Employment|Project|'
               r'Awards|Honors|Language|Spoken|Foreign|Personal|'
               r'Executive|Qualifications|Areas|Summary|Profile|'
               r'Open)\s+[A-Z][a-z]+'),
    # Header followed by separator line
    re.compile(r'^[A-Z][A-Za-z\s/&]{2,40}[-=]{3,}$'),
    # Short bold title (single line, all caps or title case, standalone)
    re.compile(r'^(SKILLS|EXPERIENCE|EDUCATION|PROJECTS|CERTIFICATIONS|'
               r'ACHIEVEMENTS|PUBLICATIONS|LANGUAGES|INTERESTS|REFERENCES|'
               r'SUMMARY|PROFILE|OBJECTIVE|TECHNICAL SKILLS)$'),
]


def detect_sections(text: str) -> List[Dict]:
    """
    Advanced resume section detection using heuristic and pattern-based approach.

    Detects section boundaries by analyzing:
    1. Known section header keyword matches
    2. Typographic patterns (ALL CAPS, Title Case, separator lines)
    3. Line density analysis (short lines that look like headers)
    4. Sequential ordering (sections appear in expected resume flow)

    Returns a list of section dicts with 'name', 'category', 'start_line',
    'end_line' (exclusive), 'content', and 'confidence'.
    """
    lines = text.split('\n')
    raw_lines = text.split('\n')
    if not lines:
        return []

    # Pre-compute line metadata for detection
    line_info = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        line_info.append({
            'index': i,
            'raw': line,
            'stripped': stripped,
            'lower': stripped.lower().rstrip(':').strip(),
            'is_empty': len(stripped) == 0,
            'length': len(stripped),
            'word_count': len(stripped.split()),
            'is_short': len(stripped) > 0 and len(stripped.split()) <= 5,
            'all_caps': bool(stripped) and stripped == stripped.upper() and len(stripped) > 2,
            'ends_with_colon': stripped.endswith(':'),
        })

    # Phase 1: Identify candidate section header lines
    candidate_headers = []  # (line_index, section_category, header_name, confidence_score)

    for i, info in enumerate(line_info):
        if info['is_empty']:
            continue

        lower = info['lower']

        # Check against known section header keywords
        for header_name, category in _ALL_SECTION_NAMES.items():
            # Exact match or match with optional colon
            if lower == header_name or lower == header_name + ':':
                candidate_headers.append((i, category, header_name, 0.95))
                break
            # Match with trailing period or dash
            if lower.rstrip('.') == header_name or lower.rstrip('-') == header_name:
                candidate_headers.append((i, category, header_name, 0.90))
                break

        # Check against ALL CAPS patterns (e.g. "EXPERIENCE", "EDUCATION")
        if info['all_caps'] and info['is_short'] and info['word_count'] <= 3:
            for pattern in _SECTION_HEADER_PATTERNS:
                if pattern.match(info['stripped']):
                    # Map to known category if possible
                    lower_clean = re.sub(r'[:\-=\s]+', '', lower)
                    found_category = None
                    for header_name, category in _ALL_SECTION_NAMES.items():
                        h_clean = re.sub(r'[:\-=\s]+', '', header_name)
                        if lower_clean == h_clean:
                            found_category = category
                            break
                    if found_category is None:
                        # Generic all-caps header - treat as custom section
                        found_category = 'custom'
                    candidate_headers.append((i, found_category, info['stripped'], 0.80))
                    break

        # Check for short title-case lines that look like section headers
        if (info['is_short'] and info['word_count'] <= 4
                and not info['all_caps'] and info['word_count'] >= 1
                and info['stripped'][0].isupper()
                and not info['ends_with_colon']):
            lower_clean = lower.rstrip(':.').strip()
            for header_name, category in _ALL_SECTION_NAMES.items():
                if lower_clean == header_name:
                    candidate_headers.append((i, category, header_name, 0.85))
                    break

    # Remove duplicate headers (same index)
    seen_indices = set()
    unique_headers = []
    for idx, cat, name, conf in candidate_headers:
        if idx not in seen_indices:
            seen_indices.add(idx)
            unique_headers.append((idx, cat, name, conf))
    candidate_headers = unique_headers

    # Sort by line index
    candidate_headers.sort(key=lambda x: x[0])

    # Phase 2: Build section boundaries from headers
    sections = []
    for k, (start_idx, category, header_name, confidence) in enumerate(candidate_headers):
        # Determine end index (next header line, or end of document)
        if k + 1 < len(candidate_headers):
            end_idx = candidate_headers[k + 1][0]
        else:
            end_idx = len(lines)

        # Extract section content (lines between start and end)
        content_lines = []
        for j in range(start_idx + 1, end_idx):
            if line_info[j]['stripped']:
                content_lines.append(lines[j])

        content = '\n'.join(content_lines).strip()

        # Skip empty sections
        if not content and category != 'custom':
            continue

        # Calculate content stats for quality assessment
        bullet_count = sum(1 for l in content_lines if l.strip().startswith(('•', '-', '*', '–', '→', '▸', '◆')))
        numbered_items = sum(1 for l in content_lines if re.match(r'^\s*\d+[.)]', l))
        total_bullets = bullet_count + numbered_items

        sections.append({
            'category': category,
            'header_name': header_name,
            'content': content,
            'content_lines': content_lines,
            'start_line': start_idx,
            'end_line': end_idx,
            'line_count': len(content_lines),
            'word_count': len(content.split()),
            'bullet_count': total_bullets,
            'confidence': confidence,
        })

    # Phase 3: If no sections detected via headers, use fallback heuristic
    if not sections:
        sections = _fallback_section_detection(lines, line_info)

    return sections


def _fallback_section_detection(lines: List[str], line_info: List[Dict]) -> List[Dict]:
    """
    Fallback section detection for resumes without clear section headers.
    Uses content analysis to identify distinct sections based on line patterns,
    spacing, and content type.
    """
    sections = []
    current_start = 0
    current_lines = []
    current_type = 'unknown'

    for i, info in enumerate(line_info):
        stripped = info['stripped']

        # Empty lines can indicate section breaks
        if info['is_empty'] and current_lines:
            # Check the accumulated lines to determine if this was a section
            section_text = '\n'.join(current_lines)
            if len(section_text.strip()) > 20:
                detected_type = _classify_section_content(section_text)
                sections.append({
                    'category': detected_type,
                    'header_name': detected_type.capitalize() if detected_type != 'unknown' else 'Section',
                    'content': section_text.strip(),
                    'content_lines': current_lines,
                    'start_line': current_start,
                    'end_line': i,
                    'line_count': len(current_lines),
                    'word_count': len(section_text.split()),
                    'bullet_count': sum(1 for l in current_lines if l.strip().startswith(('•', '-', '*', '–'))),
                    'confidence': 0.5,
                })
            current_lines = []
            current_start = i + 1
            continue

        if not info['is_empty']:
            current_lines.append(stripped)

    # Don't forget the last block
    if current_lines:
        section_text = '\n'.join(current_lines)
        if len(section_text.strip()) > 20:
            detected_type = _classify_section_content(section_text)
            sections.append({
                'category': detected_type,
                'header_name': detected_type.capitalize() if detected_type != 'unknown' else 'Section',
                'content': section_text.strip(),
                'content_lines': current_lines,
                'start_line': current_start,
                'end_line': len(lines),
                'line_count': len(current_lines),
                'word_count': len(section_text.split()),
                'bullet_count': sum(1 for l in current_lines if l.strip().startswith(('•', '-', '*', '–'))),
                'confidence': 0.5,
            })

    return sections


def _classify_section_content(text: str) -> str:
    """
    Classify a block of text into a section type based on content analysis.
    Used as fallback when no explicit header is found.
    """
    lower = text.lower()

    # Check for date patterns (strong indicator of experience section)
    date_pattern = re.compile(
        r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'[.\s]*\d{4}', re.IGNORECASE
    )
    year_pattern = re.compile(r'\b(?:19|20)\d{2}\b')

    date_count = len(date_pattern.findall(text))
    year_count = len(year_pattern.findall(text))

    # Education indicators
    edu_indicators = [
        'bachelor', 'master', 'phd', 'ph.d', 'b.tech', 'm.tech',
        'b.sc', 'm.sc', 'b.a', 'm.a', 'b.com', 'm.com', 'mba',
        'university', 'college', 'institute', 'school', 'degree',
        'diploma', 'associate', 'graduated', 'gpa',
    ]
    edu_score = sum(1 for ind in edu_indicators if ind in lower)

    # Skill indicators
    skill_indicators = [
        'proficient', 'proficiency', 'knowledge of', 'experienced in',
        'skilled in', 'expertise in', 'competencies', 'familiar with',
    ]
    skill_score = sum(1 for ind in skill_indicators if ind in lower)

    # Experience indicators
    exp_indicators = [
        'worked', 'responsible', 'managed', 'developed', 'implemented',
        'led', 'created', 'designed', 'achieved', 'delivered',
        'responsible for', 'duties included', 'role included',
    ]
    exp_score = sum(1 for ind in exp_indicators if ind in lower)

    # Project indicators
    proj_indicators = ['project', 'developed', 'built', 'created', 'implemented']
    proj_score = sum(1 for ind in proj_indicators if ind in lower)

    # Certification indicators
    cert_indicators = [
        'certified', 'certification', 'certificate', 'license',
        'credential', 'accredited',
    ]
    cert_score = sum(1 for ind in cert_indicators if ind in lower)

    # Summary indicators
    summary_indicators = [
        'professional with', 'years of experience', 'seeking',
        'dedicated', 'motivated', 'passionate', 'results-driven',
    ]
    summary_score = sum(1 for ind in summary_indicators if ind in lower)

    # Score-based classification
    # Experience sections often have date ranges and action verbs
    if date_count >= 2 and exp_score >= 2:
        return 'experience'
    if edu_score >= 2:
        return 'education'
    if skill_score >= 2:
        return 'skills'
    if cert_score >= 2:
        return 'certifications'
    if summary_score >= 2:
        return 'summary'
    if proj_score >= 2 and date_count >= 1:
        return 'projects'

    # Secondary heuristic: look at the first few lines
    first_lines = text.split('\n')[:3]
    first_text = ' '.join(first_lines).lower()

    if any(ind in first_text for ind in edu_indicators):
        return 'education'
    if any(ind in first_text for ind in ['experience', 'employment', 'work history']):
        return 'experience'
    if any(ind in first_text for ind in ['skill', 'technology', 'expertise']):
        return 'skills'
    if any(ind in first_text for ind in ['project']):
        return 'projects'
    if any(ind in first_text for ind in ['summary', 'profile', 'objective']):
        return 'summary'
    if any(ind in first_text for ind in ['certif']):
        return 'certifications'

    return 'unknown'


def calculate_section_distribution(sections: List[Dict]) -> Dict:
    """
    Analyze how well content is distributed across resume sections.
    Returns a comprehensive distribution analysis with quality scores.
    """
    if not sections:
        return {
            'total_sections': 0,
            'distribution_score': 0,
            'section_breakdown': {},
            'missing_critical_sections': [],
            'content_balance': 'none',
        }

    total_words = sum(s['word_count'] for s in sections)
    if total_words == 0:
        total_words = 1  # avoid division by zero

    # Define critical sections expected in a well-structured resume
    critical_sections = ['summary', 'experience', 'education', 'skills']
    optional_sections = [
        'projects', 'certifications', 'achievements', 'publications',
        'languages', 'interests',
    ]

    section_breakdown = {}
    found_categories = set()
    too_large_sections = []

    for section in sections:
        cat = section['category']
        word_count = section['word_count']
        content_pct = (word_count / total_words) * 100

        found_categories.add(cat)
        if cat not in section_breakdown:
            section_breakdown[cat] = {
                'word_count': 0,
                'content_percentage': 0,
                'bullet_count': 0,
                'is_present': True,
            }
        section_breakdown[cat]['word_count'] += word_count
        section_breakdown[cat]['bullets'] = section_breakdown[cat].get('bullets', 0) + section['bullet_count']

        # Flag if a single section dominates (>70% of content)
        if content_pct > 70:
            too_large_sections.append(cat)

    # Calculate percentages
    for cat in section_breakdown:
        section_breakdown[cat]['content_percentage'] = round(
            (section_breakdown[cat]['word_count'] / total_words) * 100, 1
        )

    # Check for missing critical sections
    missing_sections = []
    for crit in critical_sections:
        if crit not in found_categories:
            missing_sections.append(crit)

    # Distribution scoring:
    # - Start with 100
    # - Deduct 20 per missing critical section
    # - Deduct 10 if any section dominates >70%
    # - Deduct 15 if experience section is missing
    # - Deduct 10 if skills section is missing
    # - Deduct 10 if education section is missing
    # - Bonus 5 for projects section
    # - Bonus 5 for certifications section
    # - Bonus 5 for achievements section

    distribution_score = 100.0

    # Missing critical sections (base penalty)
    missing_critical = [s for s in missing_sections if s in critical_sections]
    distribution_score -= len(missing_critical) * 20

    # Experience section missing = big penalty (core of any resume)
    if 'experience' not in found_categories:
        distribution_score -= 15

    # Skills section missing
    if 'skills' not in found_categories:
        distribution_score -= 10

    # Education section missing
    if 'education' not in found_categories:
        distribution_score -= 10

    # Penalty for unbalanced content
    for cat in too_large_sections:
        distribution_score -= 10

    # Bonus for having extra valuable sections
    for opt in ['projects', 'certifications', 'achievements', 'publications']:
        if opt in found_categories:
            distribution_score += 5

    distribution_score = max(0, min(100, distribution_score))

    # Determine content balance rating
    if len(found_categories) >= 4 and 'experience' in found_categories and 'skills' in found_categories:
        content_balance = 'excellent'
    elif len(found_categories) >= 3 and 'experience' in found_categories:
        content_balance = 'good'
    elif len(found_categories) >= 2:
        content_balance = 'fair'
    else:
        content_balance = 'poor'

    # Calculate section quality metrics
    total_bullets = sum(s['bullet_count'] for s in sections)
    bullets_per_section = total_bullets / max(len(sections), 1)

    return {
        'total_sections': len(sections),
        'distribution_score': round(distribution_score, 2),
        'content_balance': content_balance,
        'missing_critical_sections': missing_sections,
        'found_categories': list(found_categories),
        'section_breakdown': section_breakdown,
        'total_bullets_used': total_bullets,
        'bullets_per_section': round(bullets_per_section, 1),
        'unbalanced_sections': too_large_sections,
    }


# ============================================================
# SECTION: Experience & Education Extraction
# ============================================================

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text using the skill database."""
    _ensure_nltk_data()
    text_lower = text.lower()
    found_skills = set()

    # Tokenize the text
    tokens = word_tokenize(text_lower)
    stop_words = set(stopwords.words('english'))

    # Check for multi-word skills using word-boundary matching
    for skill in SKILL_DATABASE:
        if ' ' in skill and skill in text_lower:
            escaped = re.escape(skill)
            if re.search(r'\b' + escaped + r'\b', text_lower):
                found_skills.add(skill)

    # Check single word skills
    for token in tokens:
        token_clean = token.strip('.,;:!?()[]{}"\'-')
        if token_clean in SKILL_DATABASE and token_clean not in stop_words:
            found_skills.add(token_clean)

    # Also check for mentions in skill sections
    skill_section_pattern = re.compile(
        r'(?:technical\s*skills?|skills?|technologies?|tools?|expertise|competencies|proficiencies)'
        r'[:\s]*([^.]*(?:\.[^.]*){0,2})',
        re.IGNORECASE
    )
    for match in skill_section_pattern.finditer(text):
        section_text = match.group(1).lower()
        for skill in SKILL_DATABASE:
            if skill in section_text:
                found_skills.add(skill)

    return sorted(found_skills)


def extract_experience_years(text: str) -> float:
    """Extract total years of professional experience."""
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional|work|experience)?\s*experience',
        r'experience\s*(?:of|:)?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*years?\s*(?:of)?\s*(?:professional|industry|work)?',
    ]

    years_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        years_found.extend([float(m) for m in matches if m])

    # Calculate from year date ranges (e.g. "2018 - 2022" or "2018 - Present")
    date_range_pattern = re.compile(
        r'(\d{4})\s*(?:-|–|to)\s*(\d{4}|present|current|now)',
        re.IGNORECASE
    )
    total_years = 0
    seen_ranges = set()
    for match in date_range_pattern.finditer(text):
        start = int(match.group(1))
        end_str = match.group(2).lower()
        range_key = (start, end_str)
        if range_key in seen_ranges:
            continue
        seen_ranges.add(range_key)
        if end_str in ('present', 'current', 'now'):
            end = datetime.now().year
        else:
            end = int(end_str)
        total_years += max(0, end - start)

    if years_found:
        return max(years_found)
    if total_years > 0:
        return round(total_years, 1)
    return 0.0


def extract_education(text: str) -> List[Dict]:
    """Extract education details from resume text using section detection first."""
    education = []

    # First try to find the education section using section detection
    sections = detect_sections(text)
    education_section = None
    for section in sections:
        if section['category'] == 'education':
            education_section = section
            break

    # Use education section content if found, otherwise fall back to full text
    if education_section and education_section['content']:
        source_text = education_section['content']
    else:
        source_text = text

    # Cleaner degree patterns with word boundaries
    degree_pattern = re.compile(
        r'\b(bachelor(?:\'s)?|master(?:\'s)?|ph\.?d|doctorate|associate(?:\'s)?|'
        r'b\.?\s*tech|m\.?\s*tech|mba|b\.?\s*sc|m\.?\s*sc|'
        r'b\.?\s*com|m\.?\s*com|b\.?\s*a|m\.?\s*a|b\.?\s*e|m\.?\s*e|diploma|'
        r'bachelor\s+(of|in)|master\s+(of|in)|doctor\s+(of|in))',
        re.IGNORECASE
    )

    lines = source_text.split('\n')
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        line_lower = line_stripped.lower()

        degree_match = degree_pattern.search(line_lower)
        if not degree_match:
            continue

        edu_entry = {
            'degree': line_stripped,
            'institution': '',
            'year': '',
        }

        # Look for institution name in adjacent lines (within the education section)
        for j in range(max(0, i - 3), min(len(lines), i + 4)):
            if j == i:
                continue
            cleaned = lines[j].strip()
            if not cleaned or len(cleaned) < 4:
                continue
            # Skip lines that look like bullet points or section headers
            if cleaned.startswith(('•', '-', '*', '–')) or cleaned.lower().rstrip(':') in ('education', 'experience', 'skills', 'projects'):
                continue
            # Skip lines that are just years or dates
            if re.match(r'^[\d\s\-–/]+$', cleaned):
                continue
            if not edu_entry['institution']:
                edu_entry['institution'] = cleaned

        # Look for year in the line or nearby
        year_match = re.search(r'\b(19|20)\d{2}\b', line_stripped)
        if year_match:
            edu_entry['year'] = year_match.group(0)
        else:
            # Check next line for year
            if i + 1 < len(lines):
                next_year = re.search(r'\b(19|20)\d{2}\b', lines[i + 1])
                if next_year:
                    edu_entry['year'] = next_year.group(0)

        education.append(edu_entry)

    # Deduplicate by degree (keep first occurrence)
    seen = set()
    unique = []
    for entry in education:
        # Normalize degree for dedup
        degree_key = re.sub(r'[^a-zA-Z0-9]', '', entry['degree'].lower())[:50]
        if degree_key not in seen:
            seen.add(degree_key)
            unique.append(entry)

    return unique


def extract_experience(text: str) -> List[Dict]:
    """Extract work experience entries from resume text."""
    experiences = []

    # Flexible date patterns that cover common resume formats
    month_year_pattern = re.compile(
        r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)[.\s]*\d{4}', re.IGNORECASE
    )
    # Also match compact dates like "Sept2024–May2026" or "Jan2025–Mar2025"
    compact_date_pattern = re.compile(
        r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)\s*\d{4}\s*(?:-|–|to)\s*(?:'
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)\s*\d{4}',
        re.IGNORECASE
    )

    year_range_pattern = re.compile(
        r'\b(\d{4})\s*(?:-|–|to)\s*(\d{4}|present|current|now)\b', re.IGNORECASE
    )

    # First try extraction using section detection for better accuracy
    sections = detect_sections(text)
    experience_section = None
    for section in sections:
        if section['category'] == 'experience':
            experience_section = section
            break

    if experience_section and experience_section['content']:
        section_text = experience_section['content']
        entries = _extract_experience_entries_v2(section_text, month_year_pattern, year_range_pattern, compact_date_pattern)
        experiences.extend(entries)
    else:
        # Fallback: try to find the experience section
        lines = text.split('\n')
        section_headers = [
            'experience', 'work history', 'employment', 'professional experience',
            'work experience', 'relevant experience', 'career history',
            'employment history', 'work', 'projects', 'project experience'
        ]
        other_section_headers = [
            'education', 'skills', 'technical skills', 'certifications',
            'summary', 'profile', 'objective', 'publications', 'awards',
            'languages', 'interests', 'references', 'volunteer',
            'training', 'courses', 'achievements', 'accomplishments'
        ]

        in_experience_section = False
        experience_lines = []

        for i, line in enumerate(lines):
            line_stripped = line.strip().lower().rstrip(':')
            is_other_header = any(
                re.search(r'\b' + re.escape(header) + r'\b', line_stripped)
                for header in other_section_headers
            )
            is_exp_header = any(
                re.search(r'\b' + re.escape(header) + r'\b', line_stripped)
                for header in section_headers
            )

            if is_other_header and in_experience_section:
                break
            elif is_exp_header:
                in_experience_section = True
                continue
            elif in_experience_section:
                experience_lines.append(line)

        if in_experience_section and experience_lines:
            section_text = '\n'.join(experience_lines)
            entries = _extract_experience_entries_v2(section_text, month_year_pattern, year_range_pattern, compact_date_pattern)
            experiences.extend(entries)

        # Second fallback: try splitting by blank lines
        if not experiences:
            sections_raw = re.split(r'\n\s*\n', text)
            for section in sections_raw:
                section_text = section.strip()
                if len(section_text) < 30:
                    continue
                entries = _extract_experience_entries_v2(section_text, month_year_pattern, year_range_pattern, compact_date_pattern)
                experiences.extend(entries)

    # Deduplicate experiences by title+company
    seen = set()
    unique_experiences = []
    for exp in experiences:
        key = (exp['title'], exp['company'])
        if key not in seen:
            seen.add(key)
            unique_experiences.append(exp)

    return unique_experiences


def _extract_experience_entries_v2(section_text: str, month_year_pattern, year_range_pattern, compact_date_pattern) -> List[Dict]:
    """Extract experience entries from a section of text with improved boundary detection."""
    entries = []
    lines = [l.strip() for l in section_text.split('\n') if l.strip()]
    if not lines:
        return entries

    # Step 1: Identify lines that look like job title entries
    # A job title line typically: starts with uppercase, short (1-6 words), contains no bullet
    # OR contains a compact date range like "Jan2025–Mar2025"
    entry_boundaries = []

    for i, line in enumerate(lines):
        has_compact_date = bool(compact_date_pattern.search(line))
        has_month_year = bool(month_year_pattern.search(line))
        has_year_range = bool(year_range_pattern.search(line))
        has_date = has_compact_date or has_month_year or has_year_range
        is_bullet = line.startswith(('•', '-', '*', '–', '→', '▸', '◆', '●'))
        is_numbered = bool(re.match(r'^\s*\d+[.)]\s', line))

        # A line is a potential entry start if:
        # 1. It contains a date (strong indicator of role entry), OR
        # 2. It's a short capitalized line (potential job title), BUT not a bullet
        is_entry_start = False
        if has_compact_date:
            is_entry_start = True
        elif has_date and not is_bullet and not is_numbered:
            is_entry_start = True
        elif (not is_bullet and not is_numbered
              and 1 <= len(line.split()) <= 8
              and line[0].isupper()
              and not line.endswith('.')):
            # Check that it's not a section header or generic line
            lower = line.lower()
            common_headers = {'education', 'experience', 'skills', 'projects', 'summary',
                              'profile', 'certifications', 'achievements', 'publications',
                              'languages', 'interests', 'references', 'objective',
                              'technical skills', 'work experience', 'professional summary'}
            if lower not in common_headers and not lower.rstrip(':') in common_headers:
                # Check that the line has proper title casing (not all lowercase words)
                words = line.split()
                cap_count = sum(1 for w in words if w[0].isupper())
                if cap_count >= len(words) * 0.6:
                    is_entry_start = True

        if is_entry_start:
            entry_boundaries.append(i)

    # If no clear boundaries found, treat as one entry
    if not entry_boundaries:
        # Check if first line looks like a title
        entry = _create_experience_entry_v2(lines, month_year_pattern, year_range_pattern)
        if entry:
            entries.append(entry)
        return entries

    # Step 2: Split lines into entries using boundaries
    for k, start_idx in enumerate(entry_boundaries):
        if k + 1 < len(entry_boundaries):
            end_idx = entry_boundaries[k + 1]
        else:
            end_idx = len(lines)

        entry_lines = lines[start_idx:end_idx]
        if not entry_lines:
            continue

        entry = _create_experience_entry_v2(entry_lines, month_year_pattern, year_range_pattern)
        if entry:
            entries.append(entry)

    return entries


def _create_experience_entry_v2(lines: List[str], month_year_pattern, year_range_pattern) -> Optional[Dict]:
    """Create an experience entry with improved parsing."""
    if not lines:
        return None

    title_line = lines[0]
    # Parse the title line to extract title and potentially embedded company info
    # Often the format is: "CompanyName - JobTitle" or "JobTitle, CompanyName"

    # Check if title line itself has a compact date range - extract and remove it
    compact_date_match = re.search(
        r'((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)\s*\d{4}\s*(?:-|–|to)\s*(?:'
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)\s*\d{4})',
        title_line, re.IGNORECASE
    )
    dates_from_title = ''
    if compact_date_match:
        dates_from_title = compact_date_match.group(1)
        # Remove date from title for cleaner display
        title_line = title_line.replace(dates_from_title, '').strip()

    # Also check for simple year ranges in title like "2020 - 2023"
    year_range_in_title = year_range_pattern.search(title_line)
    title_dates = ''
    if year_range_in_title:
        title_dates = f"{year_range_in_title.group(1)} - {year_range_in_title.group(2)}"
        title_line = title_line.replace(year_range_in_title.group(0), '').strip()

    # Clean up title line (remove excess spaces, trailing dashes/commas)
    title_line = re.sub(r'\s+', ' ', title_line).strip().rstrip(',;|')

    # Company: check the second line if it doesn't contain dates
    company = ''
    if len(lines) > 1:
        second_line = lines[1]
        has_date = bool(month_year_pattern.search(second_line)) or bool(year_range_pattern.search(second_line))
        is_bullet = second_line.startswith(('•', '-', '*', '–'))
        if not has_date and not is_bullet and len(second_line.split()) <= 8:
            company = second_line

    # Collect description and dates from remaining lines
    description_parts = []
    date_parts = []
    if dates_from_title:
        date_parts.append(dates_from_title)
    if title_dates:
        date_parts.append(title_dates)

    desc_start = 2 if company else 1
    for line in lines[desc_start:]:
        has_date = bool(month_year_pattern.search(line)) or bool(year_range_pattern.search(line))
        if has_date:
            # Extract date info
            months = month_year_pattern.findall(line)
            for m in months:
                date_parts.append(m)
            year_ranges = year_range_pattern.findall(line)
            for yr in year_ranges:
                date_parts.append(f"{yr[0]} - {yr[1]}")
        else:
            # Clean bullet markers
            clean = re.sub(r'^[•\-–*▸◆●]\s*', '', line)
            description_parts.append(clean)

    # Build date string (use first two date entries max)
    all_dates = list(dict.fromkeys(date_parts))  # deduplicate preserving order
    date_str = ' | '.join(all_dates[:2]) if all_dates else ''

    description = ' '.join(description_parts)
    description = re.sub(r'\s+', ' ', description).strip()

    if not title_line:
        return None

    return {
        'title': title_line,
        'company': company,
        'dates': date_str,
        'description': description,
    }


def _extract_experience_entries(section_text: str, month_year_pattern, year_range_pattern) -> List[Dict]:
    """Extract experience entries from a section of text."""
    entries = []
    section_dates_m = month_year_pattern.findall(section_text)
    section_year_ranges = year_range_pattern.findall(section_text)

    lines = [l.strip() for l in section_text.split('\n') if l.strip()]
    if not lines:
        return entries

    current_entry_lines = []

    for line in lines:
        is_date_line = bool(month_year_pattern.search(line)) or bool(year_range_pattern.search(line))

        if current_entry_lines and (is_date_line or (
            len(line.split()) <= 5 and line[0].isupper() and
            not any(line.lower().startswith(w) for w in ['and', 'the', 'a', 'an', 'in', 'on', 'at', 'with'])
        )):
            entry = _create_experience_entry(current_entry_lines, month_year_pattern, year_range_pattern)
            if entry:
                entries.append(entry)
            current_entry_lines = [line]
        else:
            current_entry_lines.append(line)

    # Process the last entry
    if current_entry_lines:
        entry = _create_experience_entry(current_entry_lines, month_year_pattern, year_range_pattern)
        if entry:
            entries.append(entry)

    return entries


def _create_experience_entry(lines: List[str], month_year_pattern, year_range_pattern) -> Optional[Dict]:
    """Create an experience entry from a list of lines."""
    if not lines:
        return None

    date_lines = []
    non_date_lines = []
    for line in lines:
        dates_m = month_year_pattern.findall(line)
        year_r = year_range_pattern.findall(line)
        if dates_m or year_r:
            date_lines.append(line)
        else:
            non_date_lines.append(line)

    if not date_lines and len(lines) < 3:
        return None

    title_line = lines[0]
    company = ''
    if len(lines) > 1:
        second_line = lines[1]
        if not (month_year_pattern.search(second_line) or year_range_pattern.search(second_line)):
            company = second_line

    all_dates = []
    for dl in date_lines:
        dates_m = month_year_pattern.findall(dl)
        year_r = year_range_pattern.findall(dl)
        all_dates.extend(dates_m)
        if year_r:
            all_dates.extend([f'{yr[0]} - {yr[1]}' for yr in year_r])

    date_str = ', '.join(all_dates[:2]) if all_dates else ''

    desc_start = 1
    if company:
        desc_start = 2
    description = ' '.join(lines[desc_start:]) if len(lines) > desc_start else ''
    for dl in date_lines:
        description = description.replace(dl, '')
    description = re.sub(r'\s+', ' ', description).strip()

    if not title_line:
        return None

    return {
        'title': title_line,
        'company': company,
        'dates': date_str,
        'description': description,
    }


# ============================================================
# SECTION: Section Quality & Content Analysis
# ============================================================

def analyze_section_quality(sections: List[Dict], text: str) -> Dict:
    """
    Analyze the quality of resume sections based on content depth,
    formatting, and best practices.

    Evaluates:
    - Bullet point usage in experience section
    - Quantified achievements
    - Action verbs presence
    - Section depth (word count per section)
    - Date formatting consistency
    - Contact information presence
    """
    quality_metrics = {
        'bullet_point_usage': 0,
        'quantified_achievements': 0,
        'action_verb_density': 0,
        'has_contact_info': False,
        'experience_quality': 0,
        'education_quality': 0,
        'skills_organization': 0,
        'overall_formatting': 0,
    }

    # Track quantified achievements across entire resume
    quantified_pattern = re.compile(
        r'\b\d+[%x]?\b|\b(?:increased|decreased|reduced|improved|generated|'
        r'saved|delivered|managed|led|achieved|grew|boosted|raised|'
        r'produced|earned|won|exceeded|surpassed)\s+(?:by\s+)?\d+',
        re.IGNORECASE
    )
    total_quantified = len(quantified_pattern.findall(text))

    # Track action verbs
    action_verb_pattern = re.compile(
        r'\b(?:developed|implemented|managed|designed|led|created|improved|'
        r'analyzed|optimized|delivered|achieved|coordinated|established|'
        r'generated|increased|reduced|launched|maintained|performed|'
        r'presented|proposed|recommended|resolved|streamlined|transformed|'
        r'built|executed|facilitated|drove|negotiated|mentored|trained)\b',
        re.IGNORECASE
    )
    total_action_verbs = len(action_verb_pattern.findall(text))

    # Contact info check
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text))
    quality_metrics['has_contact_info'] = has_email and has_phone

    # Per-section analysis
    total_bullets = 0
    experience_section_quality = 0
    education_section_quality = 0
    skills_section_quality = 0

    for section in sections:
        cat = section['category']
        content = section['content']
        word_count = section['word_count']
        bullet_count = section['bullet_count']
        total_bullets += bullet_count

        if cat == 'experience':
            # Experience quality: needs bullets, dates, quantified achievements
            experience_dates = len(re.findall(
                r'\b(?:19|20)\d{2}\b', content
            ))
            experience_bullets = bullet_count
            experience_verbs = len(action_verb_pattern.findall(content))
            experience_quantified = len(quantified_pattern.findall(content))

            score = 0
            # Bullet points are critical for experience
            if experience_bullets >= 5:
                score += 40
            elif experience_bullets >= 3:
                score += 25
            elif experience_bullets >= 1:
                score += 10

            # Dates indicate proper structure
            if experience_dates >= 4:
                score += 25
            elif experience_dates >= 2:
                score += 15

            # Action verbs show active language
            score += min(20, experience_verbs * 4)

            # Quantified achievements show impact
            score += min(15, experience_quantified * 5)

            experience_section_quality = min(100, score)

        elif cat == 'education':
            if word_count > 10:
                # Look for degree, institution, year
                has_degree = bool(re.search(
                    r'(bachelor|master|ph\.?d|mba|b\.?tech|m\.?tech|b\.?sc|m\.?sc|'
                    r'b\.?a|m\.?a|diploma|associate)', content, re.IGNORECASE
                ))
                has_institution = bool(re.search(
                    r'(university|college|institute|school)', content, re.IGNORECASE
                ))
                has_year = bool(re.search(r'\b(?:19|20)\d{2}\b', content))

                score = 0
                if has_degree:
                    score += 40
                if has_institution:
                    score += 35
                if has_year:
                    score += 25

                education_section_quality = score

        elif cat == 'skills':
            # Skills quality: well-organized with categories
            skill_bullets = bullet_count
            skills_found = len(extract_skills(content))
            has_technical_keyword = bool(re.search(
                r'(technical|programming|language|framework|database|tool)',
                content, re.IGNORECASE
            ))

            score = 0
            if skills_found >= 10:
                score += 40
            elif skills_found >= 5:
                score += 25
            elif skills_found >= 2:
                score += 10

            if skill_bullets >= 2:
                score += 20

            if has_technical_keyword:
                score += 20

            # Bonus for comma-separated skill lists (common format)
            comma_skills = len(re.findall(r'[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)+', content))
            if comma_skills >= 2:
                score += 20

            skills_section_quality = min(100, score)

    quality_metrics['bullet_point_usage'] = total_bullets
    quality_metrics['quantified_achievements'] = total_quantified
    quality_metrics['action_verb_density'] = round(total_action_verbs / max(len(text.split()), 1) * 100, 2)
    quality_metrics['experience_quality'] = experience_section_quality
    quality_metrics['education_quality'] = education_section_quality
    quality_metrics['skills_organization'] = skills_section_quality

    # Overall formatting quality
    formatting_score = 0
    if has_email and has_phone:
        formatting_score += 15
    if total_bullets >= 5:
        formatting_score += 15
    elif total_bullets >= 3:
        formatting_score += 10
    if total_action_verbs >= 10:
        formatting_score += 15
    elif total_action_verbs >= 5:
        formatting_score += 10
    if total_quantified >= 3:
        formatting_score += 15
    elif total_quantified >= 1:
        formatting_score += 8
    # Check for consistent date formatting
    date_formats = re.findall(r'\b\d{4}\b', text)
    if len(date_formats) >= 3:
        formatting_score += 10
    # Check for section headers with proper formatting
    if len(sections) >= 4:
        formatting_score += 15
    elif len(sections) >= 3:
        formatting_score += 10
    # Penalize very short resume
    if len(text.split()) < 100:
        formatting_score -= 20
    # Check for consistent line length
    lines = [l for l in text.split('\n') if l.strip()]
    if lines:
        avg_line_len = sum(len(l) for l in lines) / len(lines)
        if 30 < avg_line_len < 120:
            formatting_score += 15

    quality_metrics['overall_formatting'] = max(0, min(100, formatting_score))

    return quality_metrics


# ============================================================
# SECTION: ATS Scoring
# ============================================================

# Pre-compile reusable regex patterns for ATS scoring
_ATS_FORMAT_PATTERNS = [
    (re.compile(r'education|academic', re.IGNORECASE), 15),
    (re.compile(r'experience|employment|work history', re.IGNORECASE), 15),
    (re.compile(r'skills?|technologies?|expertise', re.IGNORECASE), 15),
    (re.compile(r'projects?|achievements?', re.IGNORECASE), 10),
    (re.compile(r'education|summary|profile', re.IGNORECASE), 10),
]
_ATS_DATE_PATTERN = re.compile(r'\d{4}')


def calculate_ats_score(
    text: str,
    skills: List[str],
    experience_years: float,
    education: List[Dict],
    sections: List[Dict],
    section_distribution: Dict,
    section_quality: Dict,
    target_role: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate ATS (Applicant Tracking System) score and its components.

    V2.0 improvements:
    - Uses actual section detection results for format scoring
    - Incorporates section distribution quality
    - Incorporates section content quality (bullets, achievements, quantified)
    - Better weighting that rewards well-structured resumes

    Returns a dict with individual scores and overall ATS score (0-100).
    """
    text_lower = text.lower()
    text_length = len(text)

    # ============================================================
    # 1. Format Score (0-100)
    # ============================================================
    format_score = 0

    # Base format: section header keywords present
    for pattern, points in _ATS_FORMAT_PATTERNS:
        if pattern.search(text_lower):
            format_score += points

    # Text length - optimal resume length (400-800 words)
    word_count = len(text.split())
    if 300 <= word_count <= 1200:
        format_score += 10
    elif 150 <= word_count < 300:
        format_score += 5

    # Line breaks indicate proper structure
    if text.count('\n') > 20:
        format_score += 5
    elif text.count('\n') > 10:
        format_score += 3

    # Dates present
    if _ATS_DATE_PATTERN.search(text):
        format_score += 5

    # Skill count
    if len(skills) >= 10:
        format_score += 5
    elif len(skills) >= 5:
        format_score += 3

    # SECTION DISTRIBUTION SCORE (new)
    # High-quality section detection directly improves format score
    dist_score = section_distribution.get('distribution_score', 0)
    format_score += dist_score * 0.15  # Max ~15 points from distribution

    # SECTION QUALITY (new)
    # Use overall formatting quality from section quality analysis
    overall_format = section_quality.get('overall_formatting', 0)
    format_score += overall_format * 0.10  # Max ~10 points from formatting quality

    # Bullet point usage bonus
    total_bullets = section_quality.get('bullet_point_usage', 0)
    if total_bullets >= 8:
        format_score += 8
    elif total_bullets >= 5:
        format_score += 5
    elif total_bullets >= 3:
        format_score += 3

    # Contact info bonus
    if section_quality.get('has_contact_info', False):
        format_score += 5

    # Cap format_score at 100
    format_score = min(100, format_score)

    # ============================================================
    # 2. Keyword Score (0-100)
    # ============================================================
    keyword_score = 0
    important_keywords = [
        'developed', 'implemented', 'managed', 'designed', 'led',
        'created', 'improved', 'analyzed', 'optimized', 'delivered',
        'achieved', 'coordinated', 'established', 'generated', 'increased',
        'reduced', 'launched', 'maintained', 'negotiated', 'organized',
        'performed', 'presented', 'proposed', 'recommended', 'resolved',
        'responsible', 'resulted', 'streamlined', 'strengthened', 'transformed',
    ]
    found_keywords = sum(
        1 for kw in important_keywords
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)
    )
    keyword_score = min(100, (found_keywords / 15) * 100)

    # Bonus for quantified keywords (revenue, cost, percentage, etc.)
    quantified_pattern = re.compile(
        r'\b\d+[%x]?\s*(?:increase|decrease|reduce|improve|grow|save|generate|deliver|achieve)',
        re.IGNORECASE
    )
    quantified_bonus = min(10, len(quantified_pattern.findall(text)) * 2)
    keyword_score = min(100, keyword_score + quantified_bonus)

    # ============================================================
    # 3. Experience Score (0-100)
    # ============================================================
    experience_score = min(100, experience_years * 10)
    if experience_years >= 10:
        experience_score = 100

    # Experience quality bonus (new)
    exp_quality = section_quality.get('experience_quality', 0)
    experience_score = min(100, experience_score + exp_quality * 0.15)

    # ============================================================
    # 4. Education Score (0-100)
    # ============================================================
    education_score = 0
    edu_text = ' '.join([e.get('degree', '') for e in education]).lower()
    education_levels = [
        (r'ph\.?d|doctorate|doctor', 100),
        (r'master|mba|m\.?\s*(tech|sc|a|com)', 90),
        (r'bachelor|b\.?\s*(tech|sc|a|com|e)', 80),
        (r'associate|diploma', 60),
    ]
    for pattern, score in education_levels:
        if re.search(pattern, edu_text, re.IGNORECASE):
            education_score = score
            break

    # Education quality bonus (new - proper formatting with institution, degree, year)
    edu_quality = section_quality.get('education_quality', 0)
    education_score = min(100, education_score + edu_quality * 0.10)

    # ============================================================
    # 5. Skills Match Score (0-100)
    # ============================================================
    categorized_skills = {}
    for skill in skills:
        category = SKILL_DATABASE.get(skill, 'unknown')
        if category not in categorized_skills:
            categorized_skills[category] = []
        categorized_skills[category].append(skill)

    skill_diversity = len(categorized_skills)
    # Improved skill scoring: balance between diversity and count
    skills_match_score = min(100, (skill_diversity / 5) * 60 + min(40, len(skills) * 3))
    skills_match_score = min(100, skills_match_score)

    # Skills organization bonus (new)
    skill_org = section_quality.get('skills_organization', 0)
    skills_match_score = min(100, skills_match_score + skill_org * 0.10)

    # ============================================================
    # 6. Content Distribution Score (new)
    # ============================================================
    # Separate score for how well content is balanced across sections
    content_distribution_score = section_distribution.get('distribution_score', 0)

    # ============================================================
    # Calculate weighted overall ATS score
    # ============================================================
    # V2.0 improved weights:
    # - Format: 15% (was 20%) - now includes distribution/quality
    # - Keyword: 20% (was 20%) - bonus for quantified results
    # - Experience: 25% (was 20%) - includes quality
    # - Education: 10% (was 15%)
    # - Skills Match: 20% (was 25%) - includes organization
    # - Content Distribution: 10% (new) - section balance

    ats_score = (
        format_score * 0.15 +
        keyword_score * 0.20 +
        experience_score * 0.25 +
        education_score * 0.10 +
        skills_match_score * 0.20 +
        content_distribution_score * 0.10
    )

    return {
        'ats_score': round(ats_score, 2),
        'format_score': round(format_score, 2),
        'keyword_score': round(keyword_score, 2),
        'experience_score': round(experience_score, 2),
        'education_score': round(education_score, 2),
        'skills_match_score': round(skills_match_score, 2),
        'content_distribution_score': round(content_distribution_score, 2),
    }


def extract_projects(text: str) -> List[Dict]:
    """
    Extract project entries from resume text.
    Uses section detection to find the projects section, then parses entries.
    """
    sections = detect_sections(text)
    project_section = None
    for section in sections:
        if section['category'] == 'projects':
            project_section = section
            break

    if not project_section:
        # Fallback: look for project-like entries across whole text
        return _extract_project_entries_from_text(text)

    return _extract_project_entries_from_text(project_section['content'])


def _extract_project_entries_from_text(text: str) -> List[Dict]:
    """Parse individual project entries from a block of text."""
    projects = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return projects

    current_entry = None
    current_lines = []

    # Patterns that indicate a new project entry title
    project_title_patterns = [
        re.compile(r'^[A-Z][A-Za-z0-9\s\-/]{2,60}$'),  # Title case line
        re.compile(r'^[A-Z][A-Z\s/]{2,50}$'),  # ALL CAPS title
        re.compile(r'^(?:Project|Title|Name)[:\s]\s*(.+)', re.IGNORECASE),
    ]

    # Technology indicator patterns
    tech_pattern = re.compile(
        r'(?:technolog(?:y|ies)|tools?|used|stack|built with|developed using|'
        r'languages?|frameworks?|libraries?|platforms?)'
        r'[:\s].+', re.IGNORECASE
    )

    date_pattern = re.compile(
        r'\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)[.\s]*\d{4}\b', re.IGNORECASE
    )
    year_pattern = re.compile(r'\b(?:19|20)\d{2}\b')

    for line in lines:
        stripped = line.strip()

        # Skip section headers
        if stripped.lower().rstrip(':') in ('projects', 'project experience', 'academic projects',
                                              'personal projects', 'technical projects', 'key projects'):
            continue

        # Skip lines that look like skill category headers (e.g. "Languages:", "FrontendTechnologies:")
        lower_stripped = stripped.lower()
        skill_category_keywords = ['languages', 'technologies', 'frameworks', 'databases', 'tools',
                                   'platforms', 'frontend', 'backend', 'machine learning', 'data science',
                                   'programming', 'devops', 'cloud', 'soft skills', 'technical skills']
        if any(stripped.lower().startswith(kw) for kw in skill_category_keywords):
            continue

        # Detect if this line looks like a project title (short, capitalized, not a bullet)
        is_bullet = stripped.startswith(('•', '-', '*', '–', '→', '▸', '◆', '●'))
        is_numbered = bool(re.match(r'^\s*\d+[.)]\s', stripped))

        is_title = False
        if not is_bullet and not is_numbered:
            words = stripped.split()
            if 1 <= len(words) <= 6:
                # Check if it's a proper title (capitalized words, not ending with period)
                if (all(w[0].isupper() for w in words if w and not w.startswith('('))
                        and not stripped.endswith('.')
                        and not any(w.lower() in ('the', 'a', 'an', 'and', 'or', 'but', 'for', 'nor', 'on', 'at', 'to', 'by', 'with', 'from', 'in', 'of') and i > 0 for i, w in enumerate(words))):
                    # Check it's not a section header
                    if not any(stripped.lower().rstrip(':') == h for h in [
                        'education', 'experience', 'skills', 'summary', 'profile',
                        'certifications', 'achievements', 'publications', 'languages',
                        'interests', 'references', 'objective'
                    ]):
                        # Check it's not a skill category-like title (single word ending with common suffixes)
                        if len(words) == 1 and any(words[0].lower().endswith(suffix) for suffix in ['ologies', 'works', 'tools', 'skills', 'stacks']):
                            pass  # Don't set is_title
                        else:
                            is_title = True

        if is_title and current_entry:
            # Save previous entry
            project = _finalize_project_entry(current_lines, tech_pattern, date_pattern, year_pattern)
            if project:
                projects.append(project)
            current_lines = [stripped]
        elif is_title and not current_entry:
            current_lines = [stripped]
        elif not is_title and current_lines:
            current_lines.append(stripped)
        elif is_bullet and not current_lines:
            # Bullet without title - treat as description-only entry
            current_lines = [f"Project {len(projects) + 1}", stripped]
        elif is_bullet and current_lines:
            current_lines.append(stripped)

    # Process last entry
    if current_lines:
        project = _finalize_project_entry(current_lines, tech_pattern, date_pattern, year_pattern)
        if project:
            projects.append(project)

    return projects


def _finalize_project_entry(
    lines: List[str],
    tech_pattern,
    date_pattern,
    year_pattern
) -> Optional[Dict]:
    """Convert collected lines into a structured project entry."""
    if not lines:
        return None

    title = lines[0] if lines else "Project"
    description_parts = []
    technologies = []
    dates = ""

    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for date information
        date_matches = date_pattern.findall(stripped)
        year_matches = year_pattern.findall(stripped)
        if date_matches or year_matches:
            if date_matches:
                dates = ', '.join(date_matches[:2])
            elif year_matches:
                dates = f"{year_matches[0]} - {year_matches[1]}" if len(year_matches) >= 2 else year_matches[0] if year_matches else ""

        # Check for technology/tools line
        if tech_pattern.match(stripped):
            # Extract tech names (words after the label)
            tech_text = re.sub(r'^[^:]*[:]\s*', '', stripped)
            # Split by common separators
            techs = re.split(r'[,;|•\-–]+', tech_text)
            technologies.extend([t.strip() for t in techs if t.strip()])
        else:
            # Remove bullet markers for clean description
            clean_line = re.sub(r'^[•\-–*▸◆●]\s*', '', stripped)
            description_parts.append(clean_line)

    # Build description
    description = ' '.join(description_parts)
    description = re.sub(r'\s+', ' ', description).strip()

    # De-duplicate technologies
    technologies = list(dict.fromkeys([t for t in technologies if t]))

    # Filter out URLs from technologies
    technologies = [t for t in technologies if not t.startswith(('http', 'www', 'github'))]

    if not description and not technologies:
        return None

    return {
        'title': title,
        'description': description[:500] if description else '',
        'technologies': technologies,
        'dates': dates,
    }


def generate_improvement_suggestions(
    skills: List[str],
    experience_years: float,
    education: List[Dict],
    experience_list: List[Dict],
    projects_list: List[Dict],
    sections: List[Dict],
    section_distribution: Dict,
    section_quality: Dict,
    skills_list: List[str]  # keeping as alias for clarity
) -> List[Dict]:
    """
    Generate actionable improvement suggestions for the resume based on
    analysis of missing sections, skill gaps, content quality, and best practices.
    Returns a list of suggestion dicts with category, priority, and recommendation.
    """
    suggestions = []

    found_categories = set(s['category'] for s in sections if s['category'] in
                           ['summary', 'experience', 'education', 'skills', 'projects',
                            'certifications', 'achievements', 'publications', 'languages'])

    missing_critical = section_distribution.get('missing_critical_sections', [])

    # ============================================================
    # 1. Missing Section Suggestions (HIGH priority)
    # ============================================================

    # Projects section
    if 'projects' not in found_categories and 'projects' not in missing_critical:
        suggestions.append({
            'category': 'missing_section',
            'priority': 'high',
            'icon': '📁',
            'title': 'Add a Projects Section',
            'recommendation': (
                'Your resume is missing a dedicated Projects section. '
                'Adding 2-3 key projects (work, academic, or personal) '
                'showcases practical application of your skills and significantly '
                'improves ATS visibility. Include project name, technologies used, '
                'and measurable outcomes.'
            ),
        })

    if 'projects' in found_categories and len(projects_list) == 0:
        suggestions.append({
            'category': 'projects_quality',
            'priority': 'medium',
            'icon': '📁',
            'title': 'Improve Project Descriptions',
            'recommendation': (
                'Your resume has a Projects section but entries were not well-detected. '
                'Ensure each project has a clear title, technologies used (e.g., '
                '"Technologies: Python, Django, PostgreSQL"), and 2-3 bullet points '
                'describing your contributions and outcomes.'
            ),
        })

    # Summary/Profile section
    if 'summary' not in found_categories:
        suggestions.append({
            'category': 'missing_section',
            'priority': 'high',
            'icon': '📝',
            'title': 'Add a Professional Summary',
            'recommendation': (
                'A 2-3 sentence professional summary at the top of your resume '
                'helps recruiters quickly understand your profile. Highlight your '
                'years of experience, key skills, and career objectives. '
                'Example: "Experienced software engineer with 5+ years building '
                'scalable web applications using Python and React."'
            ),
        })

    # Certifications section
    if 'certifications' not in found_categories:
        suggestions.append({
            'category': 'missing_section',
            'priority': 'medium',
            'icon': '🎓',
            'title': 'Consider Adding Certifications',
            'recommendation': (
                'If you hold any professional certifications (AWS, Google Cloud, '
                'Scrum Master, etc.), add a dedicated Certifications section. '
                'Certifications can boost your ATS score and differentiate you '
                'from other candidates.'
            ),
        })

    # Achievements section
    if 'achievements' not in found_categories:
        suggestions.append({
            'category': 'missing_section',
            'priority': 'medium',
            'icon': '🏆',
            'title': 'Add an Achievements/Awards Section',
            'recommendation': (
                'Highlighting awards, recognitions, or significant accomplishments '
                'adds credibility to your resume. Even small recognitions like '
                '"Employee of the Month" or hackathon wins make a difference.'
            ),
        })

    # ============================================================
    # 2. Content Quality Suggestions
    # ============================================================

    # Experience quality
    exp_quality = section_quality.get('experience_quality', 0)
    if exp_quality < 40:
        suggestions.append({
            'category': 'content_quality',
            'priority': 'high',
            'icon': '💼',
            'title': 'Improve Experience Descriptions',
            'recommendation': (
                'Your work experience section needs more detail. For each role, '
                'include 3-5 bullet points that: (1) start with strong action verbs '
                '(Developed, Implemented, Led), (2) include quantified results '
                '(e.g., "improved performance by 30%"), and (3) mention specific '
                'technologies used. Use the STAR method (Situation, Task, Action, Result).'
            ),
        })

    # Bullet point usage
    total_bullets = section_quality.get('bullet_point_usage', 0)
    if total_bullets < 5:
        suggestions.append({
            'category': 'content_quality',
            'priority': 'high',
            'icon': '📋',
            'title': 'Use More Bullet Points',
            'recommendation': (
                f'Your resume currently has only {total_bullets} bullet point(s). '
                'ATS systems and recruiters prefer bullet-pointed content as it is '
                'easier to scan. Convert paragraph descriptions into 3-5 concise '
                'bullet points per role or project.'
            ),
        })

    # Quantified achievements
    quantified = section_quality.get('quantified_achievements', 0)
    if quantified < 2:
        suggestions.append({
            'category': 'content_quality',
            'priority': 'medium',
            'icon': '📊',
            'title': 'Add Quantified Achievements',
            'recommendation': (
                'Resumes with quantified achievements (percentages, revenue impact, '
                'time saved, team size managed) perform better. Replace generic '
                'statements like "improved performance" with "improved query performance '
                'by 40% resulting in 2× faster page loads."'
            ),
        })

    # Action verb density
    verb_density = section_quality.get('action_verb_density', 0)
    if verb_density < 1.0:
        suggestions.append({
            'category': 'content_quality',
            'priority': 'medium',
            'icon': '💪',
            'title': 'Use Stronger Action Verbs',
            'recommendation': (
                'Start bullet points with powerful action verbs like: Developed, '
                'Implemented, Architected, Optimized, Led, Designed, Delivered, '
                'Transformed, Streamlined. Avoid weak verbs like "Was responsible for" '
                'or "Worked on."'
            ),
        })

    # ============================================================
    # 3. Skills-Related Suggestions
    # ============================================================

    skills_count = len(skills)
    if skills_count < 10:
        suggestions.append({
            'category': 'skills',
            'priority': 'high',
            'icon': '🛠️',
            'title': 'Expand Your Skills Section',
            'recommendation': (
                f'Only {skills_count} skills were detected from your resume. '
                'Aim to list 15-25 relevant technical skills grouped by category '
                '(Languages, Frameworks, Databases, Tools). Include both hard skills '
                'and relevant soft skills. Match skills to the jobs you are targeting.'
            ),
        })

    # Skills organization
    skill_org = section_quality.get('skills_organization', 0)
    if skill_org < 50 and skills_count >= 5:
        suggestions.append({
            'category': 'skills',
            'priority': 'medium',
            'icon': '📂',
            'title': 'Better Organize Your Skills',
            'recommendation': (
                'Organize your skills into clear categories like "Programming Languages", '
                '"Frameworks & Libraries", "Databases", "Tools & Platforms". This makes '
                'it easier for both ATS systems and recruiters to quickly assess your '
                'technical fit for a role.'
            ),
        })

    # ============================================================
    # 4. Education Suggestions
    # ============================================================

    edu_quality = section_quality.get('education_quality', 0)
    if edu_quality < 40 and len(education) > 0:
        suggestions.append({
            'category': 'education',
            'priority': 'medium',
            'icon': '📚',
            'title': 'Add More Detail to Education',
            'recommendation': (
                'Your education entries lack detail. For each degree, include: '
                'degree type and field of study, institution name, graduation year, '
                'and optionally GPA (if 3.5+), relevant coursework, or academic honors.'
            ),
        })
    elif len(education) == 0:
        suggestions.append({
            'category': 'education',
            'priority': 'medium',
            'icon': '📚',
            'title': 'Verify Education Information',
            'recommendation': (
                'No education entries were detected from your resume. Ensure your '
                'education details include degree name, institution, and graduation '
                'year. Even if you are a self-taught developer, listing relevant '
                'courses or bootcamps is beneficial.'
            ),
        })

    # ============================================================
    # 5. Formatting Suggestions
    # ============================================================

    overall_format = section_quality.get('overall_formatting', 0)
    if overall_format < 40:
        suggestions.append({
            'category': 'formatting',
            'priority': 'high',
            'icon': '🎨',
            'title': 'Improve Resume Formatting',
            'recommendation': (
                'Your resume formatting needs improvement. Use a clean, professional '
                'layout with clear section headers, consistent font sizes, and '
                'appropriate white space. Ensure contact information (email, phone) '
                'is prominently displayed at the top.'
            ),
        })

    # Contact info
    has_contact = section_quality.get('has_contact_info', False)
    if not has_contact:
        suggestions.append({
            'category': 'formatting',
            'priority': 'high',
            'icon': '📞',
            'title': 'Add Contact Information',
            'recommendation': (
                'Your resume is missing contact information (email and/or phone number). '
                'Ensure both email and phone number are clearly visible at the top of '
                'your resume. Consider adding LinkedIn profile URL and GitHub/portfolio '
                'links if relevant.'
            ),
        })

    # ============================================================
    # 6. Role-Specific Suggestions
    # ============================================================

    # Check if certain in-demand skills are missing
    high_demand_skills = {
        'python': 'Python programming skills',
        'sql': 'SQL/database skills',
        'git': 'Git version control',
        'docker': 'Docker/containerization',
        'aws': 'AWS cloud platform',
        'react': 'React frontend framework',
        'javascript': 'JavaScript programming',
    }

    missing_demand = [v for k, v in high_demand_skills.items() if k not in skills]
    if len(missing_demand) >= 3:
        suggestions.append({
            'category': 'skill_gap',
            'priority': 'medium',
            'icon': '📈',
            'title': 'Consider Adding In-Demand Skills',
            'recommendation': (
                'Your resume is missing several high-demand skills commonly sought '
                'by employers. Consider adding or highlighting: ' +
                ', '.join(missing_demand[:5]) +
                '. Even familiarity with these technologies can strengthen your profile.'
            ),
        })

    # ============================================================
    # 7. Content Balance Suggestions
    # ============================================================

    content_balance = section_distribution.get('content_balance', 'none')
    if content_balance in ('fair', 'poor', 'none'):
        unbalanced = section_distribution.get('unbalanced_sections', [])
        if unbalanced:
            suggestions.append({
                'category': 'balance',
                'priority': 'medium',
                'icon': '⚖️',
                'title': 'Balance Content Across Sections',
                'recommendation': (
                    f'The "{unbalanced[0]}" section dominates your resume '
                    'content. Aim for balanced coverage across all sections. '
                    'A well-proportioned resume (with good experience, skills, '
                    'education, and optionally projects) scores higher on ATS systems.'
                ),
            })

    return suggestions


def match_job_roles(skills: List[str], experience_years: float) -> List[Dict]:
    """
    Match candidate's profile against predefined job roles.
    Returns sorted list of role matches with scores.
    """
    job_roles = {
        'Software Engineer': {
            'required': ['python', 'javascript', 'java', 'sql', 'git'],
            'preferred': ['react', 'django', 'aws', 'docker', 'typescript'],
            'min_exp': 1,
        },
        'Data Scientist': {
            'required': ['python', 'r', 'sql', 'machine learning', 'statistics'],
            'preferred': ['tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'],
            'min_exp': 1,
        },
        'DevOps Engineer': {
            'required': ['docker', 'kubernetes', 'jenkins', 'aws', 'git', 'linux'],
            'preferred': ['terraform', 'ansible', 'ci/cd', 'python', 'bash'],
            'min_exp': 2,
        },
        'Full Stack Developer': {
            'required': ['javascript', 'react', 'node.js', 'html', 'css', 'sql'],
            'preferred': ['python', 'typescript', 'aws', 'docker', 'mongodb'],
            'min_exp': 1,
        },
        'Data Engineer': {
            'required': ['python', 'sql', 'apache spark', 'hadoop', 'aws'],
            'preferred': ['scala', 'kafka', 'airflow', 'cassandra', 'mongodb'],
            'min_exp': 2,
        },
        'Machine Learning Engineer': {
            'required': ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'sql'],
            'preferred': ['docker', 'kubernetes', 'aws', 'opencv', 'nltk'],
            'min_exp': 2,
        },
        'Frontend Developer': {
            'required': ['javascript', 'html', 'css', 'react', 'typescript'],
            'preferred': ['vue', 'angular', 'sass', 'redux', 'next.js'],
            'min_exp': 1,
        },
        'Backend Developer': {
            'required': ['python', 'django', 'sql', 'rest api', 'git'],
            'preferred': ['aws', 'docker', 'postgresql', 'redis', 'fastapi'],
            'min_exp': 1,
        },
        'Product Manager': {
            'required': ['project management', 'agile', 'scrum', 'leadership'],
            'preferred': ['jira', 'confluence', 'analytical', 'communication'],
            'min_exp': 3,
        },
        'Cloud Architect': {
            'required': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux'],
            'preferred': ['terraform', 'ansible', 'python', 'networking', 'security'],
            'min_exp': 5,
        },
    }

    skill_set = set(s.lower() for s in skills)
    matches = []

    for role, requirements in job_roles.items():
        required_skills = set(requirements['required'])
        preferred_skills = set(requirements['preferred'])
        min_exp = requirements['min_exp']

        # Calculate skill match
        matched_required = required_skills & skill_set
        matched_preferred = preferred_skills & skill_set

        required_score = (len(matched_required) / len(required_skills)) * 100 if required_skills else 0
        preferred_score = (len(matched_preferred) / len(preferred_skills)) * 100 if preferred_skills else 0

        # Experience bonus
        exp_bonus = min(20, (experience_years - min_exp) * 5) if experience_years >= min_exp else -30

        total_score = (required_score * 0.6 + preferred_score * 0.4) + exp_bonus
        total_score = max(0, min(100, total_score))

        matches.append({
            'role': role,
            'score': round(total_score, 2),
            'matched_skills': list(matched_required | matched_preferred),
            'missing_skills': list((required_skills - skill_set) | (preferred_skills - skill_set)),
            'experience_gap': max(0, min_exp - experience_years),
        })

    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


# ============================================================
# SECTION: Main Analysis Pipeline
# ============================================================

def analyze_resume(file_content: bytes, file_type: str) -> Dict:
    """
    Complete resume analysis pipeline.
    Extracts text, parses information, extracts skills, and calculates ATS score.

    V2.0 improvements:
    - Advanced section detection with multiple detection strategies
    - Section distribution analysis (content balance)
    - Section quality analysis (bullet points, achievements, formatting)
    - Improved ATS scoring with new content distribution component
    """
    # Step 1: Extract text
    text = extract_text(file_content, file_type)
    if not text:
        raise ValueError("No text could be extracted from the resume file.")

    # Step 2: Extract basic info
    email = extract_email(text)
    phone = extract_phone(text)
    candidate_name = extract_candidate_name(text)

    # Step 3: Extract skills
    skills = extract_skills(text)

    # Step 4: Extract experience
    experience_years = extract_experience_years(text)
    education = extract_education(text)
    experience_list = extract_experience(text)

    # Step 5: Advanced section detection and analysis (NEW)
    sections = detect_sections(text)
    section_distribution = calculate_section_distribution(sections)
    section_quality = analyze_section_quality(sections, text)

    # Step 6: Calculate ATS score (improved with section data)
    score_components = calculate_ats_score(
        text, skills, experience_years, education,
        sections, section_distribution, section_quality
    )

    # Step 7: Extract projects
    projects_list = extract_projects(text)

    # Step 8: Generate improvement suggestions (V3)
    improvement_suggestions = generate_improvement_suggestions(
        skills=skills,
        experience_years=experience_years,
        education=education,
        experience_list=experience_list,
        projects_list=projects_list,
        sections=sections,
        section_distribution=section_distribution,
        section_quality=section_quality,
        skills_list=skills,
    )

    # Step 9: Match job roles
    role_matches = match_job_roles(skills, experience_years)

    return {
        'parsed_text': text,
        'candidate_name': candidate_name,
        'email': email,
        'phone': phone,
        'extracted_skills': skills,
        'experience_years': experience_years,
        'education': education,
        'experience_list': experience_list,
        'projects_list': projects_list,
        'improvement_suggestions': improvement_suggestions,
        'ats_score': score_components['ats_score'],
        'keyword_score': score_components['keyword_score'],
        'format_score': score_components['format_score'],
        'experience_score': score_components['experience_score'],
        'education_score': score_components['education_score'],
        'skills_match_score': score_components['skills_match_score'],
        'content_distribution_score': score_components['content_distribution_score'],
        'section_analysis': {
            'detected_sections': [
                {
                    'category': s['category'],
                    'header_name': s['header_name'],
                    'word_count': s['word_count'],
                    'bullet_count': s['bullet_count'],
                    'lines': s['line_count'],
                }
                for s in sections
            ],
            'section_distribution': section_distribution,
            'section_quality': section_quality,
        },
        'suggested_roles': [r['role'] for r in role_matches[:3]],
        'match_scores': role_matches[:5] if role_matches else [],
    }
