'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Briefcase, Search, MapPin, Building2, Calendar, Mail,
  ExternalLink, ArrowLeft, CheckCircle, Clock, ShieldCheck, Filter, Bookmark
} from 'lucide-react';
import { api } from '@/lib/api';
import { useWoc } from './Platform';

export function CareerPortal() {
  const [tab, setTab] = useState<'all' | 'job' | 'internship'>('all');
  const [search, setSearch] = useState('');
  const [workMode, setWorkMode] = useState('');
  const [empType, setEmpType] = useState('');
  const [page, setPage] = useState(1);

  // Fetch opportunities from Django API
  const queryParams = new URLSearchParams();
  if (tab !== 'all') queryParams.set('type', tab);
  if (workMode) queryParams.set('work_mode', workMode);
  if (empType) queryParams.set('employment_type', empType);
  if (search) queryParams.set('q', search);
  queryParams.set('page', String(page));

  const { data, isLoading, error } = useQuery({
    queryKey: ['public-opportunities', tab, workMode, empType, search, page],
    queryFn: () => api(`/opportunities/?${queryParams.toString()}`),
  });

  const opportunities = data?.results || [];
  const totalCount = data?.count || 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / 20));
  const hasNext = !!data?.next;
  const hasPrev = !!data?.previous;

  return (
    <main id="main">
      <section className="hero page-hero" style={{ minHeight: 'auto', padding: '60px 0 40px' }}>
        <div className="container hero-content">
          <p className="eyebrow">CAREERS & OPPORTUNITIES</p>
          <h1>Find your next step.<br />Connect with real industry.</h1>
          <p style={{ maxWidth: '640px' }}>
            Discover verified internships, fresher opportunities, and roles from approved company partners. Apply directly via official recruitment channels.
          </p>
          <div style={{ marginTop: '20px' }}>
            <Link href="/onboarding/" className="button small outline" style={{ background: 'rgba(255,255,255,0.1)' }}>
              Are you an employer? Register your company
            </Link>
          </div>
        </div>
      </section>

      <section className="section container">
        {/* Navigation / Filter Tabs */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div className="lesson-tabs" style={{ margin: 0 }}>
            <button aria-pressed={tab === 'all'} onClick={() => { setTab('all'); setPage(1); }}>
              All Opportunities
            </button>
            <button aria-pressed={tab === 'job'} onClick={() => { setTab('job'); setPage(1); }}>
              Full-time Jobs
            </button>
            <button aria-pressed={tab === 'internship'} onClick={() => { setTab('internship'); setPage(1); }}>
              Internships
            </button>
          </div>

          <span style={{ fontSize: '13px', color: 'var(--muted)' }}>
            {isLoading ? 'Checking opportunities…' : `${data?.count || 0} active openings`}
          </span>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="catalogue-toolbar" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '32px' }}>
          <label className="search-input" style={{ gridColumn: 'span 2' }}>
            <Search size={18} />
            <input
              placeholder="Search by role, company, or skills (e.g. Python, React, Design)…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </label>

          <label>Work Mode
            <select value={workMode} onChange={(e) => { setWorkMode(e.target.value); setPage(1); }}>
              <option value="">All Work Modes</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="on_site">On-site</option>
            </select>
          </label>

          <label>Employment Type
            <select value={empType} onChange={(e) => { setEmpType(e.target.value); setPage(1); }}>
              <option value="">All Types</option>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
            </select>
          </label>
        </div>

        {/* Content Stream */}
        {isLoading ? (
          <div className="panel" style={{ textAlign: 'center', padding: '40px' }}>
            <Clock size={32} style={{ color: 'var(--crimson)', margin: '0 auto 12px' }} />
            <p>Loading published opportunities from verified employers…</p>
          </div>
        ) : error ? (
          <div className="panel" style={{ textAlign: 'center', padding: '40px', borderColor: 'var(--crimson)' }}>
            <p style={{ color: 'var(--crimson)' }}>Unable to load live opportunities. Please verify backend connection.</p>
          </div>
        ) : opportunities.length === 0 ? (
          <div className="empty-state" style={{ padding: '60px 20px' }}>
            <Briefcase size={40} />
            <h2>No active opportunities match your criteria.</h2>
            <p>Try adjusting your search terms or filters to explore more openings.</p>
            <button className="button outline small" onClick={() => { setSearch(''); setWorkMode(''); setEmpType(''); setTab('all'); }}>
              Reset Filters
            </button>
          </div>
        ) : (
          <>
            <div className="three-grid">
              {opportunities.map((opp: any) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))}
            </div>

            {totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '36px' }}>
                <button
                  type="button"
                  className="button small outline"
                  disabled={!hasPrev || page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <span style={{ fontSize: '14px', color: 'var(--muted)' }}>
                  Page {page} of {totalPages} ({totalCount} opportunities)
                </span>
                <button
                  type="button"
                  className="button small outline"
                  disabled={!hasNext || page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}

function OpportunityCard({ opportunity: opp }: { opportunity: any }) {
  return (
    <div className="card feature-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <span className={`label ${opp.opportunity_type === 'internship' ? 'outline' : ''}`}>
          {opp.opportunity_type.toUpperCase()}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <MapPin size={13} /> {opp.work_mode}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        {opp.company_logo ? (
          <img src={opp.company_logo} alt={opp.company_name} style={{ width: '36px', height: '36px', borderRadius: '6px', objectFit: 'contain' }} />
        ) : (
          <div style={{ width: '36px', height: '36px', borderRadius: '6px', background: '#EAE7E1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 size={18} style={{ color: 'var(--muted)' }} />
          </div>
        )}
        <div>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 600 }}>{opp.company_name}</h4>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{opp.location || opp.company_city || 'India'}</span>
        </div>
      </div>

      <h3 style={{ fontSize: '18px', margin: '0 0 10px', lineHeight: 1.3 }}>
        <Link href={`/careers/opportunity/?id=${opp.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
          {opp.title}
        </Link>
      </h3>

      <p style={{ fontSize: '13px', color: '#4B5563', flex: 1, margin: '0 0 16px', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {opp.description}
      </p>

      {opp.required_skills?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
          {opp.required_skills.slice(0, 3).map((sk: string) => (
            <span key={sk} style={{ fontSize: '11px', background: '#F3F4F6', padding: '3px 8px', borderRadius: '4px', color: '#374151' }}>
              {sk}
            </span>
          ))}
          {opp.required_skills.length > 3 && (
            <span style={{ fontSize: '11px', color: 'var(--muted)', alignSelf: 'center' }}>
              +{opp.required_skills.length - 3} more
            </span>
          )}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #EAE7E1', paddingTop: '14px', marginTop: 'auto' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--crimson)' }}>
          {opp.compensation || (opp.is_paid ? 'Paid' : 'Unpaid')}
        </span>
        <Link href={`/careers/opportunity/?id=${opp.id}`} className="button small outline">
          View Details
        </Link>
      </div>
    </div>
  );
}

export function OpportunityDetail() {
  const { user, demo, toast } = useWoc();
  const [oppId, setOppId] = useState<string>('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (id) setOppId(id);
  }, []);

  const { data: opp, isLoading, error } = useQuery({
    queryKey: ['opportunity-detail', oppId],
    queryFn: () => api(`/opportunities/${oppId}/`),
    enabled: !!oppId,
  });

  async function trackClick() {
    if (!user || demo || !oppId) return;
    try {
      await api(`/student/opportunities/${oppId}/track/`, 'POST', { action: 'click' });
    } catch {
      // Non-blocking
    }
  }

  async function toggleBookmark() {
    if (!user || demo || !oppId) {
      toast('Please sign in to save opportunities.');
      return;
    }
    try {
      const res = await api(`/student/opportunities/${oppId}/save/`, 'POST', { action: 'toggle' });
      setSaved(!!res.saved);
      toast(res.saved ? 'Saved to your Student Dashboard.' : 'Removed from saved opportunities.');
    } catch (err: any) {
      toast(err?.message || 'Could not update bookmark.');
    }
  }

  if (!oppId) {
    return (
      <main id="main" className="section container narrow">
        <Link href="/careers/" className="text-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
          <ArrowLeft size={16} /> Back to Careers
        </Link>
        <div className="panel" style={{ textAlign: 'center', padding: '40px' }}>
          <h2>No opportunity selected.</h2>
          <p>Please browse our opportunities catalogue to select an opening.</p>
          <Link href="/careers/" className="button">Browse Opportunities</Link>
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main id="main" className="section container narrow" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <Clock size={32} style={{ color: 'var(--crimson)', margin: '0 auto 12px' }} />
        <p>Loading opportunity details…</p>
      </main>
    );
  }

  if (error || !opp) {
    return (
      <main id="main" className="section container narrow">
        <Link href="/careers/" className="text-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
          <ArrowLeft size={16} /> Back to Careers
        </Link>
        <div className="panel" style={{ textAlign: 'center', padding: '40px', borderColor: 'var(--crimson)' }}>
          <h2>Opportunity Not Available</h2>
          <p style={{ color: 'var(--muted)' }}>
            This job or internship listing is no longer active, has expired, or is pending review.
          </p>
          <Link href="/careers/" className="button">Explore Other Openings</Link>
        </div>
      </main>
    );
  }

  // Pre-formatted mailto application link
  const mailSubject = encodeURIComponent(`Application for ${opp.title} via WOC`);
  const mailBody = encodeURIComponent(
    `Dear Hiring Team at ${opp.company_name},\n\n` +
    `I am writing to express my interest in the ${opp.title} (${opp.opportunity_type}) opportunity discovered on THE WOC platform.\n\n` +
    `Please find my qualifications and details summarized below:\n` +
    `- Highest Qualification: \n` +
    `- Key Skills: ${opp.required_skills?.join(', ') || ''}\n` +
    `- Contact Number: \n\n` +
    `I have attached my resume for your review. I look forward to the possibility of discussing how my skills contribute to your team.\n\n` +
    `Sincerely,\n` +
    `[Your Full Name]`
  );
  const mailtoLink = `mailto:${opp.recruitment_email}?subject=${mailSubject}&body=${mailBody}`;

  return (
    <main id="main">
      <div className="container" style={{ paddingTop: '32px' }}>
        <Link href="/careers/" className="text-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '24px' }}>
          <ArrowLeft size={16} /> Back to Careers Catalogue
        </Link>
      </div>

      <div className="container section detail-layout">
        <article>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
            <span className={`label ${opp.opportunity_type === 'internship' ? 'outline' : ''}`}>
              {opp.opportunity_type.toUpperCase()}
            </span>
            <span className="status-pill status-approved">VERIFIED EMPLOYER</span>
          </div>

          <h1 style={{ fontSize: '32px', lineHeight: 1.2, margin: '0 0 16px' }}>{opp.title}</h1>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
            {opp.company_logo ? (
              <img src={opp.company_logo} alt={opp.company_name} style={{ width: '48px', height: '48px', borderRadius: '8px', objectFit: 'contain' }} />
            ) : (
              <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#EAE7E1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Building2 size={24} style={{ color: 'var(--muted)' }} />
              </div>
            )}
            <div>
              <h3 style={{ margin: 0, fontSize: '18px' }}>{opp.company_name}</h3>
              {opp.company_website && (
                <a href={opp.company_website} target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: 'var(--crimson)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  {opp.company_website.replace(/^https?:\/\//, '')} <ExternalLink size={12} />
                </a>
              )}
            </div>
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid #EAE7E1', margin: '24px 0' }} />

          {opp.department&&<p><strong>Department:</strong> {opp.department}</p>}
          {opp.eligible_graduation_years&&<p><strong>Eligible graduation years:</strong> {opp.eligible_graduation_years}</p>}
          {['responsibilities','selection_process','benefits'].map(key=>opp[key]?<section key={key}><h3>{key.replaceAll('_',' ')}</h3><p style={{whiteSpace:'pre-wrap'}}>{opp[key]}</p></section>:null)}
          <h3>About the Role</h3>
          <p style={{ whiteSpace: 'pre-line', lineHeight: 1.7, color: '#2B2A27', fontSize: '15px' }}>
            {opp.description}
          </p>

          {opp.required_skills?.length > 0 && (
            <div style={{ margin: '28px 0' }}>
              <h3 style={{ marginBottom: '12px' }}>Required Skills & Technologies</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {opp.required_skills.map((skill: string) => (
                  <span key={skill} style={{ background: '#F3F4F6', color: '#1F2937', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 500 }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {opp.qualification && (
            <div style={{ margin: '24px 0' }}>
              <h3 style={{ marginBottom: '8px' }}>Eligibility & Qualifications</h3>
              <p style={{ color: '#4B5563', fontSize: '14px' }}>{opp.qualification}</p>
            </div>
          )}
        </article>

        {/* Sidebar with Application Actions */}
        <aside>
          <div className="panel detail-card" style={{ position: 'sticky', top: '100px' }}>
            <h3 style={{ margin: '0 0 16px' }}>Opportunity Overview</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px', marginBottom: '24px' }}>
              <div>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>COMPENSATION / STIPEND</span>
                <strong style={{ fontSize: '16px', color: 'var(--crimson)' }}>
                  {opp.compensation || (opp.is_paid ? 'Paid Position' : 'Unpaid')}
                </strong>
              </div>

              <div>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>WORK MODE & LOCATION</span>
                <strong>{opp.work_mode.toUpperCase()} · {opp.location || opp.company_city || 'India'}</strong>
              </div>

              <div>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>EMPLOYMENT TYPE</span>
                <strong>{opp.employment_type.replace('_', ' ').toUpperCase()}</strong>
              </div>

              {opp.duration && (
                <div>
                  <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>DURATION</span>
                  <strong>{opp.duration}</strong>
                </div>
              )}

              {opp.openings && (
                <div>
                  <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>OPENINGS</span>
                  <strong>{opp.openings} vacancies</strong>
                </div>
              )}

              {opp.deadline && (
                <div>
                  <span style={{ color: 'var(--muted)', display: 'block', fontSize: '12px' }}>APPLICATION DEADLINE</span>
                  <strong>{new Date(opp.deadline).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}</strong>
                </div>
              )}
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid #EAE7E1', margin: '20px 0' }} />

            <h4 style={{ margin: '0 0 10px', fontSize: '14px' }}>Apply Directly to Employer</h4>

            {opp.recruitment_email && (
              <a href={mailtoLink} onClick={trackClick} className="button full" style={{ marginBottom: '10px' }}>
                <Mail size={16} style={{ marginRight: '6px' }} /> Apply by Email
              </a>
            )}

            {opp.careers_url && (
              <a
                href={opp.careers_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={trackClick}
                className="button full outline"
                style={{ marginBottom: '10px' }}
              >
                <ExternalLink size={16} style={{ marginRight: '6px' }} /> Apply on Company Website
              </a>
            )}

            {user && !demo && (
              <button type="button" onClick={toggleBookmark} className="button full outline" style={{ marginBottom: '10px' }}>
                <Bookmark size={16} style={{ marginRight: '6px', fill: saved ? 'currentColor' : 'none' }} />
                {saved ? 'Saved to Dashboard' : 'Save Opportunity'}
              </button>
            )}

            <p style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.4, margin: '14px 0 0' }}>
              <strong>Direct Application:</strong> WOC does not collect your resume or act as an ATS intermediary. You will apply directly to the employer via their official email or careers portal.
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
