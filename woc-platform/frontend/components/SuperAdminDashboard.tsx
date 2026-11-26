'use client';



import React, { useState } from 'react';

import Link from 'next/link';

import { useQuery } from '@tanstack/react-query';

import {

  ShieldAlert, CheckCircle, XCircle, Clock, Building2,

  Briefcase, GraduationCap, Users, ExternalLink, AlertTriangle

} from 'lucide-react';

import { useWoc } from './Platform';

import { api, getApiBase, privateFileUrl } from '@/lib/api';

import { SuperAdminEngagementTab } from './EngagementPanels';



export function SuperAdminDashboard() {

  const { user, toast } = useWoc();

  const [tab, setTab] = useState<'overview' | 'organizations' | 'opportunities' | 'engagement' | 'accounts'>('overview');

  const [filterOrgStatus, setFilterOrgStatus] = useState<string>('pending');

  const [filterOppStatus, setFilterOppStatus] = useState<string>('pending_review');



  const isSuperAdmin = user?.authorization?.roles?.includes('super_admin') || user?.is_superuser;



  const { data: overviewData, refetch: refetchOverview } = useQuery({

    queryKey: ['super-admin-overview'],

    queryFn: () => api('/super-admin/overview/'),

    enabled: !!user && !!isSuperAdmin,

  });



  const { data: orgData, refetch: refetchOrgs, isLoading: loadingOrgs } = useQuery({

    queryKey: ['super-admin-orgs', filterOrgStatus],

    queryFn: () => api(`/super-admin/approvals/organizations/?status=${filterOrgStatus}`),

    enabled: !!user && !!isSuperAdmin,

  });



  const { data: oppData, refetch: refetchOpps, isLoading: loadingOpps } = useQuery({

    queryKey: ['super-admin-opps', filterOppStatus],

    queryFn: () => api(`/super-admin/approvals/opportunities/?status=${filterOppStatus}`),

    enabled: !!user && !!isSuperAdmin,

  });



  if (!user) {

    return (

      <main id="main" className="section container empty-state">

        <ShieldAlert size={40} />

        <h1>Platform Administration</h1>

        <p>Sign in with your Super Administrator account.</p>

        <Link href="/login/" className="button">Sign In</Link>

      </main>

    );

  }



  if (!isSuperAdmin) {

    return (

      <main id="main" className="section container empty-state">

        <AlertTriangle size={40} style={{ color: 'var(--crimson)' }} />

        <h1>Access Restricted</h1>

        <p>This portal is exclusively accessible to authorized Super Administrators with explicit organization management permissions.</p>

        <Link href="/dashboard/" className="button">Return to Dashboard</Link>

      </main>

    );

  }



  const summary = overviewData?.summary || {

    total_students: 0,

    registered_colleges: 0,

    registered_companies: 0,

    pending_organizations: 0,

    published_jobs: 0,

    published_internships: 0,

    pending_opportunities: 0,

  };



  return (

    <main id="main" className="dashboard">

      <aside className="dashboard-nav">

        <p className="eyebrow">SUPER ADMIN</p>

        <button aria-current={tab === 'overview' ? 'page' : undefined} onClick={() => setTab('overview')}>

          Overview

        </button>

        <button aria-current={tab === 'organizations' ? 'page' : undefined} onClick={() => setTab('organizations')}>

          Organization Approvals {summary.pending_organizations > 0 && <span className="tab-badge">{summary.pending_organizations}</span>}

        </button>

        <button aria-current={tab === 'opportunities' ? 'page' : undefined} onClick={() => setTab('opportunities')}>

          Opportunity Moderation {summary.pending_opportunities > 0 && <span className="tab-badge">{summary.pending_opportunities}</span>}

        </button>

        <button aria-current={tab === 'engagement' ? 'page' : undefined} onClick={() => setTab('engagement')}>

          Campus Engagement

        </button>

        <button onClick={() => setTab('accounts')}>Account Management</button>

        <a href={`${getApiBase().replace(/\/api\/?$/, '')}/admin/`} target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', marginTop: '16px' }}>

          Django Admin <ExternalLink size={12} style={{ display: 'inline', marginLeft: '4px' }} />

        </a>

      </aside>



      <div className="dashboard-body">

        <div style={{ marginBottom: '24px' }}>

          <p className="eyebrow">SUPER ADMIN CONSOLE</p>

          <h1 style={{ margin: '4px 0 0' }}>Platform Governance & Moderation</h1>

        </div>



        {tab === 'overview' && (

          <div>

            <div className="dashboard-stats" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>

              <div>

                <strong>{summary.total_students}</strong>

                <span>Total Students</span>

              </div>

              <div>

                <strong>{summary.registered_colleges}</strong>

                <span>Colleges</span>

              </div>

              <div>

                <strong>{summary.registered_companies}</strong>

                <span>Companies</span>

              </div>

              <div style={{ background: summary.pending_organizations > 0 ? '#FFFBEB' : undefined }}>

                <strong style={{ color: summary.pending_organizations > 0 ? '#B45309' : undefined }}>

                  {summary.pending_organizations}

                </strong>

                <span>Pending Orgs</span>

              </div>

              <div>

                <strong>{summary.published_jobs}</strong>

                <span>Live Jobs</span>

              </div>

              <div>

                <strong>{summary.published_internships}</strong>

                <span>Live Internships</span>

              </div>

              <div style={{ background: summary.pending_opportunities > 0 ? '#FEF2F2' : undefined }}>

                <strong style={{ color: summary.pending_opportunities > 0 ? 'var(--crimson)' : undefined }}>

                  {summary.pending_opportunities}

                </strong>

                <span>Pending Postings</span>

              </div>

            </div>



            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '32px' }}>

              <div className="panel">

                <h3>Organization Approvals</h3>

                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

                  {summary.pending_organizations} institutions and employers are currently awaiting platform verification.

                </p>

                <button className="button small" onClick={() => setTab('organizations')}>

                  Review Organizations

                </button>

              </div>



              <div className="panel">

                <h3>Opportunity Moderation</h3>

                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

                  {summary.pending_opportunities} job and internship listings submitted by companies require review before public display.

                </p>

                <button className="button small" onClick={() => setTab('opportunities')}>

                  Review Postings

                </button>

              </div>

            </div>

          </div>

        )}



        {tab === 'accounts' && <AccountManagement />}

        {tab === 'engagement' && <SuperAdminEngagementTab />}



        {tab === 'organizations' && (

          <div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>

              {['pending', 'approved', 'rejected', 'suspended'].map((st) => (

                <button

                  key={st}

                  className={`button small ${filterOrgStatus === st ? '' : 'outline'}`}

                  onClick={() => setFilterOrgStatus(st)}

                >

                  {st.toUpperCase()}

                </button>

              ))}

            </div>



            {loadingOrgs ? (

              <p>Loading organizations…</p>

            ) : orgData?.organizations?.length === 0 ? (

              <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

                <p>No organizations found matching "{filterOrgStatus}".</p>

              </div>

            ) : (

              <div className="record-list">

                {orgData?.organizations?.map((org: any) => (

                  <OrgReviewCard

                    key={`${org.kind}-${org.id}`}

                    org={org}

                    onReviewed={() => {

                      refetchOrgs();

                      refetchOverview();

                      toast('Organization review updated.');

                    }}

                  />

                ))}

              </div>

            )}

          </div>

        )}



        {tab === 'opportunities' && (

          <div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>

              {['pending_review', 'approved', 'rejected', 'suspended'].map((st) => (

                <button

                  key={st}

                  className={`button small ${filterOppStatus === st ? '' : 'outline'}`}

                  onClick={() => setFilterOppStatus(st)}

                >

                  {st.replace('_', ' ').toUpperCase()}

                </button>

              ))}

            </div>



            {loadingOpps ? (

              <p>Loading opportunities…</p>

            ) : oppData?.opportunities?.length === 0 ? (

              <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

                <p>No opportunities matching status "{filterOppStatus}".</p>

              </div>

            ) : (

              <div className="record-list">

                {oppData?.opportunities?.map((opp: any) => (

                  <OppReviewCard

                    key={opp.id}

                    opp={opp}

                    onReviewed={() => {

                      refetchOpps();

                      refetchOverview();

                      toast('Posting review updated.');

                    }}

                  />

                ))}

              </div>

            )}

          </div>

        )}

      </div>

    </main>

  );

}



function OrgReviewCard({ org, onReviewed }: { org: any; onReviewed: () => void }) {

  const [busy, setBusy] = useState(false);

  const [note, setNote] = useState('');

  const [showNoteInput, setShowNoteInput] = useState(false);

  const [pendingAction, setPendingAction] = useState<string | null>(null);



  async function executeReview(action: string) {

    setBusy(true);

    try {

      await api(`/super-admin/approvals/organizations/${org.kind}/${org.id}/review/`, 'POST', {

        action,

        note,

      });

      setShowNoteInput(false);

      setPendingAction(null);

      onReviewed();

    } catch (err: any) {

      alert(err.message || 'Review failed.');

    } finally {

      setBusy(false);

    }

  }



  return (

    <div className="record" style={{ flexDirection: 'column', alignItems: 'stretch' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>

        <div>

          <span className="label" style={{ marginRight: '8px' }}>{org.kind.toUpperCase()}</span>

          <span className={`status-pill status-${org.approval_status}`}>{org.approval_status}</span>

          <h3 style={{ marginTop: '8px' }}>{org.name}</h3>

          <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

            Location: {org.city || 'Unstated'} · Website: <a href={org.website} target="_blank" rel="noopener noreferrer">{org.website}</a>

          </p>

          <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

            {org.registration_reference&&<span>Registration reference: {org.registration_reference}<br/></span>}
            {org.has_verification_document&&<button type="button" className="text-link" onClick={async()=>{try{const url=await privateFileUrl(`/onboarding/${org.kind}/${org.id}/document/`);const a=document.createElement('a');a.href=url;a.download='verification.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{alert('Unable to download verification document.')}}}>Download verification PDF</button>}
            Contact: {org.contact_email} {org.recruitment_email && `· Recruitment: ${org.recruitment_email}`}

          </p>

          {org.submitted_by && <p style={{ fontSize: '12px', color: '#6B7280' }}>Submitted by: {org.submitted_by}</p>}

          {org.description && <p style={{ fontSize: '13px', marginTop: '6px' }}>{org.description}</p>}

          {org.review_note && (

            <p style={{ fontSize: '12px', background: '#F3F4F6', padding: '6px 10px', borderRadius: '4px', marginTop: '6px' }}>

              <strong>Audit Note:</strong> {org.review_note}

            </p>

          )}

        </div>



        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>

          {org.approval_status !== 'approved' && (

            <button className="button small" disabled={busy} onClick={() => { setPendingAction('approve'); setShowNoteInput(true); }}>

              Approve

            </button>

          )}

          {org.approval_status !== 'rejected' && (

            <button className="button small outline" disabled={busy} onClick={() => { setPendingAction('reject'); setShowNoteInput(true); }}>

              Reject

            </button>

          )}

          {org.approval_status === 'approved' && (

            <button className="button small outline" style={{ color: 'var(--crimson)', borderColor: 'var(--crimson)' }} disabled={busy} onClick={() => { setPendingAction('suspend'); setShowNoteInput(true); }}>

              Suspend

            </button>

          )}

          {org.approval_status === 'suspended' && (

            <button className="button small" disabled={busy} onClick={() => { setPendingAction('reactivate'); setShowNoteInput(true); }}>

              Reactivate

            </button>

          )}

        </div>

      </div>



      {showNoteInput && (

        <div style={{ marginTop: '16px', background: 'var(--cream)', padding: '16px', borderRadius: '6px' }}>

          <label style={{ fontSize: '13px', fontWeight: 600 }}>

            Audit / Review Note for {pendingAction?.toUpperCase()}:

            <input

              type="text"

              value={note}

              onChange={(e) => setNote(e.target.value)}

              placeholder="Add rationale, verification remarks or rejection reason..."

              style={{ marginTop: '6px' }}

            />

          </label>

          <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>

            <button className="button small" disabled={busy} onClick={() => pendingAction && executeReview(pendingAction)}>

              {busy ? 'Processing…' : `Confirm ${pendingAction}`}

            </button>

            <button className="button small outline" onClick={() => { setShowNoteInput(false); setPendingAction(null); }}>

              Cancel

            </button>

          </div>

        </div>

      )}

    </div>

  );

}



function OppReviewCard({ opp, onReviewed }: { opp: any; onReviewed: () => void }) {

  const [busy, setBusy] = useState(false);

  const [note, setNote] = useState('');

  const [showNoteInput, setShowNoteInput] = useState(false);

  const [pendingAction, setPendingAction] = useState<string | null>(null);



  async function executeReview(action: string) {

    setBusy(true);

    try {

      await api(`/super-admin/approvals/opportunities/${opp.id}/review/`, 'POST', {

        action,

        note,

      });

      setShowNoteInput(false);

      setPendingAction(null);

      onReviewed();

    } catch (err: any) {

      alert(err.message || 'Review failed.');

    } finally {

      setBusy(false);

    }

  }



  return (

    <div className="record" style={{ flexDirection: 'column', alignItems: 'stretch' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>

        <div>

          <span className="label" style={{ marginRight: '8px' }}>{opp.opportunity_type.toUpperCase()}</span>

          <span className={`status-pill status-${opp.status}`}>{opp.status.replace('_', ' ')}</span>

          <span style={{ fontSize: '13px', color: 'var(--muted)', marginLeft: '8px' }}>

            Company: <strong>{opp.company_name}</strong> ({opp.company_approval})

          </span>

          <h3 style={{ marginTop: '8px' }}>{opp.title}</h3>

          <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

            {opp.work_mode} · {opp.employment_type} · {opp.location || 'Location unstated'} · {opp.compensation || 'Unstated'}

          </p>



          <div style={{ margin: '8px 0', fontSize: '13px' }}>

            <strong>Application Destinations:</strong>{' '}

            {opp.recruitment_email && <span>Email: <code>{opp.recruitment_email}</code> </span>}

            {opp.careers_url && (

              <span>

                Careers URL: <a href={opp.careers_url} target="_blank" rel="noopener noreferrer">{opp.careers_url}</a>

              </span>

            )}

          </div>



          <details style={{ fontSize: '13px', color: '#4B5563', margin: '8px 0' }}>

            <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Read Full Description & Skills</summary>

            <p style={{ marginTop: '8px', whiteSpace: 'pre-line' }}>{opp.description}</p>

            {opp.required_skills?.length > 0 && (

              <p><strong>Skills:</strong> {opp.required_skills.join(', ')}</p>

            )}

          </details>



          {opp.review_note && (

            <p style={{ fontSize: '12px', background: '#F3F4F6', padding: '6px 10px', borderRadius: '4px', marginTop: '6px' }}>

              <strong>Review Note:</strong> {opp.review_note}

            </p>

          )}

        </div>



        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>

          {opp.status !== 'approved' && (

            <button className="button small" disabled={busy} onClick={() => { setPendingAction('approve'); setShowNoteInput(true); }}>

              Approve Posting

            </button>

          )}

          {opp.status !== 'rejected' && (

            <button className="button small outline" disabled={busy} onClick={() => { setPendingAction('reject'); setShowNoteInput(true); }}>

              Reject

            </button>

          )}

          {opp.status === 'approved' && (

            <button className="button small outline" style={{ color: 'var(--crimson)', borderColor: 'var(--crimson)' }} disabled={busy} onClick={() => { setPendingAction('suspend'); setShowNoteInput(true); }}>

              Suspend

            </button>

          )}

        </div>

      </div>



      {showNoteInput && (

        <div style={{ marginTop: '16px', background: 'var(--cream)', padding: '16px', borderRadius: '6px' }}>

          <label style={{ fontSize: '13px', fontWeight: 600 }}>

            Moderation Note / Feedback for {pendingAction?.toUpperCase()}:

            <input

              type="text"

              value={note}

              onChange={(e) => setNote(e.target.value)}

              placeholder="Reason or feedback for company recruiter..."

              style={{ marginTop: '6px' }}

            />

          </label>

          <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>

            <button className="button small" disabled={busy} onClick={() => pendingAction && executeReview(pendingAction)}>

              {busy ? 'Processing…' : `Confirm ${pendingAction}`}

            </button>

            <button className="button small outline" onClick={() => { setShowNoteInput(false); setPendingAction(null); }}>

              Cancel

            </button>

          </div>

        </div>

      )}

    </div>

  );

}





function AccountManagement() {

 const [q,setQ]=useState(''),[role,setRole]=useState(''),[status,setStatus]=useState(''),[page,setPage]=useState(1),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);

 const {data,error,isLoading,refetch}=useQuery({queryKey:['admin-accounts',q,role,status,page],queryFn:()=>api(`/super-admin/accounts/?${new URLSearchParams({q,role,status,page:String(page)})}`)});

 async function act(id:number,action:string){setBusy(true);setMessage('');try{await api('/super-admin/accounts/','POST',{user_id:id,action});setMessage('Account updated.');await refetch();}catch(e:any){setMessage(e.message);}finally{setBusy(false);}}

 return <section className="panel"><h2>Account Management</h2><div className="filter-bar"><input aria-label="Search accounts" placeholder="Search name or email" value={q} onChange={e=>{setQ(e.target.value);setPage(1);}}/><select aria-label="Account role" value={role} onChange={e=>{setRole(e.target.value);setPage(1);}}><option value="">All roles</option>{['student','college_admin','company_admin','super_admin'].map(r=><option key={r}>{r}</option>)}</select><select aria-label="Account status" value={status} onChange={e=>{setStatus(e.target.value);setPage(1);}}><option value="">All statuses</option><option value="active">active</option><option value="suspended">suspended</option></select></div>

 {isLoading&&<p>Loading accounts…</p>}{error&&<p role="alert">{error.message}<button onClick={()=>refetch()}>Retry</button></p>}{message&&<p role="status">{message}</p>}

 {data&&<><p>{Object.entries(data.statistics).map(([k,v])=>`${k}: ${v}`).join(' · ')}</p>{!data.results.length&&<p>No matching accounts.</p>}{data.results.map((u:any)=><div className="panel" key={u.id}><strong>{u.name}</strong><p>{u.email} · {u.role} · {u.is_active?'Active':'Suspended'}</p><button className="button small" disabled={busy||u.role==='super_admin'} onClick={()=>act(u.id,u.is_active?'suspend':'activate')}>{u.is_active?'Suspend':'Activate'}</button></div>)}<button disabled={page<=1} onClick={()=>setPage(page-1)}>Previous</button><span> {page} / {data.pages} </span><button disabled={page>=data.pages} onClick={()=>setPage(page+1)}>Next</button><h3>Administrative action history</h3>{data.history.map((h:any,i:number)=><p key={i}>{h.created_at} · Actor {h.user_id} · {h.event_type} · Account {h.metadata.target_user_id}</p>)}</>}

 </section>;

}

