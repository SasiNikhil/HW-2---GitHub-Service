# GitHub Issues Gateway Service

A FastAPI-based service that wraps the GitHub REST API for Issues management, providing a clean HTTP API for issue CRUD operations, comment management, and webhook handling with HMAC signature validation.

## Features

- **Issue CRUD Operations**: Create, read, update, and close GitHub issues
- **Comment Management**: Add comments to issues
- **Webhook Processing**: Secure webhook handling with HMAC SHA-256 signature verification
- **OpenAPI 3.1 Contract**: Complete API documentation with examples
- **Automated Tests**: Unit and integration tests with high coverage
- **Docker Support**: One-click deployment with Docker
- **Rate Limit Handling**: Respects GitHub API rate limits
- **Pagination Support**: Proper pagination with Link headers

## Environment Variables

The following environment variables are required:

```bash
GITHUB_TOKEN=your_fine_grained_pat_here        # Fine-grained PAT with "Issues: Read and Write" scope
GITHUB_OWNER=your_github_username              # GitHub repository owner
GITHUB_REPO=your_test_repository               # GitHub repository name
WEBHOOK_SECRET=your_webhook_secret             # Shared secret for webhook HMAC validation
PORT=8080                                      # Port the service listens on
LOG_LEVEL=INFO                                 # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create a new token with the following permissions for your test repository:
   - **Issues**: Read and write
   - **Metadata**: Read (required)
3. Copy the token and set it as `GITHUB_TOKEN`

### Webhook Setup

1. In your GitHub repository, go to Settings → Webhooks
2. Add a new webhook with:
   - **Payload URL**: `http://your-domain/webhook` (use ngrok/Cloudflared for local testing)
   - **Content type**: `application/json`
   - **Secret**: Same value as your `WEBHOOK_SECRET`
   - **Events**: Select "Issues" and "Issue comments"

## Running Locally

### Non-Docker Setup

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your values

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Docker Setup

```bash
# Build the image
docker build -t issues-gw:latest .

# Run with environment file
docker run --rm -p 8080:8080 --env-file .env issues-gw:latest

# Or with docker-compose
docker-compose up
```

## API Endpoints

Base URL: `http://localhost:8080`

### Health Check
- **GET** `/healthz` - Service health check

### Issues
- **POST** `/issues` - Create a new issue
- **GET** `/issues` - List issues (supports pagination and filtering)
- **GET** `/issues/{number}` - Get a specific issue
- **PATCH** `/issues/{number}` - Update an issue (title, body, state)

### Comments
- **POST** `/issues/{number}/comments` - Add a comment to an issue

### Webhooks
- **POST** `/webhook` - GitHub webhook endpoint

### Events (Optional)
- **GET** `/events` - List recent webhook events for debugging

## API Examples

### Create an Issue
```bash
http POST :8080/issues Content-Type:application/json \
  title="Bug: Application crashes on startup" \
  body="Steps to reproduce: 1. Start app 2. Click login 3. App crashes" \
  labels:='["bug", "high-priority"]'
```

### List Issues
```bash
# Get open issues
http GET :8080/issues

# Get closed issues with pagination
http GET :8080/issues state==closed page==1 per_page==10

# Filter by labels
http GET :8080/issues labels=="bug,high-priority"
```

### Get Specific Issue
```bash
http GET :8080/issues/1
```

### Update Issue
```bash
# Update title and body
http PATCH :8080/issues/1 Content-Type:application/json \
  title="Updated: Application crashes on startup" \
  body="Updated description with more details"

# Close an issue
http PATCH :8080/issues/1 Content-Type:application/json state="closed"

# Reopen an issue
http PATCH :8080/issues/1 Content-Type:application/json state="open"
```

### Add Comment
```bash
http POST :8080/issues/1/comments Content-Type:application/json \
  body="Thanks for reporting this issue. We're investigating."
```

### Health Check
```bash
http GET :8080/healthz
```

## Testing

### Run All Tests
```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Test Categories

**Unit Tests** (≥80% coverage):
- Route validation and error handling
- Webhook signature verification
- GitHub API error mapping
- Pagination utilities

**Integration Tests**:
- End-to-end issue CRUD operations
- Comment creation and retrieval
- Real webhook delivery testing
- Rate limit handling

## API Documentation

- **Interactive Docs**: http://localhost:8080/docs (Swagger UI)
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI Spec**: Available at `/openapi.json` or see `openapi.yaml`

## Architecture & Design

### Error Handling
- GitHub API errors are mapped to appropriate HTTP status codes
- Detailed error messages without exposing sensitive information
- Consistent error response format across all endpoints

### Pagination Strategy
- Honors GitHub's pagination semantics
- Forwards Link headers for navigation
- Supports `page` and `per_page` parameters (max 100 per page)

### Webhook Security
- HMAC SHA-256 signature verification using constant-time comparison
- Idempotent processing using GitHub delivery IDs
- Fast acknowledgment with background processing

### Rate Limiting
- Respects GitHub rate limit headers
- Implements exponential backoff on rate limit exceeded
- Returns appropriate 429/503 responses with Retry-After headers

## Security Considerations

- Environment-based configuration (no hardcoded secrets)
- Webhook signature verification prevents unauthorized requests
- Constant-time HMAC comparison prevents timing attacks
- Minimal GitHub token scopes (Issues: Read/Write only)
- No logging of sensitive data (tokens, signatures)

## Development

### Code Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application setup
├── config.py            # Configuration management
├── models.py            # Pydantic models
├── github.py            # GitHub API client
└── routes/
    ├── __init__.py
    ├── issues.py        # Issue CRUD endpoints
    ├── comments.py      # Comment endpoints
    └── webhook.py       # Webhook handling
tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── conftest.py          # Test configuration
```

### Contributing
1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## Deployment

### Docker
```bash
docker build -t issues-gw .
docker run -p 8080:8080 --env-file .env issues-gw
```

### Environment Setup for Production
- Use secure secret management for tokens
- Enable HTTPS in production
- Configure proper logging and monitoring
- Set up health checks and alerting

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check your GitHub token and permissions
2. **Webhook signature validation fails**: Verify WEBHOOK_SECRET matches GitHub
3. **Rate limit exceeded**: Wait for rate limit reset or implement caching
4. **Connection errors**: Check network connectivity to GitHub API

### Debugging
- Check logs for detailed error information
- Use `/events` endpoint to debug webhook deliveries
- Verify environment variables are set correctly
- Test GitHub token permissions with a simple API call

## License

This project is for educational purposes as part of CMPE 272 coursework.