'use client';
import {useEffect,useState} from 'react';
import {useFirebasePhone} from '@/lib/use-firebase-phone';
import {phoneError} from '@/lib/firebase-phone';
import {api} from '@/lib/api';
import {useWoc} from './Platform';

export default function MobileAuthForm({mode,onEmailSignup}:{mode:'login'|'register';onEmailSignup:()=>void}){
 const {demo,setUser,toast}=useWoc();
 const firebase=useFirebasePhone();
 const [phone,setPhone]=useState(''),[country,setCountry]=useState('+91'),[challenge,setChallenge]=useState(''),[otp,setOtp]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[preview,setPreview]=useState('');
 const [cooldown,setCooldown]=useState(0),[expires,setExpires]=useState(0);
 useEffect(()=>{if(!challenge)return;const timer=setInterval(()=>{setCooldown(n=>Math.max(0,n-1));setExpires(n=>Math.max(0,n-1))},1000);return()=>clearInterval(timer)},[challenge]);
 async function send(){
  if(busy||cooldown>0)return;
  setBusy(true);setError('');setMessage('');
  try{
   if(!demo) setPhone(await firebase.send(phone,country));
   const d={challenge_id:'firebase',message:demo?'Demo preview only. No SMS was sent.':'Verification requested. Enter the code for your number.',development_otp:demo?'123456':'',expires_in:300};
   setChallenge(d.challenge_id);setCooldown(60);setExpires(d.expires_in);setOtp('');setPreview(d.development_otp||'');setMessage(d.message);
  }catch(e){setError(phoneError(e))}finally{setBusy(false)}
 }
 async function submit(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();if(busy)return;if(!challenge){await send();return}
  setBusy(true);setError('');
  try{
   if(demo){
    if(otp!=='123456')throw Error('Use the displayed demo code.');
    setUser({id:1,name:'Demo Student',email:'',institution:'',age:18,bio:'',roles:['student'],is_staff:false,phone_number:country+phone,phone_verified:true,auth_provider:'phone'});
   }else{const idToken=await firebase.verify(otp);const d=await api('/auth/firebase-phone/','POST',{id_token:idToken});setUser(d.user)}
   firebase.reset();toast('Signed in successfully.');window.location.href='/dashboard/';
  }catch(e){setError(phoneError(e))}finally{setBusy(false)}
 }
 if(mode==='register')return <div className="auth-mobile-form auth-register-form"><p className="notice auth-wide">Create your WOC account using Email or Google first. After signing in, verify and link your mobile number in Profile settings.</p><button type="button" className="button full auth-wide" onClick={onEmailSignup}>Continue with Email</button><p className="auth-helper auth-wide">A mobile verification code cannot create a WOC account.</p></div>;
 return <form className="auth-mobile-form" onSubmit={submit}>
  <div ref={firebase.container} style={{display:'contents'}}/>
  <label className="auth-wide">Mobile number<div className="auth-phone-row"><select aria-label="Country calling code" value={country} onChange={e=>setCountry(e.target.value)} disabled={!!challenge||busy}><option value="+91">IN +91</option><option value="+1">US +1</option><option value="+44">UK +44</option><option value="+971">AE +971</option><option value="+65">SG +65</option></select><input type="tel" autoComplete="tel-national" inputMode="tel" required value={phone} onChange={e=>setPhone(e.target.value)} readOnly={!!challenge||busy} placeholder="Enter mobile number" maxLength={20}/></div></label>
  {challenge&&<div className="auth-wide auth-code-step"><div className="auth-code-heading"><span>{message}</span><button type="button" className="auth-inline-action" disabled={busy} onClick={()=>{firebase.reset();setCooldown(0);setChallenge('');setOtp('');setPreview('');setError('')}}>Change number</button></div><label>Verification code<input aria-label="Mobile verification code" type="text" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,''))} placeholder="6-digit code"/></label><div className="auth-code-heading"><small>{expires>0?`Code expires in ${Math.floor(expires/60)}:${String(expires%60).padStart(2,'0')}`:'Code expired. Request a new code.'}</small><button type="button" className="auth-inline-action" disabled={busy||cooldown>0} onClick={send}>{cooldown?`Resend in ${cooldown}s`:'Resend code'}</button></div>{preview&&<p className="notice">Local preview only — no SMS sent. Test code: <strong>{preview}</strong></p>}</div>}

  {error&&<p className="form-error auth-wide" role="alert">{error}</p>}
  <button className="button full auth-wide" disabled={busy||!phone||(!!challenge&&(otp.length!==6||expires<=0))}>{busy?'Please wait…':!challenge?'Send verification code':'Verify & sign in'}</button>
  <p className="auth-helper auth-wide">Use the mobile number previously linked through Firebase in your WOC profile.</p>
 </form>
}
