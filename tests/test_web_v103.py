from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_validate_and_helpers():
    src = r'''
let v = web.validate({"name":"Ada","age":30}, {"name":{"type":"string","required":true},"age":{"type":"number"}})
print v["ok"]
let bad = web.validate({}, {"name":{"type":"string","required":true}})
print bad["ok"]
let app = web.app()
app.options("/x", function(req){ return web.text("ok") })
let r = app.dispatch("OPTIONS", "/x")
print r["status"]
let sse = web.sse({"msg":"hi"})
print sse["headers"]["Content-Type"]
'''
    out = run(src)
    assert out == ["true", "false", "200", "text/event-stream; charset=utf-8"]
