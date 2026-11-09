from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="web.pea")
    return out


def test_web_status_helpers_v108():
    src = r'''
print web.unauthorized()["status"]
print web.forbidden()["status"]
print web.conflict()["status"]
print web.gone()["status"]
let t = web.too_many_requests("slow", 30)
print t["status"]
print t["headers"]["Retry-After"]
let u = web.unprocessable("bad", ["x"])
print u["status"]
print web.status(418, {"teapot": true})["status"]
'''
    out = run(src)
    assert out == ["401", "403", "409", "410", "429", "30", "422", "418"]
