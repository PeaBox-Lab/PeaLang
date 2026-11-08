from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="pattern.pea")
    return out


def test_match_basic():
    src = """
let x = 2
match x {
  1 => print "one"
  2, 3 => print "two or three"
  _ => print "other"
}
"""
    out = run(src)
    assert out == ["two or three"]


def test_destructuring():
    src = """
let point = [10, 20]
let [a, b] = point
print a
print b
let user = {"name": "Ada", "score": 91}
let {name, score} = user
print name
print score
"""
    out = run(src)
    assert out == ["10", "20", "Ada", "91"]

