export type PeaValue = null | boolean | number | string | PeaValue[] | {
    [key: string]: PeaValue;
};
export interface RuntimeResponse<T = PeaValue> {
    ok: boolean;
    request_id: string;
    result?: T;
    error?: {
        code: string;
        message: string;
        request_id: string;
    };
    elapsed_ms: number;
}
export interface LoadRequest {
    name: string;
    source: string;
    source_name?: string;
}
export interface InvokeRequest {
    module: string;
    function: string;
    args?: PeaValue[];
}
export declare class PeaLangClient {
    readonly baseUrl: string;
    constructor(baseUrl: string);
    private request;
    health(): Promise<Record<string, PeaValue>>;
    ready(): Promise<Record<string, PeaValue>>;
    compile(source: string, source_name?: string): Promise<RuntimeResponse<PeaValue>>;
    load(req: LoadRequest): Promise<RuntimeResponse<PeaValue>>;
    invoke<T = PeaValue>(req: InvokeRequest): Promise<RuntimeResponse<T>>;
}
