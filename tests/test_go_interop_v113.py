from pealang import execute
from pealang.interop import generate_go_client, go_available, go_run, go_version


def test_generate_go_client_contains_expected_symbols():
    source = generate_go_client("http://127.0.0.1:8787")
    assert "package pealangclient" in source
    assert 'const BaseURL = "http://127.0.0.1:8787"' in source
    assert "func (c *Client) Invoke" in source
    assert "func (c *Client) Health" in source


def test_generate_go_client_package_is_sanitized():
    source = generate_go_client("http://x", package_name="my-client!")
    assert "package my_client_" in source


def test_go_available_is_bool():
    assert isinstance(go_available(), bool)


def test_go_version_matches_availability():
    version = go_version()
    if go_available():
        assert version is not None and version.startswith("go version")
    else:
        assert version is None


def test_go_run_reports_missing_toolchain():
    result = go_run("package main\n\nfunc main() {}\n")
    assert "available" in result
    if not go_available():
        assert result["available"] is False
        assert result["ok"] is False
    else:
        assert result["available"] is True


def test_generate_go_from_pea():
    src = r'''
let g = interop.generate_go("http://127.0.0.1:8787")
print contains(g, "package pealangclient")
print contains(g, "func (c *Client) Invoke")
print type(interop.go_available())
'''
    out = []
    execute(src, output=out.append, source_name="go.pea")
    assert out == ["true", "true", "bool"]
