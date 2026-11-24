"""Unit tests for text cleaning and normalization pipeline."""
import pytest
import email
from email.message import EmailMessage
from src.text.cleaner import (
    clean_email_text,
    strip_headers,
    strip_html,
    mask_entities,
    normalize_whitespace,
    normalize_unicode,
    validate_email_row,
    is_commercial_spam,
    unified_tokenize,
    parse_mbox_message,
)


def test_strip_headers():
    raw_email = (
        "From: spoofed@phish.com\n"
        "To: victim@company.com\n"
        "Subject: Urgent security alert\n"
        "Date: Mon, 23 Oct 2026 10:00:00 +0000\n"
        "X-Mailer: MaliciousMailer 2.0\n"
        "\n"
        "Please verify your credentials immediately to avoid suspension."
    )
    cleaned = strip_headers(raw_email)
    assert "From:" not in cleaned
    assert "To:" not in cleaned
    assert "spoofed@phish.com" not in cleaned
    assert "Please verify your credentials immediately" in cleaned


def test_strip_spaced_headers():
    raw_spaced = (
        "to : john.doe@company.com\n"
        "from : hr-desk@company.com\n"
        "cc : manager@company.com\n"
        "sent : Friday, October 24, 2026 10:00 AM\n"
        "subject : Benefits enrollment deadline\n"
        "\n"
        "Please complete your annual benefits enrollment before the Friday cutoff."
    )
    cleaned = clean_email_text(raw_spaced)
    assert "to :" not in cleaned.lower()
    assert "from :" not in cleaned.lower()
    assert "subject :" not in cleaned.lower()
    assert "enrollment before the Friday cutoff" in cleaned


def test_strip_forwarded_headers():
    raw_forwarded = (
        "Hi John, take a look.\n"
        "- - - - Original Message - - - -\n"
        "From : CEO <ceo@company.com>\n"
        "Sent : Monday, October 23, 2026 9:00 AM\n"
        "To : Finance <finance@company.com>\n"
        "Subject : Wire transfer\n\n"
        "Send the funds to our new vendor account."
    )
    cleaned = clean_email_text(raw_forwarded)
    assert "Sent :" not in cleaned
    assert "Send the funds to our new vendor account." in cleaned


def test_contractions_and_quote_normalization():
    raw = "It ' s user ' s responsibility, don ' t forget “our” promise – today."
    tokens = unified_tokenize(raw)
    assert "it's" in tokens
    assert "user's" in tokens
    assert "don't" in tokens
    # ensure "it ' s" and "it's" yield identical tokens
    tokens_clean = unified_tokenize('It\'s user\'s responsibility, don\'t forget "our" promise - today.')
    assert tokens == tokens_clean


def test_strip_html():
    raw_html = (
        "<html><head><style>body { font-size: 14px; }</style>"
        "<script>alert('xss');</script></head>"
        "<body><p>Your account &amp; balance are <b>suspended</b>.</p></body></html>"
    )
    cleaned = normalize_whitespace(strip_html(raw_html))
    assert "<html" not in cleaned
    assert "<style" not in cleaned
    assert "<script" not in cleaned
    assert "alert('xss')" not in cleaned
    assert "Your account & balance are suspended." in cleaned


def test_mask_entities():
    sample_text = (
        "Visit our secure website at https://secure.paypal.auth-update.com/login "
        "or email support at security-team@paypal-notice.net or call +1-800-555-0199."
    )
    masked = mask_entities(sample_text)
    assert "https://" not in masked
    assert "paypal.auth-update.com" not in masked
    assert "<url>" in masked
    assert "security-team@paypal-notice.net" not in masked
    assert "<email>" in masked
    assert "+1-800-555-0199" not in masked
    assert "<phone>" in masked


def test_commercial_spam_detection():
    spam_sample = "Super discount on generic viagra and cialis without prescription."
    assert is_commercial_spam(spam_sample) is True

    legit_phish = "Urgent: unauthorized sign-in detected on your bank account. Verify at <url>."
    assert is_commercial_spam(legit_phish) is False


def test_clean_email_pipeline():
    raw = (
        "From: admin@bank.com\n"
        "Subject: Action Required\n\n"
        "<div>Dear customer, please click <a href='http://evil.com/reset'>here</a> "
        "or contact help@bank.com to restore your online access. "
        "This is a formal security reminder regarding your active banking profile.</div>"
    )
    cleaned = clean_email_text(raw)
    assert "<url>" in cleaned
    assert "<email>" in cleaned
    assert "http://evil.com" not in cleaned
    assert "From:" not in cleaned
    assert "<div>" not in cleaned


def test_validate_email_row():
    # Empty / placeholder
    assert validate_email_row("", "phishing")[0] is False
    assert validate_email_row("empty", "phishing")[0] is False

    # Too short (< 15 words)
    assert validate_email_row("Hello please help me with this.", "phishing")[0] is False

    # Valid long email
    valid_text = (
        "Dear customer, your account was temporarily flagged due to anomalous login activity. "
        "Please review the attached advisory and confirm your identity at the earliest opportunity. "
        "Failure to do so will result in administrative restrictions on your banking profile."
    )
    assert validate_email_row(valid_text, "phishing")[0] is True


def test_strip_reply_quotes():
    raw_reply = (
        "Sounds like a good proposal.\n"
        "> Did you review the numbers from yesterday?\n"
        "> Let me know if you need any adjustments.\n"
        "Yes, the budget allocation is completely approved."
    )
    cleaned = clean_email_text(raw_reply)
    assert "Did you review the numbers from yesterday?" not in cleaned
    assert "Sounds like a good proposal." in cleaned
    assert "Yes, the budget allocation is completely approved." in cleaned


def test_safe_mbox_parser():
    msg = EmailMessage()
    msg["Subject"] = "Test Mbox"
    msg["From"] = "test@example.com"
    msg.set_content("This is the main plain text body for mbox testing.")
    body = parse_mbox_message(msg)
    assert "This is the main plain text body for mbox testing." in body
    assert "Subject" not in body


def test_strip_rfc822_headers_and_mailing_list():
    raw_email = (
        "From exmh-workers-admin@redhat.com Tue Aug 27 10:04:58 2002\n"
        "Return-Path: <exmh-workers-admin@spamassassin.taint.org>\n"
        "Delivered-To: yyyy@localhost.netnoteinc.com\n"
        "Received: from localhost (localhost [127.0.0.1]) by phobos with ESMTP id ABC123\n"
        "Sender: exmh-workers-admin@redhat.com\n"
        "Errors-To: exmh-workers-admin@redhat.com\n"
        "Precedence: bulk\n"
        "List-Unsubscribe: <http://listman.redhat.com/mailman/listinfo/exmh-workers>\n"
        "List-Help: <mailto:exmh-workers-request@redhat.com?subject=help>\n"
        "List-Subscribe: <http://listman.redhat.com/mailman/listinfo/exmh-workers>\n"
        "Priority: normal\n"
        "Content-Description: Mail message body\n"
        "X-Mailman-Version: 2.0.11\n"
        "Message-ID: <1029945287.4797.TMDA@deepeddy.vircio.com>\n"
        "\n"
        "Here is the authentic message body regarding the Python patch.\n"
        "Please review the code changes and verify tests."
    )
    from src.text.cleaner import has_forbidden_headers_in_prefix
    cleaned = clean_email_text(raw_email)
    assert not has_forbidden_headers_in_prefix(cleaned, 300)
    assert "sender:" not in cleaned.lower()
    assert "errors-to:" not in cleaned.lower()
    assert "precedence:" not in cleaned.lower()
    assert "list-unsubscribe:" not in cleaned.lower()
    assert "list-help:" not in cleaned.lower()
    assert "list-subscribe:" not in cleaned.lower()
    assert "priority:" not in cleaned.lower()
    assert "content-description:" not in cleaned.lower()
    assert "x-mailman-version:" not in cleaned.lower()
    assert "message-id:" not in cleaned.lower()
    assert "Here is the authentic message body regarding the Python patch." in cleaned


def test_forbidden_headers_prefix_check():
    from src.text.cleaner import has_forbidden_headers_in_prefix
    bad_sample = "Sender: admin@server.com\nPrecedence: bulk\nHello world"
    assert has_forbidden_headers_in_prefix(bad_sample, 300) is True

    clean_sample = "Hello world, here is an operational update regarding our upcoming release."
    assert has_forbidden_headers_in_prefix(clean_sample, 300) is False

