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


def _escape(token: str) -> str:
    return '"' + _QUERY_SPECIAL.sub(" ", token) + '"'


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

    Each phrase is treated as an AND-of-tokens requirement (every word must be
    present somewhere in the restaurant's material). A phrase with no usable
    tokens is skipped — it contributes nothing but never errors. Returns an
    empty set when nothing matches.
    """
    if not phrases:
        return set()

    terms: list[str] = []
    for phrase in phrases:
        tokens = [t for t in _TOKEN_SEP.split(phrase) if len(t) > 1]
        terms.extend(_escape(t) for t in tokens)

    if not terms:
        return set()

    match_expr = " AND ".join(terms)
    rows = conn.execute(
        "SELECT id FROM restaurant_fts WHERE restaurant_fts MATCH ?;",
        (match_expr,),
    ).fetchall()
    return {row["id"] for row in rows}