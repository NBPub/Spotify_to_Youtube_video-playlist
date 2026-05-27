# Video Matching

**Contents**

- [Approach](#the-basic-approach)
- [Trade-off](#trade-off-a-match-vs-the-best-match)
- [Strictness](#match-strictness)
- [Normalization](#normalization)
- [Censored words](#censored-words)
- [Known limitations](#known-limitations)

## The basic approach

For each track, Phase 2 queries the YouTube Data API with a search string built from the artist and song title:

```
<Primary Artist> - <Core Song Title> Official
```

The top 3 results are inspected and the first one that passes the configured match criteria is selected. Fetching 3 results costs the same quota as 1 (100 units per `search.list` call), so checking multiple candidates is effectively free.

## Trade-off: a match vs. the best match

There are two ways to think about this problem:

- **Find _a_ match** — Accept any reasonable upload: official music video, official audio, lyric video, well-produced fan upload. Optimizes for *every song gets a video*.
- **Find _the best_ match** — Only accept official music videos from verified artist channels. Optimizes for quality and consistency, at the cost of many tracks ending up unmatched.

Current behavior leans toward the first. By default (medium strictness), the pipeline accepts any video where the song title appears as a substring of the YouTube title and at least one credited artist appears in the title or channel. This produces the highest match rate, but the resulting playlist is a mix of official videos, official audio uploads, lyric videos, and the occasional fan upload.

A stricter "music videos only" mode is planned but not yet implemented — see [below](#match-strictness).

## Match strictness

Controlled by the `MATCH_STRICTNESS` environment variable:

| Level | Behavior |
|-------|-----------|
| `low` | Fuzzy song match only. All parenthetical content is stripped from the song name first (e.g. `(Interlude)`, `(Album Version)`, `(Radio Edit)`), then every remaining song word must appear in the YouTube title (order-independent; handles compound words and repeated phrases). Artist is not checked. |
| `medium` | Song title substring match + any credited artist appears in the title or channel. **Default.** |
| `high` | Song title substring match + primary artist only (the first artist in a semicolon-separated list). |

`high` is currently artist-strict but is **intended to also filter for official music videos specifically** — requiring signals like "Official Music Video" in the title, or restricting to verified artist channels. That filtering is **not yet implemented**; until it is, `high` mostly just rejects matches credited to a featured artist rather than the primary.

## Normalization

Before comparison, both the song name and the YouTube title/channel are passed through [`normalize()`](../utils/matching.py#L8):

1. Decode HTML entities (`&amp;` → `&`, `&quot;` → `"`, `&#39;` → `'`)
2. Strip diacritics via Unicode NFKD decomposition, so stylized artist/song spellings match plain-ASCII YouTube titles (`Mýa` → `Mya`, `Beyoncé` → `Beyonce`, `Sigur Rós` → `Sigur Ros`)
3. Lowercase
4. Preserve censored words: runs of `*` between letters are replaced with `_` characters (so `F**k` survives as `f__k` rather than being collapsed to `fk` when punctuation is stripped)
5. Strip punctuation
6. Remove stopwords (`a`, `the`, `an`, `and`, `of`, `in`, `is`, `at`)

The song name itself is first passed through [`core_title()`](../utils/matching.py#L25), which strips:

- Recording/version info after ` - ` (e.g. `"Hybrid Moments - C.I. Recording 1978"` → `"Hybrid Moments"`)
- Collaboration suffixes: `(with X)`, `(feat. X)`, `(ft. X)`, `(featuring X)`

## Censored words

YouTube censors explicit words in some official titles (`F**k It` instead of `Fuck It`). The normalizer preserves the censorship pattern as per-character `_` wildcards, and the matcher treats a word containing `_` as a regex pattern where each `_` matches exactly one character: `f__k` matches `fuck` via `re.fullmatch("f..k", "fuck")`.

This applies at all strictness levels. Trailing censorship (`f***`, with no right-side letter to anchor on) is **not yet handled** and will still fail to match.

## Known limitations

### Stopword collision in artist names

 `"Del The Funky Homosapien"` normalizes to `"del funky homosapien"` (the stopword `the` is dropped). YouTube often uses the stylized `"Del tha Funky Homosapien"` — `tha` is not a stopword and is retained, so the normalized song-artist isn't a contiguous substring of the title-artist. Medium strictness rejects this; low works around it by skipping the artist check entirely.

### Artist monikers

Some artists release under multiple aliases (Del the Funky Homosapien is also "Sir DZL"; MF DOOM also released as "Viktor Vaughn", "King Geedorah", "Madvillain", etc.). These are typically tagged as distinct Spotify artists. No alias resolution is implemented — the matcher takes the artist string as given.

### Foreign-language video titles

YouTube's browser UI localizes titles based on account language, the `Accept-Language` header, and IP geolocation; the Data API does none of this and returns each video's title and channel in the uploader's primary language. A track like `"WEDNESDAY CAMPANELLA - Diablo"` (English-tagged in Exportify) returns the right video, but the API gives the title as `"水曜日のカンパネラ『ディアブロ』"` and the channel as `"水曜日のカンパネラ"` — neither has any substring overlap with the song or artist, so the match fails. The cheapest workaround would be a follow-up `videos.list?part=localizations` call to fetch the uploader's English title (costs +1 unit per candidate, and only helps when the uploader actually configured an English localization). For now: skip these and add the video to the playlist manually.
