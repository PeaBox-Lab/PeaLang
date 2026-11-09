from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v106():
    src = r'''
let ok = web.ok({"x":1})
print ok["status"]
print ok["body"]
let p = web.problem("Bad", 422, "detail")
print p["status"]
print p["headers"]["Content-Type"]
let pg = web.pagination(2, 10, 35)
print pg["pages"]
print pg["has_next"]
'''
    out = run(src)
    assert out[0] == "200"
    assert '"ok": true' in out[1]
    assert out[2] == "422"
    assert "problem+json" in out[3]
    assert out[4] == "4"
    assert out[5] == "true"
