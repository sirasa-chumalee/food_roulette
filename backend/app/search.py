"""Full-text search over restaurant descriptions (DESIGN §5 extension).

Search is **selection input only, never a safety path.** A restaurant that
matches a craving comes back in a `set` that ranking converts into a score
bump. It cannot hide anything and it never touches menu_items safety flags —
the hard filter in `filter.py` remains the only thing that decides what is
edible.

Index contents: the `restaurant_fts` table holds one row per restaurant whose
`body` is the concatenation of its name (th + en), human-written description,
and every dish name. Intent parsing (`extract.py`) produces craving phrases;
each phrase is tokenised and AND-combined so a restaurant must mention *all*
the words to be credited.
"""

from __future__ import annotations

import re
import sqlite3

# FTS5 query operators that must be neutralised before injecting raw tokens.
# Anything from a chat message could otherwise become query structure, not a
# literal word. A quoted token is treated as a literal phrase.
_QUERY_SPECIAL = re.compile(r'["*<>()~\-\^]')

# FTS5's unicode61 tokenizer matches whole words, so a token "ri" (from
# "riverside") won't substring-match into "Bustling" — keyword search stays
# word-scoped, which is what we want. Split the query on any non-alphanumeric
# run, drop 1-char tokens (too noisy), then AND them.
_TOKEN_SEP = re.compile(r"[^\w\u0080-\uFFFF]+")

# SQL LIKE wildcards that must be neutralised in a phrase used as a literal
# substring pattern (below), so a phrase like "50%" can't turn into a wildcard.
_LIKE_SPECIAL = re.compile(r"[%_\\]")

# Thai script block. Gates the LIKE fallback below to Thai phrases only — Latin
# text already space-separates words, so FTS token matching is precise there
# and a bare substring scan would reintroduce false positives like "ri" hitting
# "riverside" (word-scoping is the whole point of the FTS path for those).
_HAS_THAI = re.compile(r"[ก-๛]")

# Cuisine association ("chinese food" -> เกี๊ยว/หมูแดง/...) is not hardcoded
# here. No dish has a cuisine tag, so a plain cuisine word shares no literal
# word with the Thai dish text and would never match anything on its own —
# extract.py's prompt instead asks Gemini to add real Thai dish/ingredient
# keywords as extra cravings whenever it detects a cuisine craving. Those
# keywords arrive in `phrases` like any other craving and are matched below
# exactly the same way, so this module stays a plain deterministic matcher.


def _escape(token: str) -> str:
    return '"' + _QUERY_SPECIAL.sub(" ", token) + '"'


def _like_pattern(phrase: str) -> str:
    return "%" + _LIKE_SPECIAL.sub(lambda m: "\\" + m.group(0), phrase) + "%"


def build_index(conn: sqlite3.Connection) -> None:
    """Rebuild `restaurant_fts` from restaurants + menu_items.

    Called by ingest.py after both reference tables are loaded. Deletes and
    repopulates so stale text never lingers after a data refresh.
    """
    conn.execute("DELETE FROM restaurant_fts;")
    conn.execute(
        """
        INSERT INTO restaurant_fts (id, body)
        SELECT
            r.id,
            COALESCE(r.name_en, '') || ' ' || COALESCE(r.name_th, '')
            || ' ' || COALESCE(r.description, '')
            || ' ' || COALESCE((
                SELECT group_concat(
                    COALESCE(m.name_en, '') || ' ' || COALESCE(m.name_th, ''), ' '
                ) FROM menu_items m WHERE m.restaurant_id = r.id
            ), '')
        FROM restaurants r;
        """
    )
    conn.commit()


def match_restaurant_ids(
    conn: sqlite3.Connection, phrases: list[str]
) -> set[str]:
    """Restaurant ids whose index text matches the craving/facility phrases.

    Each phrase is its own AND-of-tokens requirement (every word *in that
    phrase* must be present somewhere in the restaurant's material) — a
    restaurant is credited if it satisfies ANY one phrase. Phrases are
    independent asks ("กาแฟ" and "ทำงาน" come from separate cravings /
    facility needs), so ANDing across phrases would demand a restaurant's
    text literally contain every unrelated word at once and match almost
    nothing. A phrase with no usable tokens is skipped — it contributes
    nothing but never errors. Returns an empty set when nothing matches.

    Thai has no spaces between words, so a multi-word Thai craving like
    "อาหารอินเดีย" (Indian food) arrives as *one* unsegmented token — FTS5's
    unicode61 tokenizer only splits on whitespace/punctuation, so that token
    can equal a restaurant's indexed word only by coincidence, even when the
    exact substring is sitting right there in its description. For phrases
    containing Thai script, a plain LIKE substring scan on the same indexed
    text is a second, independent check that catches this case; its results
    union with the FTS match rather than replacing it. This fallback is
    scoped to Thai phrases only — Latin text already space-separates words,
    so a bare substring scan there would reintroduce exactly the false
    positive ("ri" hitting "riverside") the FTS word-scoping exists to avoid.
    """
    if not phrases:
        return set()

    matched: set[str] = set()
    for phrase in phrases:
        tokens = [t for t in _TOKEN_SEP.split(phrase) if len(t) > 1]
        if tokens:
            match_expr = " AND ".join(_escape(t) for t in tokens)
            rows = conn.execute(
                "SELECT id FROM restaurant_fts WHERE restaurant_fts MATCH ?;",
                (match_expr,),
            ).fetchall()
            matched.update(row["id"] for row in rows)

        stripped = phrase.strip()
        if len(stripped) > 1 and _HAS_THAI.search(stripped):
            rows = conn.execute(
                "SELECT id FROM restaurant_fts WHERE body LIKE ? ESCAPE '\\';",
                (_like_pattern(stripped),),
            ).fetchall()
            matched.update(row["id"] for row in rows)

    return matched