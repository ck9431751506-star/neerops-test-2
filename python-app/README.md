# NeerOps v9 Python Test Application

A simple Flask REST API for testing the NeerOps v9 CI/CD pipeline.

## Features

- REST API with user management endpoints
- Health check and readiness probes
- Metrics collection and reporting
- Comprehensive logging
- Docker containerization
- Production-ready structure

## Endpoints

- `GET /` - HTML dashboard
- `GET /health` - Health check
- `GET /ready` - Readiness probe
- `GET /metrics` - Application metrics
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user
- `GET /api/status` - Application status

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/users
```

## Docker

```bash
# Build image
docker build -t neerops-python-app:latest .

# Run container
docker run -p 5000:5000 neerops-python-app:latest
```

## Testing with NeerOps v9 Pipeline

This application is designed to test the full CI/CD pipeline including:
- Code analysis (Semgrep, Bandit)
- Security scanning (Gitleaks, Trivy)
- Docker build validation (Hadolint)
- Metrics collection and Bayesian gate evaluation
- Manual approval workflow

## Version

1.0 - Initial release
