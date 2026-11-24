"""Test cleaner upgrades:
1. Strip inline header remnants (to: ... cc: ... subject:)
2. Strip forwarded blocks (-----Original Message-----, Forwarded by)
3. Strip reply quotes (> ...)
4. Mask anti-shortcut tokens:
   - <date>, <year>, <time>
   - <routing> (/hou/ect, /corp/enron, etc.)
   - <num> (5+ digits)
   - <footer_marker> (unsubscribe / mailing list footers)
"""
import re

TEST_CASES = [
    # Case 1: The user's exact reported bug
    (
        "Meeting notes from today. to: julie meyers / hou / ect <email> cc: subject: We agreed to finalize the contract by Friday.",
        "Expected: 'to: julie meyers / hou / ect <email> cc: subject:' is stripped, leaving body text."
    ),
    # Case 2: Multi-line forwarded header block
    (
        "FYI on this.\n-----Original Message-----\nFrom: Smith, John\nSent: Monday, October 24, 2001 10:15 AM\nTo: Meyers, Julie\nSubject: Budget Review\n\nPlease find the attached Q3 numbers.",
        "Expected: Original message header block stripped."
    ),
    # Case 3: Reply quotes
    (
        "I agree with your suggestion.\n> Can we move the meeting to 3 PM?\n> Let me know if that works.\nYes, 3 PM works perfectly.",
        "Expected: Quoted lines stripped."
    ),
    # Case 4: Era and routing tokens
    (
        "Sent from Houston office. Contact me at /hou/ect or call 123456789. Meeting set for 2002 at 09:30 AM on October 15, 2002.",
        "Expected: <routing>, <num>, <year>, <time>, <date> masked."
    ),
    # Case 5: Mailing list footer
    (
        "Here is the weekly Linux kernel digest.\nTo unsubscribe from this mailing list, visit http://example.com/optout or send mail to majordomo@vger.kernel.org",
        "Expected: Footer and URL masked."
    )
]

def build_enhanced_cleaner():
    # Patterns
    REPLY_QUOTE_REGEX = re.compile(r"^\s*[>|].*$", re.MULTILINE)
    
    FORWARD_BLOCK_REGEX = re.compile(
        r"(?:-----Original Message-----|-+\s*Forwarded by.*?-+|Begin forwarded message:).*?"
        r"(?=(?:Dear|\n\n|\r\n\r\n|$))",
        re.DOTALL | re.IGNORECASE
    )
    
    # Inline header leftovers pattern:
    # Matches patterns like 'to: ... cc: ... subject:' or standalone 'to: ... <email>'
    INLINE_HEADER_REGEX = re.compile(
        r"(?i)\b(?:from|to|cc|bcc|sent|subject)\s*:[ \t]*[^:\n]+?(?=(?:\b(?:from|to|cc|bcc|sent|subject)\s*:|\n|$))"
    )
    
    # Routing markers
    ROUTING_REGEX = re.compile(
        r"(?:/(?:hou|corp|ect|enron)(?:/[a-z0-9_-]+)*|"
        r"\b(?:hou/ect|ect/hou|corp/enron|enron_development)\b|"
        r"@(?:ect|enron)\b)",
        re.IGNORECASE
    )
    
    # Date patterns
    DATE_REGEX = re.compile(
        r"\b(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+)?"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s*(?:\d{4})?\b|"
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        re.IGNORECASE
    )
    
    # Time patterns
    TIME_REGEX = re.compile(
        r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?\b|"
        r"\b\d{1,2}\s*(?:AM|PM|am|pm)\b"
    )
    
    # Year patterns (1990 - 2030)
    YEAR_REGEX = re.compile(r"\b(?:199\d|20[0-2]\d)\b")
    
    # Long digit strings (5+ digits)
    LONG_NUM_REGEX = re.compile(r"\b\d{5,}\b")
    
    # Mailing list footers
    FOOTER_REGEX = re.compile(
        r"(?i)\b(?:to unsubscribe from this (?:list|newsletter|mailing list)|"
        r"click here to unsubscribe|unsubscribe instructions|"
        r"mailing-list:|list-unsubscribe:|ezmlm|majordomo|listserv)\b[^\n]*"
    )

    return {
        "reply_quote": REPLY_QUOTE_REGEX,
        "forward_block": FORWARD_BLOCK_REGEX,
        "inline_header": INLINE_HEADER_REGEX,
        "routing": ROUTING_REGEX,
        "date": DATE_REGEX,
        "time": TIME_REGEX,
        "year": YEAR_REGEX,
        "long_num": LONG_NUM_REGEX,
        "footer": FOOTER_REGEX,
    }

def clean_text_demo(text, patterns):
    t = patterns["reply_quote"].sub("", text)
    t = patterns["forward_block"].sub("", t)
    t = patterns["footer"].sub("<footer_marker>", t)
    t = patterns["inline_header"].sub("", t)
    t = patterns["routing"].sub("<routing>", t)
    t = patterns["date"].sub("<date>", t)
    t = patterns["time"].sub("<time>", t)
    t = patterns["year"].sub("<year>", t)
    t = patterns["long_num"].sub("<num>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

if __name__ == "__main__":
    patterns = build_enhanced_cleaner()
    for i, (text, desc) in enumerate(TEST_CASES):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Description: {desc}")
        print(f"Original:\n{text}")
        cleaned = clean_text_demo(text, patterns)
        print(f"Cleaned:\n{cleaned}")
