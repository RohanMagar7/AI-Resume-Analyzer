# AI Resume Analyzer

An intelligent resume analysis tool that leverages Natural Language Processing (NLP) and Machine Learning to parse, analyze, and score resumes against industry standards. Built with Django REST Framework and React, it provides detailed ATS (Applicant Tracking System) scoring, skill extraction, job role matching, and actionable improvement suggestions.

## 🚀 Features

### 📄 Resume Parsing & Analysis
- **Multi-format Support**: Upload PDF and DOCX resume files
- **Intelligent Text Extraction**: Extract and structure resume content using NLP
- **Contact Information Parsing**: Automatically extract name, email, and phone number
- **Education & Experience Detection**: Identify educational background and work history
- **Project Extraction**: Parse project entries with descriptions and technologies used

### 📊 ATS Scoring System
Comprehensive scoring across six dimensions:

| Score Component | Description |
|----------------|-------------|
| **Keyword Score** | Relevance of keywords against industry standards |
| **Format Score** | Resume structure, formatting, and readability |
| **Experience Score** | Quality and relevance of work experience |
| **Education Score** | Educational qualifications assessment |
| **Skills Match Score** | Alignment with job role requirements |
| **Content Distribution Score** | Balance of content across resume sections |

### 🎯 Job Role Matching
- Match resumes against predefined job roles
- Identify suggested roles based on skills and experience
- Calculate match percentages for different positions
- Compare required vs. preferred skill coverage

### 💡 Intelligent Suggestions
- **Section Analysis**: Detect and evaluate resume sections (summary, experience, education, skills, projects)
- **Improvement Suggestions**: Generate actionable recommendations to improve ATS score
- **Content Distribution Analysis**: Evaluate how well content is distributed across sections

### 📈 Analytics Dashboard
- **Aggregate Statistics**: View total resumes analyzed, average ATS scores, and experience metrics
- **Score Distribution**: Track score ranges (Excellent, Good, Average, Poor)
- **Top Skills**: Identify the most common skills across all analyzed resumes
- **Role Distribution**: See which job roles resumes are most frequently matched to
- **Recent Analyses**: Quick access to the most recent resume analyses

## 🏗️ Architecture

```
AI Resume Analyzer/
├── backend/                          # Django REST Framework API
│   ├── api/                          # REST API endpoints
│   │   ├── serializers.py            # DRF serializers
│   │   ├── urls.py                   # API URL routing
│   │   └── views.py                  # API view handlers
│   ├── config/                       # Django project configuration
│   │   ├── settings.py               # Settings (DB, CORS, auth)
│   │   ├── urls.py                   # Root URL configuration
│   │   └── wsgi.py                   # WSGI entry point
│   ├── media/resumes/                # Uploaded resume file storage
│   ├── resume_parser/                # Core NLP processing engine
│   │   ├── models.py                 # Resume, SkillDatabase, JobRole models
│   │   ├── parser_engine.py          # NLP analysis engine
│   │   └── admin.py                  # Django admin configuration
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Python dependencies
│   └── db.sqlite3                    # Development database
├── frontend/                         # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx         # Analytics dashboard
│   │   │   ├── Navbar.jsx            # Navigation bar
│   │   │   ├── Results.jsx           # Detailed analysis results
│   │   │   ├── ResumeList.jsx        # Resume history list
│   │   │   └── Upload.jsx            # File upload with drag & drop
│   │   ├── App.jsx                   # Root React app component
│   │   ├── api.js                    # Axios API client
│   │   ├── index.css                 # Global styles
│   │   └── main.jsx                  # React entry point
│   ├── index.html
│   ├── package.json                  # Node dependencies
│   └── vite.config.js                # Vite configuration
└── README.md
```

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Django 5.0** | Web framework |
| **Django REST Framework** | REST API construction |
| **spaCy 3.7** | Advanced NLP pipeline |
| **NLTK 3.8** | Natural language processing toolkit |
| **scikit-learn 1.5** | Machine learning utilities |
| **PyPDF2** | PDF text extraction |
| **python-docx** | DOCX text extraction |
| **pandas / numpy** | Data processing and analysis |
| **PostgreSQL / SQLite** | Database (configurable) |
| **Gunicorn** | Production WSGI server |
| **Whitenoise** | Static file serving |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool and dev server |
| **React Router 6** | Client-side routing |
| **Axios** | HTTP client for API communication |
| **Recharts** | Interactive data visualizations |

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/RohanMagar7/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
```

#### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Run database migrations
python manage.py migrate

# (Optional) Load sample job roles and skill data
python manage.py loaddata initial_data

# Create a superuser for admin access
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

#### 3. Frontend Setup
```bash
# In a new terminal, from the project root
cd frontend
npm install

# Start the Vite development server
npm run dev
```

#### 4. Access the Application
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

## 📡 API Reference

### Resume Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/` | Upload and analyze a resume |
| `GET` | `/api/resumes/` | List all analyzed resumes (paginated) |
| `GET` | `/api/resumes/<uuid>/` | Get detailed analysis for a resume |
| `DELETE` | `/api/resumes/<uuid>/` | Delete a resume record |
| `GET` | `/api/dashboard/` | Get aggregate analytics |
| `GET` | `/api/health/` | Health check endpoint |

### Upload Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Resume file (PDF or DOCX, max 10MB) |
| `target_role` | String | No | Optional target job role for matching |

### Query Parameters (List Resumes)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | Integer | 1 | Page number |
| `page_size` | Integer | 10 | Items per page (max 100) |
| `status` | String | - | Filter by status (completed, processing, failed) |
| `sort` | String | -created_at | Sort field (created_at, ats_score, experience_years) |

## 📊 Analysis Results

When a resume is analyzed, the API returns comprehensive results including:

```json
{
  "id": "uuid-string",
  "candidate_name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "extracted_skills": ["Python", "Django", "React", "PostgreSQL"],
  "experience_years": 5.5,
  "education": [
    {"degree": "B.S. Computer Science", "institution": "University", "year": "2020"}
  ],
  "experience_list": [
    {"company": "Tech Corp", "role": "Software Engineer", "duration": "2020-2024"}
  ],
  "projects_list": [
    {"name": "AI Tool", "description": "...", "technologies": ["Python", "NLP"]}
  ],
  "ats_score": 78.5,
  "keyword_score": 72.0,
  "format_score": 85.0,
  "experience_score": 70.0,
  "education_score": 80.0,
  "skills_match_score": 75.0,
  "content_distribution_score": 82.0,
  "section_analysis": {
    "sections_found": ["summary", "experience", "education", "skills", "projects"],
    "missing_sections": ["certifications"],
    "section_quality": { "...": "..." }
  },
  "improvement_suggestions": [
    "Add more quantifiable achievements in your experience section",
    "Include a professional summary at the top of your resume"
  ],
  "suggested_roles": ["Software Engineer", "Full Stack Developer"],
  "match_scores": {
    "Software Engineer": 85.5,
    "Full Stack Developer": 78.0
  },
  "status": "completed",
  "created_at": "2026-06-07T12:00:00Z"
}
```

## ⚙️ Configuration

### Database Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `USE_SQLITE` | Force SQLite for development | `True` |
| `DATABASE_URL` | Production PostgreSQL connection string | - |
| `DB_NAME` | PostgreSQL database name | `resume_analyzer` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `postgres` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |

### Django Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Secret key for Django | Auto-generated dev key |
| `DJANGO_DEBUG` | Debug mode toggle | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |

### CORS Configuration
- Development: All origins allowed when `DEBUG=True`
- Allowed origins: `http://localhost:5173`, `http://127.0.0.1:5173`

## 🔒 Security

- File type validation (PDF/DOCX only)
- File size limit (10MB)
- Input sanitization for uploaded content
- CORS configuration for frontend-backend communication

## 🧪 Development

### Running Tests
```bash
cd backend
python manage.py test
```

### Database Management
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (delete and recreate)
rm db.sqlite3 && python manage.py migrate
```

## 🚀 Production Deployment

### Backend (using Gunicorn)
```bash
cd backend
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

### Frontend Build
```bash
cd frontend
npm run build
# Output in frontend/dist/ - serve with any static server
```

### Environment Variables for Production
```bash
export DJANGO_SECRET_KEY="your-secure-secret-key"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
export USE_SQLITE="False"
export DATABASE_URL="postgres://user:pass@host:5432/dbname"
```

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Built with ❤️ by [Rohan Magar](https://github.com/RohanMagar7)