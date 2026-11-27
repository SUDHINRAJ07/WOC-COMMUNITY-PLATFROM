'use client';
import {useEffect,useState} from 'react';
import {api} from '@/lib/api';

export function SignupEmailOtp({email,initialChallenge,deliveryFailed,onVerified}:{email:string;initialChallenge:string;deliveryFailed:boolean;onVerified:()=>Promise<void>}){
 const [challenge,setChallenge]=useState(initialChallenge),[otp,setOtp]=useState(''),[cooldown,setCooldown]=useState(deliveryFailed?0:60),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(deliveryFailed?'Request a new code to verify your email.':'Check your inbox and spam folder. Your code expires in 5 minutes.');
 useEffect(()=>{if(cooldown<=0)return;const timer=setTimeout(()=>setCooldown(c=>c-1),1000);return()=>clearTimeout(timer)},[cooldown]);
 async function resend(){
  setBusy(true);setError('');
  try{const data=await api('/email/resend-otp/','POST',{email});setChallenge(data.challenge_id||'');setOtp('');setCooldown(60);setMessage('A new verification code has been sent. It expires in 5 minutes.')}
  catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function verify(e:React.FormEvent){
  e.preventDefault();setBusy(true);setError('');
  try{await api('/email/verify-otp/','POST',{email,challenge_id:challenge||undefined,otp});setMessage('Email verified. Signing you in…');await onVerified()}
  catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 return <section className="panel" style={{marginTop:20}} aria-label="Verify signup email">
  <h3>Verify your email</h3><p style={{marginTop:10}}>Enter the 6-digit code sent to <strong>{email}</strong>.</p>
  <form className="form-stack" onSubmit={verify} style={{marginTop:16}}>
   <label>Verification code<input value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,'').slice(0,6))} inputMode="numeric" autoComplete="one-time-code" maxLength={6} pattern="[0-9]{6}" required/></label>
   <button className="button full" disabled={busy||otp.length!==6}>{busy?'Please wait…':'Verify and continue'}</button>
  </form>
  <p role="status" style={{marginTop:12,fontSize:13}}>{message}</p>
  {error&&<p role="alert" className="notice">{error}</p>}
  <button type="button" className="button outline small" style={{marginTop:12}} disabled={busy||cooldown>0} onClick={resend}>{cooldown>0?`Resend in ${cooldown}s`:'Resend code'}</button>
 </section>;
}
