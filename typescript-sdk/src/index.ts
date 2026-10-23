export type PeaValue = null | boolean | number | string | PeaValue[] | {[key:string]:PeaValue};
export interface RuntimeResponse<T=PeaValue>{ok:boolean;request_id:string;result?:T;error?:{code:string;message:string;request_id:string};elapsed_ms:number}
export interface LoadRequest{name:string;source:string;source_name?:string}
export interface InvokeRequest{module:string;function:string;args?:PeaValue[]}
export class PeaLangClient {
  constructor(public readonly baseUrl:string){this.baseUrl=baseUrl.replace(/\/$/,"")}
  private async request<T>(path:string,init?:RequestInit):Promise<T>{const r=await fetch(this.baseUrl+path,init);const body=await r.json();if(!r.ok)throw new Error(body?.error?.message ?? `PeaLang HTTP ${r.status}`);return body as T}
  health(){return this.request<Record<string,PeaValue>>("/health")}
  ready(){return this.request<Record<string,PeaValue>>("/ready")}
  compile(source:string,source_name="<typescript>"){return this.request<RuntimeResponse>("/v1/compile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({source,source_name})})}
  load(req:LoadRequest){return this.request<RuntimeResponse>("/v1/modules/load",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(req)})}
  invoke<T=PeaValue>(req:InvokeRequest){return this.request<RuntimeResponse<T>>("/v1/invoke",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(req)})}
}

