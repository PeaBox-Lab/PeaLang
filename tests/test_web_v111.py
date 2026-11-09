from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v111():
    src = r'''
let v = web.validation_error([{"field": "x", "msg": "bad"}], "Nope")
print v["status"]
print web.content_type("application/json")["Content-Type"]
let h = web.merge_headers({"A": "1"}, {"B": "2"})
print h["B"]
let req = {"query": {"n": "7", "ok": "true"}, "headers": {"x-api-key": "k"}, "method": "POST"}
print web.query_int(req, "n", 0)
print web.query_bool(req, "ok", false)
let ak = web.api_key_auth("x-api-key")
print ak(req)
print web.method_is(req, ["GET", "POST"])
'''
    out = run(src)
    assert out[0] == "422"
    assert "application/json" in out[1]
    assert out[2:] == ["2", "7", "true", "k", "true"]
