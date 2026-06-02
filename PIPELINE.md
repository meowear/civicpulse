# CivicPulse Pipeline Guide

This document explains the complete CivicPulse flow: Streamlit dashboard startup,
live scraping, issue normalization, GHMC locality resolution, scoring, Supabase
storage, dashboard retrieval, Docker deployment, and CI.

## Runtime Decision

CivicPulse now uses Supabase as the only application database. The Streamlit app
and the ingestion CLI both write to and read from the same cloud table. No SQLite
or local database file is required for normal use.

The best runtime model for this project is:

- Docker for deployment packaging.
- Streamlit startup refresh for "run the pipeline when I open the website".
- Supabase for persistent cloud storage.
- CI/CD for quality checks and deployment, not for every page-open data refresh.

CI/CD is good for testing and shipping code. It is not the right mechanism for
"when a user opens the website, fetch live RSS/news data now", because CI jobs do
not run inside the user-facing app request flow. The app therefore triggers the
pipeline server-side at startup/open time and caches that refresh for a short TTL.

## Environment Variables

Create a local `.env` from `.env.example` and set these values:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-server-side-service-role-key
SUPABASE_TABLE=issues

CIVICPULSE_AUTO_REFRESH_ON_OPEN=true
CIVICPULSE_REFRESH_TTL_SECONDS=900

GEMINI_API_KEY=optional-location-fallback-key
```

`SUPABASE_SERVICE_ROLE_KEY` is the preferred variable for trusted server
deployment because the Streamlit startup refresh writes/upserts records. Use
`SUPABASE_ANON_KEY` or `SUPABASE_API_KEY` only if your Supabase Row Level
Security policies allow the required `select`, `insert`, `update`, and optional
`delete` operations. Do not expose a service role key in client-side JavaScript.
Streamlit runs this Python code on the server, so the key should live only in
server environment variables.

## Supabase Table

Create this table in the Supabase SQL editor:

```sql
create table if not exists public.issues (
    id text primary key,
    document jsonb not null,
    embedding jsonb not null,
    impact_score numeric not null,
    post_date date not null,
    traction_date date not null,
    zone text not null,
    category text not null,
    source text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_issues_dashboard
on public.issues (impact_score desc, traction_date desc, post_date desc);

create index if not exists idx_issues_zone_category
on public.issues (zone, category);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_issues_updated_at on public.issues;

create trigger trg_issues_updated_at
before update on public.issues
for each row
execute function public.set_updated_at();
```

For a classroom/demo deployment using a server-side service role key, no public
RLS policies are needed. For anon-key deployment, enable RLS and add policies
that match your security model. A permissive demo-only policy looks like this:

```sql
alter table public.issues enable row level security;

create policy "demo read issues"
on public.issues for select
using (true);

create policy "demo write issues"
on public.issues for insert
with check (true);

create policy "demo update issues"
on public.issues for update
using (true)
with check (true);
```

Use stricter policies before any public production deployment.

## What Happens When The Website Opens

`app.py` runs this sequence:

1. Loads `.env` using `src/config.py`.
2. Checks `CIVICPULSE_AUTO_REFRESH_ON_OPEN`.
3. If enabled, calls `run_live_pipeline(replace_existing=False)`.
4. Caches that refresh with `st.cache_data` for
   `CIVICPULSE_REFRESH_TTL_SECONDS` seconds so every Streamlit rerun does not
   hammer RSS feeds or Supabase.
5. Loads issues from Supabase through `load_issues()`.
6. Applies dashboard filters, sorting, mapping, trend charts, issue cards, and
   manual location triage for unresolved locations.

Because refresh uses `replace_existing=False`, new live records are upserted by
stable issue ID without wiping older rows. Running the CLI with default live
behavior can still replace the dataset when desired.

## Manual Pipeline Commands

Seed sample Hyderabad data into Supabase:

```bash
python src/ingestion/pipeline.py
```

Run live scraping and replace the current dashboard dataset:

```bash
python src/ingestion/pipeline.py --live
```

Run live scraping and append/upsert without deleting existing rows:

```bash
python src/ingestion/pipeline.py --live --append
```

Scrape a specific source URL:

```bash
python src/ingestion/pipeline.py --live --url "https://news.google.com/rss/search?q=Hyderabad%20pothole%20GHMC"
```

## Scraping Flow

Live scraping lives in `src/ingestion/scraper.py`.

The default target builder creates Google News RSS search URLs for Hyderabad
civic queries. Each query is URL-encoded and sent to Google News with a
90-day recency window:

```text
https://news.google.com/rss/search?q=<encoded Hyderabad civic query when:90d>&hl=en-IN&gl=IN&ceid=IN:en
```

Those RSS searches cover terms such as:

- GHMC complaints
- Potholes and road damage
- Sewage and drainage problems
- Water supply disruptions
- Garbage and waste dumping
- Street light outages
- Waterlogging and monsoon flood risks
- Encroachments, debris, lake pollution, and public safety issues

For each target:

1. `build_default_targets()` produces `CrawlTarget` records from the configured
   Hyderabad civic query list.
2. `_fetch_text_async()` checks whether the URL looks like RSS, Atom, feed, or
   XML. For these feed URLs it first uses a lightweight direct HTTP request with
   a browser-like user agent. This keeps the default Google News RSS path fast
   and deployable without needing a rendered browser page.
3. If the target is not a feed URL, or the direct feed fetch returns nothing,
   `_fetch_text_async()` falls back to `crawl4ai.AsyncWebCrawler`. This is the
   dynamic-page path for ordinary web pages and rendered/markdown extraction.
   Browser-crawler failures return an empty result for that source instead of
   crashing the whole pipeline.
4. `_parse_rss()` parses RSS `<item>` records or Atom `<entry>` records into
   title, description, link, and published date fields.
5. `_is_hyderabad_civic_item()` keeps only scoped Hyderabad civic records. It
   requires Hyderabad scope, rejects known noise topics, and requires a civic
   keyword such as pothole, drainage, garbage, streetlight, waterlogging, GHMC,
   or HMWSSB.
6. `_classify_category()` maps issue keywords to civic categories.
7. `_extract_area()` finds a known Hyderabad locality or asks the optional AI
   location fallback.
8. `_score_issue()` assigns raw S, F, R, and D parameters from issue text and
   post date.
9. Records are deduplicated by title, area, and source URL.

The scraper intentionally avoids unrelated topics such as elections, cricket,
movies, stock market news, and generic praise/political roadmap articles.

### RSS Search Behavior

The RSS search layer does not crawl the open web blindly. It builds a fixed set
of Hyderabad civic search phrases, asks Google News RSS for matching recent
news, and then applies local filters. This gives predictable coverage and avoids
hammering arbitrary sites. The app-level Streamlit cache TTL prevents each page
rerun from re-querying every RSS URL.

### crawl4ai Fallback Behavior

`crawl4ai` is used only after the direct feed path is insufficient. It is useful
for custom URLs passed with `--url` that are normal web pages instead of RSS
feeds. In that case crawl4ai opens the page, extracts rendered HTML/markdown,
and CivicPulse applies the same Hyderabad civic filters. The current dynamic
page fallback creates a conservative issue only when the extracted page content
itself matches the Hyderabad civic filter. A future LLM parser can replace that
generic fallback with richer multi-issue extraction.

## Location Resolution

Location logic is in `src/geo/hyderabad.py`.

The resolver maps known Hyderabad landmarks and localities to:

- GHMC zone
- Latitude
- Longitude
- Population density score P

It now includes a wider set of localities across Central, North, South, West,
East, and Secunderabad zones, including frequently occurring areas such as RTC
X Roads, Masab Tank, Yakutpura, Chanda Nagar, Vanasthalipuram, Bowenpally,
Suchitra, Moosapet, Sanathnagar, and many others. It also normalizes aliases
such as:

- `Hi Tech City`, `Hitec City` -> `hitech city`
- `L.B. Nagar`, `L B Nagar` -> `lb nagar`
- `Saroor Nagar` -> `saroornagar`
- `Toli Chowki` -> `tolichowki`
- `RTC X Roads`, `RTC Crossroads` -> `rtc cross roads`
- `Chandanagar` -> `chanda nagar`
- `Tirumalagiri`, `Tirumalgherry` -> `trimulgherry`

Resolution order:

1. Use the explicit `area` or `location` field if the scraper provided one.
2. Search the title and description for a known locality.
3. If no locality is found and `GEMINI_API_KEY` exists, ask Gemini to return one
   Hyderabad locality or `UNKNOWN`.
4. Resolve the AI-returned locality through the same deterministic GHMC map.
5. If still unresolved, assign `Unknown` zone and Hyderabad centroid
   coordinates, then show the issue in the dashboard's manual triage queue.

The AI result never directly controls zone data. It only proposes a locality
name, which must still match the local GHMC resolver.

`Unknown` is still an intentional safe fallback. It means the pipeline retained
the issue but could not confidently assign it to one of the six GHMC zones. To
reduce Unknown records, add recurring real-world locality names or spelling
variants to `LOCALITIES` and `ALIASES` in `src/geo/hyderabad.py`, then add a
unit test in `tests/test_hyderabad_geo.py`.

## Normalization

`src/ingestion/pipeline.py` converts raw scraped records into dashboard-ready
documents:

- Stable `id`
- `title`
- `area`
- `zone`
- `category`
- `description`
- `source`
- `source_url`
- ISO `post_date`
- ISO `traction_date`
- `engagement_count`
- latitude and longitude
- scoring parameters S, F, R, D, P
- final `impact_score`

If a raw issue has no ID, CivicPulse creates a deterministic ID from title,
area, post date, and source URL using UUID5. This makes Supabase upserts stable
across repeated scraping runs.

## Impact Scoring

Scoring lives in `src/core/scoring.py`.

The deterministic formula is:

```text
Impact Score = (S * 0.30) + (F * 0.25) + (R * 0.20) + (D * 0.15) + (P * 0.10)
```

Parameters are clamped from 0 to 10:

- S: severity
- F: frequency
- R: compounding risk
- D: issue duration
- P: population density

Urgency colors remain:

| Urgency | Threshold | Text | Background |
| --- | --- | --- | --- |
| Critical | >= 8.0 | `#A32D2D` | `#FCEBEB` |
| High | >= 7.0 | `#BA7517` | `#FAEEDA` |
| Medium | >= 6.0 | `#1D9E75` | `#E1F5EE` |

## Supabase Storage

Storage lives in `src/storage/vector_store.py`.

Despite the historical class name `CivicVectorStore`, the backing store is now
Supabase. Each issue row stores:

- `id`: primary key
- `document`: full issue JSON used by the dashboard
- `embedding`: deterministic hashed embedding for local semantic ranking
- `impact_score`
- `post_date`
- `traction_date`
- `zone`
- `category`
- `source`

Upserts call Supabase REST:

```text
POST /rest/v1/issues?on_conflict=id
Prefer: resolution=merge-duplicates,return=minimal
```

Dashboard reads call:

```text
GET /rest/v1/issues?select=document&order=impact_score.desc,traction_date.desc,post_date.desc
```

Search fetches documents and embeddings from Supabase, then ranks locally using:

- token overlap
- substring match
- deterministic hashed-vector cosine similarity

This keeps semantic search dependency-free while preserving cloud persistence.

## Dashboard Flow

`app.py`:

1. Refreshes live data on open, if enabled.
2. Reads all or searched issues from Supabase.
3. Converts `post_date` and `traction_date` to pandas datetimes.
4. Displays the core metrics:
   - Active
   - Critical
   - Zones Affected
   - Resolved
5. Filters by category and GHMC zone.
6. Sorts by impact score, post date, or peak traction date.
7. Shows the Hyderabad map, zone trend chart, prioritized issue cards, and GHMC
   escalation links.
8. Shows unresolved `Unknown` zone records in a manual location triage section.

## Docker

The existing `Dockerfile` remains the right deployment wrapper:

```bash
docker build -t civicpulse .
docker run --env-file .env -p 8501:8501 civicpulse
```

The container starts:

```bash
streamlit run app.py
```

When the Streamlit page opens, the server reads `.env`, refreshes live feeds
based on the TTL, writes to Supabase, then renders from Supabase.

## Streamlit Deployment Readiness

The app is ready for local Streamlit and Docker deployment once these items are
done:

- The Supabase `issues` table exists.
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_TABLE` are set as
  server-side environment variables or Streamlit secrets.
- `CIVICPULSE_AUTO_REFRESH_ON_OPEN` is set according to the deployment model.
- The deployment can install `requirements.txt`.
- The app is started with `streamlit run app.py`.

For Streamlit Community Cloud specifically, treat this as mostly ready but with
one crawler caveat:

- The default Google News RSS path now uses direct HTTP first, so it does not
  need a browser renderer for normal RSS refreshes.
- `crawl4ai` remains in `requirements.txt` for custom dynamic-page URLs. If the
  hosted environment cannot install or run crawl4ai's browser dependencies,
  dynamic-page fallback sources may return no records, but RSS feeds should
  still work.
- For the most reliable public deployment, use Docker or another server where
  crawl4ai setup can be controlled. Alternatively, keep
  `CIVICPULSE_AUTO_REFRESH_ON_OPEN=false` on Streamlit Community Cloud and run
  `python src/ingestion/pipeline.py --live --append` from a scheduled worker to
  populate Supabase.

Do not commit `.env`. In Streamlit Cloud, put the same values in the app's
server-side secrets/environment settings.

## CI/CD

`.gitlab-ci.yml` currently runs quality, security, and tests. That is the right
role for CI/CD:

- verify formatting and linting
- run type/security checks
- run tests
- deploy a Docker image or Streamlit app after successful checks

CI/CD should not be the primary "refresh data when opening the site" mechanism.
For scheduled background refreshes, add a scheduled CI job or cron task that
runs:

```bash
python src/ingestion/pipeline.py --live --append
```

That can coexist with the Streamlit open-time refresh.

## Failure Behavior

- Missing Supabase settings: the dashboard stops with a configuration message.
- Supabase unavailable: the dashboard shows a read/refresh error.
- RSS target unavailable: that source returns no records and other sources keep
  running.
- Unknown locality: the issue is retained, assigned `Unknown`, and routed to
  manual triage instead of crashing the pipeline.
- Missing Gemini key: deterministic locality matching still runs; AI fallback is
  simply skipped.

## Test Expectations

The test suite covers:

- Hyderabad locality resolution for Mehdipatnam and Kukatpally.
- Alias resolution such as L.B. Nagar and Hi Tech City.
- Unknown locality fallback.
- Impact scoring behavior.
- Supabase-store upsert/search behavior through a fake Supabase client.
- Sorting by `traction_date` behaving differently from sorting by `post_date`.

Run:

```bash
pytest tests/
```
