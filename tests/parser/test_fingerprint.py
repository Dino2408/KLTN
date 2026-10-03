import sys
sys.path.insert(0, "parser-engine")
from app.fingerprint import fingerprint, templateize

def test_same_template_same_fingerprint():
    a = "FW peer=10.0.0.1 target=10.0.0.5 attempts=17"
    b = "FW peer=10.0.0.2 target=10.0.0.5 attempts=23"
    assert fingerprint(a) == fingerprint(b)

def test_template_replaces_ip_and_numbers():
    assert "<IP>" in templateize("x 10.0.0.1 42")
