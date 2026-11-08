from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_dispatch_json():
    src = """
let app = web.app()
function home(req) { return web.json({"message": "hi", "path": req["path"]}) }
app.get("/", home)
let r = app.dispatch("GET", "/")
print r["status"]
print r["body"]
"""
    out = run(src)
    assert out[0] == "200"
    assert '"message": "hi"' in out[1]


def test_web_path_params_and_404():
    src = """
let app = web.app()
function user(req) { return web.json({"id": req["params"]["id"]}) }
app.get("/users/:id", user)
let r = app.dispatch("GET", "/users/42")
print r["status"]
print r["body"]
let missing = app.dispatch("GET", "/nope")
print missing["status"]
"""
    out = run(src)
    assert out[0] == "200"
    assert '"id": "42"' in out[1]
    assert out[2] == "404"


def test_web_static_and_post():
    import tempfile, os
    d = tempfile.mkdtemp()
    path = os.path.join(d, "hello.txt")
    with open(path, "w") as f:
        f.write("hello static")
    src = f'''
let app = web.app()
app.add_static("/static/", "{d.replace(chr(92), "/")}")
let r = app.dispatch("GET", "/static/hello.txt")
print r["status"]
print r["body"]
'''
    out = run(src)
    assert out[0] == "200"
    assert out[1] == "hello static"


def test_std_web_available():
    src = """
let app = std.web.app()
app.get("/", function(req) { return std.web.text("ok") })
let r = app.dispatch("GET", "/")
print r["status"]
print r["body"]
"""
    out = run(src)
    assert out == ["200", "ok"]

