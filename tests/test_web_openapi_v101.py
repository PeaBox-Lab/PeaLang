from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_openapi_generation():
    src = """
let app = web.app()
function home(req) { return web.json({"ok": true}) }
function get_user(req) { return web.json({"id": req["params"]["id"]}) }
app.get("/", home)
app.get("/users/:id", get_user)
app.post("/users", home)
let spec = web.openapi(app, "Demo", "1.0.0")
print spec["openapi"]
print spec["info"]["title"]
print spec["paths"]["/"]["get"]["summary"]
let paths = spec["paths"]
for k in paths {
  if k != "/" and k != "/users" {
    print paths[k]["get"]["parameters"][0]["name"]
  }
}
"""
    out = run(src)
    assert out == ["3.0.3", "Demo", "GET /", "id"]
