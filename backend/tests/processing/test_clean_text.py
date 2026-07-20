from processing.stages.clean_text import MAX_CHARS, clean_text

def test_none_and_empty_return_empty():
    assert clean_text (None) == ""
    assert clean_text("") == ""


def test_strips_html_keeps_inner_text():
    assert "Backend Engineer" in clean_text("<h1> Backend Engineer </h1>")
    assert "<" not in clean_text("<div><p>Hello </p></div>")

def test_decodes_html_entities():
    assert clean_text("R&amp;D team") == "R&D team"
    assert "\u00a0" not in clean_text("a&nbsp;b")


def test_collapses_whitespace_and_blank_lines():
    # Runs of blank lines collapse to at most ONE (paragraph break preserved);
    # trailing/leading and intra-line whitespace is squeezed.
    messy = "Line one   \n\n\n\n   Line two\t\tend  "
    cleaned = clean_text(messy)
    assert cleaned == "Line one\n\nLine two end"


def test_preserves_case_and_technical_punctuation():
    src = "Must know Node.js, C++, React Native and 3+ years"
    cleaned = clean_text(src)
    for token in ("Node.js", "C++", "React Native", "3+ years"):
        assert token in cleaned


def test_is_idempotent():
    src = "<p>Uses &amp; needs   Node.js</p>\n\n\n<p>C++</p>"
    once = clean_text(src)
    assert clean_text(once) == once


def test_truncates_to_max_chars():
    assert len(clean_text("x " * 10000)) <= MAX_CHARS


def test_realistic_messy_sample():
    raw = (
        "<div><h2>About&nbsp;the&nbsp;Role</h2>"
        "<p>We need a <b>Backend Engineer</b>.</p>"
        "<ul><li>Node.js</li><li>PostgreSQL</li></ul>"
        "<p></p><p></p>Contact: hr@acme.com</div>"
    )
    cleaned = clean_text(raw)
    assert "Backend Engineer" in cleaned
    assert "Node.js" in cleaned
    assert "PostgreSQL" in cleaned
    assert "<" not in cleaned and "&nbsp;" not in cleaned