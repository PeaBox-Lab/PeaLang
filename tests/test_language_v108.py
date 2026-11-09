from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_collection_and_string_builtins_v108():
    src = r'''
print is_empty([])
print is_empty("")
print is_empty(null)
print is_empty([1])
print compact([0, 1, null, "", false, 2])
print defaults({"a": 1}, {"a": 9, "b": 2})["b"]
let inv = invert({"x": "y"})
print inv["y"]
print to_pairs({"a": 1})[0][1]
print from_pairs([["a", 1], ["b", 2]])["b"]
print sum_by([{"v": 2}, {"v": 3}], "v")
print avg([2, 4, 6])
print capitalize("hello")
print snake_case("helloWorld")
print kebab_case("Hello World")
print slugify("Hello, World!")
print truncate("abcdef", 4)
print union([1, 2], [2, 3])
print intersection([1, 2, 3], [2, 3, 4])
print difference([1, 2, 3], [2])
'''
    out = run(src)
    assert out == [
        "true", "true", "true", "false",
        "[1, 2]",
        "2",
        "x",
        "1",
        "2",
        "5",
        "4",
        "Hello",
        "hello_world",
        "hello-world",
        "hello-world",
        "a...",
        "[1, 2, 3]",
        "[2, 3]",
        "[1, 3]",
    ]
