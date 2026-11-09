from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_predicates_and_helpers_v106():
    src = r'''
print is_null(null)
print is_list([1])
print is_dict({"a":1})
print is_string("x")
print is_number(1.2)
print is_bool(true)
print pad_start("7", 3, "0")
print pad_end("a", 3, ".")
print len(lines("a\nb"))
print floor(3.9)
print ceil(3.1)
print pow(2,5)
'''
    out = run(src)
    assert out == ["true","true","true","true","true","true","007","a..","2","3","4","32"]
