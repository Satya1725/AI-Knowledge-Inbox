from app.services.fetcher import extract_from_html


def _ingest_note(client, text, title=None):
    response = client.post("/ingest", json={"type": "note", "text": text, "title": title})
    assert response.status_code == 202, response.text
    return response.json()


def test_ingest_note_is_indexed_and_listed(client):
    created = _ingest_note(client, "Our wifi password is hunter2.\n\nThe office opens at 9am.")
    assert created["status"] == "processing"
    assert created["title"] == "Our wifi password is hunter2."

    # TestClient runs background tasks before returning, so indexing is done by now.
    items = client.get("/items").json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "ready"
    assert items[0]["chunk_count"] == 1
    assert items[0]["source_type"] == "note"


def test_query_returns_answer_with_relevant_sources(client, fake_provider):
    _ingest_note(client, "The wifi password for the office is hunter2.", title="Wifi")
    _ingest_note(client, "Bananas are rich in potassium and fibre.", title="Fruit")

    response = client.post("/query", json={"question": "what is the office wifi password?"})
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["answer"] == "Fake answer based on [1]."
    assert body["sources"][0]["title"] == "Wifi"
    assert body["sources"][0]["cited"] is True
    assert "hunter2" in fake_provider.last_prompt


def test_query_with_no_content_skips_llm(client, fake_provider):
    response = client.post("/query", json={"question": "anything at all?"})
    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert response.json()["provider"] is None
    assert fake_provider.last_prompt is None


def test_validation_errors_have_clear_messages(client):
    response = client.post("/ingest", json={"type": "note", "text": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"

    assert client.post("/ingest", json={"type": "url", "url": "not-a-url"}).status_code == 422
    assert client.post("/ingest", json={"type": "video", "url": "https://x.com"}).status_code == 422
    assert client.post("/query", json={"question": ""}).status_code == 422


def test_delete_item(client):
    item = _ingest_note(client, "temporary note")
    assert client.delete(f"/items/{item['id']}").status_code == 204
    assert client.get("/items").json()["items"] == []

    missing = client.delete(f"/items/{item['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_unconfigured_chat_provider_returns_503(client):
    # The fixture registers only a fake "openai"; an explicit request for gemini must fail clearly.
    _ingest_note(client, "some saved note about gemini")
    response = client.post("/query", json={"question": "about gemini?", "provider": "gemini"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_not_configured"


def test_falls_back_to_the_provider_that_has_a_key(monkeypatch):
    from app.ai import factory
    from app.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    factory._providers.clear()
    try:
        assert factory.resolve_provider("openai") == "gemini"
        assert factory.resolve_provider("gemini") == "gemini"
        assert factory.available_providers() == ["gemini"]
    finally:
        get_settings.cache_clear()


def test_no_keys_at_all_gives_clear_error(monkeypatch):
    import pytest

    from app.ai import factory
    from app.config import get_settings
    from app.errors import ProviderNotConfiguredError

    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    factory._providers.clear()
    try:
        with pytest.raises(ProviderNotConfiguredError, match="OPENAI_API_KEY or GEMINI_API_KEY"):
            factory.resolve_provider("openai")
    finally:
        get_settings.cache_clear()


def test_html_extraction_drops_page_chrome():
    html = """<html><head><title>My Post</title><script>var x=1</script></head>
    <body><nav>Home | About</nav><article><h1>Hello</h1><p>Real content here.</p></article>
    <footer>(c) 2026</footer></body></html>"""
    page = extract_from_html(html)
    assert page.title == "My Post"
    assert "Real content here." in page.text
    assert "Home | About" not in page.text
    assert "var x" not in page.text
