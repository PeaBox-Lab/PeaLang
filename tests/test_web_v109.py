from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v109():
    src = r'''
print web.bad_request()["status"]
print web.server_error()["status"]
print web.not_modified()["status"]
print web.moved_permanently("/a")["status"]
print web.see_other("/b")["status"]
print web.temporary_redirect("/c")["status"]
print web.permanent_redirect("/d")["status"]
let sh = web.security_headers()
print sh["X-Frame-Options"]
let q = web.parse_query("a=1&b=x&b=y")
print q["a"]
print web.build_query({"a": 1, "b": "x"})
'''
    out = run(src)
    assert out == ["400", "500", "304", "301", "303", "307", "308", "DENY", "1", "a=1&b=x"]
