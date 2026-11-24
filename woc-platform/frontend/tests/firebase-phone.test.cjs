const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const ts=require('typescript');
const React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');

function compile(file,imports={}) {
 const source=fs.readFileSync(path.join(__dirname,'..',file),'utf8');
 const {outputText}=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}});
 const module={exports:{}};
 new Function('require','module','exports',outputText)(id=>id in imports?imports[id]:require(id),module,module.exports);
 return module.exports;
}
function fixture() {
 const calls={init:0,captcha:0,clear:0,send:0,confirm:0,deleted:0};
 let sendError,confirmError,pending;
 const app={name:'test'};
 const auth={};
 const confirmation={confirm:async()=>{calls.confirm++;if(confirmError)throw confirmError;return {user:{getIdToken:async()=>'signed-id-token'}}}};
 const client=compile('lib/firebase-phone.ts',{
  'firebase/app':{getApps:()=>[],initializeApp:()=>{calls.init++;return app},deleteApp:async()=>{calls.deleted++}},
  'firebase/auth':{initializeAuth:(_,options)=>{assert.ok(options.persistence);return auth},inMemoryPersistence:{},signOut:async()=>{},
   RecaptchaVerifier:class {constructor(){calls.captcha++}clear(){calls.clear++}},
   signInWithPhoneNumber:async()=>{calls.send++;if(sendError)throw sendError;if(pending)return pending;return confirmation}},
 });
 const container={replaceChildren(){}};
 return {client,calls,session:new client.FirebasePhoneSession(container),setSendError:e=>sendError=e,setConfirmError:e=>confirmError=e,setPending:p=>pending=p};
}
function configured(run) {
 const keys=['API_KEY','AUTH_DOMAIN','PROJECT_ID','APP_ID'].map(k=>'NEXT_PUBLIC_FIREBASE_'+k);
 const before=keys.map(k=>process.env[k]);
 keys.forEach(k=>process.env[k]='unit-test-config');
 return Promise.resolve().then(run).finally(()=>keys.forEach((k,i)=>{if(before[i]===undefined)delete process.env[k];else process.env[k]=before[i]}));
}
test('normalizes India and international numbers and rejects invalid input',()=>{
 const {client}=fixture();
 assert.equal(client.normalizeMobile('98765 43210'),'+919876543210');
 assert.equal(client.normalizeMobile('+44 7700 900123'),'+447700900123');
 assert.equal(client.normalizeMobile('202-555-0123','+1'),'+12025550123');
 for(const value of ['12345','hello9876543210','+910123456789','++919876543210']) {
  assert.throws(()=>client.normalizeMobile(value));
 }
});
test('missing config fails before creating Firebase app or sending SMS',async()=>{
 const saved=process.env.NEXT_PUBLIC_FIREBASE_API_KEY;delete process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
 try{const f=fixture();await assert.rejects(f.session.send('+919876543210'),/not configured/);assert.equal(f.calls.send,0);assert.equal(f.calls.init,0)}
 finally{if(saved!==undefined)process.env.NEXT_PUBLIC_FIREBASE_API_KEY=saved}
});
test('send, verify and backend retry use one app and one OTP confirmation',()=>configured(async()=>{
 const f=fixture();await f.session.send('+919876543210');
 assert.equal(await f.session.verify('123456'),'signed-id-token');
 assert.equal(await f.session.verify('123456'),'signed-id-token');
 assert.equal(f.calls.init,1);assert.equal(f.calls.confirm,1);
 await f.session.dispose();assert.equal(f.calls.deleted,1);assert.equal(f.calls.clear,1);
}));
test('wrong OTP can be corrected without resending SMS',()=>configured(async()=>{
 const f=fixture();await f.session.send('+919876543210');f.setConfirmError({code:'auth/invalid-verification-code'});
 await assert.rejects(f.session.verify('000000'));f.setConfirmError(null);
 assert.equal(await f.session.verify('123456'),'signed-id-token');assert.equal(f.calls.send,1);
}));
test('resending replaces captcha and confirmation without duplicating apps',()=>configured(async()=>{
 const f=fixture();await f.session.send('+919876543210');await f.session.verify('123456');
 await f.session.send('+919876543210');await f.session.verify('654321');
 assert.equal(f.calls.captcha,2);assert.equal(f.calls.clear,1);assert.equal(f.calls.init,1);assert.equal(f.calls.confirm,2);
}));
test('send failure clears captcha and cannot produce a proof',()=>configured(async()=>{
 const f=fixture();f.setSendError({code:'auth/quota-exceeded'});
 await assert.rejects(f.session.send('+919876543210'));assert.equal(f.calls.clear,1);
 await assert.rejects(f.session.verify('123456'),/Request/);
 f.setSendError(null);await f.session.send('+919876543210');assert.equal(f.calls.init,1);
}));
test('concurrent send is rejected and disposed pending requests stay cancelled',()=>configured(async()=>{
 const f=fixture();let release;f.setPending(new Promise(resolve=>release=resolve));
 const first=f.session.send('+919876543210');
 await assert.rejects(f.session.send('+919876543210'),/already in progress/);
 await new Promise(resolve=>setImmediate(resolve));
 await f.session.dispose();release({confirm:async()=>{throw Error('must not confirm')}});
 await assert.rejects(first,/cancelled/);await assert.rejects(f.session.verify('123456'),/cancelled/);
 assert.equal(f.calls.clear,1);
}));
test('OTP, quota, region, billing and domain errors are actionable',()=>{
 const {client}=fixture();
 for(const code of ['invalid-verification-code','code-expired','quota-exceeded','operation-not-allowed','billing-not-enabled','unauthorized-domain','captcha-check-failed']) {
  const message=client.phoneError({code:'auth/'+code});assert.ok(message.length>20);assert.ok(!message.includes('undefined'));
 }
});
test('mobile registration guides Email signup without phone account creation',()=>{
 const component=compile('components/MobileAuthForm.tsx',{
  '@/lib/use-firebase-phone':{useFirebasePhone:()=>({container:{current:null},reset(){}})},
  '@/lib/firebase-phone':{phoneError:()=>''},'@/lib/api':{api:()=>{throw Error('no API calls during render')}},
  './Platform':{useWoc:()=>({demo:false,setUser(){},toast(){}})},
 }).default;
 const register=renderToStaticMarkup(React.createElement(component,{mode:'register',onEmailSignup(){}}));
 assert.match(register,/Continue with Email/);assert.match(register,/cannot create a WOC account/);
 assert.doesNotMatch(register,/Verify &amp; create account|type="tel"/);
 const login=renderToStaticMarkup(React.createElement(component,{mode:'login',onEmailSignup(){}}));
 assert.match(login,/auth-mobile-form/);assert.match(login,/Send verification code/);assert.match(login,/type="tel"/);
});
