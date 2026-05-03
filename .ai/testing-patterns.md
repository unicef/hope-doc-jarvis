# Testing Patterns: Factories & Fixtures

This document enforces Bitcaster's testing standards, ensuring a strict separation of concerns between model generation and test data provision.

## Core Mandates

1**Wrapping:** Tests MUST use `pytest` fixtures that wrap these Factory instances, customising them for specific scenarios.
2**Consistency:** Fixtures should be clear, specific, and defined in the same test file that uses them.
3**Reusability:** Common fixtures can reside in `conftest.py` if they are reused across multiple modules.

## Best Practices
- **Importing:** Avoid importing Django models or Factories at the module level in test files to prevent premature Django initialisation. Import them inside the fixture function or use `if TYPE_CHECKING`.
- **Customisation:** Use the `configure_model` context manager for minor object adjustments within a test instead of creating multiple similar fixtures.
