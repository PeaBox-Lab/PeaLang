from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="pattern.pea")
    return out


def test_match_expression():
    src = """
let x = 2
let result = match x {
  1 => "one"
  2 => "two"
  _ => "other"
}
print result
"""
    out = run(src)
    assert out == ["two"]


def test_for_destructuring():
    src = """
let pairs = [[1,2],[3,4]]
for [a,b] in pairs { print a + b }
let users = [{"name":"Ada"},{"name":"Linus"}]
for {name} in users { print name }
"""
    out = run(src)
    assert out == ["3", "7", "Ada", "Linus"]
