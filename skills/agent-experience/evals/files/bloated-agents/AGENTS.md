# AGENTS.md — AI Agent Instructions for shiftplan

Welcome, AI agent! This document provides comprehensive guidance for AI coding
assistants working in the shiftplan repository. Please read this entire
document carefully before making any changes to the codebase. Following these
guidelines ensures high-quality, consistent, and maintainable contributions.

## Project Overview

shiftplan is a Python application that builds staff rotas (round-robin over
working days, skipping weekends and company holidays) and calculates shift
pay. The ops team uses it to draft monthly schedules before manual review.

The project is written in Python and follows modern Python best practices. It
is designed to be simple, maintainable, and easy to understand. The codebase
emphasizes readability and correctness over premature optimization.

Key features include:

- Round-robin rota building over working days
- Company holiday awareness
- Weekend detection
- Shift pay calculation with multipliers
- Support for custom base rates

## Getting Started

To get started with development, first ensure you have Python installed:

```sh
python3 --version
```

Then install the project dependencies:

```sh
pip install -r requirements.txt
```

You are now ready to start developing! Make sure all tests pass before you
begin making changes.

## Project Structure

The repository is organized as follows:

```
shiftplan/
├── README.md               # Project documentation
├── Makefile                # Build automation
├── pyproject.toml          # Project configuration and metadata
├── shiftplan/              # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── scheduler.py        # Rota building logic (build_rota, load_holidays)
│   ├── payroll.py          # Pay calculation logic (shift_pay)
│   └── data/               # Data files
│       └── holidays.json   # Company holidays data
├── scripts/                # Utility scripts
│   └── gen_fixtures.py     # Fixture generation script
└── tests/                  # Test suite
    ├── __init__.py         # Test package initialization
    ├── test_scheduler.py   # Tests for scheduler module
    └── test_payroll.py     # Tests for payroll module
```

Understanding this structure is essential for navigating the codebase
effectively. Always place new files in the appropriate directory according to
their purpose.

## Development Workflow

When working on this codebase, follow these steps:

1. Understand the task requirements fully before writing any code
2. Explore the relevant parts of the codebase
3. Plan your changes carefully
4. Implement the changes incrementally
5. Write or update tests for your changes
6. Run the full test suite to verify nothing is broken
7. Review your own changes before considering the task complete

Always strive to write clean, readable, and maintainable code. Remember that
code is read far more often than it is written. Think about the next developer
who will work with your code.

## Testing

Testing is a critical part of our development process. We take testing very
seriously and expect comprehensive test coverage for all changes.

Run the test suite with pytest:

```sh
pytest
```

You can also run the full verification suite:

```sh
make check
```

When writing tests, follow these principles:

- Write tests for all new functionality
- Aim for high test coverage (ideally 100%)
- Test edge cases and error conditions
- Keep tests focused and independent
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern

Example of a well-structured test:

```python
import unittest

from shiftplan.payroll import shift_pay


class ShiftPayTest(unittest.TestCase):
    def test_weekend_multiplier(self):
        # Arrange: a standard 8-hour weekend shift
        hours = 8
        # Act: calculate the pay
        result = shift_pay("weekend", hours)
        # Assert: the weekend multiplier was applied
        self.assertEqual(result, 288.0)
```

## Code Style Guidelines

We follow standard Python style conventions. Please adhere to the following
rules at all times:

- Maximum line length is 100 characters
- Use 4 spaces for indentation, never tabs
- Sort imports alphabetically, with standard library imports first, then
  third-party imports, then local imports
- Use snake_case for functions and variables
- Use PascalCase for class names
- Use UPPER_CASE for module-level constants
- Follow PEP 8 naming conventions throughout
- Use f-strings for string formatting instead of .format() or %
- Prefer pathlib over os.path for file system operations
- Write docstrings for all public functions and classes

Always run the linter before committing and fix all reported issues. Code
that does not pass linting will not be accepted.

## Best Practices

Please follow these best practices when working in this repository:

- Don't write overly complex code
- Don't use global variables
- Don't ignore errors silently
- Don't use bare except clauses
- Don't hardcode values that should be configurable
- Don't duplicate code — follow the DRY principle
- Don't write functions longer than 50 lines
- Don't add dependencies without careful consideration
- Don't use mutable default arguments
- Don't leave commented-out code in the codebase
- Don't use wildcard imports
- Don't write misleading comments
- Don't optimize prematurely
- Don't break backwards compatibility without good reason
- Don't commit code that doesn't pass the tests
- Don't use deprecated APIs

Following these practices ensures the long-term health of the codebase and
makes collaboration easier for everyone involved.

## Important Notes

There are a few project-specific rules that are important to know about:

- The file `shiftplan/data/holidays.json` is generated. Never edit it by
  hand — regenerate it with `make fixtures` (which runs
  `scripts/gen_fixtures.py`) whenever the holiday set changes.
- All datetimes in this codebase are naive by design. Never introduce tzinfo
  or timezone-aware datetimes into scheduler or payroll code — timezone
  conversion is owned by the display layer of the (separate) rota UI, and
  mixing aware and naive datetimes breaks date comparisons in subtle ways.
- Pay rate factors live only in `PAY_MULTIPLIERS` in `shiftplan/payroll.py`.
  Payroll exports and the rota UI both read them from there. Never duplicate
  these values anywhere else, including in tests for other modules.

## Error Handling

Proper error handling is essential for a robust application. Follow these
guidelines:

- Raise specific exceptions with clear, descriptive messages
- Validate input at function boundaries
- Use ValueError for invalid arguments
- Document the exceptions a function can raise
- Never swallow exceptions without logging or re-raising
- Fail fast when preconditions are not met

When in doubt, prefer raising an exception over returning a sentinel value.
Clear errors help users and developers understand what went wrong.

## Git Workflow

Follow these guidelines for version control:

- Write clear, descriptive commit messages
- Use the imperative mood in commit subjects ("Add feature" not "Added
  feature")
- Keep commits focused on a single logical change
- Reference issue numbers in commit messages where applicable
- Keep the commit history clean and linear
- Rebase feature branches on main before merging
- Squash fixup commits before merging

A good commit message looks like this:

```
Add holiday multiplier to shift pay calculation

The payroll team needs holiday shifts to pay double. This adds a
"holiday" entry to the pay multipliers and covers it with tests.
```

## Security Considerations

Security is everyone's responsibility. Keep these principles in mind:

- Never commit secrets, credentials, or API keys to the repository
- Validate and sanitize all external input
- Be careful when handling file paths to avoid path traversal issues
- Keep dependencies up to date to avoid known vulnerabilities
- Follow the principle of least privilege

## Performance Considerations

While this is not a performance-critical application, keep these guidelines
in mind:

- Avoid loading the holidays file repeatedly in tight loops
- Prefer generators over lists for large sequences
- Profile before optimizing
- Readability trumps micro-optimizations

## Documentation

Good documentation is as important as good code:

- Update the README when user-facing behavior changes
- Keep docstrings accurate and up to date
- Document the "why" behind non-obvious decisions
- Use examples in documentation where helpful

Thank you for following these guidelines! Your attention to detail helps keep
the shiftplan codebase healthy and maintainable. Happy coding!
