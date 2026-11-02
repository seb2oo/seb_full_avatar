
import re

AVATAR_TAGS = [

    # ============================================================
    # NATURAL / CONVERSATIONAL — HIGH PRIORITY
    # ============================================================

    "[natural conversational tone]",
    "[warm and natural conversational tone]",
    "[friendly and relaxed conversational tone]",
    "[casual and spontaneous tone]",
    "[warm tone]",
    "[friendly tone]",
    "[calm tone]",
    "[relaxed tone]",
    "[confident but relaxed tone]",
    "[professional but approachable tone]",

    # ============================================================
    # EMOTIONS — HIGH PRIORITY
    # ============================================================

    "[happy]",
    "[excited]",
    "[excited but still natural]",
    "[amused]",
    "[slightly amused]",
    "[sad]",
    "[worried]",
    "[slightly worried]",
    "[nervous]",
    "[slightly nervous but trying to stay confident]",
    "[surprised]",
    "[genuinely surprised]",
    "[angry]",
    "[frustrated]",
    "[confused]",
    "[serious but still warm and approachable]",
    "[thoughtful]",
    "[curious and engaged]",

    # ============================================================
    # HUMAN REACTIONS
    # ============================================================

    "[laughing]",
    "[chuckling]",
    "[laughing softly and naturally]",
    "[sigh]",
    "[inhale]",
    "[exhale]",
    "[clearing throat]",

    # ============================================================
    # RHYTHM / PAUSES
    # ============================================================

    "[pause]",
    "[short pause]",
    "[long pause]",
    "[pause briefly as if thinking]",
    "[slight hesitation before answering]",
    "[speaking slowly]",

    # ============================================================
    # VOICE / DELIVERY
    # ============================================================

    "[whisper]",
    "[soft voice]",
    "[low voice]",
    "[loud]",
    "[emphasis]",
    "[natural voice with a slight smile]",
    "[calm and reassuring voice]",
    "[answer naturally as if speaking to a friend]",
]


# ================================================================
# OTHER USEFUL TAGS / FREE-FORM EXPRESSIONS
# Kept here for future testing, but NOT part of the 50 core tags.
# ================================================================

# --- Natural / conversational ---
# "[gentle tone]"
# "[neutral tone]"
# "[casual tone]"
# "[confident tone]"
# "[professional tone]"
# "[reassuring tone]"
# "[empathetic tone]"
# "[playful tone]"
# "[teasing tone]"
# "[welcoming tone]"

# --- Emotions ---
# "[delighted]"
# "[enthusiastic]"
# "[delight]"
# "[disappointed]"
# "[shocked]"
# "[relieved]"
# "[concerned tone]"
# "[comforting tone]"
# "[quietly disappointed]"
# "[gently concerned]"
# "[calm but slightly excited]"
# "[happy and enthusiastic]"
# "[reassuring and empathetic]"
# "[serious and thoughtful]"
# "[surprised but genuinely happy]"

# --- Human reactions ---
# "[chuckle]"
# "[tsk]"
# "[deep sigh]"
# "[yawning]"
# "[groaning]"
# "[panting]"
# "[moaning]"
# "[audience laughter]"
# "[quiet laugh]"
# "[slight amused laugh]"
# "[a brief natural chuckle]"
# "[take a small breath before speaking]"
# "[slight sigh before continuing]"

# --- Thinking / conversational behavior ---
# "[hesitating]"
# "[thinking]"
# "[thoughtful pause]"
# "[dramatic pause]"
# "[thinking aloud]"
# "[explaining clearly]"
# "[explaining this clearly and patiently]"
# "[answering thoughtfully]"
# "[clarifying]"
# "[correcting myself]"
# "[asking a question]"
# "[answering confidently]"
# "[sound genuinely interested in the conversation]"
# "[sound thoughtful and reflective]"
# "[sound reassuring and sincere]"

# --- Pace ---
# "[slowly]"
# "[speaking quickly]"
# "[fast-paced]"
# "[slightly slower and more deliberate]"
# "[slightly faster and more energetic]"
# "[dynamic conversational delivery]"

# --- Volume / voice ---
# "[very soft voice]"
# "[low volume]"
# "[quietly]"
# "[loud voice]"
# "[shouting]"
# "[screaming]"
# "[volume up]"
# "[volume down]"
# "[soft and intimate delivery]"
# "[lower the voice for a more intimate moment]"
# "[raise the energy gradually]"

# --- Intonation / emphasis ---
# "[strong emphasis]"
# "[slight emphasis]"
# "[dramatic emphasis]"
# "[questioning tone]"
# "[uncertain tone]"
# "[reassuring tone]"
# "[subtle emotional emphasis]"
# "[strong emphasis on the important words]"
# "[build excitement gradually]"

# --- Advanced free-form combinations ---
# "[warm, friendly and slightly amused]"
# "[calm, thoughtful and reassuring]"
# "[excited, energetic and spontaneous]"
# "[slightly tired but still friendly]"
# "[curious, engaged and enthusiastic]"
# "[empathetic and gently reassuring]"
# "[playful and slightly teasing]"
# "[serious but friendly]"
# "[confident but not arrogant]"
# "[enthusiastic without exaggerating]"
# "[speak spontaneously without sounding rehearsed]"
# "[speak naturally as if telling a story]"
# "[tell this like a personal story]"




# ============================================================
# AVATAR TAG FILTER
# ============================================================

AVATAR_TAG_PATTERN = re.compile(
    "|".join(
        re.escape(tag)
        for tag in sorted(AVATAR_TAGS, key=len, reverse=True)
    ),
    flags=re.IGNORECASE,
)


def remove_avatar_tags(text):
    """
    Remove official avatar tags + common LLM-generated variations.
    """

    if not text:
        return ""

    text = str(text)

    # --------------------------------------------------------
    # 1. Remove exact tags from AVATAR_TAGS
    # --------------------------------------------------------

    cleaned = AVATAR_TAG_PATTERN.sub("", text)

    # --------------------------------------------------------
    # 2. Remove common variations generated by the LLM
    # --------------------------------------------------------

    # pause / pausing variations
    cleaned = re.sub(
        r"\[\s*paus(?:e|ing)\s+"
        r"(?:briefly|slightly|for a moment)?\s*"
        r"(?:as if thinking|while thinking|before answering)?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # laugh / laughing variations
    cleaned = re.sub(
        r"\[\s*laugh(?:ing)?"
        r"(?:\s+(?:softly|slightly|naturally))?"
        r"(?:\s+and\s+naturally)?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # sigh / sighing
    cleaned = re.sub(
        r"\[\s*sigh(?:ing)?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # whisper / whispering
    cleaned = re.sub(
        r"\[\s*whisper(?:ing)?"
        r"(?:\s+(?:softly|quietly))?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # smile / smiling
    cleaned = re.sub(
        r"\[\s*smil(?:e|ing)"
        r"(?:\s+(?:warmly|softly|slightly|naturally))?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # think / thinking
    cleaned = re.sub(
        r"\[\s*(?:think|thinking|thoughtful)"
        r"(?:\s+(?:for a moment|briefly|slightly|as if thinking))?\s*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # 3. Generic avatar-style tags
    # --------------------------------------------------------

    AVATAR_KEYWORDS = (
      r"tone|voice|speaking|speak|talking|talk|"
      r"laugh|laughing|chuckle|chuckling|"
      r"sigh|sighing|"
      r"pause|pausing|"
      r"whisper|whispering|"
      r"inhale|exhale|breath|breathing|"
      r"smile|smiling|"
      r"think|thinking|thoughtful|"
      r"hesitat\w*|"
      r"excited|happy|sad|angry|"
      r"worried|nervous|surprised|"
      r"confused|frustrated|"
      r"amused|curious|serious|"
      r"calm|relaxed|friendly|warm|"
      r"natural|naturally|"
      r"loud|soft|quiet|low|"
      r"emphasis|clearing throat"
      r"confident|"
      r"relieved|relief|"
      r"stressed|stress|"
      )

    cleaned = re.sub(
        rf"\[(?=[^\[\]]*(?:{AVATAR_KEYWORDS}))"
        rf"[^\[\]]*\]",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )


    # --------------------------------------------------------
    # Remove emotional annotations between asterisks
    # Examples:
    # *warm and natural*
    # **laughing softly**
    # *thoughtful pause*
    # --------------------------------------------------------

    cleaned = re.sub(
        rf"(?<!\w)\*{{1,2}}\s*"
        rf"(?=[^*\n]{{0,100}}\b(?:{AVATAR_KEYWORDS})\b)"
        rf"[^*\n]{{1,100}}?"
        rf"\s*\*{{1,2}}(?!\w)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # 4. Clean remaining whitespace
    # --------------------------------------------------------

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)

    return cleaned.strip()



def remove_avatar_tags_for_streaming(raw_text):
    """
    Streaming-safe avatar tag cleaner.

    Removes completed tags and hides incomplete avatar tags
    while the LLM is still generating them.
    """

    if not raw_text:
        return ""

    raw_text = str(raw_text)

    # First remove all completed avatar tags
    cleaned = remove_avatar_tags(raw_text)

    # --------------------------------------------------------
    # Detect an incomplete [ ... tag at the end
    # --------------------------------------------------------

    last_open = raw_text.rfind("[")
    last_close = raw_text.rfind("]")

    if last_open > last_close:

        partial = raw_text[last_open:]
        partial_lower = partial.lower().lstrip("[ ")

        avatar_prefixes = (
            "tone",
            "warm",
            "friendly",
            "calm",
            "relaxed",
            "happy",
            "excited",
            "amused",
            "sad",
            "worried",
            "nervous",
            "surprised",
            "angry",
            "frustrated",
            "confused",
            "serious",
            "thoughtful",
            "curious",
            "laugh",
            "chuckl",
            "sigh",
            "inhale",
            "exhale",
            "pause",
            "paus",
            "whisper",
            "soft",
            "low",
            "loud",
            "emphasis",
            "clearing",
            "speaking",
            "answer",
            "think",
            "thinking",
        )

        if any(
            partial_lower.startswith(prefix)
            for prefix in avatar_prefixes
        ):
            cleaned_before = raw_text[:last_open]
            cleaned = remove_avatar_tags(cleaned_before)

        
    # --------------------------------------------------------
    # Hide incomplete *emotional annotations during streaming
    # --------------------------------------------------------

    match = re.search(
        r"(?<!\w)\*{1,2}([^*\n]{0,100})$",
        raw_text,
    )

    if match:

        partial = match.group(1).strip().lower()

        avatar_prefixes = (
            "warm", "natural", "friendly",
            "happy", "excited", "amused",
            "sad", "worried", "nervous",
            "surprised", "angry", "frustrated",
            "confused", "serious", "thoughtful",
            "curious", "laugh", "chuckl",
            "sigh", "pause", "whisper",
            "soft", "low", "loud",
            "calm", "relaxed", "confident",
            "playful", "gentle", "speaking",
            "thinking", "hesitat", "smil",
            "answer", "voice", "tone",
            "breath", "emphasis",
        )

        if not partial or any(
            partial.startswith(prefix)
            or prefix.startswith(partial)
            for prefix in avatar_prefixes
        ):
            cleaned = remove_avatar_tags(
                raw_text[:match.start()]
            )



    return cleaned


import re


def clean_avatar_text_for_tts(text: str) -> str:
    """
    Prepare LLM output for TTS.

    - Convert *emotion* into [emotion].
    - Convert **emotion** into [emotion].
    - Preserve all existing [emotion] tags,
      including custom tags.
    - Remove trailing tags without spoken text.
    - Preserve normal text and punctuation.
    """

    if not text:
        return ""

    text = str(text)

    # --------------------------------------------------------
    # 1. Convert asterisk annotations into square-bracket tags
    # --------------------------------------------------------

    def convert_asterisk_tag(match):
        content = match.group(1).strip()

        if not content:
            return ""

        return f"[{content}]"

    # Double asterisks: **happy** -> [happy]
    text = re.sub(
        r"(?<!\*)\*\*\s*([^*\n]{1,120}?)\s*\*\*(?!\*)",
        convert_asterisk_tag,
        text,
    )

    # Single asterisks: *happy* -> [happy]
    text = re.sub(
        r"(?<!\*)\*\s*([^*\n]{1,120}?)\s*\*(?!\*)",
        convert_asterisk_tag,
        text,
    )

    # --------------------------------------------------------
    # 2. Remove trailing tags
    #
    # Example:
    # "Hello! [happy]" -> "Hello!"
    # --------------------------------------------------------

    text = re.sub(
        r"(?:\s*\[[^\[\]\n]{1,120}\]\s*)+$",
        "",
        text,
    )

    # --------------------------------------------------------
    # 3. Normalize whitespace
    # --------------------------------------------------------

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()




# ============================================================
# BUILD EXACT TAG LIST FOR SYSTEM PROMPT
# ============================================================
#
# IMPORTANT:
#
# We are NOT redefining AVATAR_TAGS.
#
# We are simply converting the existing list into text so the
# LLM knows the exact tags it is allowed to generate.
# ============================================================

AVATAR_TAGS_TEXT = "\n".join(

    f"- {tag}"

    for tag in AVATAR_TAGS

)
