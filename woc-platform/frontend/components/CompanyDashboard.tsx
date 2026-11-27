'use client';



import React, { useState, useEffect } from 'react';

import Link from 'next/link';

import { useQuery } from '@tanstack/react-query';

import {

  Building2, Briefcase, PlusCircle, CheckCircle, Clock,

  XCircle, AlertCircle, Edit, Trash2, ExternalLink, Globe, Mail, Users

} from 'lucide-react';

import { useWoc } from './Platform';

import { api } from '@/lib/api';



export function CompanyDashboard() {

  const { user, toast } = useWoc();

  const [activeTab, setActiveTab] = useState<'overview' | 'profile' | 'post' | 'manage' | 'partnerships'>('overview');

  const [postType, setPostType] = useState<'job' | 'internship'>('job');

  const [editingOpp, setEditingOpp] = useState<any>(null);



  // Queries

  const { data: dashboardData, refetch: refetchDashboard, isLoading: loadingDash } = useQuery({

    queryKey: ['company-dashboard', user?.id],

    queryFn: () => api('/company/dashboard/'),

    enabled: !!user,

  });



  const [oppPage, setOppPage] = useState(1);

  const [oppFilter, setOppFilter] = useState('all');



  const { data: opportunitiesData, refetch: refetchOpps, isLoading: loadingOpps } = useQuery({

    queryKey: ['company-opportunities', user?.id, oppPage, oppFilter],

    queryFn: () => {

      const q = new URLSearchParams();

      q.set('page', String(oppPage));

      if (oppFilter !== 'all') q.set('status', oppFilter);

      return api(`/company/opportunities/?${q.toString()}`);

    },

    enabled: !!user,

  });



  const isCompanyAdmin = user?.authorization?.roles?.includes('company_admin');

  const companyMembership = user?.authorization?.company_memberships?.[0];



  if (!user) {

    return (

      <main id="main" className="section container empty-state">

        <Building2 size={40} />

        <h1>Employer Portal</h1>

        <p>Please sign in to access your company dashboard.</p>

        <Link href="/login/" className="button">Sign In</Link>

      </main>

    );

  }



  // Pending approval state

  if (!isCompanyAdmin) {

    return (

      <main id="main" className="section container narrow">

        <div className="panel" style={{ textAlign: 'center', padding: '40px 24px' }}>

          <Clock size={48} style={{ color: 'var(--crimson)', margin: '0 auto 16px' }} />

          <h2>Organization Review in Progress</h2>

          <p style={{ color: 'var(--muted)', maxWidth: '480px', margin: '0 auto 20px' }}>

            {companyMembership?.company_name

              ? `Your registration for "${companyMembership.company_name}" has been received and is awaiting Super Admin verification.`

              : 'You have not registered an employer organization yet.'}

          </p>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>

            <Link href="/onboarding/" className="button outline">View Registration Status</Link>

            <Link href="/onboarding/?type=company" className="button">Organization status</Link>

          </div>

        </div>

      </main>

    );

  }



  const metrics = dashboardData?.metrics || {

    total_opportunities: 0,

    active_jobs: 0,

    active_internships: 0,

    pending_review: 0,

    drafts: 0,

    closed: 0,

  };



  return (

    <main id="main" className="dashboard">

      <aside className="dashboard-nav">

        <p className="eyebrow">COMPANY PORTAL</p><button aria-current={activeTab==='partnerships'?'page':undefined} onClick={()=>setActiveTab('partnerships')}>College partnerships</button>

        <button aria-current={activeTab === 'overview' ? 'page' : undefined} onClick={() => { setActiveTab('overview'); setEditingOpp(null); }}>

          Overview

        </button>

        <button aria-current={activeTab === 'profile' ? 'page' : undefined} onClick={() => { setActiveTab('profile'); setEditingOpp(null); }}>

          Company Profile

        </button>

        <button

          aria-current={activeTab === 'post' && postType === 'job' ? 'page' : undefined}

          onClick={() => { setActiveTab('post'); setEditingOpp(null); setPostType('job'); }}

        >

          Post a Job

        </button>

        <button aria-current={activeTab==='post' && postType==='internship'?'page':undefined} onClick={()=>{setActiveTab('post');setEditingOpp(null);setPostType('internship')}}>Post an Internship</button>

        <button aria-current={activeTab === 'manage' ? 'page' : undefined} onClick={() => { setActiveTab('manage'); setEditingOpp(null); }}>

          Manage Postings {metrics.pending_review > 0 && <span className="tab-badge">{metrics.pending_review}</span>}

        </button>

        

      </aside>



      <div className="dashboard-body">

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>

          <div>

            <p className="eyebrow">AUTHORIZED EMPLOYER</p>

            <h1 style={{ margin: '4px 0 0' }}>{activeTab==='overview'?'Build your next team.':dashboardData?.company?.name || 'Company Dashboard'}</h1><p>{dashboardData?.company?.name} · Approved company workspace</p>

          </div>

          {activeTab !== 'post' && (

            <div style={{ display: 'flex', gap: '8px' }}>

              <button className="button small" onClick={() => { setActiveTab('post'); setPostType('job'); setEditingOpp(null); }}>

                <PlusCircle size={15} style={{ marginRight: '6px' }} /> Post a Job

              </button>

              <button className="button small outline" onClick={() => { setActiveTab('post'); setPostType('internship'); setEditingOpp(null); }}>

                <PlusCircle size={15} style={{ marginRight: '6px' }} /> Post Internship

              </button>

            </div>

          )}

        </div>



        {activeTab === 'partnerships' && <CompanyPartnerships/>}
        {activeTab === 'overview' && (

          <OverviewTab

            metrics={metrics}

            opportunities={opportunitiesData?.results || []}

            onPostJob={() => { setActiveTab('post'); setPostType('job'); }}

            onManage={() => setActiveTab('manage')}

          />

        )}



        {activeTab === 'profile' && (

          <CompanyProfileTab

            company={dashboardData?.company}

            onSaved={() => { refetchDashboard(); toast('Company profile updated.'); }}

          />

        )}



        {activeTab === 'post' && (

          <OpportunityFormTab key={editingOpp?.id || postType}

            editingOpp={editingOpp}

            defaultType={postType}

            onSaved={() => {

              refetchDashboard();

              refetchOpps();

              setActiveTab('manage');

              setEditingOpp(null);

            }}

            onCancel={() => { setActiveTab('manage'); setEditingOpp(null); }}

          />

        )}



        {activeTab === 'manage' && (

          <ManageOpportunitiesTab

            opportunities={opportunitiesData?.results || []}

            totalCount={opportunitiesData?.count || 0}

            hasNext={!!opportunitiesData?.next}

            hasPrev={!!opportunitiesData?.previous}

            page={oppPage}

            setPage={setOppPage}

            filter={oppFilter}

            setFilter={setOppFilter}

            loading={loadingOpps}

            onEdit={(opp: any) => { setEditingOpp(opp); setActiveTab('post'); }}

            onUpdated={() => { refetchDashboard(); refetchOpps(); }}

          />

        )}

      </div>

    </main>

  );

}



function OverviewTab({ metrics, opportunities, onPostJob, onManage }: any) {

  return (

    <div>

      <div className="dashboard-stats" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>

        <div>

          <strong>{metrics.active_jobs}</strong>

          <span>Active Jobs</span>

        </div>

        <div>

          <strong>{metrics.active_internships}</strong>

          <span>Active Internships</span>

        </div>

        <div>

          <strong>{metrics.pending_review}</strong>

          <span>In Review</span>

        </div>

        <div>

          <strong>{metrics.drafts}</strong>

          <span>Drafts</span>

        </div>

        <div>

          <strong>{metrics.closed}</strong>

          <span>Closed</span>

        </div>

      </div>



      <div style={{ marginTop: '32px' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>

          <h3>Recent Postings</h3>

          <button className="text-link" onClick={onManage}>View all postings</button>

        </div>



        {opportunities.length === 0 ? (

          <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

            <Briefcase size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />

            <p>No opportunities posted yet. Create your first job or internship listing to discover students.</p>

            <button className="button" onClick={onPostJob} style={{ marginTop: '12px' }}>Post Your First Opportunity</button>

          </div>

        ) : (

          <div className="record-list">

            {opportunities.slice(0, 5).map((o: any) => (

              <div className="record" key={o.id}>

                <div>

                  <span className={`label ${o.opportunity_type === 'internship' ? 'outline' : ''}`} style={{ marginRight: '8px' }}>

                    {o.opportunity_type.toUpperCase()}

                  </span>

                  <span className={`status-pill status-${o.status}`}>

                    {o.status.replace('_', ' ')}

                  </span>

                  <h3 style={{ marginTop: '8px' }}>{o.title}</h3>

                  <p style={{ fontSize: '13px', color: 'var(--muted)' }}>

                    {o.work_mode} · {o.employment_type} · {o.location || 'Location unstated'}

                  </p>

                </div>

                <button className="button outline small" onClick={onManage}>Manage</button>

              </div>

            ))}

          </div>

        )}

      </div>

    </div>

  );

}



function CompanyProfileTab({ company, onSaved }: { company: any; onSaved: () => void }) {

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState('');



  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {

    e.preventDefault();

    setBusy(true);

    setError('');

    const fd = new FormData(e.currentTarget);

    const payload = Object.fromEntries(fd.entries());

    try {

      await api('/company/profile/', 'PATCH', payload);

      onSaved();

    } catch (err: any) {

      setError(err.message || 'Failed to update company profile.');

    } finally {

      setBusy(false);

    }

  }



  return (

    <div className="panel">

      <h3>Company Profile & Recruiting Details</h3>

      <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '24px' }}>

        This information appears publicly on your published job and internship postings so students can verify your organization.

      </p>



      <form onSubmit={handleSubmit} className="form-stack">

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>Company Name

            <input name="name" defaultValue={company?.name || ''} required />

          </label>

          <label>Industry

            <input name="industry" defaultValue={company?.industry || ''} placeholder="e.g. Software, Healthcare, FinTech" />

          </label>

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>Headquarters / Location

            <input name="city" defaultValue={company?.city || ''} placeholder="e.g. Bengaluru, Karnataka" />

          </label>

          <label>Company Size

            <select name="company_size" defaultValue={company?.company_size || ''}>

              <option value="">Select size</option>

              <option value="1-10">1-10 employees (Startup)</option>

              <option value="11-50">11-50 employees</option>

              <option value="51-200">51-200 employees</option>

              <option value="201-500">201-500 employees</option>

              <option value="500+">500+ employees (Enterprise)</option>

            </select>

          </label>

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>Official Website (HTTPS)

            <input name="website" type="url" defaultValue={company?.website || ''} required placeholder="https://company.com" />

          </label>

          <label>Official Careers Portal URL (HTTPS)

            <input name="careers_website" type="url" defaultValue={company?.careers_website || ''} placeholder="https://company.com/careers" />

          </label>

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>General Contact Email

            <input name="contact_email" type="email" defaultValue={company?.contact_email || ''} required />

          </label>

          <label>Dedicated Recruitment Email

            <input name="recruitment_email" type="email" defaultValue={company?.recruitment_email || ''} placeholder="careers@company.com" />

          </label>

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>Contact Person / Lead Recruiter

            <input name="contact_person" defaultValue={company?.contact_person || ''} placeholder="Full Name" />

          </label>

          <label>Company Logo URL (HTTPS)

            <input name="logo_url" type="url" defaultValue={company?.logo_url || ''} placeholder="https://example.com/logo.png" />

          </label>

        </div>



        <label>About the Company

          <textarea name="description" rows={4} defaultValue={company?.description || ''} placeholder="Describe your mission, products, and engineering culture..." />

        </label>



        {error && <p className="form-error" role="alert">{error}</p>}



        <button className="button" disabled={busy} style={{ alignSelf: 'flex-start' }}>

          {busy ? 'Saving Profile…' : 'Save Company Profile'}

        </button>

      </form>

    </div>

  );

}



function OpportunityFormTab({ editingOpp, defaultType, onSaved, onCancel }: any) {

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState('');

  const [oppType, setOppType] = useState<'job' | 'internship'>(editingOpp?.opportunity_type || defaultType);
  const [applicationMode,setApplicationMode]=useState(editingOpp?.recruitment_email?(editingOpp?.careers_url?'both':'email'):(editingOpp?.careers_url?'website':'both'));



  async function handleSave(submitForReview = false) {

    const form = document.getElementById('opp-form') as HTMLFormElement;

    if (!form.reportValidity()) return;



    setBusy(true);

    setError('');

    const fd = new FormData(form);

    const data: any = Object.fromEntries(fd.entries());



    // Clean array

    data.required_skills = data.skills_input ? data.skills_input.split(',').map((s: string) => s.trim()).filter(Boolean) : [];

    delete data.skills_input;
    if(applicationMode==='website')data.recruitment_email='';
    if(applicationMode==='email')data.careers_url='';



    data.is_paid = data.is_paid === 'true';

    if (!data.openings) delete data.openings;

    else data.openings = Number(data.openings);

    if (!data.deadline) delete data.deadline;



    try {

      let resultOpp;

      if (editingOpp) {

        resultOpp = await api(`/company/opportunities/${editingOpp.id}/`, 'PATCH', data);

        if (submitForReview) {

          await api(`/company/opportunities/${editingOpp.id}/submit/`, 'POST');

        }

      } else {

        resultOpp = await api('/company/opportunities/', 'POST', data);

        if (submitForReview) {

          await api(`/company/opportunities/${resultOpp.id}/submit/`, 'POST');

        }

      }

      onSaved();

    } catch (err: any) {

      setError(err.message || 'Failed to save opportunity.');

    } finally {

      setBusy(false);

    }

  }



  return (

    <div className="panel">

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>

        <h3>{editingOpp ? `Edit ${editingOpp.opportunity_type === 'internship' ? 'Internship' : 'Job'}` : `Post New ${oppType === 'internship' ? 'Internship' : 'Job'}`}</h3>

        <button type="button" className="text-link" onClick={onCancel}>Cancel</button>

      </div>



      {editingOpp?.status === 'approved' && (

        <div className="notice" style={{ marginBottom: '20px', borderLeftColor: '#F59E0B' }}>

          <strong>Note:</strong> This posting is currently published. Saving modifications to content or application links will automatically re-queue it for Super Admin review before republication.

        </div>

      )}



      <form id="opp-form" onSubmit={(e) => { e.preventDefault(); handleSave(false); }} className="form-stack">

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

          <label>Opportunity Type

            <select name="opportunity_type" value={oppType} onChange={(e) => setOppType(e.target.value as any)}>

              <option value="job">Full-time / Part-time Job</option>

              <option value="internship">Student Internship</option>

            </select>

          </label>

          <label>Role Title

            <input name="title" defaultValue={editingOpp?.title || ''} required placeholder="e.g. Junior Python Developer" />

          </label>

        </div>



        <label>Department<input name="department" defaultValue={editingOpp?.department || ''} placeholder="Engineering / Analytics"/></label>

        <label>Department<input name="department" defaultValue={editingOpp?.department || ''} placeholder="Engineering / Analytics"/></label>
        <label>Detailed Description

          <textarea name="description" rows={6} defaultValue={editingOpp?.description || ''} required minLength={30} placeholder="Describe responsibilities, team structure, tech stack, and what the candidate will work on..." />

        </label>



        <label>Responsibilities<textarea name="responsibilities" defaultValue={editingOpp?.responsibilities || ''} rows={3}/></label>

        <label>Eligible graduation years<input name="eligible_graduation_years" defaultValue={editingOpp?.eligible_graduation_years || ''} placeholder="2026, 2027, 2028"/></label>

        <label>Selection process<textarea name="selection_process" defaultValue={editingOpp?.selection_process || ''} rows={2}/></label>

        <label>Benefits<textarea name="benefits" defaultValue={editingOpp?.benefits || ''} rows={2}/></label>

        <label>Responsibilities<textarea name="responsibilities" defaultValue={editingOpp?.responsibilities || ''} rows={3}/></label>
        <label>Eligible graduation years<input name="eligible_graduation_years" defaultValue={editingOpp?.eligible_graduation_years || ''} placeholder="2026, 2027, 2028"/></label>
        <label>Selection process<textarea name="selection_process" defaultValue={editingOpp?.selection_process || ''} rows={2}/></label>
        <label>Benefits<textarea name="benefits" defaultValue={editingOpp?.benefits || ''} rows={2}/></label>
        <label>Required Skills (comma separated)

          <input name="skills_input" defaultValue={editingOpp?.required_skills?.join(', ') || ''} placeholder="e.g. Python, Django, React, REST APIs" />

        </label>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>

          <label>Employment Type

            <select name="employment_type" defaultValue={editingOpp?.employment_type || 'full_time'}>

              <option value="full_time">Full-time</option>

              <option value="part_time">Part-time</option>

              <option value="contract">Contract</option>

            </select>

          </label>



          <label>Work Mode

            <select name="work_mode" defaultValue={editingOpp?.work_mode || 'on_site'}>

              <option value="on_site">On-site</option>

              <option value="remote">Remote</option>

              <option value="hybrid">Hybrid</option>

            </select>

          </label>



          <label>Location

            <input name="location" defaultValue={editingOpp?.location || ''} placeholder="e.g. Bengaluru / Remote" />

          </label>

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>

          <label>{oppType === 'internship' ? 'Stipend Amount' : 'Salary Range'}

            <input name="compensation" defaultValue={editingOpp?.compensation || ''} placeholder={oppType === 'internship' ? 'e.g. ₹15,000 / month' : 'e.g. ₹6-8 LPA'} />

          </label>



          <label>Remuneration Status

            <select name="is_paid" defaultValue={editingOpp?.is_paid !== false ? 'true' : 'false'}>

              <option value="true">Paid Position</option>

              <option value="false">Unpaid</option>

            </select>

          </label>



          <label>Number of Openings

            <input name="openings" type="number" min={1} defaultValue={editingOpp?.openings || ''} placeholder="e.g. 2" />

          </label>



          {oppType === 'internship' && (

            <label>Internship Duration

              <input name="duration" defaultValue={editingOpp?.duration || ''} placeholder="e.g. 3 Months" />

            </label>

          )}

        </div>



        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>

          <label>Required Qualification

            <input name="qualification" defaultValue={editingOpp?.qualification || ''} placeholder="e.g. B.E / B.Tech / BCA" />

          </label>

          <label>Experience Required

            <input name="experience_level" defaultValue={editingOpp?.experience_level || ''} placeholder="e.g. Freshers / 0-1 year" />

          </label>

          <label>Application Deadline (Optional)

            <input name="deadline" type="date" defaultValue={editingOpp?.deadline || ''} />

          </label>

        </div>



        <div className="panel" style={{ background: 'var(--cream)', borderColor: '#E8E5DF' }}>

          <h4 style={{ margin: '0 0 8px' }}>Application Destination (At least one required for approval)</h4><label>How should students apply?<select value={applicationMode} onChange={e=>setApplicationMode(e.target.value)}><option value="both">WOC email application and official website</option><option value="email">Apply through WOC — profile and PDF resume by email</option><option value="website">Official website only</option></select></label>

          <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 16px' }}>

            Choose how you want to receive applications. WOC email applications include student-consented profile details and their PDF resume.

          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>

            <label hidden={applicationMode==='website'}>Recruitment Application Email

              <input name="recruitment_email" type="email" disabled={applicationMode==='website'} required={applicationMode==='email'} defaultValue={editingOpp?.recruitment_email || ''} placeholder="jobs@company.com" />

            </label>

            <label hidden={applicationMode==='email'}>Official Careers Webpage Link (HTTPS)

              <input name="careers_url" type="url" disabled={applicationMode==='email'} required={applicationMode==='website'} defaultValue={editingOpp?.careers_url || ''} placeholder="https://company.com/apply/job-id" />

            </label>

          </div>

        </div>



        {error && <p className="form-error" role="alert">{error}</p>}



        <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>

          <button type="button" className="button" disabled={busy} onClick={() => handleSave(true)}>

            {busy ? 'Saving…' : 'Submit for Super Admin Review'}

          </button>

          <button type="button" className="button outline" disabled={busy} onClick={() => handleSave(false)}>

            Save as Draft

          </button>

          <button type="button" className="text-link" onClick={onCancel} style={{ marginLeft: 'auto' }}>

            Cancel

          </button>

        </div>

      </form>

    </div>

  );

}



function ManageOpportunitiesTab({ opportunities, totalCount, hasNext, hasPrev, page, setPage, filter, setFilter, loading, onEdit, onUpdated }: any) {

  const { toast } = useWoc();

  const [actionBusy, setActionBusy] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(totalCount / 20));

  const filtered = opportunities;



  async function handleSubmitReview(id: string) {

    setActionBusy(id);

    try {

      await api(`/company/opportunities/${id}/submit/`, 'POST');

      toast('Opportunity submitted for review.');

      onUpdated();

    } catch (err: any) {

      toast(err.message || 'Failed to submit.');

    } finally {

      setActionBusy(null);

    }

  }



  async function handleClose(id: string) {

    if (!window.confirm('Are you sure you want to close this opportunity? It will be removed from the public portal.')) return;

    setActionBusy(id);

    try {

      await api(`/company/opportunities/${id}/close/`, 'POST');

      toast('Opportunity closed.');

      onUpdated();

    } catch (err: any) {

      toast(err.message || 'Failed to close.');

    } finally {

      setActionBusy(null);

    }

  }



  async function handleDeleteDraft(id: string) {

    if (!window.confirm('Delete this draft permanently?')) return;

    setActionBusy(id);

    try {

      await api(`/company/opportunities/${id}/`, 'DELETE');

      toast('Draft deleted.');

      onUpdated();

    } catch (err: any) {

      toast(err.message || 'Failed to delete draft.');

    } finally {

      setActionBusy(null);

    }

  }



  return (

    <div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>

        {['all', 'draft', 'pending_review', 'approved', 'rejected', 'closed'].map((st) => (

          <button

            key={st}

            className={`button small ${filter === st ? '' : 'outline'}`}

            onClick={() => { setFilter(st); setPage(1); }}

          >

            {st === 'all' ? 'All Opportunities' : st.replace('_', ' ').toUpperCase()}

          </button>

        ))}

      </div>



      {loading ? (

        <p>Loading opportunities…</p>

      ) : filtered.length === 0 ? (

        <div className="panel" style={{ textAlign: 'center', padding: '40px' }}>

          <p>No opportunities match the selected filter.</p>

        </div>

      ) : (

        <>

          <div className="record-list">

          {filtered.map((opp: any) => (

            <div className="record" key={opp.id} style={{ alignItems: 'flex-start' }}>

              <div style={{ flex: 1 }}>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>

                  <span className={`label ${opp.opportunity_type === 'internship' ? 'outline' : ''}`}>

                    {opp.opportunity_type.toUpperCase()}

                  </span>

                  <span className={`status-pill status-${opp.status}`}>

                    {opp.status.replace('_', ' ')}

                  </span>

                  {opp.deadline && (

                    <span style={{ fontSize: '12px', color: 'var(--muted)' }}>

                      Deadline: {new Date(opp.deadline).toLocaleDateString('en-IN')}

                    </span>

                  )}

                </div>



                <h3>{opp.title}</h3>

                <p style={{ fontSize: '14px', margin: '4px 0 8px' }}>

                  {opp.work_mode} · {opp.employment_type} · {opp.location || 'Location unstated'} · {opp.compensation || (opp.is_paid ? 'Paid' : 'Unpaid')}

                </p>



                {opp.review_note && (

                  <div style={{ background: '#FEF3C7', padding: '8px 12px', borderRadius: '4px', fontSize: '13px', color: '#92400E', marginTop: '8px' }}>

                    <strong>Moderation feedback:</strong> {opp.review_note}

                  </div>

                )}

              </div>



              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>

                {opp.status === 'approved' && (

                  <Link href={`/careers/opportunity/?id=${opp.id}`} className="button small outline" target="_blank">

                    <ExternalLink size={14} style={{ marginRight: '4px' }} /> View Live

                  </Link>

                )}



                {['draft', 'rejected'].includes(opp.status) && (

                  <button

                    className="button small"

                    disabled={actionBusy === opp.id}

                    onClick={() => handleSubmitReview(opp.id)}

                  >

                    Submit for Review

                  </button>

                )}



                {opp.status !== 'closed' && (

                  <button className="button small outline" onClick={() => onEdit(opp)}>

                    <Edit size={14} style={{ marginRight: '4px' }} /> Edit

                  </button>

                )}



                {opp.status === 'approved' && (

                  <button

                    className="button small outline"

                    style={{ color: 'var(--crimson)', borderColor: 'var(--crimson)' }}

                    disabled={actionBusy === opp.id}

                    onClick={() => handleClose(opp.id)}

                  >

                    Close

                  </button>

                )}



                {opp.status === 'draft' && (

                  <button

                    className="icon-button"

                    title="Delete draft"

                    disabled={actionBusy === opp.id}

                    onClick={() => handleDeleteDraft(opp.id)}

                  >

                    <Trash2 size={16} style={{ color: 'var(--crimson)' }} />

                  </button>

                )}

              </div>

            </div>

          ))}

        </div>



        {totalPages > 1 && (

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '24px' }}>

            <button

              type="button"

              className="button small outline"

              disabled={!hasPrev || page <= 1}

              onClick={() => setPage((p: number) => Math.max(1, p - 1))}

            >

              Previous

            </button>

            <span style={{ fontSize: '13px', color: 'var(--muted)' }}>

              Page {page} of {totalPages} ({totalCount} opportunities)

            </span>

            <button

              type="button"

              className="button small outline"

              disabled={!hasNext || page >= totalPages}

              onClick={() => setPage((p: number) => p + 1)}

            >

              Next

            </button>

          </div>

        )}

        </>

      )}

    </div>

  );

}


function CompanyPartnerships(){const [page,setPage]=useState(1);const {data,error,isLoading}=useQuery({queryKey:['company-partnerships',page],queryFn:()=>api(`/company/partnerships/?page=${page}`)});return <section className="panel"><h2>College partnerships</h2><p>Read-only relationships managed by colleges.</p>{isLoading&&<p>Loading…</p>}{error&&<p role="alert">{error.message}</p>}{data?.results?.map((p:any)=><div className="record" key={p.id}><strong>{p.institution_name}</strong><p>{p.partnership_type} · {p.status}</p></div>)}{data&&!data.results.length&&<p>No college partnerships yet.</p>}<button className="text-link" disabled={!data?.previous} onClick={()=>setPage(page-1)}>Previous</button> <button className="text-link" disabled={!data?.next} onClick={()=>setPage(page+1)}>Next</button></section>}
