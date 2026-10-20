# Automation Recipes
- Read JSON: `let config = json.read("config.json")`
- Read CSV: `let rows = csv.read("employees.csv")`
- Create paths: `let target = path.join("output", "report.json")`
- Require a secret: `let key = env.require("API_KEY")`
- Call an API: `let response = http.get(url, {"Authorization": "Bearer " + key}, 10)`
- Parse the response: `let data = http.json(response)`
- Run a trusted tool: `process.run("python", ["script.py"], 30)` with `--allow-process`.
