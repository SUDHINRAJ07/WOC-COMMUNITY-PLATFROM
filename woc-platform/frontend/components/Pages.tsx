'use client';
import {useEffect,useState,ReactNode} from 'react';
import Link from 'next/link';
import {motion,useReducedMotion,AnimatePresence} from 'motion/react';
import {Swiper,SwiperSlide} from 'swiper/react';
import {Navigation,Pagination} from 'swiper/modules';
import 'swiper/css';import 'swiper/css/pagination';
import {Users,BookOpen,Briefcase,Rocket,Calendar,Globe,Trophy,Music,Check,MapPin,Clock,Search,ChevronLeft,ChevronRight,Pause,Play,ShieldCheck,GraduationCap,Lightbulb,HeartHandshake,CheckCircle,Layers} from 'lucide-react';
import {useQuery} from '@tanstack/react-query';
import {useForm} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {z} from 'zod';
import {modules,programs,Program,money} from '@/lib/data';
import {api} from '@/lib/api';
import {programImage,moduleImage} from '@/lib/images';
import {useWoc,Registration} from './Platform';
import MobileAuthForm from './MobileAuthForm';
const icons=[Users,BookOpen,Briefcase,Rocket,Calendar,Globe,Trophy,Music];
export function Reveal({children,className=''}:{children:ReactNode;className?:string}){const reduce=useReducedMotion();return <motion.div className={className} initial={false} whileInView={reduce?{}:{y:[16,0],opacity:[.75,1]}} viewport={{once:true,amount:.12}} transition={{duration:.55,ease:'easeOut'}}>{children}</motion.div>}
function Eyebrow({children}:{children:ReactNode}){return <p className="eyebrow">{children}</p>}
function Title({label,title,description}:{label:string;title:string;description?:string}){return <div className="section-heading"><Eyebrow>{label}</Eyebrow><h2>{title}</h2>{description&&<p>{description}</p>}</div>}
const heroSlides=[{title:<>Empowering Students.<br/>Creating Opportunities.</>,sub:'BE THE CHANGE.',text:'Discover a unified platform for learning, careers, innovation and meaningful student experiences.',image:'campus-hero.webp',cta:'Explore WOC',link:'/about/',other:'Join Our Community',otherLink:'/register/'},{title:<>Learn. Build.<br/>Connect. Grow.</>,sub:'PRACTICAL SKILLS. NEW POSSIBILITIES.',text:'Develop practical skills, connect with mentors and build work you can be proud of.',image:'innovation-lab-original.webp',cta:'Explore Academy',link:'/academy/',other:'Discover Careers',otherLink:'/careers/'},{title:<>Beyond the<br/>Classroom.</>,sub:'FIND YOUR PEOPLE. FIND YOUR STAGE.',text:'Explore sports, cultural competitions, student leadership and innovation in one community.',image:'campus-festival.webp',cta:'Explore Events',link:'/events/',other:'Discover Campus Life',otherLink:'/culturals/'}];
export function Home(){const [slide,setSlide]=useState(0),[playing,setPlaying]=useState(true);const reduce=useReducedMotion();const h=heroSlides[slide];useEffect(()=>{if(!playing||reduce)return;const t=setInterval(()=>setSlide(s=>(s+1)%3),6500);return()=>clearInterval(t)},[playing,reduce]);return <main id="main"><section className="hero"><AnimatePresence initial={false}><motion.div className="hero-image" key={`hero-${slide}`} style={{backgroundImage:`url('/images/${h.image}')`,backgroundPosition:h.image==='innovation-lab-original.webp'?'center top':undefined}} initial={{opacity:0,scale:1.04}} animate={{opacity:1,scale:1}} exit={{opacity:0}} transition={{opacity:{duration:reduce?0:.7},scale:{duration:reduce?0:6}}}/></AnimatePresence><div className="hero-overlay"/><div className="container hero-content"><motion.div key={slide} initial={false} animate={reduce?{}:{y:[18,0],opacity:[.7,1]}} transition={{duration:.7}}><Eyebrow>{h.sub}</Eyebrow><h1>{h.title}</h1><p>{h.text}</p><div className="actions"><Link className="button" href={h.link}>{h.cta}</Link><Link className="button ghost" href={h.otherLink}>{h.other}</Link></div></motion.div><div className="hero-controls"><div className="slide-dots" aria-label="Hero slides">{heroSlides.map((_,i)=><button key={i} aria-label={`Show slide ${i+1}`} aria-pressed={slide===i} onClick={()=>setSlide(i)}/>)}</div><span className="slide-count">0{slide+1} / 03</span><button onClick={()=>setSlide((slide+2)%3)} aria-label="Previous slide"><ChevronLeft size={18}/></button><button onClick={()=>setSlide((slide+1)%3)} aria-label="Next slide"><ChevronRight size={18}/></button><button onClick={()=>setPlaying(!playing)} aria-label={playing?'Pause hero autoplay':'Play hero autoplay'}>{playing?<Pause size={15}/>:<Play size={15}/>}</button></div></div></section><section className="feature-band"><div className="container feature-grid">{[{name:'Student Community',icon:Users,link:'association'},{name:'Skill Development',icon:BookOpen,link:'academy'},{name:'Career Opportunities',icon:Briefcase,link:'careers'},{name:'Campus Experiences',icon:GraduationCap,link:'events'}].map((f,i)=><Reveal key={f.name}><Link href={`/${f.link}/`} className="feature-card"><f.icon size={44} strokeWidth={1.15}/><h2>{f.name}</h2><span className="feature-circle"><ChevronRight size={20}/></span></Link><p className="feature-caption">{['Find your people and grow together.','Turn curiosity into practical ability.','Explore your next professional step.','Make your campus years meaningful.'][i]}</p></Reveal>)}</div></section><section className="section container about-layout"><Reveal className="about-collage"><img src="/images/innovation-lab.webp" alt="Illustrative students collaborating on a prototype" loading="lazy"/><div className="image-note">Ideas grow<br/><em>when we connect.</em></div><span className="photo-caption">Original AI-created campus imagery</span></Reveal><Reveal><Eyebrow>ABOUT WIND OF CHANGE</Eyebrow><h2>Your ambition.<br/>A world of <em>possibilities.</em></h2><p>WOC brings campus communities, practical learning and industry pathways into one student journey. A place to find your people, build your skills and explore what comes next.</p><div className="value-line"><ShieldCheck/><div><h3>Purposeful learning</h3><p>Practice, projects and feedback that help you progress.</p></div></div><div className="value-line"><HeartHandshake/><div><h3>A community around you</h3><p>Peers, mentors and institutions working towards opportunity.</p></div></div><Link href="/about/" className="text-link">Discover WOC</Link></Reveal></section><section className="section pale"><div className="container"><Title label="ONE PLATFORM. EIGHT POSSIBILITIES." title="Find your path with WOC." description="Start with what matters to you. Discover where it can take you."/><div className="module-grid">{modules.map((m,i)=>{const Icon=icons[i];return <Reveal key={m.slug}><Link href={`/${m.slug}/`} className="module-card"><img className="module-photo" src={moduleImage(m.slug)} alt="" loading="lazy"/><h3>{m.name}</h3><p>{m.description}</p><span>Explore {m.name}</span></Link></Reveal>})}</div></div></section><section className="section container"><div className="heading-row"><Title label="WOC ACADEMY" title="Learn something. Build something."/><Link href="/academy/" className="text-link">Explore all courses</Link></div><p className="sample-note">Sample catalogue · Proposed course fees and delivery require confirmation.</p><Swiper modules={[Pagination]} pagination={{clickable:true}} spaceBetween={25} slidesPerView={1} breakpoints={{680:{slidesPerView:2},1024:{slidesPerView:3}}}>{programs.filter(p=>p.module==='academy').map(p=><SwiperSlide key={p.slug}><ProgramCard program={p}/></SwiperSlide>)}</Swiper></section><section className="why-section"><div className="container split"><Reveal><Eyebrow>WHY CHOOSE WOC?</Eyebrow><h2>More than a moment.<br/>A journey forward.</h2><p>Connect learning with the things you can make, the people you can meet and the opportunities you can explore.</p><ul className="checklist">{['Practical skill development','Campus communities and peer support','Employer verification before live listings','Mentorship, ideas and innovation'].map(x=><li key={x}><Check size={18}/>{x}</li>)}</ul></Reveal><img src="/images/campus-hero.webp" alt="Illustrative campus community of students" loading="lazy"/></div></section><section className="section container"><div className="heading-row"><Title label="CAREERS & INTERNSHIPS" title="Your next chapter starts here."/><Link href="/careers/" className="text-link">Explore opportunities</Link></div><p className="sample-note">Illustrative roles only. No live vacancies or hiring guarantees.</p><div className="three-grid">{programs.filter(p=>p.module==='careers').map(p=><ProgramCard key={p.slug} program={p} compact/>)}</div></section><section className="campus-section"><img src="/images/campus-festival.webp" alt="AI-created illustration of a student cultural festival" loading="lazy"/><div className="container campus-content"><Eyebrow>CAMPUS LIFE</Eyebrow><h2>Bring your energy.<br/>Find your stage.</h2><div className="campus-links"><Link href="/sports/"><img className="campus-card-photo" src="/images/sports-cricket.webp" alt="Student cricket" loading="lazy"/><Trophy/><h3>Play with purpose.</h3><p>Cricket, football, badminton and your campus team.</p><span>Explore Sports</span></Link><Link href="/culturals/"><img className="campus-card-photo" src="/images/dance-performance.webp" alt="Student cultural stage" loading="lazy"/><Music/><h3>Make it your moment.</h3><p>Music, dance, theatre and creative expression.</p><span>Explore Culturals</span></Link></div></div></section><section className="section container"><div className="heading-row"><Title label="MEET. LEARN. EXPERIENCE." title="There’s something to be part of."/><Link href="/events/" className="text-link">View all events</Link></div>{programs.filter(p=>p.module==='events').map(p=><Reveal key={p.slug}><Link href={`/events/${p.slug}/`} className="event-row"><img className="event-photo" src={programImage(p)} alt="" loading="lazy"/><span className="date-tile"><Calendar size={24}/><small>TBA</small></span><div><span className="label">{p.category} · Sample event</span><h3>{p.title}</h3><p><MapPin size={14}/>{p.details.venue}</p></div><span className="event-detail-link">View event</span></Link></Reveal>)}</section><section className="section pale"><div className="container"><Title label="WOC INCUBATION" title="Big possibilities start with an idea." description="A proposed founder journey from a real problem to a useful prototype."/><div className="steps">{['Idea','Validation','Prototype','Mentorship','Demo Day'].map((s,i)=><div key={s}><span><Lightbulb size={22}/></span><h3>{s}</h3><p>{['Find a problem worth solving.','Talk to potential customers.','Build and test something small.','Get constructive expert feedback.','Show what you have learned.'][i]}</p></div>)}</div><Link className="button" href="/incubation/">Explore Founders Lab</Link></div></section><section className="section container partner-section"><Eyebrow>INSTITUTIONS & INDUSTRY</Eyebrow><h2>Better opportunities.<br/>Built together.</h2><p>We welcome conversations with colleges, mentors, employers and program supporters. Partner relationships appear here only after confirmation.</p><div className="partner-types">{['College pilot partners','Employer project partners','Mentors & program supporters'].map(s=><span key={s}><Globe size={20}/>{s}</span>)}</div><Link href="/partnerships/" className="button outline">Become a Partner</Link></section><section className="impact-section"><div className="container"><Title label="OUTCOMES THAT MATTER" title="Real progress. Clearly reported." description="Our public impact dashboard will display verified results after pilot delivery."/><div className="impact-grid">{['Members','Campus Chapters','Courses','Events','Career Outcomes'].map(s=><div key={s}><span>—</span><h3>{s}</h3><p>Awaiting verified pilot data</p></div>)}</div></div></section><section className="section container split"><div><Eyebrow>STUDENT VOICES</Eyebrow><h2>Your experience<br/>belongs in the story.</h2><p>Approved student testimonials will appear after our first pilots. We publish real experiences with consent.</p><Link href="/contact/?kind=feedback" className="text-link">Share your feedback</Link></div><div className="quote-empty"><Users size={38} strokeWidth={1}/><h3>Community stories are coming.</h3><p>Learning, belonging and new possibilities, in students’ own words.</p></div></section><section className="section pale"><div className="container"><Title label="FROM THE WOC JOURNAL" title="Ideas for your next step."/><div className="three-grid">{['Build a portfolio that shows your work','Make the most of your campus community','Start with a problem worth solving'].map((s,i)=><Link className="journal-card" key={s} href={`/news/?story=${i}`}><img className="journal-photo" src={`/images/${['course-design','campus-hero','innovation-lab'][i]}.webp`} alt="" loading="lazy"/><span>{['LEARNING','COMMUNITY','INNOVATION'][i]}</span><h3>{s}</h3><p>{['A practical guide to documenting projects.','Small ways to participate and contribute.','Simple questions for aspiring founders.'][i]}</p><span className="text-link">Read the guide</span></Link>)}</div></div></section><FinalCTA/></main>}
export function ProgramCard({program:p,compact=false}:{program:Program;compact?:boolean}){const idx=modules.findIndex(m=>m.slug===p.module);const Icon=icons[idx]||Layers;return <article className={`program-card ${compact?'compact':''}`}><Link className={`program-visual visual-${p.module}`} href={`/${p.module}/${p.slug}/`} aria-label={`View ${p.title}`}><img src={programImage(p)} alt={`${p.category} learning and participation`} loading="lazy"/><span>{p.category}</span></Link><div className="program-body"><div className="label">{p.category}<span className="sample-chip">Sample</span></div><h3><Link href={`/${p.module}/${p.slug}/`}>{p.title}</Link></h3><p>{p.description}</p><div className="program-meta"><span><Clock size={14}/>{p.duration}</span>{p.module==='academy'?<strong>{money(p.fee)}</strong>:<span><MapPin size={14}/>Chennai / Online</span>}</div><Link href={`/${p.module}/${p.slug}/`} className="card-link">View details</Link></div></article>}
function FinalCTA(){return <section className="final-cta"><div className="container"><div><Eyebrow>BE THE CHANGE.</Eyebrow><h2>Your Journey<br/>Starts with WOC.</h2></div><div className="actions"><Link href="/register/" className="button light">Become a Member</Link><Link href="/careers/" className="button ghost">Explore Opportunities</Link></div></div></section>}
function PageHero({label,title,text,image}:{label:string;title:string;text:string;image?:string}){const copy=<><Link href="/" className="breadcrumb">Home / {label}</Link><Eyebrow>{label}</Eyebrow><h1>{title}</h1><p>{text}</p></>;return <section className={`page-hero${image?' event-detail-hero':''}`}><div className="container">{image?<div className="event-hero-grid"><div>{copy}</div><img className="event-hero-photo" src={image} alt={title}/></div>:copy}</div></section>}
export function PageView({section,slug}:{section:string;slug?:string}){if(slug){const p=programs.find(p=>p.slug===slug&&p.module===section);return p?<Detail program={p}/>:<main id="main" className="section container"><h1>Program not found.</h1></main>};if(modules.some(m=>m.slug===section))return <Catalogue section={section}/>;if(['login','register','verify','forgot-password','reset-password'].includes(section))return <Auth mode={section}/>;if(section==='dashboard')return <Dashboard/>;if(section==='admin')return <Admin/>;if(section==='certificate')return <VerifyCertificate/>;if(section==='contact')return <Contact/>;if(section==='about')return <About/>;if(section==='news')return <Journal/>;return <Policies type={section}/>}
function Catalogue({section}:{section:string}){const m=modules.find(m=>m.slug===section)!;const [q,setQ]=useState(''),[category,setCategory]=useState('All');useEffect(()=>setQ(new URLSearchParams(window.location.search).get('q')||''),[]);const data=programs.filter(p=>p.module===section);const filtered=data.filter(p=>(category==='All'||p.category===category)&&(p.title+' '+p.description).toLowerCase().includes(q.toLowerCase()));return <main id="main" className="feature-catalogue"><PageHero label={m.name} title={m.line} text={m.description}/><section className="section container"><div className="catalogue-toolbar"><label className="search-input"><Search size={18}/><input aria-label={`Search ${m.name}`} placeholder={`Search ${m.name.toLowerCase()}…`} value={q} onChange={e=>setQ(e.target.value)}/></label><label>Category<select value={category} onChange={e=>setCategory(e.target.value)}>{['All',...new Set(data.map(p=>p.category))].map(c=><option key={c}>{c}</option>)}</select></label></div><p className="sample-note">Sample catalogue for platform demonstration. Dates, availability and partnerships are unconfirmed. {section==='careers'&&'These are not live jobs.'}</p><div className="three-grid">{filtered.map(p=><ProgramCard key={p.slug} program={p}/>)}</div>{!filtered.length&&<div className="empty-state"><Search/><h2>No matches yet.</h2><p>Try another keyword or category.</p><button className="button outline" onClick={()=>{setQ('');setCategory('All')}}>Clear search</button></div>}{section==='sports'&&<div className="section"><h2>Fixtures & results</h2><p>Fixtures and approved results will appear after teams and schedules are confirmed.</p></div>}{section==='culturals'&&<div className="section"><h2>Auditions, schedules & results</h2><p>Participant schedules and approved results will appear after competition confirmation.</p></div>}{section==='partnerships'&&<Link href="/contact/?kind=partnership" className="button">Discuss a partnership</Link>}</section><FinalCTA/></main>}
function Detail({program:p}:{program:Program}){const {user,records,registerProgram,toast,demo}=useWoc();const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');const record=records.find(r=>r.program.slug===p.slug);async function submit(e:React.FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setError('');const data=Object.fromEntries(new FormData(e.currentTarget));try{await registerProgram(p.slug,data);setOpen(false)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}return <main id="main"><PageHero label={modules.find(m=>m.slug===p.module)!.name} title={p.title} text={p.description} image={p.module==='events'?programImage(p):undefined}/><div className="container section detail-layout"><article><p className="sample-note">Sample {p.module==='careers'?'role, not a live vacancy':'program'} · Dates and delivery pending confirmation.</p><Eyebrow>{p.category}</Eyebrow><h2>Make your next step meaningful.</h2><p>{p.description}</p><h3 className="subheading">{p.module==='careers'?'What this sample role explores':'What you’ll explore'}</h3><ul className="checklist">{(p.details.outcomes||p.details.skills||['A supportive student community','Practical participation and feedback','A documented next step']).map(o=><li key={o}><Check/>{o}</li>)}</ul>{p.module==='academy'&&<><h3 className="subheading">Learning pathway</h3>{['Understand the problem','Practice with a small task','Build and present your project'].map((s,i)=><details className="curriculum" key={s}><summary>Lesson {i+1}: {s}</summary><p>{['Start with a clear goal, identify your audience and define what success looks like.','Work through a focused exercise. Keep notes on your assumptions and explain what you tried.','Create a small deliverable, check your work and describe the result in plain language.'][i]}</p></details>)}<p className="muted">This is a sample learning outline. A WOC completion certificate is not an accredited degree or a job guarantee.</p></>}{p.module==='incubation'&&<div className="notice">No funding, equity investment or investor access is guaranteed. Applications require review.</div>}{p.module==='association'&&p.slug==='school-chapter'&&<div className="notice">Under-18 participation needs school and guardian permission. School partnerships require a separate safeguarding process before live activities.</div>}{p.module==='sports'&&<div className="notice">Team size: {p.details.min_players}–{p.details.max_players} players. Eligibility and final tournament rules require organiser confirmation.</div>}<h3 className="subheading">Questions before joining?</h3><p>Ask about eligibility, accessibility or the proposed delivery format.</p><Link href={`/contact/?kind=${p.module}`} className="text-link">Contact the WOC team</Link></article><aside className="detail-sidebar">{p.module!=='events'&&<div className="detail-visual"><img src={programImage(p)} alt={p.title}/></div>}<div className="sidebar-content"><span className="label">{p.module==='academy'?'PROPOSED FEE':'SAMPLE PROGRAM'}</span><h2>{money(p.fee)}</h2><dl><div><dt>Duration</dt><dd>{p.duration}</dd></div><div><dt>Location</dt><dd>{p.details.venue||'Chennai / Online'}</dd></div><div><dt>Date</dt><dd>{p.details.date||'To be announced'}</dd></div><div><dt>Level</dt><dd>{p.level||'Open to eligible students'}</dd></div></dl>{record?<><div className="success-box"><CheckCircle size={18}/> {record.status}</div><Link className="button full" href="/dashboard/">View dashboard</Link></>:!user?<Link className="button full" href="/login/">Sign in to participate</Link>:<button className="button full" onClick={()=>setOpen(true)}>{p.module==='careers'?'Save sample application':p.module==='incubation'?'Submit your idea':p.module==='sports'?'Register your team':'Register interest'}</button>}<p className="muted small-copy">{Number(p.fee)>0?'Payment integration is pending. This records an enquiry; no money is collected.':'Sample registrations help demonstrate the workflow.'}</p></div></aside></div>{open&&<div className="modal-backdrop" onClick={()=>setOpen(false)}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="registration-title" onClick={e=>e.stopPropagation()}><h2 id="registration-title">{p.title}</h2><p>Registering as {user?.name}. {demo?'Saved only in this browser.':'Saved in your WOC account.'}</p><form onSubmit={submit}>{p.module==='sports'&&<><label>Team name<input name="team" required maxLength={100}/></label><label>Players, one per line<textarea name="players" required rows={5}/></label></>}{p.module==='culturals'&&<><label>Participation format<select name="format"><option>Solo</option><option>Group</option></select></label><label>Group / performance name<input name="team"/></label></>}{p.module==='incubation'&&<label>Your problem, idea and intended customer<textarea name="idea" required minLength={30} rows={5}/></label>}{p.module==='association'&&<label>Institution name<input name="institution" required/></label>}{p.module==='careers'&&<label>Why are you interested in this sample role?<textarea name="motivation" minLength={20} required/></label>}<label>Anything we should know?<textarea name="notes" maxLength={1500}/></label><label className="checkbox"><input type="checkbox" required/>I understand this is a sample program and agree to the privacy notice.</label>{error&&<p className="form-error" role="alert">{error}</p>}<div className="actions"><button className="button" disabled={busy}>{busy?'Saving…':'Submit registration'}</button><button type="button" className="button outline" onClick={()=>setOpen(false)}>Cancel</button></div></form></section></div>}</main>}
const authSchema=z.object({email:z.email('Enter a valid email.'),password:z.string().min(8,'Use at least 8 characters.')});
function GoogleIcon(){
 return <svg width="18" height="18" viewBox="0 0 24 24" style={{marginRight:'10px',flexShrink:0}}>
  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
 </svg>;
}

function Auth({mode}:{mode:string}){
 const {demo,user,setUser,toast}=useWoc();
 const [method,setMethod]=useState<'email'|'mobile'>('email');
 const [googleAvailable,setGoogleAvailable]=useState(false);
 useEffect(()=>{if(demo){setGoogleAvailable(true);return}if(['login','register'].includes(mode))api('/auth/google/url/').then(d=>setGoogleAvailable(!!d.configured)).catch(()=>setGoogleAvailable(false))},[demo,mode]);
 const [error,setError]=useState(''),[success,setSuccess]=useState(''),[verification,setVerification]=useState(''),[busy,setBusy]=useState(false);
 const [resendEmail,setResendEmail]=useState(''),[resendMsg,setResendMsg]=useState(''),[resendError,setResendError]=useState(''),[resendCooldown,setResendCooldown]=useState(0),[resendBusy,setResendBusy]=useState(false);
 const [linkTicket,setLinkTicket]=useState('');
 const [googleCode,setGoogleCode]=useState(''),[showLinkPassword,setShowLinkPassword]=useState(false),[linkEmail,setLinkEmail]=useState(''),[linkPassword,setLinkPassword]=useState('');
 const [forgotEmail,setForgotEmail]=useState(''),[forgotCooldown,setForgotCooldown]=useState(0);
 const [newPassword,setNewPassword]=useState(''),[confirmPassword,setConfirmPassword]=useState(''),[resetToken,setResetToken]=useState('');
 const {register,handleSubmit,formState:{errors}}=useForm<z.infer<typeof authSchema>>({resolver:zodResolver(authSchema)});

 useEffect(()=>{
  if(resendCooldown<=0)return;
  const timer=setInterval(()=>setResendCooldown(c=>Math.max(0,c-1)),1000);
  return()=>clearInterval(timer);
 },[resendCooldown]);

 useEffect(()=>{
  if(forgotCooldown<=0)return;
  const timer=setInterval(()=>setForgotCooldown(c=>Math.max(0,c-1)),1000);
  return()=>clearInterval(timer);
 },[forgotCooldown]);

 useEffect(()=>{
  if(mode==='reset-password'&&typeof window!=='undefined'){
   const params=new URLSearchParams(window.location.search);
   const t=params.get('token');
   if(t) setResetToken(t);
  }
 },[mode]);

 useEffect(()=>{
  if(mode==='verify'&&typeof window!=='undefined'){
   const params=new URLSearchParams(window.location.search);
   if(params.get('google_callback')==='true'){
    const code=params.get('code');
    const err=params.get('error');
    if(err){setError(err==='access_denied'?'Google sign-in was cancelled.':`Google sign-in error: ${err}`);return}
    if(code){setGoogleCode(code);processGoogleCode(code)}
    return;
   }
   const token=params.get('token');
   if(token&&!success&&!error&&!busy){verify(token)}
  }
 },[mode]);

 async function processGoogleCode(code:string,linkPwd?:string){
  setBusy(true);setError('');setSuccess('');
  try{
   const redirect_uri=window.location.origin+'/verify/?google_callback=true';
   const payload:Record<string,string>=linkPwd&&linkTicket?{link_token:linkTicket}:{code,redirect_uri,state:new URLSearchParams(window.location.search).get('state')||''};
   if(linkPwd)payload.link_password=linkPwd;
   const d=await api('/auth/google/','POST',payload);
   setUser(d.user);
   toast(d.action==='created'?'Welcome to WOC! Account created with Google.':'Signed in with Google.');
   window.location.href='/dashboard/';
  }catch(err:any){
   if(err.data?.action==='require_link_password'){
    setLinkTicket(err.data.link_token);setLinkEmail(err.data.email);
    setShowLinkPassword(true);
   }
   setError(err.message||'Google authentication failed.');
  }finally{setBusy(false)}
 }

 async function handleGoogleLogin(){
  setBusy(true);setError('');
  try{
   if(demo){
    setUser({id:2,name:'Google Student',email:'student.google@example.com',institution:'Campus University',age:20,bio:'Signed in via Google account.',roles:['student'],is_staff:false,email_verified:true,auth_provider:'google'});
    toast('Demo session started via Google.');
    window.location.href='/dashboard/';
    return;
   }
   const d=await api('/auth/google/url/');
   if(d.url){
    window.location.href=d.url;
   }else{
    setError(d.error||'Google sign-in is not configured yet. Please sign in with email and password.');
   }
  }catch(err:any){
   setError(err.message||'Failed to initialize Google login.');
  }finally{setBusy(false)}
 }

 async function submit(data:z.infer<typeof authSchema>,e?:React.BaseSyntheticEvent){
  setBusy(true);setError('');setSuccess('');setResendMsg('');setResendError('');
  try{
   if(demo){
    setUser({id:1,name:mode==='register'?new FormData(e?.target).get('name') as string:'Demo Student',email:data.email,institution:'',age:18,bio:'',roles:['student'],is_staff:false,email_verified:true});
    toast('Demo session started. No account was created on a server.');
    window.location.href='/dashboard/';
    return;
   }
   if(mode==='register'){
    const f=Object.fromEntries(new FormData(e?.target));
    const d=await api('/register/','POST',{...f,...data,age:Number(f.age),terms:!!f.terms,guardian_consent:!!f.guardian_consent});
    setSuccess(d.message);
    if(d.delivery_status==='failed')setError(d.delivery_error);
    setResendEmail(data.email);
    setVerification(d.development_verification_url||'');
   }else{
    const d=await api('/login/','POST',{...data,otp:new FormData(e?.target).get('otp')});
    setUser(d.user);
    window.location.href='/dashboard/';
   }
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 async function handleForgotSubmit(e:React.FormEvent){
  e.preventDefault();
  if(!forgotEmail||forgotCooldown>0)return;
  setBusy(true);setError('');setSuccess('');setVerification('');
  try{
   if(demo){
    setSuccess('If an account exists with this email address, a password reset link has been sent.');
    setVerification('/reset-password/?token=demo-token-12345');
    setForgotCooldown(60);
    toast('Demo reset link prepared.');
    return;
   }
   const d=await api('/password-reset/request/','POST',{email:forgotEmail});
   setSuccess(d.message);
   setForgotCooldown(60);
   if(d.development_reset_url)setVerification(d.development_reset_url);
  }catch(err:any){
   setError(err.message||'Failed to send password reset email.');
  }finally{setBusy(false)}
 }

 async function handleResetSubmit(e:React.FormEvent){
  e.preventDefault();
  if(!resetToken){setError('A password reset token is required.');return}
  if(newPassword.length<8){setError('Password must be at least 8 characters long.');return}
  if(newPassword!==confirmPassword){setError('Passwords do not match.');return}
  setBusy(true);setError('');setSuccess('');
  try{
   if(demo){
    setSuccess('Your password has been successfully reset. You can now sign in with your new password.');
    toast('Demo password reset successful.');
    return;
   }
   const d=await api('/password-reset/confirm/','POST',{
    token:resetToken,
    password:newPassword,
    confirm_password:confirmPassword
   });
   setSuccess(d.message);
   toast('Password updated successfully.');
  }catch(err:any){
   setError(err.message||'Failed to reset password.');
  }finally{setBusy(false)}
 }

 async function verify(tokenOverride?:string){
  const token=tokenOverride||new URLSearchParams(window.location.search).get('token');
  if(!token){setError('No verification token provided. Request a fresh verification link below.');return}
  setBusy(true);setError('');
  try{
   const d=await api('/verify/','POST',{token});
   setSuccess(d.message);
   if(d.email)setResendEmail(d.email);
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 async function handleResend(e:React.FormEvent){
  e.preventDefault();
  if(!resendEmail||resendCooldown>0)return;
  setResendBusy(true);setResendError('');setResendMsg('');
  try{
   const d=await api('/resend-verification/','POST',{email:resendEmail});
   setResendMsg(d.message);
   setResendCooldown(60);
   if(d.development_verification_url)setVerification(d.development_verification_url);
  }catch(e){setResendError((e as Error).message)}finally{setResendBusy(false)}
 }

 return <main id="main" className={`auth-page auth-refresh ${mode==='register'?'register-page':''}`}>
  <div className="auth-image">
   <img src="/images/campus-hero.webp" alt="Illustrative WOC student community"/>
   <div><Eyebrow>BE THE CHANGE.</Eyebrow><h2>Your next chapter<br/>starts with you.</h2></div>
  </div>
  <section className="auth-form"><div className="auth-panel">
   <Eyebrow>WELCOME TO THE WOC</Eyebrow>
   <h1>{mode==='register'?'Find your place.':mode==='verify'?'Email verification.':mode==='forgot-password'?'Reset your password.':mode==='reset-password'?'Set new password.':'Good to see you.'}</h1>
   <p>{demo?'Showcase mode: use any email and an 8-character password to explore. Do not enter a real password.':mode==='register'?(method==='mobile'?'Create your student account with a mobile verification code.':'Create your student account. Verify your email before signing in.'):mode==='verify'?'Confirming your student credentials.':mode==='forgot-password'?'Enter your registered email address and we will send you a secure link to reset your password.':mode==='reset-password'?'Choose a strong, secure password for your WOC student account.':method==='mobile'?'Sign in with a code sent to your verified mobile number.':'Sign in to your WOC account.'}</p>
   {user&&<Link href="/dashboard/" className="text-link">Continue to dashboard</Link>}
   {mode==='verify'?(
    <div>
     {busy&&<p className="notice">Verifying credentials…</p>}
     {showLinkPassword?(
      <div className="panel" style={{marginTop:'16px'}}>
       <h3>Link Your WOC Account</h3>
       <p style={{fontSize:'13px',color:'var(--muted)'}}>
        An account with this email already exists on THE WOC. Please enter your existing password to verify ownership and securely link your Google account.
       </p>
       <form onSubmit={e=>{e.preventDefault();processGoogleCode(googleCode,linkPassword)}}>
        <label>WOC Account Password
         <input type="password" required value={linkPassword} onChange={e=>setLinkPassword(e.target.value)} autoFocus placeholder="Enter existing password"/>
        </label>
        {error&&<p className="form-error" role="alert">{error}</p>}
        <button className="button full" disabled={busy||!linkPassword}>
         {busy?'Linking…':'Verify & Link Google Account'}
        </button>
       </form>
      </div>
     ):success?(
      <div className="success-box" role="status">
       <CheckCircle size={20}/>
       <div>
        <strong>{success}</strong>
        <p style={{margin:'6px 0 0'}}>Your account is active. You can now access all learning programs, campus events, and student resources.</p>
        <div style={{marginTop:'14px'}}><Link href="/login/" className="button small">Sign in to your account</Link></div>
       </div>
      </div>
     ):(
      <>
       {error&&<p className="form-error" role="alert">{error}</p>}
       {!busy&&<div className="panel" style={{marginTop:'16px'}}>
        <h3>Request fresh verification link</h3>
        <p style={{fontSize:'13px',color:'var(--muted)'}}>Verification links expire after 24 hours and can only be used once.</p>
        <form onSubmit={handleResend}>
         <label>Email address<input type="email" required value={resendEmail} onChange={e=>setResendEmail(e.target.value)} placeholder="student@example.com"/></label>
         <button className="button" disabled={resendBusy||resendCooldown>0}>
          {resendBusy?'Sending…':resendCooldown>0?`Resend in ${resendCooldown}s`:'Send verification email'}
         </button>
        </form>
        {resendMsg&&<p className="success-box" style={{marginTop:'12px'}} role="status">{resendMsg}</p>}
        {resendError&&<p className="form-error" style={{marginTop:'12px'}} role="alert">{resendError}</p>}
        {verification&&<p style={{marginTop:'10px'}}><a className="text-link" href={verification}>Local development: open verification link</a></p>}
       </div>}
      </>
     )}
    </div>
   ):mode==='forgot-password'?(
    <div>
     {success?(
      <div className="success-box" role="status">
       <CheckCircle size={20}/>
       <div>
        <strong>Check your email</strong>
        <p style={{margin:'6px 0 0',fontSize:'13px'}}>{success}</p>
        {verification&&<p style={{marginTop:'8px'}}><a className="text-link" href={verification}>Local development: open reset link</a></p>}
        <div style={{marginTop:'14px'}}>
         <Link href="/login/" className="button small">Back to sign in</Link>
        </div>
       </div>
      </div>
     ):(
      <form onSubmit={handleForgotSubmit}>
       <label>Email address
        <input type="email" required value={forgotEmail} onChange={e=>setForgotEmail(e.target.value)} placeholder="student@example.com" autoFocus/>
       </label>
       {error&&<p className="form-error" role="alert">{error}</p>}
       <button className="button full" disabled={busy||forgotCooldown>0}>
        {busy?'Sending…':forgotCooldown>0?`Resend in ${forgotCooldown}s`:'Send password reset link'}
       </button>
      </form>
     )}
    </div>
   ):mode==='reset-password'?(
    <div>
     {success?(
      <div className="success-box" role="status">
       <CheckCircle size={20}/>
       <div>
        <strong>Password Reset Complete</strong>
        <p style={{margin:'6px 0 0',fontSize:'13px'}}>{success}</p>
        <div style={{marginTop:'14px'}}>
         <Link href="/login/" className="button small">Sign in to your account</Link>
        </div>
       </div>
      </div>
     ):(
      <form onSubmit={handleResetSubmit}>
       {!resetToken&&(
        <label>Reset token
         <input type="text" required value={resetToken} onChange={e=>setResetToken(e.target.value)} placeholder="Paste your reset token"/>
        </label>
       )}
       <label>New password
        <input type="password" required minLength={8} value={newPassword} onChange={e=>setNewPassword(e.target.value)} placeholder="At least 8 characters" autoComplete="new-password"/>
       </label>
       <label>Confirm new password
        <input type="password" required minLength={8} value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)} placeholder="Confirm new password" autoComplete="new-password"/>
       </label>
       {newPassword&&confirmPassword&&newPassword!==confirmPassword&&(
        <p className="form-error" style={{fontSize:'12px',marginTop:'-6px'}}>Passwords do not match.</p>
       )}
       {error&&<p className="form-error" role="alert">{error}</p>}
       <button className="button full" disabled={busy||!newPassword||!confirmPassword||newPassword!==confirmPassword}>
        {busy?'Updating…':'Reset password'}
       </button>
      </form>
     )}
    </div>
   ):(
    <div className="auth-methods">
     <div className="auth-method-tabs" role="tablist" aria-label="Sign-in method">
      <button type="button" role="tab" aria-selected={method==='email'} onClick={()=>{setMethod('email');setError('')}}>Email</button>
      <button type="button" role="tab" aria-selected={method==='mobile'} onClick={()=>{setMethod('mobile');setError('')}}>Mobile OTP</button>
     </div>
     {method==='mobile'?<MobileAuthForm key={mode} mode={mode==='register'?'register':'login'}/>:<>
     {googleAvailable&&<><button type="button" className="google-btn" disabled={busy} onClick={handleGoogleLogin}>
      <GoogleIcon/> Continue with Google
     </button>
     <div className="auth-divider"><span>or continue with email</span></div></>}
     <form className={`auth-email-form ${mode==='register'?'auth-register-form':''}`} onSubmit={handleSubmit(submit)}>
      {mode==='register'&&<><label>Full name<input name="name" required autoComplete="name"/></label><div className="two-grid"><label>Age<input name="age" type="number" min={13} max={100} required/></label><label>Institution<input name="institution" required/></label></div></>}
      <label>Email address<input {...register('email')} type="email" autoComplete="email"/>{errors.email&&<span className="form-error">{errors.email.message}</span>}</label>
      <div className="auth-password-field" style={{marginBottom:'16px'}}>
       <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'4px'}}>
        <label htmlFor="auth-password" className="auth-password-label">Password</label>
        {mode==='login'&&<Link href="/forgot-password/" className="text-link" style={{fontSize:'12px'}}>Forgot password?</Link>}
       </div>
       <input id="auth-password" {...register('password')} type="password" autoComplete={mode==='register'?'new-password':'current-password'}/>
       {errors.password&&<span className="form-error">{errors.password.message}</span>}
      </div>
      {mode==='login'&&<details className="auth-staff"><summary>Staff sign-in</summary><label>Authenticator code<input name="otp" inputMode="numeric" autoComplete="one-time-code" placeholder="6-digit authenticator code"/></label></details>}
      {mode==='register'&&<><label className="checkbox"><input name="guardian_consent" type="checkbox"/>For under-18 participation, I confirm school and guardian permission. Live participation requires separate verification.</label><label className="checkbox"><input name="terms" type="checkbox" required/>I agree to the <Link href="/terms/">Terms</Link> and <Link href="/privacy/">Privacy Notice</Link>.</label></>}
      <button className="button full" disabled={busy}>{busy?'Please wait…':demo?'Enter demo account':mode==='register'?'Create account':'Sign in'}</button>
     </form>
     </>}
    </div>
   )}
   {error&&mode!=='verify'&&mode!=='forgot-password'&&mode!=='reset-password'&&<p className="form-error" role="alert">{error}</p>}
   {success&&mode==='register'&&(
    <div className="success-box" role="status" style={{marginTop:'16px'}}>
     <CheckCircle size={20}/>
     <div>
      <strong>{success}</strong>
      <p style={{margin:'6px 0 0',fontSize:'13px'}}>Please check your inbox and click the verification link to activate your account.</p>
      {verification&&<p style={{marginTop:'8px'}}><a className="text-link" href={verification}>Local development: open verification link</a></p>}
      <div style={{marginTop:'12px',borderTop:'1px solid rgba(0,0,0,0.08)',paddingTop:'10px'}}>
       <p style={{fontSize:'12px',color:'var(--muted)',margin:'0 0 6px'}}>Didn't receive the email?</p>
       <button type="button" className="button outline small" disabled={resendBusy||resendCooldown>0} onClick={handleResend}>
        {resendBusy?'Sending…':resendCooldown>0?`Wait ${resendCooldown}s`:'Resend verification email'}
       </button>
       {resendMsg&&<p style={{fontSize:'12px',color:'var(--crimson)',margin:'6px 0 0'}}>{resendMsg}</p>}
      </div>
     </div>
    </div>
   )}
   <p>{mode==='forgot-password'||mode==='reset-password'?<>Remember your password? <Link className="text-link" href="/login/">Sign in</Link></>:mode==='register'?'Already a member? ':'New to WOC? '} {mode!=='forgot-password'&&mode!=='reset-password'&&<Link className="text-link" href={mode==='register'?'/login/':'/register/'}>{mode==='register'?'Sign in':'Join the community'}</Link>}</p>
  </div></section>
 </main>;
}
function NotificationsView({notifications,refetch}:{notifications:any;refetch:()=>void}){
 const {demo,toast}=useWoc();
 const [busy,setBusy]=useState(false);
 const unreadCount=demo?1:(notifications?.unread_count||0);
 const items=demo?[{id:1,message:'Welcome to THE WOC student community! Explore programs in the Academy or register for campus events.',read:false,created_at:new Date().toISOString()}]:(notifications?.results||[]);

 async function markAll(){
  if(demo){toast('Marked all as read in demo mode.');return}
  setBusy(true);
  try{
   await api('/notifications/','PATCH',{all:true});
   refetch();
   toast('All notifications marked as read.');
  }catch(e:any){toast(e.message||'Failed to mark notifications as read.')}
  finally{setBusy(false)}
 }

 async function markSingle(id:number){
  if(demo){toast('Marked as read.');return}
  try{
   await api('/notifications/','PATCH',{id});
   refetch();
  }catch{}
 }

 return <div className="notifications-container">
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'20px'}}>
   <div>
    <h2 style={{margin:0,fontSize:'22px'}}>All Notifications</h2>
    <p style={{margin:'4px 0 0',fontSize:'13px',color:'var(--muted)'}}>
     {unreadCount>0?`You have ${unreadCount} unread update${unreadCount>1?'s':''}.`:'All notifications are up to date.'}
    </p>
   </div>
   {unreadCount>0&&(
    <button className="button outline small" disabled={busy} onClick={markAll}>
     Mark all as read
    </button>
   )}
  </div>
  {items.length>0?(
   <div className="notification-list">
    {items.map((n:{id:number;message:string;read:boolean;created_at?:string})=>(
     <div key={n.id} className={`notification-card ${!n.read?'unread':''}`}>
      <div style={{flex:1}}>
       <div style={{display:'flex',alignItems:'center',gap:'6px',marginBottom:'6px'}}>
        {!n.read&&<span className="notification-dot" title="Unread"/>}
        <strong style={{fontSize:'14px',color:'var(--ink)'}}>{n.message}</strong>
       </div>
       {n.created_at&&(
        <small style={{color:'var(--muted)',fontSize:'12px'}}>
         {new Date(n.created_at).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}
        </small>
       )}
      </div>
      {!n.read&&(
       <button
        type="button"
        className="button outline small"
        style={{fontSize:'11px',padding:'4px 10px',flexShrink:0}}
        onClick={()=>markSingle(n.id)}
       >
        Mark read
       </button>
      )}
     </div>
    ))}
   </div>
  ):(
   <Empty title="You’re all caught up." text="Updates about your course enrollments, event registrations, and campus opportunities will appear here."/>
  )}
 </div>;
}

function Dashboard(){const {user,demo,records,refresh,setUser,toast}=useWoc();const [tab,setTab]=useState('Overview');const [selected,setSelected]=useState<Registration|null>(null);const {data:notifications,refetch:refetchNotifications}=useQuery({queryKey:['notifications',user?.id],queryFn:()=>api('/notifications/'),enabled:!!user&&!demo});useEffect(()=>{if(user)refresh()},[user]);if(!user)return <main id="main" className="section container empty-state"><Users/><h1>Your WOC account.</h1><p>Sign in to view your courses, applications and registrations.</p><Link href="/login/" className="button">Sign in</Link></main>;const mapping:Record<string,string>={'My Courses':'academy','My Applications':'careers','My Events':'events','My Sports':'sports','My Culturals':'culturals','My Chapters':'association','My Startups':'incubation','My Partnerships':'partnerships'};const filtered=tab==='Overview'?records:records.filter(r=>r.program.module===mapping[tab]);return <main id="main" className="dashboard"><aside className="dashboard-nav"><p className="eyebrow">MY WOC</p>{['Overview',...Object.keys(mapping),'Certificates','Notifications','Settings'].map(t=><button aria-current={tab===t?'page':undefined} key={t} onClick={()=>{setTab(t);setSelected(null)}}>{t}{t==='Notifications'&&(notifications?.unread_count||0)>0&&<span className="tab-badge">{notifications.unread_count}</span>}</button>)}{user.is_staff&&<Link href="/admin/">Administration</Link>}<button onClick={async()=>{if(!demo)await api('/logout/','POST');setUser(null);toast('Signed out.')}}>Sign out</button></aside><div className="dashboard-body"><Eyebrow>{demo?'BROWSER DEMO ACCOUNT':'STUDENT DASHBOARD'}</Eyebrow><h1>{tab==='Overview'?`Hello, ${user.name.split(' ')[0]}.`:tab}</h1><p>Your learning, applications and campus experiences, together.</p>{selected?<Learning record={selected} close={()=>setSelected(null)}/>:tab==='Settings'?<ProfileForm/>:tab==='Certificates'?<div className="record-list">{records.filter(r=>r.certificate).map(r=><div className="record" key={r.id}><h3>{r.program.title}</h3><Link href={`/certificate/?id=${r.certificate}`}>Verify certificate</Link></div>)}{!records.some(r=>r.certificate)&&<Empty title="No certificates yet." text="Certificates appear after a passing assessment and staff approval."/>}</div>:tab==='Notifications'?<NotificationsView notifications={notifications} refetch={refetchNotifications}/>:<><div className="dashboard-stats"><div><strong>{records.filter(r=>r.program.module==='academy').length}</strong><span>Learning registrations</span></div><div><strong>{records.filter(r=>r.program.module==='events').length}</strong><span>Event registrations</span></div><div><strong>{records.filter(r=>r.certificate).length}</strong><span>Issued certificates</span></div></div><div className="record-list">{filtered.map(r=><div className="record" key={r.id}><div><span className="label">{r.program.module}</span><h3>{r.program.title}</h3><p>{r.status.replaceAll('_',' ')} · {new Date(r.created_at).toLocaleDateString('en-IN')}</p><small>Reference: {r.id}</small></div>{r.program.module==='academy'?<button className="button outline small" onClick={()=>setSelected(r)}>My learning</button>:<Link className="text-link" href={`/${r.program.module}/${r.program.slug}/`}>View details</Link>}</div>)}{!filtered.length&&<Empty title="Your next experience is waiting." text="Explore a program and register to see it here."/>}</div><Link href="/academy/" className="button">Explore learning</Link></>}</div></main>}
function Empty({title,text}:{title:string;text:string}){return <div className="empty-state"><BookOpen size={32}/><h2>{title}</h2><p>{text}</p></div>}
function ProfileForm(){
 const {user,setUser,demo,toast}=useWoc();
 return <div>
  <form className="panel form-stack" onSubmit={async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));try{if(demo)setUser({...user!,...data} as typeof user);else setUser((await api('/me/','PATCH',data)).user);toast('Profile updated.')}catch(e){toast((e as Error).message)}}}><label>Name<input name="name" defaultValue={user?.name} required/></label><label>Institution<input name="institution" defaultValue={user?.institution}/></label><label>About you<textarea name="bio" defaultValue={user?.bio} maxLength={2000}/></label><button className="button">Save profile</button></form>
  <PhoneVerification/>
 </div>;
}

function PhoneVerification(){
 const {user,setUser,demo,toast}=useWoc();
 const [phone,setPhone]=useState(user?.phone_number||'');
 const [countryCode,setCountryCode]=useState('+91');
 const [challengeId,setChallengeId]=useState('');
 const [otp,setOtp]=useState('');
 const [step,setStep]=useState<'idle'|'otp_sent'|'verified'>(user?.phone_verified?'verified':'idle');
 const [cooldown,setCooldown]=useState(0);
 const [expiresIn,setExpiresIn]=useState(300);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [msg,setMsg]=useState('');
 const [devOtp,setDevOtp]=useState('');

 useEffect(()=>{
  if(user?.phone_verified){setStep('verified')}
 },[user?.phone_verified]);

 useEffect(()=>{
  if(cooldown<=0)return;
  const t=setInterval(()=>setCooldown(c=>Math.max(0,c-1)),1000);
  return()=>clearInterval(t);
 },[cooldown]);

 useEffect(()=>{
  if(step!=='otp_sent'||expiresIn<=0)return;
  const t=setInterval(()=>setExpiresIn(c=>Math.max(0,c-1)),1000);
  return()=>clearInterval(t);
 },[step,expiresIn]);

 async function sendOtp(e?:React.FormEvent){
  if(e)e.preventDefault();
  if(!phone||cooldown>0)return;
  setBusy(true);setError('');setMsg('');setDevOtp('');
  try{
   if(demo){
    setChallengeId('demo-challenge');
    setStep('otp_sent');
    setCooldown(60);
    setExpiresIn(300);
    setMsg('Demo OTP sent: use 123456 to verify.');
    setDevOtp('123456');
    return;
   }
   const d=await api('/phone/send-otp/','POST',{phone,country_code:countryCode});
   setChallengeId(d.challenge_id);
   setStep('otp_sent');
   setCooldown(60);
   setExpiresIn(d.expires_in||300);
   setMsg(d.message);
   if(d.development_otp)setDevOtp(d.development_otp);
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 async function verifyOtp(e:React.FormEvent){
  e.preventDefault();
  if(!otp||otp.length!==6)return;
  setBusy(true);setError('');setMsg('');
  try{
   if(demo){
    if(otp==='123456'){
     setUser({...user!,phone_number:phone,phone_verified:true});
     setStep('verified');
     toast('Phone verified (Demo mode).');
     return;
    }else{throw new Error('Incorrect demo OTP. Enter 123456.')}
   }
   const d=await api('/phone/verify-otp/','POST',{challenge_id:challengeId,otp});
   setUser({...user!,phone_number:d.phone,phone_verified:true});
   setStep('verified');
   toast('Mobile number verified successfully.');
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }

 return <div className="panel" style={{marginTop:'24px'}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'14px'}}>
   <h3 style={{margin:0}}>Mobile Number Verification</h3>
   {step==='verified'?(
    <span className="badge-verified"><CheckCircle size={14}/> Verified</span>
   ):(
    <span className="badge-unverified">Unverified</span>
   )}
  </div>
  <p style={{fontSize:'13px',color:'var(--muted)',marginTop:0}}>
   Verify your mobile number to receive timely updates on sports matches, cultural auditions, and hackathons via SMS.
  </p>
  {step==='verified'?(
   <div className="success-box">
    <CheckCircle size={18}/>
    <div>
     <strong>Verified mobile number: {user?.phone_number}</strong>
     <p style={{fontSize:'12px',margin:'4px 0 0'}}>Your mobile is securely linked to your WOC account.</p>
     <button type="button" className="text-link" style={{marginTop:'8px',fontSize:'12px'}} onClick={()=>setStep('idle')}>Change mobile number</button>
    </div>
   </div>
  ):step==='idle'?(
   <form onSubmit={sendOtp} className="form-stack">
    <label>Mobile Number
     <div className="phone-input-row">
      <select value={countryCode} onChange={e=>setCountryCode(e.target.value)}>
       <option value="+91">+91 (IN)</option>
       <option value="+1">+1 (US)</option>
       <option value="+44">+44 (UK)</option>
       <option value="+971">+971 (UAE)</option>
       <option value="+65">+65 (SG)</option>
      </select>
      <input type="tel" required value={phone} onChange={e=>setPhone(e.target.value)} placeholder="Enter 10-digit mobile number" maxLength={15}/>
     </div>
    </label>
    {error&&<p className="form-error" role="alert">{error}</p>}
    <button className="button" disabled={busy||!phone}>
     {busy?'Sending OTP…':'Send Verification OTP'}
    </button>
   </form>
  ):(
   <div className="otp-card">
    <h4>Enter 6-Digit Verification Code</h4>
    <p style={{fontSize:'13px',color:'var(--muted)'}}>
     We sent a 6-digit OTP to <strong>{phone}</strong>.
    </p>
    {msg&&<p className="notice" style={{fontSize:'13px'}}>{msg}</p>}
    {devOtp&&<p className="notice" style={{fontSize:'13px',color:'#0066cc'}}>Test mode OTP: <strong>{devOtp}</strong></p>}
    <form onSubmit={verifyOtp} className="form-stack">
     <label>6-Digit OTP
      <input type="text" inputMode="numeric" required maxLength={6} pattern="[0-9]{6}" value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,''))} placeholder="123456" autoFocus style={{fontSize:'20px',letterSpacing:'6px',textAlign:'center',maxWidth:'240px'}}/>
     </label>
     <div className="otp-timer">
      <Clock size={15}/>
      {expiresIn>0?(
       <span>OTP expires in: {Math.floor(expiresIn/60)}:{(expiresIn%60).toString().padStart(2,'0')}</span>
      ):(
       <span style={{color:'var(--crimson)'}}>OTP has expired. Please resend code.</span>
      )}
     </div>
     {error&&<p className="form-error" role="alert">{error}</p>}
     <div style={{display:'flex',gap:'12px',alignItems:'center'}}>
      <button className="button" disabled={busy||otp.length!==6||expiresIn<=0}>
       {busy?'Verifying…':'Verify OTP'}
      </button>
      <button type="button" className="button outline small" disabled={busy||cooldown>0} onClick={sendOtp}>
       {cooldown>0?`Resend in ${cooldown}s`:'Resend OTP'}
      </button>
      <button type="button" className="text-link" style={{fontSize:'13px',marginLeft:'auto'}} onClick={()=>{setStep('idle');setOtp('')}}>Cancel</button>
     </div>
    </form>
   </div>
  )}
 </div>;
}
function Learning({record:r,close}:{record:Registration;close:()=>void}){const {demo,refresh,toast}=useWoc();const [lessons,setLessons]=useState<number[]>((r.data.lessons as number[])||[]);const [active,setActive]=useState(0);const questions=[{q:'What makes a project goal useful?',a:['It is broad and vague.','It names a clear outcome.','It uses many buzzwords.']},{q:'How should you handle feedback?',a:['Consider it and test improvements.','Ignore it.','Hide the project.']},{q:'What belongs in a project presentation?',a:['Only a title.','Only a certificate.','The problem, approach and evidence.']}];return <section className="panel learning"><button className="text-link" onClick={close}>Back to dashboard</button><h2>{r.program.title}</h2>{demo&&<p className="notice">Preview lesson viewer. Progress and assessment submission require the local Django backend.</p>}<div className="lesson-tabs">{['Understand','Practice','Build'].map((t,i)=><button key={t} aria-pressed={active===i} onClick={()=>setActive(i)}>{lessons.includes(i)?'✓ ':''}{t}</button>)}</div><h3>{['Start with a clear problem','Practice deliberately','Show what you built'][active]}</h3><p>{['Choose one person you want to help. Write down their problem, the context and a measurable goal. Avoid jumping to a solution before understanding the need.','Create a small exercise related to your goal. Record your assumptions, try one approach and ask a peer for feedback. Explain what worked and what you would improve.','Turn your practice into a small deliverable. Describe the problem, the approach, your evidence and one next step. This demonstration curriculum is intended to exercise the platform workflow.'][active]}</p><button className="button outline" disabled={demo} onClick={async()=>{try{const d=await api(`/learning/${r.id}/`,'POST',{action:'lesson',lesson:active});setLessons(d.data.lessons);await refresh();toast('Lesson completed.')}catch(e){toast((e as Error).message)}}}>{lessons.includes(active)?'Lesson completed':'Mark lesson complete'}</button><h3 className="subheading">Assessment & project</h3><form onSubmit={async e=>{e.preventDefault();const d=new FormData(e.currentTarget);try{await api(`/learning/${r.id}/`,'POST',{action:'assessment',answers:questions.map((_,i)=>Number(d.get('q'+i))),project:d.get('project')});await refresh();toast('Assessment saved. Passing submissions go to staff review.');close()}catch(e){toast((e as Error).message)}}}>{questions.map((q,i)=><fieldset key={q.q}><legend>{q.q}</legend>{q.a.map((a,n)=><label className="checkbox" key={a}><input type="radio" name={'q'+i} value={n} required/>{a}</label>)}</fieldset>)}<label>Project description<textarea name="project" minLength={30} required placeholder="Describe your problem, approach and result…"/></label><button className="button" disabled={demo||lessons.length<3}>Submit assessment for review</button></form></section>}
function Admin(){const {user,demo,toast}=useWoc();const {data,refetch,isLoading}=useQuery({queryKey:['admin-records'],queryFn:()=>api('/admin/records/'),enabled:!!user?.is_staff&&!demo});if(!user?.is_staff)return <main id="main" className="section container"><h1>Administration</h1><p>This area requires an authorised staff account. Roles are enforced by the backend.</p><Link href="/login/" className="button">Sign in</Link></main>;return <main id="main" className="section container"><Eyebrow>AUTHORISED STAFF</Eyebrow><h1>Applications & approvals</h1><p>Every status change is recorded in the audit log.</p>{isLoading&&<p>Loading applications…</p>}{data?.results?.map((r:Registration)=><div className="record" key={r.id}><div><h3>{r.program.title}</h3><p>{r.student} · {r.email} · {r.status}</p><details><summary>Submitted details</summary><pre>{JSON.stringify(r.data,null,2)}</pre></details></div><select aria-label={`Update ${r.student} application`} value="" onChange={async e=>{try{await api('/admin/records/','PATCH',{id:r.id,status:e.target.value});refetch();toast('Status updated.')}catch(e){toast((e as Error).message)}}}><option value="">Update status</option>{['approved','rejected','enrolled','shortlisted','completed'].map(s=><option key={s}>{s}</option>)}</select></div>)}<h2 className="subheading">Enquiries</h2>{data?.enquiries?.map((d:{id:number;name:string;email:string;message:string})=><div className="record" key={d.id}><div><h3>{d.name}</h3><p>{d.email}</p><p>{d.message}</p></div></div>)}<a href="http://localhost:8317/admin/" className="text-link">Open Django content administration</a></main>}
function Contact(){const {demo,toast}=useWoc();const [sent,setSent]=useState(false);return <main id="main"><PageHero label="Contact WOC" title="Let’s start a conversation." text="A college pilot, a student question or an industry collaboration. Tell us what you have in mind."/><section className="container section split"><div><Eyebrow>BUILD WITH US</Eyebrow><h2>A clear first step.<br/>A meaningful connection.</h2><p>Share your context and the outcome you would like to explore. Contact details will be published after the WOC team confirms its official channels.</p><div className="value-line"><HeartHandshake/><div><h3>Colleges & institutions</h3><p>Discuss a defined campus pilot.</p></div></div><div className="value-line"><Briefcase/><div><h3>Employers & partners</h3><p>Explore student projects, mentoring or program support.</p></div></div></div><form className="panel" onSubmit={async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));try{if(demo){const saved=JSON.parse(localStorage.getItem('woc-demo-enquiries')||'[]');localStorage.setItem('woc-demo-enquiries',JSON.stringify([...saved,data]));toast('Sample enquiry saved in this browser; it has not been sent.')}else{await api('/enquiries/','POST',data);toast('Enquiry saved for the WOC team.')}setSent(true)}catch(e){toast((e as Error).message)}}}>{sent?<div className="success-box"><CheckCircle/>Thank you. {demo?'Your sample enquiry is stored locally.':'Your enquiry has been recorded.'}</div>:<><label>Your name<input name="name" required/></label><label>Email address<input name="email" type="email" required/></label><label>I’m interested in<select name="kind"><option>College partnership</option><option>Student membership</option><option>Employer collaboration</option><option>Mentorship</option><option>Events & campus life</option><option>Other enquiry</option></select></label><label>Your message<textarea name="message" required minLength={10} rows={5}/></label><label className="checkbox"><input type="checkbox" required/>I agree to the privacy notice and being contacted about this enquiry.</label><button className="button">{demo?'Save sample enquiry':'Send enquiry'}</button></>}</form></section></main>}
function About(){return <main id="main" className="feature-reference"><PageHero label="About WOC" title="Be the Change." text="A student-to-industry ecosystem built around knowledge, networks and the courage to begin."/><section className="section container split"><img className="rounded-image" src="/images/innovation-lab.webp" alt="Illustrative students developing an idea"/><div><Eyebrow>OUR PURPOSE</Eyebrow><h2>Connect ambition<br/>with possibility.</h2><p>WOC’s proposed model brings practical learning, campus communities, career pathways and innovation into a coordinated student experience.</p><p>We are beginning with a Chennai-focused pilot approach. Institutions, employers and program partners will be represented as confirmed partners only after agreement.</p><ul className="checklist"><li><Check/>Student participation with clear expectations.</li><li><Check/>Learning backed by projects and feedback.</li><li><Check/>Truthful opportunity and outcome reporting.</li></ul></div></section><section className="section pale"><div className="container"><Title label="OUR APPROACH" title="One community. Different pathways."/><div className="three-grid about-audience"><div className="panel"><img className="panel-photo" src="/images/school-discovery.webp" alt="Learning community" loading="lazy"/><Users/><h3>School students</h3><p>Discovery and creativity, with school involvement, guardian permission and separate safeguarding.</p></div><div className="panel"><img className="panel-photo" src="/images/course-python.webp" alt="Students building practical skills" loading="lazy"/><BookOpen/><h3>College students</h3><p>Practical learning, projects, campus experiences and career exploration.</p></div><div className="panel"><img className="panel-photo" src="/images/industry-partners.webp" alt="Industry collaboration" loading="lazy"/><Globe/><h3>Institutions & industry</h3><p>Defined pilots, clear responsibilities and measurable delivery.</p></div></div></div></section><FinalCTA/></main>}
const stories=[{title:'Build a portfolio that shows your work',paragraphs:['Choose a project with a clear problem and a specific user. A small, complete project is easier to discuss than a large unfinished one.','Show your process: the goal, the decisions you made, your evidence and what you would improve. Give credit for any tools, templates and team contributions.','Include a short demonstration and a readable project description. Ask someone unfamiliar with the project to test whether they can understand it.']},{title:'Make the most of your campus community',paragraphs:['Join an activity that matches your curiosity. Start by participating consistently and understanding what the group needs.','Contribute in a specific way, such as documenting an event, helping a peer or organising a small discussion. Ask for feedback and respect others’ time.','Keep a record of what you learned. Leadership grows through dependable contributions, not just titles.']},{title:'Start with a problem worth solving',paragraphs:['Describe the person facing the problem and when it happens. Interview potential users before building a solution.','Test the smallest useful assumption. A conversation, sketch or simple prototype can reveal whether the need is real.','Record what changed your mind. Clear learning and honest evidence are useful outcomes, even when the first idea changes.']}];
function Journal(){const [i,setI]=useState(0);useEffect(()=>{const n=Number(new URLSearchParams(window.location.search).get('story')||0);if(n>=0&&n<3)setI(n)},[]);return <main id="main"><PageHero label="WOC Journal" title="Ideas for your next step." text="Practical editorial guides for learning, community and student innovation."/><section className="section container journal-layout"><nav aria-label="Journal articles">{stories.map((s,n)=><button key={s.title} aria-pressed={n===i} onClick={()=>setI(n)}>{s.title}</button>)}</nav><article><Eyebrow>WOC EDITORIAL GUIDE</Eyebrow><h2>{stories[i].title}</h2>{stories[i].paragraphs.map(p=><p key={p}>{p}</p>)}</article></section></main>}
function VerifyCertificate(){const {demo}=useWoc();const [id,setId]=useState(''),[result,setResult]=useState<{id:string;name:string;program:string;issued_at:string;sample:boolean}|null>(null),[error,setError]=useState('');useEffect(()=>setId(new URLSearchParams(window.location.search).get('id')||''),[]);return <main id="main" className="section container narrow"><Eyebrow>CERTIFICATE VERIFICATION</Eyebrow><h1>Check a WOC credential.</h1><p>Enter the certificate reference exactly as shown on the issued credential.</p><form onSubmit={async e=>{e.preventDefault();setError('');setResult(null);try{if(demo)throw new Error('Verification requires the local Django backend. Demo registrations do not issue credentials.');setResult(await api('/certificates/'+encodeURIComponent(id)+'/'))}catch(e){setError((e as Error).message)}}}><label>Certificate reference<input required value={id} onChange={e=>setId(e.target.value)}/></label><button className="button">Verify certificate</button></form>{error&&<p role="alert" className="form-error">{error}</p>}{result&&<div className="certificate"><ShieldCheck size={38}/><Eyebrow>{result.sample?'SAMPLE PROGRAM COMPLETION':'VERIFIED COMPLETION RECORD'}</Eyebrow><h2>{result.name}</h2><p>{result.program}</p><p>Issued {new Date(result.issued_at).toLocaleDateString('en-IN')}</p><small>{result.id}</small><p>This is a program completion record, not an accredited qualification.</p><button className="button outline" onClick={()=>window.print()}>Print record</button></div>}</main>}
function Policies({type}:{type:string}){const privacy=type==='privacy';return <main id="main" className="section container narrow"><Eyebrow>WOC PLATFORM</Eyebrow><h1>{privacy?'Privacy notice':'Participation terms'}</h1><p className="notice">Pilot policy draft. The operating organisation must approve final policies and official contact details before public enrolment.</p>{(privacy?[['What is collected','Account name, email, age, institution, program registrations and information you choose to submit. This pilot does not request government identity documents.'],['How information is used','To operate your account, record participation, review applications and provide program updates. Data sharing with employers requires a defined purpose and appropriate permission.'],['Children and school participation','Users under 18 require separate guardian and school permissions. An account checkbox does not replace verified consent or a safeguarding process.'],['Retention and requests','Contact the WOC team using the enquiry form to request access, correction or deletion. A formal retention schedule and response process must be approved before production launch.'],['Demo storage','In the hosted showcase, demo account details and registrations stay in your browser. Clear site storage to remove those records. No analytics or advertising trackers are installed.']]:[['Sample programs','The catalogue is illustrative. Dates, prices, venues and availability require confirmation before live delivery. Sample jobs are not live vacancies.'],['Participation','Provide accurate information, respect fellow participants and follow institution and organiser rules. School users need appropriate permissions.'],['Fees and refunds','No online payments are collected in this release. A payment provider and approved cancellation/refund policy are needed before paid checkout can launch.'],['Learning and opportunities','Courses, certificates and community participation do not guarantee employment, accredited qualifications, funding or investment. Employers make independent hiring decisions.'],['Conduct and safety','Report concerns through the contact form. Live school, sports and cultural activities require approved safeguarding, eligibility and incident procedures.']]).map(([h,p])=><section key={h}><h2>{h}</h2><p>{p}</p></section>)}<Link href="/contact/" className="text-link">Contact the WOC team</Link></main>}
