"""Test borderline marketing detection and quarantine logic."""
import pytest
from src.text.cleaner import classify_content_status, clean_email_text

def test_blatant_commercial_spam():
    text = (
        "Get cheap online pharmacy prescriptions without doctor visit. "
        "Generic viagra and cialis on sale with overnight discreet shipping directly to your door."
    )
    status, reason = classify_content_status(text)
    assert status == "commercial_spam_excluded"
    assert "blatant marketing cue" in reason

def test_borderline_marketing_quarantined():
    text = (
        "Dear member, refinance your home today with our guaranteed lowest rate. "
        "This special promotion for our readers is available for a limited time. "
        "Click here to opt out from our weekly mailing list."
    )
    status, reason = classify_content_status(text)
    assert status == "borderline_quarantined"
    assert "ambiguous promotional cue" in reason

def test_legitimate_phishing_overrides_marketing():
    text = (
        "Urgent: Security alert on your online banking account. "
        "Unauthorized login detected from IP <url>. Confirm your account immediately to prevent permanent suspension."
    )
    status, reason = classify_content_status(text)
    assert status == "valid"

def test_clean_corporate_email():
    text = (
        "Please review the attached quarterly earnings spreadsheet before our morning risk committee conference call. "
        "We need sign-off on the transmission contracts by Thursday."
    )
    status, reason = classify_content_status(text)
    assert status == "valid"
