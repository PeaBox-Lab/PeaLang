from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_v109_builtins():
    src = r'''
print has_path({"a": {"b": 1}}, "a.b")
print has_path({"a": 1}, "a.b")
print set_path({"a": {"b": 1}}, "a.b", 9)["a"]["b"]
print map_values({"a": 1, "b": 2}, function(v, k){ return v * 2 })["b"]
print map_keys({"a": 1}, function(k, v){ return upper(k) })["A"]
print pick_by({"a": 1, "b": 0}, function(v, k){ return v > 0 })["a"]
print omit_by({"a": 1, "b": 0}, function(v, k){ return v == 0 })["a"]
print len(shuffle([1, 2, 3]))
print product([2, 3, 4])
print median([1, 3, 2, 4])
print parse_int(" 42 ")
print parse_int("x", -1)
print parse_float("3.5")
print strip_prefix("foobar", "foo")
print strip_suffix("foobar", "bar")
print len(sha256("abc")) == 64
print url_decode(url_encode("a b&c"))
print html_escape("<a>")
print title_case("hello world")
print center("x", 3, "-")
'''
    out = run(src)
    assert out == [
        "true", "false", "9", "4", "1", "1", "1", "3", "24", "2.5",
        "42", "-1", "3.5", "bar", "foo", "true", "a b&c", "&lt;a&gt;",
        "Hello World", "-x-",
    ]
