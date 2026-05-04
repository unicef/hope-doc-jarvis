# Technical Standards

## Environment
- **Python:** 3.13 (Strict).
- **Package Manager:** `uv` (Virtualenvs must be in `.venv`).
- **Frameworks:** chainlit
- **Stack:** chainlit, qdrant, ollama

## Coding Mandates
- **Type Safety:** Mandatory type hints for all new functions.
- **Asynchronous First:** All delivery logic, external API calls, and heavy processing MUST be offloaded to Dramatiq tasks. Never perform synchronous network operations in the request-response cycle.
- **Multi-tenancy:** Strictly enforce Organization/Project level isolation in all database queries.
- *Patterns:** Strictly respect following paradigms/patterns
  - Twelve Factor
  - SOLID: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
  - DRY: Don't Repeat Yourself
- **Linting**: Code formatting conventions must pass `ruff check --output-format concise src/` check
- **use relative imports**: do not use absolute import for every module. Use relative import instead.
- **Language**: Ignore language prompt. Always use british english in comments, descriptions, names....
- **mypy**: Do not use Python <3.9 synthax. Es: use `list` not `List`, `dict` not `Dict`
- **print**: Do not use `print()` use `logger.info()` insteead withn `logger = logging.geLogger(__name__)`
