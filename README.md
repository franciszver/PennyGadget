# 🎓 ElevareAI

**ElevareAI** is a comprehensive AI-powered tutoring platform that supports students between sessions with adaptive practice, conversational Q&A, personalized nudges, and progress tracking.

[![Status](https://img.shields.io/badge/status-production%20ready-green)]()
[![Tests](https://img.shields.io/badge/tests-127%20passing-brightgreen)]()
[![API](https://img.shields.io/badge/API-64%20endpoints-blue)]()
[![Version](https://img.shields.io/badge/version-1.0.0-orange)]()

---

## ✨ What You Can Do with ElevareAI

### For Students
- 📚 **Get AI-Generated Practice Problems** - Receive adaptive practice questions that adjust to your skill level using an Elo rating system
- 💬 **Ask Questions Anytime** - Get instant answers to your study questions with confidence labels (High/Medium/Low) and tutor escalation when needed
- 📊 **Track Your Progress** - Monitor multiple learning goals with visual progress dashboards, completion percentages, and streaks
- 🎯 **Set and Manage Goals** - Create learning goals, track completion, and reset goals to improve your Elo ratings
- 📝 **Review Session Summaries** - Get narrative recaps of your tutoring sessions with actionable next steps
- 💌 **Receive Personalized Nudges** - Get smart reminders for inactivity, goal completion, and cross-subject suggestions
- 💬 **Message Your Tutor** - Communicate directly with your tutor through threaded messaging

### For Tutors
- 🎛️ **Override AI Recommendations** - Instantly update student progress, goals, and practice difficulty with tutor overrides
- 📈 **View Student Analytics** - Access detailed dashboards showing student progress, engagement, and performance metrics
- 💬 **Communicate with Students** - Message students directly and respond to flagged items
- 📊 **Monitor Confidence Levels** - Track AI confidence scores and identify when students need additional support

### For Parents
- 👀 **View Student Progress** - Access parent dashboards to see your child's learning progress, goals, and achievements
- 📧 **Receive Progress Updates** - Get weekly progress emails and notifications about your child's learning journey
- 📊 **Export Progress Data** - Download detailed reports of your child's academic progress

### For Administrators
- 📊 **Analytics Dashboards** - Comprehensive overview of all students, override patterns, confidence telemetry, and retention metrics
- 🧪 **A/B Testing Framework** - Test different nudge strategies and features to optimize student engagement
- 📤 **Data Export** - Export analytics data for further analysis
- 🔗 **Integration Management** - Connect with LMS systems (Canvas, Blackboard), calendars (Google, Outlook), and webhooks

---

## 🚀 Quick Start

### Backend (API)
```bash
# Option 1: Using Python module (Recommended)
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using the run script
python run_server.py

# Option 3: Using helper script
.\START_SERVER.ps1  # Windows
./START_SERVER.sh   # Linux/Mac
```

### Frontend
```bash
cd examples/frontend-starter
npm install
npm run dev
# Open http://localhost:3000
```

### Docker
```bash
# Build and start all services (PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# API available at http://localhost:8000
# Database available at localhost:5432
```

**Note:** Make sure to set environment variables in `.env` file or export them before running `docker-compose up`.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Frontend Development](#-frontend-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## ✨ Features

### Core MVP Features
- ✅ **Session Summaries** - Narrative recaps with actionable next steps
- ✅ **Adaptive Practice** - AI-generated questions with difficulty adjustment
- ✅ **Conversational Q&A** - Confidence-labeled answers with escalation
- ✅ **Personalized Nudges** - Inactivity, goal completion, cross-subject suggestions
- ✅ **Tutor Overrides** - Immediate dashboard updates
- ✅ **Progress Tracking** - Multi-goal tracking with visualizations
- ✅ **Messaging** - Tutor-student communication threads

### Post-MVP Features
- ✅ **Elo Rating System** - Adaptive skill assessment with rating increases/decreases
- ✅ **Goal Reset** - Reset completed goals with low Elo to improve skills
- ✅ **Conversation History** - Persistent Q&A history across sessions
- ✅ **Analytics Dashboards** - Parent and admin views with exports
- ✅ **Advanced Analytics** - Override patterns, confidence telemetry, retention
- ✅ **Integrations** - LMS, Calendar, Push Notifications, Webhooks
- ✅ **A/B Testing** - Framework for testing nudges and features

### Enhancements
- ✅ **Email Notifications** - Message, nudge, and progress emails
- ✅ **Conversation History** - Context-aware Q&A with follow-up detection
- ✅ **Practice Quality** - AI-generated item validation and improvement
- ✅ **Nudge Personalization** - Student insights and personalized messaging

---

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **AI/LLM**: OpenAI GPT-4 (via LangChain)
- **Authentication**: AWS Cognito JWT
- **Email**: AWS SES
- **Testing**: Pytest (127 tests)
- **Logging**: Structlog
- **Validation**: Pydantic 2.5

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **State Management**: TanStack Query
- **HTTP Client**: Axios
- **Routing**: React Router

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: SQL migration scripts
- **Deployment**: AWS-ready (ECS/Fargate, RDS, S3)
- **CI/CD**: GitHub Actions (planned)
- **Monitoring**: Built-in metrics endpoint
- **Logging**: Structured logging with file rotation

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PennyGadget
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your configuration
   # Minimum required variables:
   # - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
   # - OPENAI_API_KEY
   # - COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID (for authentication)
   ```

4. **Set up database**
   ```bash
   # Create database and run migrations
   python scripts/setup_db.py
   
   # Or with custom env file
   python scripts/setup_db.py --env-file .env
   
   # Optional: Seed demo data
   python scripts/seed_demo_data.py
   ```

5. **Run the server**
   ```bash
   python -m uvicorn src.api.main:app --reload
   ```

6. **Access API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** (create `.env` file):
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pennygadget
DB_USER=postgres
DB_PASSWORD=your-password
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# AWS Cognito (Authentication)
COGNITO_USER_POOL_ID=your-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_REGION=us-east-1

# AWS SES (Email)
SES_FROM_EMAIL=noreply@yourdomain.com
SES_REGION=us-east-1

# AWS S3 (Optional - for transcripts)
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
API_VERSION=v1
API_BASE_URL=http://localhost:8000

# Feature Flags
ENABLE_AI_PRACTICE_GENERATION=true
ENABLE_NUDGES=true
ENABLE_ANALYTICS=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Nudge Configuration
DEFAULT_NUDGE_FREQUENCY_CAP=1
NUDGE_INACTIVITY_THRESHOLD_DAYS=7
NUDGE_MIN_SESSIONS_THRESHOLD=3

# Confidence Thresholds
CONFIDENCE_HIGH_THRESHOLD=0.75
CONFIDENCE_MEDIUM_THRESHOLD=0.50

# Adaptive Practice (Elo Rating)
ELO_K_FACTOR=32
ELO_DEFAULT_RATING=1000
ELO_MIN_RATING=400
ELO_MAX_RATING=2000

# External Services (Optional)
RAILS_APP_URL=https://your-rails-app.com
WEBHOOK_SECRET=your-webhook-secret
```

3. **Run database migrations:**
```bash
python scripts/setup_db.py --env-file .env
```

4. **Start the server:**
```bash
python run_server.py
# Or: uvicorn src.api.main:app --reload
```

### API Endpoints

#### Health & Status
- `GET /` - Root endpoint with service info
- `GET /health` - Health check with database status
- `GET /metrics` - Application metrics (production: protect with auth)

#### Session Summaries
- `POST /api/v1/summaries` - Create summary from session
- `GET /api/v1/summaries/{user_id}` - Get session summaries for user

#### Adaptive Practice
- `POST /api/v1/practice/assign` - Assign practice items to student
- `POST /api/v1/practice/assignments/{id}/complete` - Complete practice assignment (updates Elo rating)
- Elo ratings increase with correct answers and decrease with incorrect answers

#### Conversational Q&A
- `POST /api/v1/qa/query` - Submit student query and get AI answer
- `GET /api/v1/enhancements/qa/conversation-history/{student_id}` - Get persistent conversation history
- `GET /api/v1/qa/conversation-context/{student_id}` - Get conversation context

#### Progress Tracking
- `GET /api/v1/progress/{user_id}` - Get student progress dashboard

#### Goals Management
- `GET /api/v1/goals` - Get all goals for student
- `POST /api/v1/goals` - Create new goal
- `POST /api/v1/goals/{goal_id}/reset` - Reset completed goal (status, completion, Elo)
- `DELETE /api/v1/goals/{goal_id}` - Delete goal

#### Personalized Nudges
- `POST /api/v1/nudges/check` - Check if nudge should be sent
- `POST /api/v1/nudges/{nudge_id}/engage` - Track nudge engagement

#### Tutor Overrides
- `POST /api/v1/overrides` - Create tutor override
- `GET /api/v1/overrides/{student_id}` - Get overrides for student

#### Messaging System
- `POST /api/v1/threads` - Create new message thread
- `POST /api/v1/threads/{thread_id}/messages` - Send message in thread
- `GET /api/v1/threads` - List message threads
- `GET /api/v1/threads/{thread_id}` - Get thread details
- `POST /api/v1/threads/{thread_id}/close` - Close thread
- `POST /api/v1/threads/from-flagged-item` - Create thread from flagged item

#### Analytics Dashboards
- `GET /api/v1/dashboards/parent/student/{student_id}` - Parent dashboard for student
- `GET /api/v1/dashboards/parent/students` - Parent dashboard for all students
- `GET /api/v1/dashboards/admin/overview` - Admin overview dashboard
- `GET /api/v1/dashboards/admin/overrides` - Admin override analytics
- `GET /api/v1/dashboards/admin/confidence` - Admin confidence analytics
- `GET /api/v1/dashboards/admin/nudges` - Admin nudge analytics
- `GET /api/v1/dashboards/admin/export` - Export dashboard data

#### Advanced Analytics
- `GET /api/v1/analytics/override-patterns` - Analyze override patterns
- `GET /api/v1/analytics/confidence-telemetry` - Get confidence telemetry
- `GET /api/v1/analytics/retention` - Get retention metrics
- `GET /api/v1/analytics/engagement/{user_id}` - Get user engagement metrics
- `GET /api/v1/analytics/ab-tests/{test_name}/results` - Get A/B test results
- `POST /api/v1/analytics/ab-tests` - Create A/B test
- `GET /api/v1/analytics/ab-tests/statistical-significance` - Check statistical significance

#### Integrations
- `POST /api/v1/integrations/lms/canvas/sync` - Sync with Canvas LMS
- `POST /api/v1/integrations/lms/blackboard/sync` - Sync with Blackboard LMS
- `POST /api/v1/integrations/lms/submit-grade` - Submit grade to LMS
- `POST /api/v1/integrations/calendar/google/sync` - Sync with Google Calendar
- `POST /api/v1/integrations/calendar/google/create-event` - Create Google Calendar event
- `POST /api/v1/integrations/calendar/outlook/sync` - Sync with Outlook Calendar
- `POST /api/v1/integrations/calendar/outlook/create-event` - Create Outlook Calendar event
- `POST /api/v1/integrations/notifications/push` - Send push notification
- `POST /api/v1/integrations/notifications/register-device` - Register device for push
- `POST /api/v1/integrations/notifications/unregister-device` - Unregister device
- `POST /api/v1/integrations/webhooks` - Create webhook
- `GET /api/v1/integrations/webhooks` - List webhooks
- `POST /api/v1/integrations/webhooks/trigger` - Trigger webhook
- `GET /api/v1/integrations/webhooks/{webhook_id}/events` - Get webhook events
- `POST /api/v1/integrations/webhooks/events/{event_id}/retry` - Retry webhook event

#### Enhancements
- `POST /api/v1/email/send` - Send email notification
- `POST /api/v1/email/weekly-progress` - Send weekly progress email
- `POST /api/v1/email/batch` - Send batch emails

### Authentication

The API supports two authentication methods:

1. **User Authentication (AWS Cognito JWT)**
   - Required for user-facing endpoints
   - Include the token in the Authorization header:
   ```
   Authorization: Bearer <your-jwt-token>
   ```

2. **Service-to-Service Authentication (API Key)**
   - Required for service-to-service calls
   - Include the API key in the X-API-Key header:
   ```
   X-API-Key: <your-api-key>
   ```

**Note:** Health check endpoints (`/`, `/health`) do not require authentication.

### Error Handling

The API returns standardized error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [API Documentation](http://localhost:8000/docs) for complete endpoint list with interactive testing.

---

## 💻 Frontend Development

### Starter Template
A complete React frontend starter is available in `examples/frontend-starter/`:

```bash
cd examples/frontend-starter
npm install
npm run dev
```

### Features
- ✅ React Router navigation
- ✅ TanStack Query for API state management
- ✅ Axios HTTP client with interceptors
- ✅ Authentication context and protected routes
- ✅ Complete page implementations:
  - Dashboard - Overview, quick actions, and nudges
  - Practice - Adaptive practice assignments with Elo rating updates
  - Q&A - Conversational question answering with persistent history
  - Progress - Student progress tracking with Elo ratings
  - Goals - Goal management with Elo ratings and reset functionality
  - Messaging - Tutor-student communication
  - Settings - User preferences
  - Login - Authentication

### Integration
- See `_docs/guides/FRONTEND_INTEGRATION.md` for detailed integration guide
- API client examples available in `examples/api-client/`
- Frontend starter includes complete authentication flow
- Complete feature documentation in `examples/frontend-starter/FEATURES_COMPLETE.md`

---

## 🚢 Deployment

### Staging
```bash
# Create staging environment
python scripts/create_staging_env.py

# Deploy to staging
.\scripts\deploy_to_staging.ps1  # Windows
./scripts/deploy_to_staging.sh   # Linux/Mac
```

### Production
- See `_docs/guides/DEPLOYMENT_CHECKLIST.md` for deployment checklist
- See `_docs/active/DEPLOYMENT_PRD.md` for complete deployment guide
- AWS deployment scripts in `scripts/deployment/`:
  - `deploy-aws.ps1` - Initial setup (Steps 1-5)
  - `deploy-aws-step2.ps1` - Infrastructure (Steps 6-12)
  - `deploy-aws-step3.ps1` - Backend deployment (Steps 13-16)
  - `deploy-aws-step4.ps1` - Database & demo setup (Steps 17-19)
  - `deploy-aws-step5.ps1` - Frontend deployment (Steps 20-23)
- AWS infrastructure setup scripts in `scripts/setup_aws_infrastructure.sh/.ps1`
- Docker production configuration in `Dockerfile` (multi-stage build)

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_practice.py

# With coverage
pytest --cov=src tests/
```

### Test Coverage
- **127 tests** covering all features
- Unit tests for services and models
- Integration tests for complete workflows
- Edge case coverage for practice, progress, and Q&A
- Golden response tests for AI consistency
- Test fixtures and helpers in `tests/fixtures/`

### Running Specific Tests
```bash
# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_practice.py -v

# Run with coverage report
pytest --cov=src --cov-report=html tests/

# Run only integration tests
pytest tests/test_integration_*.py
```

---

## 📖 Documentation

### PRDs (Product Requirements Documents)
- `_docs/active/MVP_PRD.md` - MVP features
- `_docs/active/POST_MVP_PRD.md` - Post-MVP features
- `_docs/active/FRONTEND_PRD.md` - Frontend development
- `_docs/active/DEPLOYMENT_PRD.md` - Production deployment
- `_docs/active/USER_TESTING_PRD.md` - User testing
- `_docs/PRD_INDEX.md` - Complete PRD index

### Guides
- `_docs/guides/QUICK_START.md` - Quick setup guide
- `_docs/guides/DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- `_docs/guides/USER_TESTING.md` - Beta testing guide
- `_docs/guides/STAGING_SETUP.md` - Staging environment
- `_docs/guides/FRONTEND_INTEGRATION.md` - Frontend integration
- `_docs/guides/DEPLOYMENT.md` - Deployment guide
- `_docs/guides/DEMO_GUIDE.md` - Demo guide
- `_docs/guides/CI_CD.md` - CI/CD pipeline
- `_docs/guides/PERFORMANCE_OPTIMIZATION.md` - Performance guide

### Status & Next Steps
- `_docs/status/PROJECT_STATUS.md` - Complete project status
- `_docs/NEXT_STEPS.md` - Next steps guide

---

## 🛠️ Project Structure

```
PennyGadget/
├── src/                           # Source code
│   ├── api/                       # FastAPI application
│   │   ├── handlers/              # Route handlers (13 files)
│   │   │   ├── summaries.py       # Session summaries
│   │   │   ├── practice.py        # Adaptive practice
│   │   │   ├── qa.py              # Q&A system
│   │   │   ├── progress.py        # Progress tracking
│   │   │   ├── nudges.py          # Personalized nudges
│   │   │   ├── overrides.py       # Tutor overrides
│   │   │   ├── messaging.py       # Messaging system
│   │   │   ├── goals.py            # Goals management
│   │   │   ├── dashboards.py      # Analytics dashboards
│   │   │   ├── advanced_analytics.py  # Advanced analytics
│   │   │   ├── integrations.py    # External integrations
│   │   │   └── enhancements.py    # Enhancement features
│   │   ├── schemas/               # Pydantic request/response models
│   │   └── middleware/             # Middleware
│   │       ├── auth.py            # Authentication
│   │       ├── error_handlers.py  # Error handling
│   │       ├── metrics.py         # Metrics collection
│   │       └── request_logging.py # Request logging
│   ├── services/                  # Business logic services
│   │   ├── ai/                    # AI/LLM services
│   │   │   ├── openai_client.py   # OpenAI client
│   │   │   ├── summarizer.py      # Summary generation
│   │   │   ├── prompts.py         # Prompt templates
│   │   │   ├── confidence.py      # Confidence scoring
│   │   │   └── query_analyzer.py  # Query analysis
│   │   ├── analytics/             # Analytics services
│   │   │   ├── aggregator.py      # Data aggregation
│   │   │   ├── advanced.py        # Advanced analytics
│   │   │   ├── exporter.py        # Data export
│   │   │   └── ab_testing.py      # A/B testing
│   │   ├── goals/                  # Goal services
│   │   │   └── progress.py        # Goal progress tracking
│   │   ├── practice/              # Practice services
│   │   │   ├── adaptive.py       # Adaptive difficulty
│   │   │   ├── generator.py       # Practice generation
│   │   │   └── quality.py         # Quality validation
│   │   ├── nudges/                # Nudge services
│   │   │   ├── engine.py          # Nudge engine
│   │   │   ├── personalization.py # Personalization
│   │   │   └── email_service.py   # Email nudges
│   │   ├── qa/                    # Q&A services
│   │   │   └── conversation_history.py  # Conversation tracking
│   │   ├── integrations/          # External integrations
│   │   │   ├── lms.py             # LMS integration
│   │   │   ├── calendar.py        # Calendar integration
│   │   │   ├── notifications.py   # Push notifications
│   │   │   └── webhooks.py        # Webhook system
│   │   └── notifications/          # Notification services
│   │       └── email.py           # Email notifications
│   ├── models/                    # SQLAlchemy database models
│   │   ├── user.py                # User model
│   │   ├── session.py             # Session model
│   │   ├── summary.py             # Summary model
│   │   ├── practice.py            # Practice models
│   │   ├── qa.py                  # Q&A models
│   │   ├── progress.py            # Progress models
│   │   ├── nudge.py               # Nudge model
│   │   ├── override.py            # Override model
│   │   ├── messaging.py           # Messaging models
│   │   ├── subject.py             # Subject model
│   │   ├── goal.py                # Goal model
│   │   ├── integration.py         # Integration models
│   │   └── tutor_student.py       # Tutor-student relationships
│   ├── config/                     # Configuration
│   │   ├── settings.py            # Application settings
│   │   └── database.py            # Database configuration
│   └── utils/                      # Utility modules
│       ├── logging_config.py      # Logging setup
│       ├── metrics.py             # Metrics utilities
│       └── cache.py               # Caching utilities
├── tests/                          # Test suite (127 tests)
│   ├── test_api_endpoints.py      # API endpoint tests
│   ├── test_models.py             # Model tests
│   ├── test_practice_edge_cases.py # Practice edge cases
│   ├── test_integrations.py       # Integration tests
│   ├── test_gamification.py       # Gamification tests
│   └── ...                        # Additional test files
├── examples/                       # Code examples
│   ├── frontend-starter/          # Complete React frontend
│   │   ├── src/
│   │   │   ├── pages/             # 9 page components
│   │   │   ├── components/        # Reusable components
│   │   │   ├── contexts/          # React contexts
│   │   │   ├── hooks/             # Custom hooks
│   │   │   └── services/          # API services
│   │   └── package.json
│   ├── react/                     # React component examples
│   └── api-client/                # API client examples
├── scripts/                        # Utility scripts
│   ├── deployment/                 # AWS deployment scripts
│   │   ├── deploy-aws.ps1         # Initial AWS setup
│   │   ├── deploy-aws-step2.ps1    # Infrastructure setup
│   │   ├── deploy-aws-step3.ps1    # Backend deployment
│   │   ├── deploy-aws-step4.ps1    # Database & demo setup
│   │   ├── deploy-aws-step5.ps1    # Frontend deployment
│   │   ├── deploy-frontend.ps1     # Frontend deployment
│   │   └── ...                     # Additional deployment scripts
│   ├── setup_db.py                # Database setup
│   ├── seed_demo_data.py          # Demo data seeding
│   ├── create_staging_env.py      # Staging environment
│   ├── setup_beta_testing.py      # Beta testing setup
│   ├── verify_complete_system.py  # System verification
│   ├── verify_all_demo_accounts.py # Demo account verification
│   └── ...                        # Additional scripts
├── migrations/                     # Database migrations
│   └── 001_initial_schema.sql     # Initial database schema
├── logs/                           # Application logs
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile                      # Docker image definition
├── requirements.txt                # Python dependencies
├── run_server.py                   # Development server runner
├── START_SERVER.sh/.ps1            # Server startup scripts
└── _docs/                          # Documentation
    ├── active/                     # Active PRDs
    ├── guides/                     # Setup and deployment guides
    ├── status/                     # Project status
    └── qa/                         # QA documentation
```

---

## 🎯 Next Steps

1. **Set up Staging Environment**
   - Run `python scripts/create_staging_env.py`
   - Configure `.env.staging`
   - Deploy to staging

2. **Develop Frontend**
   - Use `examples/frontend-starter/`
   - Integrate with API
   - Customize styling

3. **Begin Beta Testing**
   - Run `python scripts/setup_beta_testing.py`
   - Recruit test users
   - Collect feedback

4. **Deploy to Production**
   - Follow `DEPLOYMENT_CHECKLIST.md`
   - Configure production services
   - Monitor and optimize

See `_docs/NEXT_STEPS.md` for detailed next steps.

---

## 📊 Project Statistics

- **API Endpoints**: 64+ endpoints across 12 route handlers
- **Test Coverage**: 127 tests passing
- **Services**: 20+ service modules across 8 service categories
- **Database Models**: 15+ SQLAlchemy models
- **Frontend Pages**: 9 complete React pages
- **Lines of Code**: ~15,000+ lines
- **Python Dependencies**: 30+ packages
- **Database Tables**: 15+ tables with indexes and constraints

---

## 🤝 Contributing

1. Review the relevant PRD in `_docs/active/`
2. Check existing code structure
3. Write tests for new features
4. Update documentation
5. Submit pull request

---

## 📞 Support

- **Documentation**: See `_docs/guides/` directory
- **API Docs**: http://localhost:8000/docs
- **PRDs**: See `_docs/active/`
- **Status**: See `_docs/status/PROJECT_STATUS.md`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License** is a permissive open-source license that allows:
- Commercial use
- Modification
- Distribution
- Private use
- Patent use

The only requirement is to include the license and copyright notice.

---

## 🎉 Status

**✅ All Features Implemented**  
**✅ Production Ready**  
**✅ Fully Documented**  
**✅ Ready for Next Phase**

See `_docs/status/PROJECT_STATUS.md` for complete status.

---

**Built with ❤️ for education**
