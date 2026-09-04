import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.services.sanitizer import sanitize_html

def test_sanitizer_strips_script_tags():
    raw_html = "<div><h1>Empowered Teams</h1><script>alert('XSS')</script><p>Content text</p></div>"
    clean_html = sanitize_html(raw_html)
    assert "<script>" not in clean_html
    assert "alert" not in clean_html
    assert "<h1>Empowered Teams</h1>" in clean_html

def test_sanitizer_strips_onerror_event_handlers():
    raw_html = "<img src='x' onerror='alert(document.cookie)' alt='diagram'/>"
    clean_html = sanitize_html(raw_html)
    assert "onerror" not in clean_html
    assert "alert" not in clean_html
    assert "<img" in clean_html

def test_sanitizer_strips_javascript_urls():
    raw_html = "<a href='javascript:alert(1)'>Click here</a>"
    clean_html = sanitize_html(raw_html)
    assert "javascript:" not in clean_html
    assert "alert" not in clean_html

def test_sanitizer_preserves_safe_elements():
    raw_html = "<div class='card'><h2>SPADE Framework</h2><ul><li>Setting</li><li>People</li></ul></div>"
    clean_html = sanitize_html(raw_html)
    assert "<h2>SPADE Framework</h2>" in clean_html
    assert "<li>Setting</li>" in clean_html
