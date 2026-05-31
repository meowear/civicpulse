from pathlib import Path

from src.data.sample_issues import build_sample_issues
from src.ingestion.pipeline import normalize_issue
from src.storage.vector_store import CivicVectorStore


def test_vector_store_upserts_and_searches_issues(tmp_path: Path) -> None:
    store = CivicVectorStore(tmp_path / "issues.db")
    issues = [normalize_issue(issue) for issue in build_sample_issues()]

    assert store.upsert_issues(issues) == len(issues)
    assert store.count() == len(issues)

    results = store.search("metro potholes in west hyderabad", limit=3)

    assert not results.empty
    assert "Kukatpally" in results.iloc[0]["area"]


def test_vector_store_search_ignores_unrelated_queries(tmp_path: Path) -> None:
    store = CivicVectorStore(tmp_path / "issues.db")
    issues = [normalize_issue(issue) for issue in build_sample_issues()]
    store.upsert_issues(issues)

    results = store.search("zzzz-not-a-civic-topic", limit=3)

    assert results.empty
