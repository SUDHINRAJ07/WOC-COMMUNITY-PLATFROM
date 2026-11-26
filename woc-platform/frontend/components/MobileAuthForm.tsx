'use client';
import {redirectAfterAuthentication} from '@/lib/api';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {api} from '@/lib/api';
import {useWoc} from './Platform';

export default function MobileAuthForm({mode,onEmailSignup}:{mode:'login'|'register';onEmailSignup:()=>void}){
 const {demo,setUser,toast}=useWoc();
 const [phone,setPhone]=useState(''),[country,setCountry]=useState('+91'),[challenge,setChallenge]=useState(''),[otp,setOtp]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[preview,setPreview]=useState(''),[deliveryMode,setDeliveryMode]=useState<'live'|'test'|''>('');
 const [cooldown,setCooldown]=useState(0),[expires,setExpires]=useState(0);
 useEffect(()=>{if(!challenge)return;const timer=setInterval(()=>{setCooldown(n=>Math.max(0,n-1));setExpires(n=>Math.max(0,n-1))},1000);return()=>clearInterval(timer)},[challenge]);
 async function send(){
  if(busy||cooldown>0)return;
  setBusy(true);setError('');setMessage('');
  try{
   const d=demo?{challenge_id:'demo',message:'Browser demo only. No SMS sent.',development_otp:'123456',expires_in:300,delivery_mode:'test'}:await api('/phone/send-otp/','POST',{phone,country_code:country,purpose:mode});
   if(d.phone)setPhone(d.phone);
   setChallenge(d.challenge_id);setCooldown(60);setExpires(d.expires_in);setOtp('');setPreview(d.development_otp||'');setDeliveryMode(d.delivery_mode||'live');setMessage(d.message);
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function submit(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();if(busy)return;if(!challenge){await send();return}
  setBusy(true);setError('');
  const data=Object.fromEntries(new FormData(e.currentTarget));
  try{
   if(demo){
    if(otp!=='123456')throw Error('Use the displayed demo code.');
    setUser({id:1,name:'Demo Student',email:'',institution:'',age:18,bio:'',roles:['student'],is_staff:false,phone_number:country+phone,phone_verified:true,auth_provider:'phone'});
   }else{const d=await api('/auth/phone/','POST',{...data,terms:!!data.terms,guardian_consent:!!data.guardian_consent,action:mode,challenge_id:challenge,otp});setUser(d.user)}
   toast('Signed in successfully.');await redirectAfterAuthentication();
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 return <form className={`auth-mobile-form ${mode==='register'?'auth-register-form':''}`} onSubmit={submit}>
  {mode==='register'&&<><label>Full name<input name="name" autoComplete="name" maxLength={150} required/></label><label>Age<input name="age" type="number" min={13} max={100} required/></label><label className="auth-wide">Institution<input name="institution" autoComplete="organization" maxLength={200} required/></label></>}
  <label className="auth-wide">Mobile number<div className="auth-phone-row"><select aria-label="Country calling code" value={country} onChange={e=>setCountry(e.target.value)} disabled={!!challenge||busy}><option value="+91">IN +91</option><option value="+1">US +1</option><option value="+44">UK +44</option><option value="+971">AE +971</option><option value="+65">SG +65</option></select><input type="tel" autoComplete="tel-national" inputMode="tel" required value={phone} onChange={e=>setPhone(e.target.value)} readOnly={!!challenge||busy} placeholder="Enter mobile number" maxLength={20}/></div></label>
  {challenge&&<div className="auth-wide auth-code-step"><div className="auth-code-heading"><span>{message}</span><button type="button" className="auth-inline-action" disabled={busy} onClick={()=>{setCooldown(0);setChallenge('');setOtp('');setPreview('');setError('')}}>Change number</button></div><label>Verification code<input aria-label="Mobile verification code" type="text" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,''))} placeholder="6-digit code"/></label><div className="auth-code-heading"><small>{expires>0?`Code expires in ${Math.floor(expires/60)}:${String(expires%60).padStart(2,'0')}`:'Code expired. Request a new code.'}</small><button type="button" className="auth-inline-action" disabled={busy||cooldown>0} onClick={send}>{cooldown?`Resend in ${cooldown}s`:'Resend code'}</button></div>{preview&&<p className="notice">Local preview only — no SMS sent. Test code: <strong>{preview}</strong></p>}</div>}

  {mode==='register'&&<div className="auth-wide auth-consents"><label className="checkbox"><input name="guardian_consent" type="checkbox"/>Under 18? I confirm school and guardian permission.</label><label className="checkbox"><input name="terms" type="checkbox" required/>I agree to the <Link href="/terms/">Terms</Link> and <Link href="/privacy/">Privacy Notice</Link>.</label></div>}
  {error&&<p className="form-error auth-wide" role="alert">{error}</p>}
  <button className="button full auth-wide" disabled={busy||!phone||(!!challenge&&(otp.length!==6||expires<=0))}>{busy?'Please wait…':!challenge?'Send verification code':mode==='register'?'Verify & create account':'Verify & sign in'}</button>
  <p className="auth-helper auth-wide">{deliveryMode==='test'||demo?'Local preview: test OTP appears on this screen.':'Enter the 6-digit verification code sent via SMS to your mobile number.'}</p>
 </form>
}
