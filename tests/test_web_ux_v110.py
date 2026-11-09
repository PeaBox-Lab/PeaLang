from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v110():
    src = r'''
let h = web.health({"version": "x"})
print h["status"]
let e = web.envelope([1, 2], {"n": 2})
print e["status"]
let l = web.with_links({"id": 1}, {"self": "/x"})
print l["_links"]["self"]
let n = web.negotiate({"headers": {"accept": "application/json"}}, {"json": {"ok": true}})
print n["status"]
'''
    out = run(src)
    assert out == ["200", "200", "/x", "200"]


def test_ux_v110():
    src = r'''
print len(ux.quickstart()) > 10
let cmds = ux.commands()
print len(cmds) > 10
'''
    out = run(src)
    assert out == ["true", "true"]
