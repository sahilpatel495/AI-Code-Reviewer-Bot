# AI Code Reviewer Bot

A production-ready GitHub App that performs automated AI-driven code reviews on Pull Requests using Google's Gemini AI models.

## 🚀 Features

- **Automated Code Reviews**: Triggers on PR events (`opened`, `synchronize`, `ready_for_review`)
- **Multi-Language Support**: Python, JavaScript/TypeScript, Java, SQL, Go, Rust
- **Static Analysis Integration**: ESLint, Prettier, Ruff, Black, Bandit, mypy, SQLFluff
- **AI-Powered Analysis**: Uses Gemini 2.5 Pro for deep analysis and Gemini Flash for fast reviews
- **Structured Output**: JSON-formatted comments with severity levels and categories
- **GitHub Integration**: Posts inline comments and status checks
- **Configurable Rules**: Repository-specific configuration via `.ai-reviewer.yml`
- **Slash Commands**: `/re-review`, `/focus security`, `/snooze`
- **Feedback Loop**: Tracks comment reactions and effectiveness
- **Scalable Architecture**: FastAPI + Celery + Redis + PostgreSQL

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub App    │    │   FastAPI App   │    │  Celery Worker  │
│                 │    │                 │    │                 │
│  Webhook Events │───▶│  Webhook Handler│───▶│  Review Tasks   │
│  PR Comments    │◀───│  API Endpoints  │◀───│  AI Analysis    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │                 │    │                 │
                       │  Review Sessions│    │  Task Queue     │
                       │  Comments       │    │  Caching        │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Queue**: Celery + Redis
- **Database**: PostgreSQL
- **AI Models**: Google Gemini 2.5 Pro / Flash
- **Static Analyzers**: ESLint, Prettier, Ruff, Black, Bandit, mypy, SQLFluff
- **Deployment**: Docker, Docker Compose

## 📦 Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-code-reviewer-bot.git
cd ai-code-reviewer-bot
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for static analysis)
npm install -g eslint prettier typescript
```

### 3. Environment Configuration

Create a `.env` file:

```bash
# GitHub App Configuration
GITHUB_APP_ID=your_github_app_id
GITHUB_APP_PRIVATE_KEY=your_private_key_content_or_path
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_PRO=gemini-2.0-flash-exp
GEMINI_MODEL_FLASH=gemini-1.5-flash

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ai_reviewer

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application Configuration
APP_NAME=AI Code Reviewer Bot
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Review Configuration
MAX_COMMENTS_PER_PR=20
MAX_DIFF_SIZE_MB=10
REVIEW_TIMEOUT_SECONDS=300

# Static Analyzer Configuration
ENABLE_PYTHON_ANALYZERS=true
ENABLE_JS_ANALYZERS=true
ENABLE_JAVA_ANALYZERS=true
ENABLE_SQL_ANALYZERS=true
```

### 4. Database Setup

```bash
# Create database
createdb ai_reviewer

# Run migrations (if using Alembic)
alembic upgrade head
```

### 5. GitHub App Setup

1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Create a new GitHub App with these permissions:
   - **Read**: contents, metadata, pull requests
   - **Write**: pull request comments, commit statuses, checks
3. Set webhook URL to: `https://your-domain.com/webhook/github`
4. Copy the App ID and generate a private key
5. Update your `.env` file with the credentials

### 6. Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Update your `.env` file with the API key

## 🚀 Running the Application

### Development Mode

```bash
# Start the FastAPI application
python app.py

# Start Celery worker (in another terminal)
celery -A jobs.review_task worker --loglevel=info

# Start Celery beat for periodic tasks (in another terminal)
celery -A jobs.review_task beat --loglevel=info
```

### Production Mode with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=3
```

## 📝 Usage

### Automatic Reviews

The bot automatically reviews pull requests when:

- A PR is opened
- New commits are pushed to a PR
- A draft PR is marked as ready for review

### Manual Reviews

Trigger a manual review via API:

```bash
curl -X POST "http://localhost:8000/review" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-username",
    "repo": "your-repo",
    "pull_number": 123,
    "focus_area": "security"
  }'
```

### Repository Configuration

Create `.ai-reviewer.yml` in your repository root:

```yaml
rules:
  security: strict
  performance: moderate
  style: off
max_comments: 20
languages:
  - python
  - javascript
  - sql
focus_areas:
  - security
  - performance
excluded_files:
  - "*.md"
  - "docs/**"
  - "tests/**"
```

### Slash Commands

Add these commands in PR comments:

- `/re-review` - Rerun the full review
- `/focus security` - Review only security aspects
- `/snooze` - Disable bot for this PR

## 🔧 Configuration

### Environment Variables

| Variable                 | Description                  | Default                    |
| ------------------------ | ---------------------------- | -------------------------- |
| `GITHUB_APP_ID`          | GitHub App ID                | Required                   |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key       | Required                   |
| `GITHUB_WEBHOOK_SECRET`  | Webhook secret               | Required                   |
| `GEMINI_API_KEY`         | Gemini API key               | Required                   |
| `DATABASE_URL`           | PostgreSQL connection string | Required                   |
| `REDIS_URL`              | Redis connection string      | `redis://localhost:6379/0` |
| `MAX_COMMENTS_PER_PR`    | Maximum comments per PR      | `20`                       |
| `REVIEW_TIMEOUT_SECONDS` | Review timeout               | `300`                      |

### Static Analyzers

The bot supports various static analyzers:

**Python:**

- Ruff (linting)
- Black (formatting)
- Bandit (security)
- mypy (type checking)

**JavaScript/TypeScript:**

- ESLint (linting)
- Prettier (formatting)
- TypeScript compiler (type checking)

**SQL:**

- SQLFluff (linting and formatting)

**Java:**

- Basic syntax checking

**Go/Rust:**

- Basic syntax checking

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_webhook.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests
pytest tests/test_integration.py
```

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# Service status
curl http://localhost:8000/stats
```

### Logs

```bash
# View application logs
docker-compose logs -f app

# View worker logs
docker-compose logs -f worker

# View all logs
docker-compose logs -f
```

### Metrics

The application tracks:

- Review completion rate
- Average review duration
- Comment effectiveness
- Error rates
- API usage

## 🚀 Deployment

### Docker Deployment

```bash
# Build production image
docker build -t ai-code-reviewer:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

#### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t ai-code-reviewer .
docker tag ai-code-reviewer:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-code-reviewer:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-code-reviewer:latest
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-code-reviewer
gcloud run deploy --image gcr.io/PROJECT-ID/ai-code-reviewer --platform managed
```

#### Railway

```bash
# Deploy to Railway
railway login
railway init
railway up
```

### Environment Variables for Production

Set these in your deployment platform:

```bash
# Required
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY=your_private_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_production_database_url
REDIS_URL=your_production_redis_url

# Optional
DEBUG=false
LOG_LEVEL=INFO
MAX_COMMENTS_PER_PR=20
REVIEW_TIMEOUT_SECONDS=300
```

## 🔒 Security

### GitHub App Security

- Use environment variables for sensitive data
- Rotate private keys regularly
- Limit app permissions to minimum required
- Use webhook signature verification

### API Security

- Validate all webhook signatures
- Rate limit API endpoints
- Use HTTPS in production
- Implement proper error handling

### Data Privacy

- No PR code is stored permanently
- Only metadata and review results are persisted
- Review sessions are cleaned up after 30 days
- All data is encrypted in transit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
ruff check .
black .

# Run type checking
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/your-username/ai-code-reviewer-bot/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/ai-code-reviewer-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-code-reviewer-bot/discussions)

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for providing the AI models
- [GitHub](https://github.com/) for the platform and API
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Celery](https://docs.celeryproject.org/) for task queue management
- All the open-source static analysis tools used

## 📈 Roadmap

- [ ] Support for more programming languages
- [ ] Custom AI model fine-tuning
- [ ] Advanced code quality metrics
- [ ] Integration with CI/CD pipelines
- [ ] Slack/Teams notifications
- [ ] Custom review templates
- [ ] Batch review processing
- [ ] Advanced analytics dashboard

---

**Made with ❤️ for the developer community**
