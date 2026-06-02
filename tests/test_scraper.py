from src.ingestion.scraper import _is_feed_url, build_default_targets


def test_default_targets_are_rss_feed_urls() -> None:
    targets = build_default_targets()

    assert targets
    assert all(_is_feed_url(target.url) for target in targets)


def test_feed_url_detection_handles_rss_atom_and_plain_web_pages() -> None:
    assert _is_feed_url("https://news.google.com/rss/search?q=Hyderabad%20GHMC")
    assert _is_feed_url("https://example.com/feed.xml")
    assert _is_feed_url("https://example.com/posts.atom")
    assert not _is_feed_url("https://example.com/hyderabad-civic-issue")
