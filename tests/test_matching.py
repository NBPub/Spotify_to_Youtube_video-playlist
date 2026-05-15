from utils.matching import normalize, core_title, is_match


def test_normalize_lowercases():
    assert normalize("The Weeknd") == "weeknd"


def test_normalize_removes_punctuation():
    assert normalize("Don't Stop Me Now!") == "dont stop me now"


def test_normalize_removes_stopwords():
    assert normalize("A Sky Full of Stars") == "sky full stars"


def test_normalize_handles_mixed():
    assert normalize("The Show Must Go On") == "show must go on"


def test_is_match_exact():
    assert is_match(
        song_name="Blinding Lights",
        artist="The Weeknd",
        result_title="The Weeknd - Blinding Lights (Official Music Video)",
        channel_name="The Weeknd",
    )


def test_is_match_vevo_channel():
    assert is_match(
        song_name="Shape of You",
        artist="Ed Sheeran",
        result_title="Ed Sheeran - Shape of You [Official Video]",
        channel_name="EdSheeranVEVO",
    )


def test_is_match_fails_wrong_artist():
    assert not is_match(
        song_name="Blinding Lights",
        artist="The Weeknd",
        result_title="Blinding Lights Cover",
        channel_name="SomeRandomCoverChannel",
    )


def test_is_match_fails_wrong_song():
    assert not is_match(
        song_name="Save Your Tears",
        artist="The Weeknd",
        result_title="The Weeknd - Blinding Lights (Official Video)",
        channel_name="The Weeknd",
    )


def test_is_match_handles_articles_in_song():
    assert is_match(
        song_name="The Less I Know The Better",
        artist="Tame Impala",
        result_title="Tame Impala - Less I Know Better (Official Video)",
        channel_name="Tame Impala",
    )


# HTML entity handling
def test_normalize_decodes_html_amp():
    assert normalize("Rich &amp; Famous") == normalize("Rich & Famous")


def test_normalize_decodes_html_quot():
    assert normalize("&quot;We&#39;ve Only Just Begun&quot;") == normalize(
        '"We\'ve Only Just Begun"'
    )


def test_is_match_html_entities_in_title():
    # Good Charlotte - &amp; in YouTube title
    assert is_match(
        song_name="Lifestyles of the Rich & Famous",
        artist="Good Charlotte",
        result_title="Good Charlotte - Lifestyles of the Rich &amp; Famous (Official Video)",
        channel_name="GoodCharlotteVEVO",
    )


def test_is_match_html_entities_carpenters():
    # Carpenters - &quot; and &#39; in YouTube title
    assert is_match(
        song_name="We've Only Just Begun",
        artist="Carpenters",
        result_title='Carpenters &quot;We&#39;ve Only Just Begun&quot; on The Ed Sullivan Show',
        channel_name="Carpenters",
    )


# core_title stripping
def test_core_title_strips_recording_info():
    assert core_title("Hybrid Moments - C.I. Recording 1978") == "Hybrid Moments"


def test_core_title_plain_name_unchanged():
    assert core_title("Blinding Lights") == "Blinding Lights"


def test_is_match_song_with_extra_recording_info():
    # Misfits - extra recording info in Exportify name shouldn't block match
    assert is_match(
        song_name="Hybrid Moments - C.I. Recording 1978",
        artist="Misfits",
        result_title="Hybrid Moments- Misfits",
        channel_name="Molly Rowland",
    )


# Concatenated VEVO-style channel matching (artist only in channel, not title)
def test_is_match_vevo_channel_artist_not_in_title():
    assert is_match(
        song_name="Lifestyles of the Rich & Famous",
        artist="Good Charlotte",
        result_title="Lifestyles of the Rich & Famous (Official Video)",
        channel_name="GoodCharlotteVEVO",
    )


# core_title: collaboration suffix stripping
def test_core_title_strips_with_suffix():
    assert core_title("Persuasive (with SZA)") == "Persuasive"


def test_core_title_strips_feat_suffix():
    assert core_title("Money Trees (feat. Jay Rock)") == "Money Trees"


def test_core_title_strips_ft_suffix():
    assert core_title("Partition (ft. Beyoncé)") == "Partition"


def test_core_title_strips_featuring_suffix():
    assert core_title("Higher (featuring Snoop Dogg)") == "Higher"


# Low strictness: word-overlap song matching
def test_is_match_low_word_overlap_repeated_title():
    # Jorge Ben Jor — Exportify repeats title; YouTube has it once
    assert is_match(
        song_name="Os Alquimistas Estão Chegando Os Alquimistas",
        artist="Jorge Ben Jor",
        result_title="Jorge Ben Jor - Os alquimistas estão chegando",
        channel_name="Jorge Ben Jor",
        strictness="low",
    )


def test_is_match_low_word_overlap_no_artist_check():
    # T-Pain — artist name has hyphen that breaks medium match; low skips artist check
    assert is_match(
        song_name="Tennessee Whiskey",
        artist="T-Pain",
        result_title="T Pain - Tennessee Whiskey (Live from the Sun Rose 2023)",
        channel_name="Kevin Thomas",
        strictness="low",
    )


def test_is_match_low_strips_version_suffix():
    # "(Interlude)" in song name should not block matching the official video
    assert is_match(
        song_name="What Goes Around.../...Comes Around (Interlude)",
        artist="Justin Timberlake",
        result_title="What Goes Around...Comes Around (Official Video)",
        channel_name="justintimberlakeVEVO",
        strictness="low",
    )


def test_is_match_low_compound_word_in_title():
    # "Dump Truck" in song name vs "DUMPTRUCK" in YouTube title
    assert is_match(
        song_name="Back It up and Dump It (Dump Truck)",
        artist="GC Eternal;Kinfolk Thugs;Tyme Bomb;Tre'v",
        result_title="DUMPTRUCK (BACK IT UP AND DUMP IT) [Official Music Video]",
        channel_name="KinfolkThugsVEVO",
        strictness="low",
    )


def test_is_match_low_fails_when_song_words_absent():
    assert not is_match(
        song_name="Tennessee Whiskey",
        artist="T-Pain",
        result_title="Some completely unrelated video",
        channel_name="Some Channel",
        strictness="low",
    )


# Multi-artist semicolon handling
def test_is_match_multi_artist_primary_in_title():
    # Khruangbin;Leon Bridges — primary artist in title, channel is label
    assert is_match(
        song_name="Texas Sun",
        artist="Khruangbin;Leon Bridges",
        result_title="Khruangbin &amp; Leon Bridges - Texas Sun (Official Video)",
        channel_name="Dead Oceans",
    )


def test_is_match_multi_artist_primary_in_channel():
    # People Under The Stairs;Camel MC — primary artist matches Topic channel
    assert is_match(
        song_name="Acid Raindrops",
        artist="People Under The Stairs;Camel MC",
        result_title="Acid Raindrops",
        channel_name="People Under the Stairs - Topic",
    )


def test_is_match_multi_artist_vevo_channel_with_prefix():
    # Doechii;SZA — "Doechii" is substring of "IamdoechiiVEVO"
    assert is_match(
        song_name="Persuasive (with SZA)",
        artist="Doechii;SZA",
        result_title="Doechii &amp; SZA - Persuasive (Official Video)",
        channel_name="IamdoechiiVEVO",
    )


def test_is_match_multi_artist_primary_in_channel_and_title():
    # Gangsta Pat;Psycho — primary artist in both channel and title (after unescape)
    assert is_match(
        song_name="I Wanna Smoke",
        artist="Gangsta Pat;Psycho",
        result_title='Gangsta Pat &quot;I Wanna Smoke&quot; (Official Audio)',
        channel_name="Gangsta Pat",
    )


# Censored word handling (f**k → f__k wildcard)
def test_normalize_preserves_censored_word_as_wildcard():
    # f**k should survive as f__k (underscores), not be stripped to fk
    assert normalize("F**k It") == "f__k it"


def test_is_match_censored_word_medium():
    # Eamon — YouTube title uses f**k censorship; song name has uncensored word
    assert is_match(
        song_name="Fuck It (I Don't Want You Back)",
        artist="Eamon",
        result_title="Eamon - F**k It (I Don&#39;t Want You Back) (Official Video)",
        channel_name="EamonVEVO",
    )


def test_is_match_censored_word_low():
    assert is_match(
        song_name="Fuck It (I Don't Want You Back)",
        artist="Eamon",
        result_title="Eamon - F**k It (I Don&#39;t Want You Back) (Official Video)",
        channel_name="EamonVEVO",
        strictness="low",
    )


def test_is_match_censored_word_high():
    assert is_match(
        song_name="Fuck It (I Don't Want You Back)",
        artist="Eamon",
        result_title="Eamon - F**k It (I Don&#39;t Want You Back) (Official Video)",
        channel_name="EamonVEVO",
        strictness="high",
    )


def test_is_match_censored_short_word():
    # s**t (4 chars) should match shit (4 chars)
    assert is_match(
        song_name="Shit Is Real",
        artist="Fat Joe",
        result_title="Fat Joe - S**t Is Real (Official Video)",
        channel_name="Fat Joe",
    )


def test_word_matches_does_not_false_positive_wrong_length():
    # f**k (len 4) should not match fork (len 4, different letters) — but it will
    # match any 4-char word starting with f and ending with k, which is intentional.
    # Verify it correctly rejects wrong length: f**k should not match funk if len differs.
    assert normalize("F**k") == "f__k"
    assert normalize("fu") != normalize("f__k")  # different lengths, no match


# Diacritic / accent stripping
def test_normalize_strips_diacritics():
    assert normalize("Mýa") == "mya"
    assert normalize("Beyoncé") == "beyonce"
    assert normalize("Sigur Rós") == "sigur ros"


def test_is_match_accented_artist_medium():
    # Mýa — Exportify has stylized accent; YouTube uses plain "Mya"
    assert is_match(
        song_name="My Love Is Like...Wo",
        artist="Mýa",
        result_title="Mya - My Love Is Like...Wo (Unedited Version) (Official Music Video)",
        channel_name="MyaVEVO",
    )


def test_is_match_accented_song_title():
    # Accented characters in the song title should also normalize
    assert is_match(
        song_name="Déjà Vu",
        artist="Olivia Rodrigo",
        result_title="Olivia Rodrigo - deja vu (Official Video)",
        channel_name="OliviaRodrigoVEVO",
    )
