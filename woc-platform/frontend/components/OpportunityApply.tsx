'use client';
import {useState,useEffect,useRef} from 'react';
import Link from 'next/link';
import {api} from '@/lib/api';

export function OpportunityApply({id,signedIn}:{id:string;signedIn:boolean}){
 const dialog=useRef<HTMLElement>(null);
 const [preview,setPreview]=useState<any>(null),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[consent,setConsent]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 useEffect(()=>{if(!open)return;const previous=document.activeElement as HTMLElement|null;dialog.current?.querySelector<HTMLButtonElement>('button')?.focus();return()=>previous?.focus()},[open]);
 async function show(){setOpen(true);setBusy(true);setError('');try{setPreview(await api(`/student/opportunities/${id}/apply/`))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{const result=await api(`/student/opportunities/${id}/apply/`,'POST',{consent});setMessage(result.message);setPreview({...preview,delivery_state:'sent'})}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <>{signedIn?<button type="button" className="button full" onClick={show}>Apply</button>:<Link href="/login/" className="button full">Sign in to apply</Link>}
 {open&&<div className="modal-backdrop" onClick={()=>{if(!busy)setOpen(false)}}><section ref={dialog} onKeyDown={e=>{if(e.key==='Escape'&&!busy)setOpen(false);if(e.key==='Tab'){const items=dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled)');if(!items?.length)return;const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}}} className="modal career-apply-modal" role="dialog" aria-modal="true" aria-label="Review application" onClick={e=>e.stopPropagation()}><button type="button" className="text-link" disabled={busy} onClick={()=>setOpen(false)}>Close</button><h2>Review your application</h2>
 {busy&&!preview&&<p role="status">Loading your profile…</p>}{error&&<p role="alert" className="form-error">{error}</p>}{message&&<p role="status" className="notice">{message}</p>}
 {preview&&<><p>Your details will be sent to <strong>{preview.recipient}</strong>.</p><dl className="career-application-summary">{[['Name',preview.student.name],['Email',preview.student.email],['Verified phone',preview.student.phone],['LinkedIn',preview.student.linkedin_url],['Institution',preview.student.institution],['Qualification',preview.student.qualification],['Department',preview.student.department],['Graduation year',preview.student.graduation_year],['Skills',(preview.student.skills||[]).join(', ')],['Resume',preview.student.resume_name||'No PDF resume uploaded']].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value||'—'}</dd></div>)}</dl>
 <Link href="/dashboard/?tab=profile" className="text-link">Update profile or resume</Link>
 {preview.notice&&<p className="notice">{preview.notice}</p>}{!preview.email_verified&&<p className="notice">Verify your email in My Profile before applying.</p>}
 {preview.delivery_state==='sent'?<p className="notice">Application already submitted.</p>:preview.delivery_state==='sending'?<p className="notice">Delivery is processing or awaiting confirmation. Contact support before retrying.</p>:<form onSubmit={submit}><label className="checkbox"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I agree to share the profile details shown above and my PDF resume with this company.</label><button className="button full" disabled={busy||!consent||!preview.can_send||!preview.email_verified||!preview.student.resume_name}>{busy?'Sending…':'Send application'}</button></form>}</>}
 </section></div>}</>;
}
