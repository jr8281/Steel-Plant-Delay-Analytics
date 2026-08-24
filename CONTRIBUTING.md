# Contributing Guidelines

Thank you for your interest in Steel Plant Delay Analytics!

## Development Setup

```bash
git clone <repo-url>
cd Steel-Plant-Delay-Analytics
cp .env.example .env
# Edit .env with your credentials
docker compose up --build
```

## Code Standards

- **Python**: 3.11+, PEP 8 with Black (line length 120)
- **Type hints**: Required for all function parameters and returns
- **Tests**: All new features require corresponding tests (pytest)
- **Commits**: Use conventional commits (feat:, fix:, docs:, test:)

## Testing

```bash
docker compose exec backend pytest -v
docker compose exec backend pytest --cov=app --cov-report=html
```
