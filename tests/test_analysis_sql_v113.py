from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_sql_group_by():
    src = r'''
let d = [{"team": "a", "score": 10}, {"team": "a", "score": 20}, {"team": "b", "score": 5}]
let g = analysis.sql(d, "SELECT team, SUM(score) AS total FROM data GROUP BY team ORDER BY team")
print len(g)
print g[0]["total"]
print g[1]["total"]
'''
    assert run(src) == ["2", "30", "5"]


def test_sql_value_and_window_function():
    src = r'''
let d = [{"c": "x", "v": 3}, {"c": "x", "v": 1}, {"c": "y", "v": 2}]
print analysis.sql_value(d, "SELECT COUNT(*) FROM data")
let r = analysis.sql(d, "SELECT c, v, RANK() OVER (PARTITION BY c ORDER BY v DESC) AS rnk FROM data ORDER BY c, rnk")
print r[0]["rnk"]
print r[1]["rnk"]
'''
    assert run(src) == ["3", "1", "2"]


def test_sql_handles_nested_values():
    src = r'''
let d = [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]
let r = analysis.sql(d, "SELECT id FROM data WHERE tags LIKE '%a%' ORDER BY id")
print len(r)
print r[0]["id"]
'''
    assert run(src) == ["1", "1"]


def test_file_roundtrip(tmp_path):
    csv_path = str(tmp_path / "d.csv").replace("\\", "/")
    json_path = str(tmp_path / "d.json").replace("\\", "/")
    jsonl_path = str(tmp_path / "d.jsonl").replace("\\", "/")
    src = f'''
let d = [{{"a": 1, "b": "x"}}, {{"a": 2, "b": "y"}}]
analysis.write_csv_file("{csv_path}", d)
print len(analysis.read_csv_file("{csv_path}"))
analysis.write_json_file("{json_path}", d)
print len(analysis.read_json_file("{json_path}"))
analysis.write_jsonl_file("{jsonl_path}", d)
print len(analysis.read_jsonl_file("{jsonl_path}"))
'''
    assert run(src) == ["2", "2", "2"]
