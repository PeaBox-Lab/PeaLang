from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_extras():
    src = r'''
let e = web.etag({"a":1})
print len(e["headers"]["ETag"]) > 0
let err = web.json_error("bad", 422, "E1")
print err["status"]
print err["body"]
'''
    out = run(src)
    assert out[0] == "true"
    assert out[1] == "422"
    assert '"code": "E1"' in out[2]
