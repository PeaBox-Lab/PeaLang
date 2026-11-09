from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_v112():
    src = r'''
let rj = {"headers": {"accept": "application/json, text/plain"}}
let rh = {"headers": {"accept": "text/html"}}
print web.accepts_json(rj)
print web.accepts_html(rj)
print web.accepts_html(rh)
print web.no_cache()["Pragma"]
print web.vary("Accept", "Origin")["Vary"]
print web.link_header({"self": "/a"})["Link"]
'''
    out = run(src)
    assert out == ["true", "false", "true", "no-cache", "Accept, Origin", '</a>; rel="self"']
