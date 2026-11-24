"""Email text cleaning, header stripping, HTML normalization, token masking, and filtering."""
import re
import unicodedata
import email
from email.message import Message
from bs4 import BeautifulSoup
import pandas as pd

# Regex patterns for RFC 822 / MIME email headers and forwarded blocks
# Regex patterns for RFC 822 / MIME email headers and forwarded blocks
HEADER_PATTERNS = [
    # Initial RFC 822 envelope mbox From line
    re.compile(r"^From\s+[^\r\n]*\r?\n?", re.IGNORECASE | re.MULTILINE),
    # Full multiline RFC 822 / MIME / mailing-list headers, allowing leading spaces and multiline folded continuation lines
    re.compile(
        r"^[ \t]*(?:From|To|Cc|Bcc|Date|Sent|Subject|Received|Message-ID|Return-Path|Delivered-To|"
        r"Content-Type|Content-Transfer-Encoding|MIME-Version|In-Reply-To|References|Status|Lines|Importance|"
        r"Sender|Errors-To|Precedence|Priority|Content-[A-Za-z0-9-]+|Reply-To|Mail-[A-Za-z0-9-]+|"
        r"Organization|Mailing-List|Resent-[A-Za-z0-9-]+|List-[A-Za-z0-9-]+|X-[A-Za-z0-9_-]+)\s*:[^\r\n]*(?:\r?\n[ \t]+[^\r\n]*)*\r?\n?",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"(?:-----Original Message-----|-+\s*Forwarded by.*?-+|Begin forwarded message:|"
        r"-\s*-\s*-\s*-\s*Original Message\s*-\s*-\s*-\s*-|"
        r"-\s*-\s*-\s*-\s*Forwarded by.*?\s*-\s*-\s*-\s*-).*?"
        r"(?=(?:Dear|\n[A-Z0-9][a-z0-9-]+:|\n\n|\r\n\r\n|$))",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:-+\s*Forwarded by.*?-+|-\s*-\s*-\s*-\s*Forwarded by.*?\s*-\s*-\s*-\s*-|forwarded by[^\n]*)",
        re.IGNORECASE,
    ),
]

# Reply quote pattern: lines starting with > or |
REPLY_QUOTE_REGEX = re.compile(r"^\s*[>|].*$", re.MULTILINE)

# Inline / spaced header remnants: matches collapsed header chains like 'to : ... cc : ... subject :'
SPACED_HEADER_CHAIN_REGEX = re.compile(
    r"\b(?:to|cc|bcc|sent|from)\s*:[ \t]*[^:\n]*?(?=\b(?:to|cc|bcc|sent|from|subject)\s*:)",
    re.IGNORECASE,
)
EMPTY_SPACED_HEADER_REGEX = re.compile(
    r"\b(?:to|cc|bcc|sent|from|subject)\s*:[ \t]*(?=\b(?:to|cc|bcc|sent|from|subject)\s*:|\n|$)",
    re.IGNORECASE,
)
INLINE_SUBJECT_TAG = re.compile(r"\b(?:subject|sent)\s*:\s*", re.IGNORECASE)

# Leftover inline / residual header artifacts
INLINE_LEFTOVER_HEADER_REGEX = re.compile(
    r"\b(?:sender|errors-to|precedence|list-unsubscribe|list-help|list-subscribe|list-id|list-post|list-archive|priority|content-description|message-id|received|x-[a-z0-9_-]+)\s*:[^\n]*",
    re.IGNORECASE,
)

# Forbidden header patterns check for the first 300 characters
FORBIDDEN_HEADER_REGEX = re.compile(
    r"\b(sender:|errors-to:|precedence:|list-unsubscribe:|list-help:|list-subscribe:|priority:|content-description:|message-id:|received:|x-[a-z0-9_-]+:)",
    re.IGNORECASE,
)

def has_forbidden_headers_in_prefix(text: str, prefix_len: int = 300) -> bool:
    """Return True if any forbidden RFC 822 or mailing-list header pattern appears in the first prefix_len characters."""
    if not isinstance(text, str):
        return False
    return bool(FORBIDDEN_HEADER_REGEX.search(text[:prefix_len]))

# Spaced header prefix at line start: e.g. "from : John Doe\n" or "to : Jane Doe\n"
LINE_SPACED_HEADER_REGEX = re.compile(
    r"^\s*(?:to|from|cc|bcc|sent|subject|date|message-id|sender|errors-to|precedence|priority|content-description|received|x-[a-z0-9_-]+)\s*:\s*[^\n]*\n?",
    re.IGNORECASE | re.MULTILINE,
)

# Regex patterns for dynamic tokens
URL_REGEX = re.compile(
    r"(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*|"
    r"(?:https?://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?[^\s]*",
    re.IGNORECASE,
)
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
# Formatted phone numbers (with +, parentheses, or dashes/dots)
PHONE_REGEX = re.compile(
    r"(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]\d{3,4}[-.\s]\d{3,4}\b"
)

# Anti-shortcut / Era / Boilerplate tokens
ROUTING_REGEX = re.compile(
    r"(?:/(?:hou|corp|ect|enron)(?:/[a-z0-9_-]+)*|"
    r"\b(?:hou/ect|ect/hou|corp/enron|enron_development)\b|"
    r"@(?:ect|enron)\b)",
    re.IGNORECASE,
)
DATE_REGEX = re.compile(
    r"\b(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+)?"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s*(?:\d{4})?\b|"
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    re.IGNORECASE,
)
TIME_REGEX = re.compile(
    r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?\b|"
    r"\b\d{1,2}\s*(?:AM|PM|am|pm)\b"
)
YEAR_REGEX = re.compile(r"\b(?:199\d|20[0-2]\d)\b")
LONG_NUM_REGEX = re.compile(r"\b\d{5,}\b")
FOOTER_REGEX = re.compile(
    r"(?i)\b(?:to unsubscribe from this (?:list|newsletter|mailing list)|"
    r"click here to unsubscribe|unsubscribe instructions|"
    r"mailing-list:|list-unsubscribe:|ezmlm|majordomo|listserv)\b[^\n]*"
)

# Blatant commercial / adult / pharmaceutical / stock spam cues that lack deceptive identity spoofing
BLATANT_COMMERCIAL_SPAM = re.compile(
    r"\b(viagra|cialis|levitra|soma|phentermine|vicodin|xanax|valium|"
    r"hot lil horny|super horny|megasize your|enlarge your|penis enlargement|"
    r"online pharmacy|canadian pharmacy|prescriptions without|"
    r"stock alert|otcbb|penny stock|target stock|strong buy alert)\b",
    re.IGNORECASE,
)

# Borderline cues: marketing/offers that do not steal credentials or impersonate authorities
BORDERLINE_MARKETING_CUES = re.compile(
    r"\b(exclusive offer|limited time discount|unbeatable prices|lowest mortgage rates|"
    r"pre-approved credit card|guaranteed lowest rate|refinance your home|"
    r"special promotion for our readers|unsubscribe from this newsletter|"
    r"click here to opt out|to be removed from our mailing list)\b",
    re.IGNORECASE,
)

# Deception / Phishing indicators that override benign marketing
DECEPTION_INDICATORS = re.compile(
    r"\b(unauthorized login|suspended account|security alert|verify your identity|"
    r"update your billing information|confirm your account|unusual activity detected|"
    r"account will be locked|wire transfer|beneficiary|inheritance fund|western union)\b",
    re.IGNORECASE,
)

# Normalization maps
QUOTE_DASH_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "`": "'", "´": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "−": "-", "―": "-",
}


def strip_rfc822_initial_block(text: str) -> str:
    """If the text starts with RFC 822 headers / mbox line, strip the top header block ending at the first blank line."""
    if not isinstance(text, str):
        return ""
    lines = text.lstrip().splitlines()
    if not lines:
        return text
    first_line = lines[0]
    header_start = re.match(
        r"^(?:From\s+|Return-Path:|Received:|Delivered-To:|Message-ID:|Sender:|Errors-To:|Date:|Subject:|To:|Cc:|Bcc:|X-[A-Za-z0-9_-]+:|[A-Za-z0-9_-]+\s*:[ \t]*)",
        first_line,
        re.IGNORECASE,
    )
    if header_start:
        parts = re.split(r"\r?\n[ \t]*\r?\n", text, maxsplit=1)
        if len(parts) == 2:
            header_candidate, body = parts
            header_lines = [l for l in header_candidate.splitlines() if l.strip()]
            header_count = sum(1 for l in header_lines if re.match(r"^(?:From\s+|[A-Za-z0-9_-]+\s*:|\s+)", l))
            if header_lines and (header_count / len(header_lines) >= 0.7):
                return body
    return text


def strip_headers(text: str) -> str:
    """Strip RFC 822 headers, forwarded-message blocks, reply quotes, and spaced inline header remnants."""
    if not isinstance(text, str):
        return ""
    cleaned = strip_rfc822_initial_block(text)
    # 1. Strip reply quotes
    cleaned = REPLY_QUOTE_REGEX.sub("", cleaned)
    # 2. Strip line-based spaced headers (e.g., "From : abc@def\n", "To : xyz\n")
    cleaned = LINE_SPACED_HEADER_REGEX.sub("", cleaned)
    # 3. Strip multiline RFC headers & forward blocks
    for pat in HEADER_PATTERNS:
        cleaned = pat.sub("", cleaned)
    # 4. Strip inline/spaced header remnants and chains
    cleaned = SPACED_HEADER_CHAIN_REGEX.sub("", cleaned)
    cleaned = EMPTY_SPACED_HEADER_REGEX.sub("", cleaned)
    cleaned = INLINE_SUBJECT_TAG.sub("", cleaned)
    cleaned = INLINE_LEFTOVER_HEADER_REGEX.sub("", cleaned)
    return cleaned


def strip_html(text: str) -> str:
    """Convert HTML content to plain text, preserving href links and stripping scripts/styles."""
    if not isinstance(text, str):
        return ""
    if "<" in text and ">" in text:
        try:
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style", "noscript", "meta"]):
                tag.decompose()
            for a in soup.find_all("a", href=True):
                href = a.get("href", "").strip()
                if href and not href.startswith("mailto:"):
                    a.replace_with(f" {a.get_text()} {href} ")
                elif href.startswith("mailto:"):
                    a.replace_with(f" {a.get_text()} {href[7:]} ")
            cleaned = soup.get_text(separator=" ")
        except Exception:
            cleaned = text
    else:
        cleaned = text
    return cleaned


def normalize_unicode(text: str) -> str:
    """Normalize unicode representation using NFKC and unify quotes and dashes."""
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKC", text)
    for orig, repl in QUOTE_DASH_MAP.items():
        t = t.replace(orig, repl)
    # Unify contractions: e.g. "it ' s" -> "it's", "can ' t" -> "can't"
    t = re.sub(r"(\w)\s*'\s*([stmd]|re|ve|ll)\b", r"\1'\2", t, flags=re.IGNORECASE)
    return t


def mask_entities(text: str) -> str:
    """Mask URLs, emails, phones, routing markers, dates, years, times, and long digits."""
    if not isinstance(text, str):
        return ""
    # Mask mailing list footers
    masked = FOOTER_REGEX.sub("<footer_marker>", text)
    # Mask URLs and emails
    masked = URL_REGEX.sub("<url>", masked)
    masked = EMAIL_REGEX.sub("<email>", masked)
    # Mask phones
    masked = PHONE_REGEX.sub(
        lambda m: "<phone>" if len(re.sub(r"\D", "", m.group(0))) >= 7 else m.group(0),
        masked,
    )
    # Mask routing text
    masked = ROUTING_REGEX.sub("<routing>", masked)
    # Mask dates, times, years
    masked = DATE_REGEX.sub("<date>", masked)
    masked = TIME_REGEX.sub("<time>", masked)
    masked = YEAR_REGEX.sub("<year>", masked)
    # Mask long digit strings
    masked = LONG_NUM_REGEX.sub("<num>", masked)
    return masked


def normalize_whitespace(text: str) -> str:
    """Collapse excess whitespace and fix unnatural spacing before punctuation."""
    if not isinstance(text, str):
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    return t


def is_commercial_spam(text: str) -> bool:
    """Identify pure commercial/marketing spam that lacks deceptive identity spoofing."""
    if not isinstance(text, str):
        return False
    return bool(BLATANT_COMMERCIAL_SPAM.search(text))


def classify_content_status(text: str) -> tuple[str, str]:
    """Classify email text into valid, commercial_spam, or borderline."""
    if not isinstance(text, str) or not text.strip():
        return "empty_text", "empty or whitespace only"

    if text.strip().lower() == "empty":
        return "empty_text", "literal 'empty' placeholder"

    words = text.split()
    if len(words) < 15:
        return "too_short", f"word count {len(words)} < 15 minimum"

    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii / max(1, len(text)) > 0.40:
        return "non_english_or_corrupt", "high non-ASCII byte ratio (> 40%)"

    # Blatant pharmacy / adult / stock spam
    blatant_match = BLATANT_COMMERCIAL_SPAM.search(text)
    if blatant_match:
        return "commercial_spam_excluded", f"blatant marketing cue: '{blatant_match.group(0)}'"

    # Check for borderline marketing vs deception
    borderline_match = BORDERLINE_MARKETING_CUES.search(text)
    if borderline_match:
        if not DECEPTION_INDICATORS.search(text):
            return "borderline_quarantined", f"ambiguous promotional cue without clear deception: '{borderline_match.group(0)}'"

    return "valid", "passed all cleaning checks"


def clean_email_text(
    text: str, max_chars: int = 5000, mask_tokens: bool = True
) -> str:
    """Full text cleaning pipeline for a single email body."""
    if not isinstance(text, str) or not text.strip():
        return ""

    if text.strip().lower() == "empty":
        return ""

    # 1. Strip headers
    t = strip_headers(text)

    # 2. Strip HTML and styles
    t = strip_html(t)

    # 3. Unicode normalization & quote/dash/contraction unification
    t = normalize_unicode(t)

    # 4. Entity masking
    if mask_tokens:
        t = mask_entities(t)

    # 5. Collapse whitespace
    t = normalize_whitespace(t)

    # 5b. Residual header safety check on first 300 characters
    if has_forbidden_headers_in_prefix(t, 300):
        t = INLINE_LEFTOVER_HEADER_REGEX.sub("", t)
        t = normalize_whitespace(t)

    # 6. Length cap (truncate beyond max_chars at word boundary)
    if len(t) > max_chars:
        t = t[:max_chars].rsplit(" ", 1)[0]

    return t


def validate_email_row(
    cleaned_text: str,
    raw_label: str,
    min_words: int = 15,
) -> tuple[bool, str]:
    """Validate a cleaned email text row against rejection rules."""
    status, reason = classify_content_status(cleaned_text)
    return (status == "valid", status)


def unified_tokenize(text: str) -> list[str]:
    """Unified word-level tokenizer preserving special tokens and contractions.
    
    Ties '<url>', '<email>', '<phone>', '<routing>', '<date>', '<time>', '<year>', '<num>', '<footer_marker>'
    as atomic tokens, collapses contractions (e.g., 'user's' or 'it's'), and splits other words and punctuation.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Normalize quotes and contractions first
    t = normalize_unicode(text.lower())
    
    # Token pattern: special mask tags OR alphanumeric words with internal apostrophes/hyphens OR single punctuation
    pattern = re.compile(
        r"<[a-z_]+>|[a-z0-9]+(?:'[a-z]+)?|[^\s\w]",
        re.IGNORECASE,
    )
    tokens = pattern.findall(t)
    return tokens


def parse_mbox_message(msg: Message) -> str:
    """Safely parse mbox email extracting plain text body, ignoring attachments and headers."""
    body_parts = []
    html_parts = []

    def extract_from_part(part):
        # Ignore attachments
        disposition = part.get_content_disposition()
        if disposition and disposition.lower() == "attachment":
            return
        
        content_type = part.get_content_type().lower()
        payload = part.get_payload(decode=True)
        if not payload:
            return
        
        # Decode charset
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = payload.decode("latin-1", errors="replace")
            
        if content_type == "text/plain":
            body_parts.append(text)
        elif content_type == "text/html":
            html_parts.append(text)

    if msg.is_multipart():
        for part in msg.walk():
            extract_from_part(part)
    else:
        extract_from_part(msg)

    if body_parts:
        full_text = "\n".join(body_parts)
    elif html_parts:
        full_text = strip_html("\n".join(html_parts))
    else:
        full_text = ""

    return full_text
