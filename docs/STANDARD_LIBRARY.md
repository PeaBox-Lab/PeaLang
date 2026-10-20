# Automation Standard Library v0.3.0

## file
`file.read(path)`, `write(path, content)`, `append`, `copy`, `move`, `delete`, `exists`, `list`, and `mkdir`. Text is UTF-8.

## path
`path.join(...)`, `name`, `stem`, `extension`, `parent`, and `absolute`.

## json
`json.parse(text)`, `stringify(value, indent?)` where indent `0` creates compact JSON, `read(path)`, and `write(path, value, indent?)`.

## csv
`csv.read(path)` returns a list of dictionaries. `csv.write(path, rows, columns?)` writes a header. Values read from CSV are strings by design.

## env
`env.get(name, default?)`, `env.has(name)`, and `env.require(name)`. Use environment variables for credentials. Never commit secrets.

## datetime
`datetime.now()` returns UTC ISO 8601 text. `today`, `parse`, `format`, `add_days`, and `timestamp` are also available.

## regex
`regex.match(pattern, text)` searches for a match. `find`, `replace`, and `split` use Python-compatible regular expressions in this release.

## http
`http.get(url, headers?, timeout?)`, `post(url, body?, headers?, timeout?)`, `request(method, url, body?, headers?, timeout?)`, `json(response)`, and `urlencode(values)`. Responses contain `status`, `ok`, `headers`, `text`, and final `url`. HTTP error status responses are returned rather than thrown; connection and timeout failures become `PeaError` values through the interpreter.

## process
`process.run(command, args?, timeout?, cwd?)` uses an argument list and never invokes a shell. It returns `exit_code`, `stdout`, `stderr`, and `ok`. It is disabled unless explicitly enabled.
