'use client';
import {useEffect,useRef} from 'react';
import {FirebasePhoneSession,normalizeMobile} from './firebase-phone';

export function useFirebasePhone() {
 const container=useRef<HTMLDivElement>(null);
 const session=useRef<FirebasePhoneSession|null>(null);
 function reset() {
  const previous=session.current;session.current=null;
  if(previous) void previous.dispose().catch(()=>{});
 }
 useEffect(()=>reset,[]);
 return {
  container,reset,
  async send(raw:string,country:string) {
   const phone=normalizeMobile(raw,country);
   if(!container.current) throw Error('Phone verification is not ready. Please try again.');
   session.current ||= new FirebasePhoneSession(container.current);
   await session.current.send(phone);
   return phone;
  },
  async verify(code:string) {
   if(!session.current) throw Error('Request a verification code first.');
   return session.current.verify(code);
  },
 };
}
