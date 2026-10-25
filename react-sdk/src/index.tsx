

import React,{createContext,useCallback,useContext,useMemo,useState} from "react";
import {PeaLangClient,PeaValue} from "@pealang/client";
const Context=createContext<PeaLangClient|null>(null);
export function PeaLangProvider({baseUrl,children}:{baseUrl:string;children:React.ReactNode}){const client=useMemo(()=>new PeaLangClient(baseUrl),[baseUrl]);return <Context.Provider value={client}>{children}</Context.Provider>}
export function usePeaLang(){const value=useContext(Context);if(!value)throw new Error("usePeaLang requires PeaLangProvider");return value}
export function usePeaFunction<T=PeaValue>(module:string,fn:string){const client=usePeaLang();const [loading,setLoading]=useState(false);const [error,setError]=useState<Error|null>(null);const invoke=useCallback(async(...args:PeaValue[])=>{setLoading(true);setError(null);try{const r=await client.invoke<T>({module,function:fn,args});if(!r.ok)throw new Error(r.error?.message ?? "PeaLang invocation failed");return r.result as T}catch(e){setError(e as Error);throw e}finally{setLoading(false)}},[client,module,fn]);return {invoke,loading,error}}
export type PeaUiNode={type:"text"|"button"|"stack";text?:string;action?:string;children?:PeaUiNode[]};
export function PeaUi({node,onAction}:{node:PeaUiNode;onAction?:(action:string)=>void}){if(node.type==="text")return <span>{node.text}</span>;if(node.type==="button")return <button onClick={()=>node.action&&onAction?.(node.action)}>{node.text}</button>;return <div>{node.children?.map((x,i)=><PeaUi key={i} node={x} onAction={onAction}/>)}</div>}


