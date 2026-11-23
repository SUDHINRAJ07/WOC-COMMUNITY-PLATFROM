export const localBackend=()=>typeof window!=='undefined'&&['localhost','127.0.0.1'].includes(window.location.hostname);
const apiBase=()=>process.env.NEXT_PUBLIC_API_URL||`http://${typeof window==='undefined'?'localhost':window.location.hostname}:8317/api`;
let csrf='';
export async function api(path:string,method='GET',data?:unknown){
 if(method!=='GET'&&!csrf){const r=await fetch(apiBase()+'/csrf/',{credentials:'include'});csrf=(await r.json()).csrfToken;}
 const r=await fetch(apiBase()+path,{method,credentials:'include',headers:{'Content-Type':'application/json',...(csrf?{'X-CSRFToken':csrf}:{})},...(data?{body:JSON.stringify(data)}:{})});
 const json=await r.json();if(!r.ok)throw new Error(json.error||json.detail||'Something went wrong. Please try again.');if(json.csrfToken)csrf=json.csrfToken;return json;
}
