from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v105():
    src = r'''
print web.no_content()["status"]
print web.created({"id":1})["status"]
print web.accepted({"q":1})["status"]
print web.cache_control(60, true)["Cache-Control"]
let ba = web.basic_auth("u","p")
print ba["Authorization"]
'''
    out = run(src)
    assert out[0] == "204"
    assert out[1] == "201"
    assert out[2] == "202"
    assert out[3] == "public, max-age=60"
    assert out[4].startswith("Basic ")
