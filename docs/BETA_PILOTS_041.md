
# PeaLang 0.41 Beta/Pilot Gate

Candidate pilots are included for Python/FastAPI HR rules and Java-sidecar service extensions. They are runnable reference pilots, not fabricated production deployments. The readiness model requires two pilots to be explicitly marked `validated` before the pilot gate passes.

Stable host integration targets are Python embedding, Java runtime sidecar and TypeScript runtime client. Performance policy defaults to <=10% median regression, <=100 ms startup and <=25 ms p95 invocation as release thresholds until real pilot baselines replace them.

