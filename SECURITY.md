# Security Policy

## Supported Versions

Security fixes are applied to the active development branch until a formal release cadence is established.

## Reporting a Vulnerability

Please do not open public issues for suspected vulnerabilities. Report privately to the maintainers with:

- a description of the vulnerability
- reproduction steps
- affected files or endpoints
- any known impact

## Secret Handling

Never commit API keys, `.env` files, Streamlit secrets, database dumps, or credentials. Use `.env.example` for documentation only.

## Scraping Safety

Scrapers must use conservative request rates, clear user agents, and graceful failure paths. Missing or malformed external data must not crash the dashboard.
