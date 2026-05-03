# System Architecture


## Project Layout
- `src/hope_jarvis/`: Main package.
- `tests/`: Project test suite (mirrors `src/` structure).
- `docs/`: MkDocs source files.
- `docker/`: Docker related files.


## Patterns & Anti-Patterns
- **Production Safety:** NEVER use `factory-boy` factories outside of testing environments.
- **Modularity:** Prefer composition over complex inheritance for dispatchers and agents.
