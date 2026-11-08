from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_group_cors_patch():
    src = '''
let app = web.app()
app.enable_cors("*")
let api = app.group("/api")
api.get("/ping", function(req){ return web.json({"ok": true}) })
app.patch("/items/:id", function(req){ return web.json({"id": req["params"]["id"]}) })
let r = app.dispatch("GET", "/api/ping")
print r["status"]
print r["headers"]["Access-Control-Allow-Origin"]
let p = app.dispatch("PATCH", "/items/7")
print p["body"]
let o = app.dispatch("OPTIONS", "/anything")
print o["status"]
'''
    out = run(src)
    assert out[0] == "200"
    assert out[1] == "*"
    assert '"id": "7"' in out[2]
    assert out[3] == "204"
