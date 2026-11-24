import {deleteApp, getApps, initializeApp, type FirebaseApp} from 'firebase/app';
import {initializeAuth, inMemoryPersistence, RecaptchaVerifier, signInWithPhoneNumber, signOut, type Auth, type ConfirmationResult} from 'firebase/auth';

export function normalizeMobile(raw: string, country = '+91'): string {
 const input = raw.trim();
 if (!/^\+?[\d\s().-]+$/.test(input)) throw Error('Enter a valid mobile number.');
 const digits = input.replace(/\D/g, '');
 const phone = input.startsWith('+') ? '+' + digits : country + digits;
 if (!/^\+[1-9]\d{7,14}$/.test(phone) || (phone.startsWith('+91') && !/^\+91[6-9]\d{9}$/.test(phone))) throw Error('Enter a valid mobile number, including its country code.');
 return phone;
}

export function phoneError(error: unknown): string {
 const code = (error as {code?:string})?.code;
 const messages: Record<string,string> = {
  'auth/invalid-verification-code':'Incorrect OTP. Check the code and try again.',
  'auth/code-expired':'OTP expired. Request a new code.',
  'auth/session-expired':'Verification expired. Request a new code.',
  'auth/too-many-requests':'Too many attempts. Please wait before trying again.',
  'auth/quota-exceeded':'SMS quota is exhausted. Please try again later.',
  'auth/invalid-phone-number':'Enter a valid mobile number with its country code.',
  'auth/captcha-check-failed':'Security verification failed. Please try sending the code again.',
  'auth/invalid-app-credential':'Security verification failed. Check the authorized domain and try again.',
  'auth/unauthorized-domain':'This website domain is not authorized for Firebase phone verification.',
  'auth/operation-not-allowed':'Phone authentication or the SMS destination region is not enabled.',
  'auth/billing-not-enabled':'Firebase SMS billing must be enabled before sending real OTP messages.',
  'auth/network-request-failed':'Could not reach Firebase. Check your connection and try again.',
 };
 return (code && messages[code]) || (code ? 'Firebase phone verification failed. Please try again.' : error instanceof Error ? error.message : 'Phone verification failed.');
}

let sequence = 0;
export class FirebasePhoneSession {
 private app?: FirebaseApp;
 private auth?: Auth;
 private verifier?: RecaptchaVerifier;
 private confirmation?: ConfirmationResult;
 private token = '';
 private disposed = false;
 private sending = false;
 constructor(private container: HTMLElement) {}
 private alive() { if(this.disposed) throw Error('Verification was cancelled. Please start again.'); }
 private init() {
  this.alive();
  if(this.auth) return this.auth;
  const config = {
   apiKey:process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
   authDomain:process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
   projectId:process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
   appId:process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  };
  if(Object.values(config).some(value=>!value)) throw Error('Firebase phone verification is not configured. Contact WOC support.');
  let name: string;
  do {name=`woc-phone-${++sequence}`;} while(getApps().some(app=>app.name===name));
  this.app = initializeApp(config,name);
  // Firebase is a temporary proof of ownership, never the WOC login session.
  this.auth = initializeAuth(this.app,{persistence:inMemoryPersistence});
  this.auth.languageCode = 'en';
  return this.auth;
 }
 private clearCaptcha() {this.verifier?.clear();this.verifier=undefined;this.container.replaceChildren();}
 async send(phone:string) {
  this.alive();
  if(this.sending) throw Error('A verification request is already in progress.');
  this.sending=true;
  this.confirmation=undefined;this.token='';
  try {
   const auth=this.init();
   await signOut(auth);this.alive();
   this.clearCaptcha();
   this.verifier=new RecaptchaVerifier(auth,this.container,{size:'invisible'});
   const confirmation=await signInWithPhoneNumber(auth,phone,this.verifier);
   this.alive();this.confirmation=confirmation;
  } catch(error) {if(!this.disposed)this.clearCaptcha();throw error;}
  finally {this.sending=false;}
 }
 async verify(code:string) {
  this.alive();
  if(this.token) return this.token; // Permit retrying a failed Django request without replaying the OTP.
  if(!this.confirmation) throw Error('Request a verification code first.');
  const result=await this.confirmation.confirm(code);
  this.alive();
  const token=await result.user.getIdToken();
  this.alive();this.token=token;
  return token;
 }
 async dispose() {
  this.disposed=true;this.confirmation=undefined;this.token='';this.clearCaptcha();
  // Deleting this isolated in-memory Auth app cannot affect other WOC components.
  if(this.app) {await deleteApp(this.app);this.app=undefined;this.auth=undefined;}
 }
}
