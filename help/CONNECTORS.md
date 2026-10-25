# Connector help

Create REST: `connector("rest", "https://api.example.com", headers=bearer(token))`. Create GraphQL: `connector("graphql", endpoint)`. Convert records using `.dataframe(...)`; paginate using `.paginate(...)`. Configure timeout, retries, backoff and max_pages through connector options.

