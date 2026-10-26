export class PeaLangClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.baseUrl = baseUrl.replace(/\/$/, "");
    }
    async request(path, init) { const r = await fetch(this.baseUrl + path, init); const body = await r.json(); if (!r.ok)
        throw new Error(body?.error?.message ?? `PeaLang HTTP ${r.status}`); return body; }
    health() { return this.request("/health"); }
    ready() { return this.request("/ready"); }
    compile(source, source_name = "<typescript>") { return this.request("/v1/compile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source, source_name }) }); }
    load(req) { return this.request("/v1/modules/load", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) }); }
    invoke(req) { return this.request("/v1/invoke", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) }); }
}
