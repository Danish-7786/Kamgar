from xlrd.biffh import unpack_unicode_update_pos
from __future__ import annotations


import html
import re
import unicodedata

from bs4 import BeautifulSoup


# Longest description we keep. Requirements lead in almost every posting,
# so a head-truncation is a safe cost lever for the LLM call in Module 3.
MAX_CHARS = 8000

def _strip_html(text: str)-> str:
    """HTML -> text with a real parser (never regex). Keeps line structure."""
    # "html.parser" is stdlib-backed; no lxml dependency required.
    soup = BeautifulSoup(text,"html.parser")
    return soup.get_text(separator="\n")

def _collapse_whitespace(text:str)-> str:
    lines = [line.strip() for line in text.splitlines()]
    # how to read this 
    # start from for line in text.splitlines()
    #  text.splitlines() breaks the sentence in array of sentences which are divides by line break
    # line.strip() remove trailing spaces
    out: list[str] = []
    # declare the list[str] of var out
    
    for line in lines:
                # Allow at most one consecutive blank line.
        if line == "" and (not out or out[-1] == ""):
            # not out checks if out is not empty and out[-1] checks the last element if its not null

            continue
        out.append(line)
    return "\n".join(out).strip()

def clean_text(raw:str  | None)-> str:
    """Normalize a raw job description to clean plain text.

    Steps: guard -> strip HTML -> decode entities -> Unicode NFKC ->
    collapse whitespace -> cap length. Case and punctuation are preserved
    ("Node.js", "C++", "3+ years") because they carry signal.
    """

    if not raw:
        return ""

    text = _strip_html(raw) 
    text = html.unescape(text)  # &amp; -> &, &nbsp; -> space
    text = unicodedata.normalize("NFKC",text)  # canonicaclize looks-alikes
    text = text.replace("\u00a0", " ")             # stray non-breaking spaces
    text = re.sub(r"[ \t]+", " ", text)            # collapse intra-line runs
    text = _collapse_whitespace(text)

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rstrip()
    return text




