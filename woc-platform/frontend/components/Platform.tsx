'use client';
import {createContext,useContext,useState,useEffect,useRef,ReactNode} from 'react';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {QueryClient,QueryClientProvider,useQuery,useQueryClient} from '@tanstack/react-query';
import {Menu,X,Search,Instagram,Linkedin,Mail,ChevronDown,Wind,ArrowUp,CheckCircle,Bell} from 'lucide-react';
import {api,isDemoMode,getApiBase,privateFileUrl} from '@/lib/api';
import {modules} from '@/lib/data';
export type User={id:number;name:string;email:string;institution:string;age:number|null;bio:string;professional_headline?:string;address?:string;pin_code?:string;languages?:string[];current_status?:string;city?:string;state?:string;qualification?:string;skills?:string[];interests?:string[];career_goals?:string;resume_url?:string;graduation_year?:number|null;education_start_year?:number|null;department?:string;has_photo?:boolean;has_resume?:boolean;has_supporting_document?:boolean;linkedin_url?:string;github_url?:string;roles:string[];is_staff:boolean;is_superuser?:boolean;email_verified?:boolean;email_verified_at?:string|null;phone_number?:string;phone_verified?:boolean;phone_verified_at?:string|null;auth_provider?:string;notification_preferences?:Record<string,boolean>;authorization?:{roles:string[];dashboard_url:string;colleges?:any[];companies?:any[];college_memberships?:any[];company_memberships?:any[];permissions?:string[]}};
export type Registration={id:string;program:import('@/lib/data').Program;status:string;data:Record<string,unknown>;created_at:string;certificate?:string;student?:string;email?:string};
type Context={user:User|null;setUser:(u:User|null)=>void;demo:boolean;toast:(s:string)=>void;records:Registration[];refresh:()=>Promise<void>;registerProgram:(slug:string,data:Record<string,unknown>)=>Promise<void>};
const Ctx=createContext<Context>(null!);export const useWoc=()=>useContext(Ctx);
function AccountIdentity({onSignOut,signingOut}:{onSignOut:()=>void;signingOut:boolean}){
 const {user}=useWoc();const [photo,setPhoto]=useState('');const [open,setOpen]=useState(false);const menuRef=useRef<HTMLDivElement>(null);
 useEffect(()=>{const close=(event:PointerEvent)=>{if(!menuRef.current?.contains(event.target as Node))setOpen(false)};const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')setOpen(false)};document.addEventListener('pointerdown',close);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',escape)}},[]);
 useEffect(()=>{let active=true,url='';setPhoto('');if(user?.has_photo)privateFileUrl('/student/profile/files/photo/').then(value=>{url=value;if(active)setPhoto(value);else URL.revokeObjectURL(value)}).catch(()=>{});return()=>{active=false;if(url)URL.revokeObjectURL(url)}},[user]);
 if(!user)return null;
 const name=user.name||user.email||'My account';const initials=name.split(/\s+/).slice(0,2).map(part=>part[0]).join('').toUpperCase();
 const destination=user.authorization?.dashboard_url||'/dashboard/';
 return <div className="account-menu" ref={menuRef}><button type="button" className="account-identity" aria-expanded={open} aria-label={`${name} — account options`} onClick={()=>setOpen(!open)}>{photo?<img src={photo} alt=""/>:<span>{initials}</span>}<strong>{name}</strong><ChevronDown size={14}/></button>{open&&<div className="account-dropdown"><a href={destination==='/dashboard/'?'/dashboard/?tab=profile':destination} onClick={()=>setOpen(false)}>{destination==='/dashboard/'?'My profile':'My portal'}</a><button type="button" disabled={signingOut} onClick={onSignOut}>{signingOut?'Signing out…':'Sign out'}</button></div>}</div>;

}
function NotificationBell(){
 const {user,demo,toast}=useWoc();
 const [open,setOpen]=useState(false);
 const popoverRef=useRef<HTMLDivElement>(null);
 const qc=useQueryClient();
 const {data}=useQuery({
  queryKey:['notifications',user?.id],
  queryFn:()=>api('/notifications/'),
  enabled:!!user&&!demo,
  refetchInterval:20000
 });
 const unreadCount=demo?1:(data?.unread_count||0);
 const list=demo?[{id:1,message:'Welcome to THE WOC student community!',read:false,created_at:new Date().toISOString()}]:(data?.results||[]).slice(0,5);

 useEffect(()=>{
  const outside=(e:PointerEvent)=>{if(!popoverRef.current?.contains(e.target as Node))setOpen(false)};
  document.addEventListener('pointerdown',outside);
  return()=>document.removeEventListener('pointerdown',outside);
 },[]);

 async function markAll(){
  if(demo){toast('Notifications marked as read in demo mode.');setOpen(false);return}
  try{
   await api('/notifications/','PATCH',{all:true});
   qc.invalidateQueries({queryKey:['notifications']});
  }catch{}
 }

 async function markItem(id:number){
  if(demo){setOpen(false);return}
  try{
   await api('/notifications/','PATCH',{id});
   qc.invalidateQueries({queryKey:['notifications']});
  }catch{}
 }

 return <div className="bell-container" ref={popoverRef}>
  <button type="button" className="bell-btn" aria-label={`Notifications ${unreadCount>0?`(${unreadCount} unread)`:''}`} onClick={()=>setOpen(!open)}>
   <Bell size={20}/>
   {unreadCount>0&&<span className="bell-badge">{unreadCount>9?'9+':unreadCount}</span>}
  </button>
  {open&&(
   <div className="notification-popover" role="region" aria-label="Notifications list">
    <div className="popover-header">
     <strong>Notifications</strong>
     {unreadCount>0&&<button type="button" onClick={markAll} className="text-link" style={{fontSize:'12px',background:'none',border:'none',cursor:'pointer'}}>Mark all read</button>}
    </div>
    <div className="popover-body">
     {list.length>0?(
      list.map((n:{id:number;message:string;read:boolean;created_at?:string})=>(
       <div key={n.id} className={`popover-item ${!n.read?'unread':''}`} onClick={()=>markItem(n.id)} style={{cursor:'pointer'}}>
        <span style={{fontWeight:!n.read?600:400}}>{n.message}</span>
        {n.created_at&&<span className="time">{new Date(n.created_at).toLocaleDateString('en-IN',{month:'short',day:'numeric'})}</span>}
       </div>
      ))
     ):(
      <p style={{padding:'20px 16px',textAlign:'center',color:'var(--muted)',fontSize:'13px',margin:0}}>No notifications yet</p>
     )}
    </div>
    <div className="popover-footer">
     <Link href={user?.authorization?.dashboard_url||"/dashboard/"} onClick={()=>setOpen(false)} className="text-link" style={{fontSize:'12px',fontWeight:600}}>
      Go to Dashboard →
     </Link>
    </div>
   </div>
  )}
 </div>;
}

function Shell({children}:{children:ReactNode}){
 const [user,setUserState]=useState<User|null>(null),[demo,setDemo]=useState(false),[records,setRecords]=useState<Registration[]>([]),[message,setMessage]=useState(''),[apiError,setApiError]=useState(''),[mobile,setMobile]=useState(false),[search,setSearch]=useState(false),[term,setTerm]=useState(''),[sticky,setSticky]=useState(false),[openMenu,setOpenMenu]=useState<string|null>(null);const path=usePathname();const navRef=useRef<HTMLElement>(null);
 const toast=(s:string)=>setMessage(s);
 const setUser=(u:User|null)=>{setUserState(u);if(demo){if(u)sessionStorage.setItem('woc-demo-user',JSON.stringify(u));else sessionStorage.removeItem('woc-demo-user')}};
 const refresh=async()=>{
  if(demo){
   setRecords(JSON.parse(localStorage.getItem('woc-demo-records')||'[]'));
  }else{
   try{
    const d=await api('/records/');
    setRecords(d.results||[]);
    setApiError('');
   }catch(err:any){
    if(err.message&&err.message.includes('Cannot connect')){
     setApiError(err.message);
    }
   }
  }
 };
 useEffect(()=>{
  const isDemo=isDemoMode();
  setDemo(isDemo);
  if(isDemo){
   const saved=sessionStorage.getItem('woc-demo-user');
   if(saved)setUserState(JSON.parse(saved));
   setRecords(JSON.parse(localStorage.getItem('woc-demo-records')||'[]'));
  }else{
   api('/me/')
    .then(d=>{
     setUserState(d.user);
     refresh();
     setApiError('');
    })
    .catch((err:any)=>{
     if(err.message&&err.message.includes('Cannot connect')){
      setApiError(err.message);
     }
    });
  }
  const scroll=()=>setSticky(window.scrollY>30);
  scroll();
  window.addEventListener('scroll',scroll,{passive:true});
  return()=>window.removeEventListener('scroll',scroll);
 },[]);
 useEffect(()=>{setMobile(false);setSearch(false);setOpenMenu(null)},[path]);useEffect(()=>{if(!message)return;const t=setTimeout(()=>setMessage(''),6500);return()=>clearTimeout(t)},[message]);
 useEffect(()=>{
  const outside=(event:PointerEvent)=>{if(!navRef.current?.contains(event.target as Node))setOpenMenu(null)};
  const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){setOpenMenu(null);setMobile(false)}};
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);
  return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape)};
 },[]);
 async function registerProgram(slug:string,data:Record<string,unknown>){if(!user)throw new Error('Please sign in before registering.');if(demo){const p=(await import('@/lib/data')).programs.find(p=>p.slug===slug)!;if(records.some(r=>r.program.slug===slug))throw new Error('You already registered for this sample program.');const r={id:crypto.randomUUID(),program:p,status:'sample registration',data,created_at:new Date().toISOString()};const next=[r,...records];setRecords(next);localStorage.setItem('woc-demo-records',JSON.stringify(next));toast('Sample registration saved in this browser.')}else{await api('/records/','POST',{program:slug,data});await refresh();toast('Registration saved. View its status in your dashboard.')}}
 const [signingOut,setSigningOut]=useState(false);
 const queryClient=useQueryClient();
 async function signOut(){
  if(signingOut)return;
  setSigningOut(true);
  try{
   if(!demo)await api('/logout/','POST');
   await queryClient.cancelQueries();queryClient.clear();setUser(null);setRecords([]);
   sessionStorage.removeItem('woc-registration-role');
   window.location.href='/login/';
  }catch(error:any){toast(error.message||'Unable to sign out. Please retry.');setSigningOut(false)}
 }
 const dashboardLink = user?.authorization?.dashboard_url || '/dashboard/';
 const signedInRoles=user?.authorization?.roles||[];
 const pendingRole=dashboardLink==='/onboarding/'?(user?.authorization?.company_memberships?.length?'Company':user?.authorization?.college_memberships?.some(m=>m.role==='college_admin')?'College':''):'';
 const accountRole=signedInRoles.includes('super_admin')?'Super Admin':signedInRoles.includes('company_admin')?'Company':signedInRoles.includes('college_admin')?'College':pendingRole;
 useEffect(()=>{
  if(accountRole&&['/','/dashboard/','/dashboard'].includes(path)&&dashboardLink!=='/dashboard/')window.location.replace(dashboardLink);
 },[accountRole,path,dashboardLink]);
 const dashboardText = user?.authorization?.roles?.includes('super_admin')
  ? 'Super Admin'
  : user?.authorization?.roles?.includes('company_admin')
  ? 'Company Hub'
  : user?.authorization?.roles?.includes('college_admin')
  ? 'College Portal'
  : 'Dashboard';
 const routeRole=['/register-college/','/login-college/','/register-college','/login-college'].includes(path)?'College':['/register-company/','/login-company/','/register-company','/login-company'].includes(path)?'Company':'';
 const portalRole = accountRole || routeRole || (path.startsWith('/college') ? 'College' : path.startsWith('/company') ? 'Company' : path.startsWith('/super-admin') ? 'Super Admin' : '');
 const portalHeaderRef=useRef<HTMLElement>(null);
 useEffect(()=>{
  const header=portalHeaderRef.current;if(!header)return;
  const measure=()=>header.parentElement?.style.setProperty('--portal-header-height',`${header.offsetHeight}px`);
  measure();const observer=new ResizeObserver(measure);observer.observe(header);return()=>observer.disconnect();
 },[portalRole,path]);
 if(portalRole) return <Ctx.Provider value={{user,setUser,demo,toast,records,refresh,registerProgram}}><div className="organization-shell"><div className="organization-ribbon">BE THE CHANGE. BUILD YOUR FUTURE.</div><header ref={portalHeaderRef} className="portal-header"><Link href={dashboardLink} className="brand"><Wind size={30}/><span>WOC<small>WIND OF CHANGE</small></span></Link><strong>{portalRole==='College'?'Institution workspace':portalRole==='Company'?'Employer workspace':'Platform administration'}</strong><div className="actions">{user&&<NotificationBell/>}{user&&<AccountIdentity onSignOut={signOut} signingOut={signingOut}/>}{!user&&<><Link href="/join/">Choose your portal ↗</Link><Link className="button small outline" href={portalRole==='College'?'/login-college/':portalRole==='Company'?'/login-company/':'/login/'}>Sign in</Link></>}</div></header>{apiError&&<p role="alert" className="notice">{apiError}</p>}{children}{message&&<div className="toast" role="status">{message}</div>}</div></Ctx.Provider>;
 return <Ctx.Provider value={{user,setUser,demo,toast,records,refresh,registerProgram}}><a className="skip-link" href="#main">Skip to content</a>{demo&&<div className="demo-banner">Interactive showcase · Sample programs · Browser-only demo account · No payments collected</div>}{apiError&&<div className="connection-error-banner" role="alert"><span>⚠️ {apiError}</span><button type="button" onClick={()=>{setApiError('');refresh()}} className="button small outline" style={{marginLeft:'12px',padding:'4px 10px',fontSize:'12px'}}>Retry</button></div>}<div className="topbar"><div className="container"><span>BE THE CHANGE. &nbsp; BUILD YOUR FUTURE.</span><div><Link href="/contact/">Help & enquiries</Link><Link href={user?dashboardLink:'/login/'}>{user?(user.name||'My account'):'Login / Register'}</Link></div></div></div><header className={`header ${sticky?'scrolled':''} ${path==='/'?'home-header':''}`}><div className="container header-inner"><Link href="/" className="brand" aria-label="WOC home"><Wind size={33} strokeWidth={1.4}/><span>WOC<small>WIND OF CHANGE</small></span></Link><nav ref={navRef} aria-label="Main navigation" onClick={e=>{if((e.target as HTMLElement).closest('a'))setOpenMenu(null)}} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))setOpenMenu(null)}} className={mobile?'open':''}><Link href="/" onMouseEnter={()=>setOpenMenu(null)} onFocus={()=>setOpenMenu(null)} aria-current={path==='/'?'page':undefined}>Home</Link>{[{name:'Discover',items:['about','association','partnerships']},{name:'Opportunities',items:['academy','careers','incubation']},{name:'Campus Life',items:['events','sports','culturals']}].map(group=><div key={group.name} className="nav-group" onMouseEnter={()=>{if(window.matchMedia('(hover: hover)').matches)setOpenMenu(current=>current===group.name?current:null)}}><button type="button" className="nav-summary" aria-expanded={openMenu===group.name} onClick={e=>{e.preventDefault();setOpenMenu(openMenu===group.name?null:group.name)}}>{group.name}<ChevronDown size={13}/></button><div className="dropdown" hidden={openMenu!==group.name}>{group.items.map(slug=><Link key={slug} href={`/${slug}/`}>{modules.find(m=>m.slug===slug)?.name||'About WOC'}<small>{modules.find(m=>m.slug===slug)?.line||'Our mission and approach'}</small></Link>)}</div></div>)}<Link href="/contact/" onMouseEnter={()=>setOpenMenu(null)} onFocus={()=>setOpenMenu(null)}>Contact</Link></nav><div className="header-actions"><button className="icon-button search-toggle" aria-label="Search WOC" onClick={()=>setSearch(!search)}><Search size={20}/></button>{user&&<NotificationBell/>}{user?<><AccountIdentity onSignOut={signOut} signingOut={signingOut}/></>:<Link href="/join/" className="button small">Join WOC</Link>}<button className="icon-button mobile-toggle" aria-label={mobile?'Close navigation':'Open navigation'} aria-expanded={mobile} onClick={()=>setMobile(!mobile)}>{mobile?<X/>:<Menu/>}</button></div></div>{search&&<form className="searchbar container" onSubmit={e=>{e.preventDefault();window.location.href='/academy/?q='+encodeURIComponent(term)}}><label htmlFor="site-search">Find a course</label><input id="site-search" autoFocus value={term} onChange={e=>setTerm(e.target.value)} placeholder="Try Python, design, communication…"/><button className="button small">Search</button></form>}</header>{children}<footer className="footer"><div className="container footer-grid"><div><Link href="/" className="brand"><Wind size={30}/><span>WOC<small>WIND OF CHANGE</small></span></Link><p>Connecting student ambition with learning, community and real-world possibilities.</p><Link className="footer-contact" href="/contact/"><Mail size={17}/>Get in touch</Link></div><div><h3>Discover WOC</h3>{['about','association','partnerships','onboarding','news'].map(x=><Link key={x} href={`/${x}/`}>{x==='partnerships'?'Partnerships':x==='onboarding'?'Employers & Colleges':x==='news'?'News & stories':x[0].toUpperCase()+x.slice(1)}</Link>)}</div><div><h3>Explore</h3>{['academy','careers','incubation','events','sports','culturals'].map(x=><Link key={x} href={`/${x}/`}>{x[0].toUpperCase()+x.slice(1)}</Link>)}</div><div><h3>Stay connected</h3><p>Hear about programs and campus opportunities.</p><Newsletter/><div className="social-links"><Link href="/contact/" aria-label="Ask about WOC social channels"><Instagram size={18}/></Link><Link href="/contact/" aria-label="Contact WOC for professional partnerships"><Linkedin size={18}/></Link></div></div></div><div className="container footer-bottom"><span>© {new Date().getFullYear()} THE WOC — Wind of Change.</span><div><Link href="/privacy/">Privacy</Link><Link href="/terms/">Terms</Link><Link href="/certificate/">Verify certificate</Link></div></div></footer>{message&&<div className="toast" role="status"><CheckCircle size={20}/><span>{message}</span><button onClick={()=>setMessage('')} className="icon-button" aria-label="Dismiss notification"><X size={18}/></button></div>}{sticky&&<button className="back-top" onClick={()=>window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})} aria-label="Back to top"><ArrowUp size={19}/></button>}</Ctx.Provider>
}
function Newsletter(){const {demo,toast}=useWoc();const [email,setEmail]=useState('');return <form onSubmit={async e=>{e.preventDefault();try{if(demo){localStorage.setItem('woc-newsletter',email);toast('Sample newsletter preference saved in this browser.')}else{await api('/enquiries/','POST',{name:'Newsletter subscriber',email,kind:'newsletter',message:'Please send me WOC program updates.'});toast('Newsletter request saved.')}setEmail('')}catch(e){toast((e as Error).message)}}}><label className="sr-only" htmlFor="newsletter">Your email</label><input id="newsletter" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="Your email address"/><button className="button small" type="submit">Subscribe</button></form>}
export default function Platform({children}:{children:ReactNode}){const [client]=useState(()=>new QueryClient());return <QueryClientProvider client={client}><Shell>{children}</Shell></QueryClientProvider>}
