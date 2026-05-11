import html
import re

STOPWORDS = {"a", "the", "an", "and", "of", "in", "is", "at"}


def normalize(text: str) -> str:
    text = html.unescape(text)
    text = text.lower()
    # Preserve censored-word patterns (f**k, s**t) by replacing * runs between
    # letters with underscores before the punctuation strip — underscores survive
    # [^\w\s] and act as per-character wildcards during word matching.
    text = re.sub(r"(?<=\w)\*+(?=\w)", lambda m: "_" * len(m.group()), text)
    text = re.sub(r"[^\w\s]", "", text)
    words = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(words)


def core_title(song_name: str) -> str:
    """Return core song title, stripping recording/version info after ' - ' and
    collaboration suffixes like '(with X)', '(feat. X)', '(ft. X)', '(featuring X)'."""
    title = song_name.split(" - ")[0].strip()
    title = re.sub(
        r"\s*\((?:with|feat\.?|ft\.?|featuring)\s[^)]*\)",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    return title


def _word_matches(song_word: str, title_word: str) -> bool:
    """Exact equality, or wildcard match when a word contains underscores (censored
    chars preserved by normalize). Each underscore matches exactly one character."""
    if song_word == title_word:
        return True
    for word, other in ((title_word, song_word), (song_word, title_word)):
        if "_" in word and len(word) == len(other):
            pattern = re.escape(word).replace("_", ".")
            if re.fullmatch(pattern, other):
                return True
    return False


def _song_in_title(norm_song: str, norm_title: str) -> bool:
    """Substring check with wildcard fallback when norm_title contains censored
    chars (underscores). Falls back to word-overlap matching in that case."""
    if norm_song in norm_title:
        return True
    if "_" in norm_title:
        return _song_words_in_title(norm_song, norm_title)
    return False


def _song_words_in_title(norm_song: str, norm_title: str) -> bool:
    """All unique words from the song name appear in the title (order-independent).
    Falls back to substring-within-word matching to handle compound words like
    'dump truck' → 'dumptruck' or 't pain' → 'tpain'."""
    title_words = set(norm_title.split())
    return all(
        any(_word_matches(word, tw) for tw in title_words)
        or any(word in tw for tw in title_words)
        for word in set(norm_song.split())
    )


def _artist_matches_title_or_channel(norm_artist: str, norm_title: str, norm_channel: str) -> bool:
    return (
        norm_artist in norm_title
        or norm_artist in norm_channel
        or norm_artist.replace(" ", "") in norm_channel.replace(" ", "")
    )


def is_match(
    song_name: str,
    artist: str,
    result_title: str,
    channel_name: str,
    strictness: str = "medium",
) -> bool:
    """
    Check whether a YouTube result matches the given song and artist.

    Strictness levels:
      low    — fuzzy song match only; artist not checked. All parenthetical content
               is stripped from the song name (e.g. '(Interlude)', '(Album Version)'),
               then all unique remaining words must appear in the title
               (order-independent; also handles compound words like 'dump truck' →
               'dumptruck' and repeated phrases in Exportify track names).
      medium — (default) exact song title substring match + any semicolon-separated
               artist must match the title or channel name (including concatenated
               VEVO-style).
      high   — exact song title substring match + primary artist only (first before
               ';') must match. Intended for official music videos; official video
               filtering (title signals, verified channels) is pending.
    """
    norm_title = normalize(result_title)
    norm_channel = normalize(channel_name)

    if strictness == "low":
        # Strip all parenthetical content for maximum permissiveness — version/type
        # suffixes like (Interlude), (Album Version), (Radio Edit) shouldn't block a match.
        song_base = re.sub(r"\s*\([^)]*\)", "", core_title(song_name)).strip()
        return _song_words_in_title(normalize(song_base), norm_title)

    norm_song = normalize(core_title(song_name))

    if not _song_in_title(norm_song, norm_title):
        return False

    artists = [a.strip() for a in artist.split(";")]
    if strictness == "high":
        artists = artists[:1]  # primary artist only

    return any(
        _artist_matches_title_or_channel(normalize(a), norm_title, norm_channel)
        for a in artists
    )
