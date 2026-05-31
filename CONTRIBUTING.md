# Contributing to CivicPulse

Thank you for helping improve CivicPulse. This project tracks Hyderabad civic issues, so contributions should preserve locality accuracy, safe scraping behavior, and the deterministic impact scoring model.

## Development Setup

```bash
pip install -r requirements.txt
python src/ingestion/pipeline.py --live
streamlit run app.py
```

## Validation

Run the test suite before opening a pull request:

```bash
pytest tests/
```

For quality checks:

```bash
ruff check .
ruff format --check .
mypy src
bandit -r src
```

## Pull Request Expectations

- Keep changes focused and avoid unrelated refactors.
- Do not hardcode API keys, tokens, or private endpoints.
- Preserve the impact scoring weights unless an issue explicitly approves a scoring change.
- Use ISO 8601 dates (`YYYY-MM-DD`) for stored civic issue dates.
- Include Hyderabad-specific test cases when changing geocoding, sorting, or scoring.

## Commit Messages

Use concise conventional prefixes:

- `feat:` for new user-visible features
- `fix:` for bug fixes
- `docs:` for documentation-only changes
- `test:` for test changes
- `chore:` for maintenance
