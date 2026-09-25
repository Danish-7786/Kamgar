import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock

import pytest
import requests

import collect_ats_jobs
from scraper import ats_collectors as ats
from utils.httpClient import create_session, fetch_jobs


def company(source="greenhouse", board="example"):
    return {"name": "Example", "source": source, "board": board}


def test_greenhouse_mapping_and_description(monkeypatch):
    posting = {
        "id": 123, "title": "Engineer", "absolute_url": "https://example.com/job/123",
        "content": "&lt;p&gt;Build APIs &amp;amp; tools&lt;/p&gt;",
        "location": None, "updated_at": "2026-09-22T10:00:00Z",
    }
    fetch = Mock(return_value=[posting])
    monkeypatch.setattr(ats, "fetch_jobs", fetch)
    jobs = ats.collect_greenhouse(None, company())
    assert jobs[0]["external_id"] == "123"
    assert jobs[0]["description"] == "Build APIs & tools"
    assert jobs[0]["date_posted"] is None
    assert jobs[0]["location"] is None
    assert jobs[0]["raw_payload"] == posting
    fetch.assert_called_once_with(
        None, "https://boards-api.greenhouse.io/v1/boards/example/jobs",
        params={"content": "true"},
    )


def test_ashby_skips_unlisted_and_maps_missing_optional_fields(monkeypatch):
    posting = {
        "title": "Engineer", "jobUrl": "https://example.com/job/1",
        "descriptionHtml": "<p>Build APIs</p>", "publishedAt": "2026-09-22T10:00:00Z",
    }
    fetch = Mock(return_value=[{"isListed": False}, posting])
    monkeypatch.setattr(ats, "fetch_jobs", fetch)
    jobs = ats.collect_ashby(None, company("ashby", "Example"))
    assert len(jobs) == 1
    assert jobs[0]["description"] == "Build APIs"
    assert jobs[0]["external_id"] == posting["jobUrl"]
    assert jobs[0]["date_posted"] == "2026-09-22"
    assert jobs[0]["raw_payload"] == posting
    assert fetch.call_args.args[1].endswith("/Example")


def test_bad_company_and_http_failure_do_not_stop_other_companies(monkeypatch):
    greenhouse = Mock(side_effect=requests.HTTPError("404 board not found"))
    ashby = Mock(return_value=[{"title": "Engineer"}])
    monkeypatch.setattr(ats, "collect_greenhouse", greenhouse)
    monkeypatch.setattr(ats, "collect_ashby", ashby)
    jobs, reports = ats.collect_companies([
        {"name": "Missing board"}, None, company(), company("ashby"),
    ])
    assert jobs == [{"title": "Engineer"}]
    assert [r["status"] for r in reports] == ["failed", "failed", "failed", "success"]
    assert "404" in reports[2]["error"]
    assert reports[3]["job_count"] == 1


def test_malformed_posting_does_not_publish_partial_company_batch(monkeypatch):
    monkeypatch.setattr(ats, "fetch_jobs", Mock(side_effect=[
        [{"id": 1, "title": "Engineer", "absolute_url": "https://example.com/1"},
         {"id": 2, "title": "Missing URL"}],
        [],
    ]))
    jobs, reports = ats.collect_companies([company(), company("ashby")])
    assert jobs == []
    assert [r["status"] for r in reports] == ["failed", "success"]


@pytest.mark.parametrize("entry", [
    {"name": " ", "source": "ashby", "board": "x"},
    company("unsupported"), company(board="https://example.com"),
])
def test_invalid_company_is_reported_without_request(entry, monkeypatch):
    fetch = Mock()
    monkeypatch.setattr(ats, "fetch_jobs", fetch)
    jobs, reports = ats.collect_companies([entry])
    assert jobs == []
    assert reports[0]["status"] == "failed"
    fetch.assert_not_called()


def test_load_companies_default_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    companies = ats.load_companies()
    assert {c["source"] for c in companies} == {"greenhouse", "ashby"}


def test_load_companies_rejects_old_object_format(tmp_path):
    path = tmp_path / "companies.json"
    path.write_text('{"name": ""}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON list"):
        ats.load_companies(path)


@pytest.mark.parametrize("payload", [{}, {"jobs": None}, []])
def test_fetch_jobs_rejects_invalid_response_and_sets_timeout(payload):
    session = Mock()
    session.get.return_value.json.return_value = payload
    with pytest.raises(ValueError, match="jobs list"):
        fetch_jobs(session, "https://example.com/jobs")
    assert session.get.call_args.kwargs["timeout"] == (5, 30)
    session.get.return_value.raise_for_status.assert_called_once()


@pytest.mark.parametrize("statuses, expected_calls, fails", [
    ([503, 200], 2, False),
    ([429, 200], 2, False),
    ([503, 503, 503, 503], 4, True),
    ([404], 1, True),
])
def test_http_retry_behavior(statuses, expected_calls, fails):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status = statuses[min(len(calls), len(statuses) - 1)]
            calls.append(status)
            body = b'{"jobs": []}'
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with create_session() as session:
            # Exercise the real retry adapter against a local HTTP server.
            session.trust_env = False
            adapter = session.get_adapter("https://")
            adapter.max_retries = adapter.max_retries.new(backoff_factor=0)
            session.mount("http://", adapter)
            url = f"http://127.0.0.1:{server.server_port}/jobs"
            if fails:
                with pytest.raises(requests.HTTPError):
                    fetch_jobs(session, url)
            else:
                assert fetch_jobs(session, url) == []
        assert len(calls) == expected_calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_cli_saves_successful_results_alongside_failures(tmp_path, monkeypatch):
    registry = tmp_path / "companies.json"
    registry.write_text(json.dumps([company()]), encoding="utf-8")
    output = tmp_path / "results.json"
    result = ([{"title": "Engineer"}], [{
        "company": "Example", "source": "greenhouse", "status": "failed",
        "error": "HTTPError: 404", "job_count": 0,
    }])
    collect = Mock(return_value=result)
    monkeypatch.setattr(collect_ats_jobs, "collect_companies", collect)
    assert collect_ats_jobs.main([
        "--companies", str(registry), "--output", str(output),
    ]) == 1
    collect.assert_called_once_with([company()])
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved == {"jobs": result[0], "reports": result[1]}
