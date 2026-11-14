"""Reactive React SDK helpers for PeaLang (v1.4.0).

Provides dependency-free code generation for React hooks and components
that integrate with PeaLang's browser WASM runtime.  Generates TypeScript/JSX
source for usePeaScript, usePeaDataFrame, usePeaQuery, and usePeaValidation hooks.
"""

from __future__ import annotations

from typing import Any


REACT_HOOKS = {
    "usePeaScript": "Execute a PeaLang script in the browser WASM runtime and return the result.",
    "usePeaDataFrame": "Load a DataFrame into the browser and provide reactive filtering/sorting.",
    "usePeaQuery": "Run a SQL query against a PeaLang DataFrame in the browser.",
    "usePeaValidation": "Validate form data using PeaLang schema rules.",
}


def generate_react_hooks() -> str:
    """Generate React hook source code for PeaLang integration."""
    return '''import { useState, useEffect, useCallback, useMemo } from "react";

// PeaLang React SDK — generated hooks

export interface PeaRuntime {
  load(url: string): Promise<void>;
  call(name: string, ...args: any[]): any;
}

export function usePeaRuntime(wasmUrl: string): { runtime: PeaRuntime | null; loading: boolean; error: string | null } {
  const [runtime, setRuntime] = useState<PeaRuntime | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const mod = await import("./pealang-wasm.js");
        const instance = await mod.loadPeaWasm(wasmUrl);
        if (mounted) {
          setRuntime({ load: async (u) => {}, call: (n, ...a) => instance.exports[n](...a) });
          setLoading(false);
        }
      } catch (e: any) {
        if (mounted) { setError(e.message); setLoading(false); }
      }
    })();
    return () => { mounted = false; };
  }, [wasmUrl]);

  return { runtime, loading, error };
}

export function usePeaScript(runtime: PeaRuntime | null, script: string): { result: any; loading: boolean; error: string | null } {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async () => {
    if (!runtime) return;
    setLoading(true);
    setError(null);
    try {
      const r = runtime.call("executeScript", script);
      setResult(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [runtime, script]);

  useEffect(() => { run(); }, [run]);

  return { result, loading, error };
}

export function usePeaDataFrame(runtime: PeaRuntime | null, data: any[]): { frame: any; filter: (pred: any) => void; sort: (col: string, asc?: boolean) => void; rows: any[] } {
  const [frame, setFrame] = useState<any>(null);
  const [rows, setRows] = useState<any[]>(data);

  const filter = useCallback((pred: any) => {
    setRows(prev => prev.filter(pred));
  }, []);

  const sort = useCallback((col: string, asc: boolean = true) => {
    setRows(prev => [...prev].sort((a, b) => asc ? (a[col] > b[col] ? 1 : -1) : (a[col] < b[col] ? 1 : -1)));
  }, []);

  useEffect(() => { setRows(data); }, [data]);

  return { frame, filter, sort, rows };
}

export function usePeaQuery(runtime: PeaRuntime | null, data: any[], query: string): { result: any[]; loading: boolean; error: string | null } {
  const [result, setResult] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runtime || !data.length) return;
    setLoading(true);
    try {
      const r = runtime.call("sqlQuery", JSON.stringify(data), query);
      setResult(Array.isArray(r) ? r : []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [runtime, data, query]);

  return { result, loading, error };
}

export function usePeaValidation(schema: any): { validate: (data: any) => { valid: boolean; errors: any[] }; errors: any[] } {
  const [errors, setErrors] = useState<any[]>([]);

  const validate = useCallback((data: any) => {
    const errs: any[] = [];
    for (const field of schema.fields || []) {
      if (field.required && (data[field.name] === undefined || data[field.name] === null)) {
        errs.push({ field: field.name, error: "required" });
      }
    }
    setErrors(errs);
    return { valid: errs.length === 0, errors: errs };
  }, [schema]);

  return { validate, errors };
}
'''


def generate_data_grid_adapter() -> str:
    """Generate zero-copy TypedArray/JSON adapter for frontend table engines."""
    return '''// PeaLang Data Grid Adapter — zero-copy bridge to ag-Grid / TanStack Table

export function peaFrameToGridRows(frame: { columns: string[]; rows: any[] }): any[] {
  return frame.rows.map((row, idx) => ({ ...row, _rowIndex: idx }));
}

export function peaFrameToColumnDefs(frame: { columns: string[] }): any[] {
  return frame.columns.map(col => ({
    field: col,
    headerName: col,
    sortable: true,
    filter: true,
    resizable: true,
  }));
}

export function peaFilterRows(rows: any[], predicate: (row: any) => boolean): any[] {
  return rows.filter(predicate);
}

export function peaSortRows(rows: any[], column: string, ascending: boolean = true): any[] {
  return [...rows].sort((a, b) => {
    const va = a[column], vb = b[column];
    if (va < vb) return ascending ? -1 : 1;
    if (va > vb) return ascending ? 1 : -1;
    return 0;
  });
}
'''


def generate_chart_adapter() -> str:
    """Generate adapter for Vega-Lite / Chart.js integration."""
    return '''// PeaLang Chart Adapter — bridge to Vega-Lite and Chart.js

export function peaToVegaLite(frame: { columns: string[]; rows: any[] }, mark: string = "bar"): any {
  return {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    data: { values: frame.rows },
    mark,
    encoding: {
      x: { field: frame.columns[0], type: "nominal" },
      y: { field: frame.columns[1], type: "quantitative" },
    },
  };
}

export function peaToChartJs(frame: { columns: string[]; rows: any[] }): any {
  const labels = frame.rows.map(r => r[frame.columns[0]]);
  const data = frame.rows.map(r => r[frame.columns[1]]);
  return {
    type: "bar",
    data: { labels, datasets: [{ label: frame.columns[1], data }] },
    options: { responsive: true },
  };
}
'''


def build_react_sdk_namespace() -> dict[str, Any]:
    return {
        "generate_react_hooks": generate_react_hooks,
        "generate_data_grid_adapter": generate_data_grid_adapter,
        "generate_chart_adapter": generate_chart_adapter,
        "REACT_HOOKS": REACT_HOOKS,
    }
