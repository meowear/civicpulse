from src.ingestion.pipeline import normalize_issue


def test_normalize_issue_uses_title_and_description_for_locality() -> None:
    issue = normalize_issue(
        {
            "title": "Overflowing drain near Jubilee Hills Road No 36",
            "area": "Hyderabad",
            "category": "Drainage",
            "description": "Residents near Jubilee Hills report sewage overflow after rain.",
            "post_date": "2026-05-20",
            "traction_date": "2026-05-21",
        }
    )

    assert issue["zone"] == "Central"
