
export async function loadPeaWasm(url, imports = {}) {
  const bytes = await (await fetch(url)).arrayBuffer();
  return WebAssembly.instantiate(bytes, imports);
}
