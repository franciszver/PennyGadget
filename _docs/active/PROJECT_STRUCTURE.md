# 📁 Project Structure
**Product:** AI Study Companion MVP  
**Architecture:** AWS Serverless (API Gateway + Lambda/ECS)  
**Language:** Python (recommended for AI/ML) or Node.js  
**Database:** PostgreSQL on AWS RDS

---

## Recommended Project Structure

```
PennyGadget/
├── _docs/                          # Documentation (existing)
│   ├── active/                     # Active PRDs and specs
│   ├── qa/                         # Test cases and golden responses
│   └── executed/                   # Completed/archived docs
│
├── src/                            # Source code
│   ├── api/                        # API Gateway handlers
│   │   ├── handlers/              # Lambda handlers
│   │   │   ├── summaries.py      # POST /summaries
│   │   │   ├── practice.py        # POST /practice/assign
│   │   │   ├── qa.py              # POST /qa/query
│   │   │   ├── nudges.py          # POST /nudges/send
│   │   │   ├── overrides.py       # POST /overrides
│   │   │   └── progress.py        # GET /progress/:user_id
│   │   ├── middleware/            # Auth, logging, error handling
│   │   │   ├── auth.py            # Cognito token validation
│   │   │   ├── logger.py          # Structured logging
│   │   │   └── errors.py          # Error handling
│   │   └── utils/                 # Shared utilities
│   │       ├── db.py              # Database connection pool
│   │       ├── validators.py      # Input validation
│   │       └── responses.py       # Standardized API responses
│   │
│   ├── services/                  # Business logic services
│   │   ├── ai/                    # AI/LLM services
│   │   │   ├── openai_client.py  # OpenAI API wrapper
│   │   │   ├── prompts.py         # Prompt templates
│   │   │   ├── confidence.py      # Confidence calculation
│   │   │   └── summarizer.py     # Session summary generation
│   │   ├── practice/              # Practice assignment logic
│   │   │   ├── adaptive.py        # Difficulty adjustment (Elo)
│   │   │   ├── bank_manager.py    # Practice bank operations
│   │   │   └── generator.py      # AI practice item generation
│   │   ├── nudges/                # Nudge system
│   │   │   ├── engine.py          # Nudge decision logic
│   │   │   ├── personalizer.py    # Personalization
│   │   │   └── email_service.py   # AWS SES integration
│   │   └── analytics/             # Analytics tracking
│   │       ├── tracker.py         # Event tracking
│   │       └── aggregator.py      # Analytics aggregation
│   │
│   ├── models/                    # Database models (ORM)
│   │   ├── user.py                # User model
│   │   ├── session.py             # Session model
│   │   ├── summary.py             # Summary model
│   │   ├── practice.py            # Practice models
│   │   ├── qa.py                  # Q&A model
│   │   ├── nudge.py               # Nudge model
│   │   └── override.py             # Override model
│   │
│   └── config/                    # Configuration
│       ├── settings.py            # Environment settings
│       ├── database.py            # DB connection config
│       └── aws.py                 # AWS service configs
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   │   ├── test_confidence.py
│   │   ├── test_adaptive.py
│   │   └── test_summarizer.py
│   ├── integration/               # Integration tests
│   │   ├── test_api_endpoints.py
│   │   └── test_db_operations.py
│   ├── golden/                    # Golden response tests
│   │   ├── test_session_summaries.py
│   │   ├── test_practice_assignment.py
│   │   ├── test_qa_interactions.py
│   │   ├── test_nudges.py
│   │   ├── test_overrides.py
│   │   └── test_progress_dashboard.py
│   └── fixtures/                  # Test data
│       ├── transcripts.json
│       ├── practice_items.json
│       └── users.json
│
├── infrastructure/                # Infrastructure as Code
│   ├── terraform/                 # Terraform configs (recommended)
│   │   ├── main.tf                # Main infrastructure
│   │   ├── rds.tf                 # PostgreSQL RDS
│   │   ├── lambda.tf              # Lambda functions
│   │   ├── api_gateway.tf         # API Gateway
│   │   ├── cognito.tf              # Cognito setup
│   │   ├── ses.tf                 # SES configuration
│   │   └── variables.tf           # Variables
│   └── cloudformation/            # Alternative: CloudFormation
│       └── template.yaml
│
├── scripts/                       # Utility scripts
│   ├── setup_db.py                # Database setup/migrations
│   ├── seed_data.py               # Demo data generation
│   ├── run_tests.py               # Test runner
│   └── deploy.sh                  # Deployment script
│
├── .github/                       # GitHub workflows
│   └── workflows/
│       ├── ci.yml                 # Continuous integration
│       └── deploy.yml             # Deployment pipeline
│
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies (if using Node)
├── .env.example                   # Environment variables template
├── .gitignore
├── README.md                      # Project overview
└── docker-compose.yml             # Local development setup
```

---

## Technology Stack Recommendations

### Backend Language: **Python 3.11+**
**Why:**
- Excellent AI/ML libraries (OpenAI SDK, langchain)
- Strong PostgreSQL support (psycopg2, SQLAlchemy)
- AWS SDK (boto3) is mature
- Easy to read and maintain

**Alternative:** Node.js/TypeScript
- Faster cold starts for Lambda
- Good AWS SDK support
- TypeScript for type safety

### Database ORM: **SQLAlchemy** (Python) or **Prisma** (Node.js)
- Type-safe models
- Migration support
- Connection pooling

### API Framework: **FastAPI** (Python) or **Express** (Node.js)
- FastAPI: Auto-generated OpenAPI docs, async support
- Express: Mature, large ecosystem

### Testing: **pytest** (Python) or **Jest** (Node.js)
- Golden response validation
- Integration test support
- Mock AWS services

---

## Key Files to Create First

### 1. `src/config/settings.py`
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    # AWS
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str
    ses_from_email: str
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"
    
    # App
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
```

### 2. `src/config/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from src.config.settings import settings

# Connection pool for Lambda/ECS
engine = create_engine(
    f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections before use
)
```

### 3. `src/api/handlers/summaries.py` (Example)
```python
from fastapi import APIRouter, Depends, HTTPException
from src.services.ai.summarizer import SessionSummarizer
from src.models.summary import Summary
from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/summaries", tags=["summaries"])

@router.post("/")
async def create_summary(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Generate summary from session transcript"""
    summarizer = SessionSummarizer()
    summary = await summarizer.generate_summary(session_id, current_user.id)
    return summary
```

---

## Development Workflow

### 1. Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up local PostgreSQL (Docker)
docker-compose up -d postgres

# Run migrations
python scripts/setup_db.py

# Seed demo data
python scripts/seed_data.py

# Run tests
pytest tests/
```

### 2. Testing Golden Responses
```bash
# Run golden response tests
pytest tests/golden/ -v

# Compare against expected outputs
pytest tests/golden/ --golden-compare
```

### 3. Deployment
```bash
# Build Lambda packages
./scripts/build_lambda.sh

# Deploy infrastructure
cd infrastructure/terraform
terraform apply

# Deploy functions
./scripts/deploy.sh
```

---

## Environment Variables

Create `.env.example`:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pennygadget
DB_USER=postgres
DB_PASSWORD=your_password

# AWS
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_xxxxx
SES_FROM_EMAIL=noreply@yourdomain.com

# OpenAI
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Next Steps

1. **Initialize Project**
   - Choose Python or Node.js
   - Set up project structure
   - Create `requirements.txt` or `package.json`

2. **Set Up Database**
   - Run schema migrations
   - Create initial seed data

3. **Implement Core Services**
   - Start with database models
   - Build AI services (summarizer, confidence calculator)
   - Implement adaptive practice algorithm

4. **Build API Endpoints**
   - Start with one endpoint (e.g., `/summaries`)
   - Add authentication middleware
   - Test with golden responses

5. **Deploy to AWS**
   - Set up RDS instance
   - Deploy Lambda functions
   - Configure API Gateway

---

## Integration with Rails App (NOT IMPLEMENTED — aspirational, future integration only)

There is no Rails app in this codebase. A Rails caller was documented from early planning but never built; the real, implemented caller is the React frontend using JWT. The snippet below is kept only as a sketch of what a future service-to-service integration might look like.

### API Contract
```ruby
# Rails example (aspirational, not implemented)
class AIServiceClient
  BASE_URL = ENV['AI_SERVICE_URL']
  
  def create_summary(session_id, transcript)
    HTTParty.post(
      "#{BASE_URL}/api/v1/summaries",
      headers: { 'Authorization' => "Bearer #{api_key}" },
      body: { session_id: session_id, transcript: transcript }
    )
  end
end
```

### Authentication
- User requests: self-hosted JWT tokens (`Authorization: Bearer <jwt>`) — this is what's actually implemented.
- Service-to-service: not implemented. If built later, it must use a scoped identity that still passes the object-ownership check (#67/#68), not a shared static API key.

---

## Documentation Structure

- **PRDs:** `_docs/active/` - Product requirements
- **Schema:** `_docs/active/DATABASE_SCHEMA.md` - Database design
- **Priority:** `_docs/active/IMPLEMENTATION_PRIORITY.md` - Implementation order
- **Golden Responses:** `_docs/qa/golden_responses.yaml` - Test expectations
- **This File:** `_docs/active/PROJECT_STRUCTURE.md` - Project organization

