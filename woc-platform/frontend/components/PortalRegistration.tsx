'use client';
import {useEffect} from 'react';
import Link from 'next/link';
import {GraduationCap,School,Building2} from 'lucide-react';
import {Auth} from './Pages';
import {OnboardingView} from './OnboardingView';
import {useWoc} from './Platform';

export function JoinCommunity(){return <main id="main" className="section pale"><div className="container"><p className="eyebrow">FIND YOUR PLACE</p><h1>Join our community.</h1><p>Choose your journey with WOC.</p><div className="portal-choices">{[{name:'Student',path:'/register/',Icon:GraduationCap,line:'Learn skills, discover careers and enjoy campus life.'},{name:'College',path:'/register-college/',Icon:School,line:'Connect students, training, placements and industry.'},{name:'Company',path:'/register-company/',Icon:Building2,line:'Publish approved jobs and internships for emerging talent.'}].map(({name,path,Icon,line})=><article className="panel" key={name}><Icon size={32} color="var(--red)"/><h2>Join as {name}</h2><p>{line}</p><Link className="button" href={path} onClick={()=>{if(name==='Student')sessionStorage.removeItem('woc-registration-role');else sessionStorage.setItem('woc-registration-role',name.toLowerCase());}}>Continue as {name} →</Link></article>)}</div><p>Already registered? <Link className="text-link" href="/login/">Sign in</Link></p></div></main>}

export function OrganizationRegistration({role}:{role:'college'|'company'}){
 const {user}=useWoc();
 useEffect(()=>{sessionStorage.setItem('woc-registration-role',role)},[role]);
 if(user)return <OnboardingView initialType={role}/>;
 return <Auth mode="register" registrationRole={role}/>;
}
