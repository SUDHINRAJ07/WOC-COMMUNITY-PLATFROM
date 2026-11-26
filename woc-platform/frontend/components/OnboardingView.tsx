'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Building2, GraduationCap, Clock, CheckCircle, XCircle, AlertCircle, ExternalLink, ArrowRight } from 'lucide-react';
import { useWoc } from './Platform';
import { api } from '@/lib/api';
import {OrganizationEvidence} from './ProfileFiles';

export function OnboardingView({initialType}:{initialType?:'company'|'college'}={}) {
  const { user, toast } = useWoc();
  const [tab, setTab] = useState<'company' | 'college'>(initialType || 'company');

  useEffect(()=>{const intent=initialType || new URLSearchParams(window.location.search).get('type') || sessionStorage.getItem('woc-registration-role');if(intent==='college'||intent==='company')setTab(intent)},[initialType]);
  // Company Form state
  const [companyName, setCompanyName] = useState('');
  const [companyCity, setCompanyCity] = useState('');
  const [companyWebsite, setCompanyWebsite] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [companyDesc, setCompanyDesc] = useState('');
  const [companyBusy, setCompanyBusy] = useState(false);
  const [companyError, setCompanyError] = useState('');
  const [companySuccess, setCompanySuccess] = useState('');

  // College Form state
  const [collegeName, setCollegeName] = useState('');
  const [collegeCity, setCollegeCity] = useState('');
  const [collegeWebsite, setCollegeWebsite] = useState('');
  const [collegeEmail, setCollegeEmail] = useState('');
  const [collegeAddress, setCollegeAddress] = useState('');
  const [collegeBusy, setCollegeBusy] = useState(false);
  const [collegeError, setCollegeError] = useState('');
  const [collegeSuccess, setCollegeSuccess] = useState('');

  // Queries for existing onboarding submissions
  const { data: userCompanies, refetch: refetchCompanies, isLoading: loadingCompanies } = useQuery({
    queryKey: ['my-company-onboarding', user?.id],
    queryFn: () => api('/onboarding/company/'),
    enabled: !!user,
  });

  const { data: userColleges, refetch: refetchColleges, isLoading: loadingColleges } = useQuery({
    queryKey: ['my-college-onboarding', user?.id],
    queryFn: () => api('/onboarding/college/'),
    enabled: !!user,
  });

  const companiesList = userCompanies?.results || [];
  const collegesList = userColleges?.results || [];

  async function handleCompanySubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!user) {
      setCompanyError('Please sign in or create an account first.');
      return;
    }
    setCompanyBusy(true);
    setCompanyError('');
    setCompanySuccess('');

    try {
      const extra = Object.fromEntries(new FormData(e.target as HTMLFormElement));
      await api('/onboarding/company/', 'POST', {
        contact_phone:extra.contact_phone || '', state:extra.state || '', registration_reference:extra.registration_reference || '',industry:extra.industry || '',company_size:extra.company_size || '',contact_person:extra.contact_person || '',recruitment_email:extra.recruitment_email || '',
        name: companyName.trim(),
        city: companyCity.trim() || undefined,
        website: companyWebsite.trim(),
        contact_email: companyEmail.trim(),
        description: companyDesc.trim() || undefined,
      });
      sessionStorage.removeItem('woc-registration-role');
      setCompanySuccess('Company onboarding request submitted! It is now pending Super Admin review.');
      setCompanyName('');
      setCompanyCity('');
      setCompanyWebsite('');
      setCompanyEmail('');
      setCompanyDesc('');
      refetchCompanies();
      toast('Company onboarding request submitted.');
    } catch (err: any) {
      setCompanyError(err.message || 'Failed to submit company onboarding request.');
    } finally {
      setCompanyBusy(false);
    }
  }

  async function handleCollegeSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!user) {
      setCollegeError('Please sign in or create an account first.');
      return;
    }
    setCollegeBusy(true);
    setCollegeError('');
    setCollegeSuccess('');

    try {
      const extra = Object.fromEntries(new FormData(e.target as HTMLFormElement));
      await api('/onboarding/college/', 'POST', {
        contact_phone:extra.contact_phone || '', state:extra.state || '', registration_reference:extra.registration_reference || '',
        name: collegeName.trim(),
        city: collegeCity.trim(),
        website: collegeWebsite.trim() || undefined,
        contact_email: collegeEmail.trim(),
        address: collegeAddress.trim() || undefined,
      });
      sessionStorage.removeItem('woc-registration-role');
      setCollegeSuccess('College onboarding request submitted! It is now pending Super Admin review.');
      setCollegeName('');
      setCollegeCity('');
      setCollegeWebsite('');
      setCollegeEmail('');
      setCollegeAddress('');
      refetchColleges();
      toast('College onboarding request submitted.');
    } catch (err: any) {
      setCollegeError(err.message || 'Failed to submit college onboarding request.');
    } finally {
      setCollegeBusy(false);
    }
  }

  return (
    <main id="main" className="organization-onboarding">
      <section className="organization-intro">
        <div className="container hero-content">
          <p className="eyebrow">OFFICIAL ORGANIZATION DETAILS</p>
          <h1>Join as {tab==='college'?'College':'Company'}.<br/>Build with WOC.</h1>
          <p style={{ maxWidth: '640px' }}>
            Register your institution or enterprise to publish opportunities, sponsor challenges, and engage with ambitious students across colleges.
          </p>
        </div>
      </section>

      <section className="section container narrow">
        {/* Tab switcher */}
        <div style={{ display: initialType?'none':'flex', gap: '12px', borderBottom: '2px solid var(--border)', marginBottom: '32px' }}>
          <button
            onClick={() => setTab('company')}
            style={{
              padding: '12px 20px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              borderBottom: tab === 'company' ? '3px solid var(--crimson)' : '3px solid transparent',
              color: tab === 'company' ? 'var(--crimson)' : 'var(--muted)',
              marginBottom: '-2px',
            }}
          >
            <Building2 size={18} /> For Companies & Employers
          </button>
          <button
            onClick={() => setTab('college')}
            style={{
              padding: '12px 20px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              borderBottom: tab === 'college' ? '3px solid var(--crimson)' : '3px solid transparent',
              color: tab === 'college' ? 'var(--crimson)' : 'var(--muted)',
              marginBottom: '-2px',
            }}
          >
            <GraduationCap size={18} /> For Colleges & Institutions
          </button>
        </div>

        {!user && (
          <div className="panel" style={{ background: '#fffbeb', borderColor: '#fef3c7', marginBottom: '24px', padding: '16px' }}>
            <p style={{ margin: 0, fontSize: '14px', color: '#92400e' }}>
              <strong>Note:</strong> You must be signed in with your personal or institutional email to register an organization.
              {' '}<Link href="/login/" className="text-link" style={{ fontWeight: 600 }}>Sign in here</Link> or <Link href="/register/" className="text-link" style={{ fontWeight: 600 }}>create an account</Link>.
            </p>
          </div>
        )}

        {/* Company Registration Section */}
        {tab === 'company' && (
          <div>
            <div className="panel" style={{ padding: '32px', marginBottom: '40px' }}>
              <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>Register Your Organization</h2>
              <p style={{ color: 'var(--muted)', fontSize: '14px', marginBottom: '24px' }}>
                Once verified by Super Admin, you will gain access to the Company Dashboard to post jobs, internships, and manage hiring destinations.
              </p>

              {companyError && <div className="form-error" role="alert" style={{ marginBottom: '16px' }}>{companyError}</div>}
              {companySuccess && <div className="success-box" role="alert" style={{ marginBottom: '16px' }}>{companySuccess}</div>}

              <form onSubmit={handleCompanySubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                  <label>
                    Company Name *
                    <input
                      required
                      maxLength={200}
                      placeholder="e.g. Acme Technologies India"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                    />
                  </label>
                  <label>
                    Corporate Website (HTTPS) *
                    <input
                      type="url"
                      required
                      placeholder="https://company.example.com"
                      value={companyWebsite}
                      onChange={(e) => setCompanyWebsite(e.target.value)}
                    />
                  </label>
                  <label>
                    Contact / Official Email *
                    <input
                      type="email"
                      required
                      placeholder="contact@company.example.com"
                      value={companyEmail}
                      onChange={(e) => setCompanyEmail(e.target.value)}
                    />
                  </label>
                  <label>
                    City / Primary Office
                    <input
                      maxLength={100}
                      placeholder="e.g. Chennai, Bengaluru, Mumbai"
                      value={companyCity}
                      onChange={(e) => setCompanyCity(e.target.value)}
                    />
                  </label>
                </div>

                <label style={{ marginTop: '16px', display: 'block' }}>
                  Company Overview & Mission
                  <textarea
                    rows={4}
                    maxLength={2000}
                    placeholder="Briefly describe what your organization does and what kinds of talent or student collaboration you are seeking…"
                    value={companyDesc}
                    onChange={(e) => setCompanyDesc(e.target.value)}
                  />
                </label>

                <div className="two-grid"><label>Official contact phone<input name="contact_phone" type="tel"/></label><label>State / region<input name="state"/></label></div><label>Official registration reference<input name="registration_reference"/></label><div className="two-grid"><label>Industry<input name="industry"/></label><label>Company size<select name="company_size"><option>1–10</option><option>11–50</option><option>51–200</option><option>201–500</option><option>500+</option></select></label></div><label>Official contact person<input name="contact_person"/></label><label>Recruitment email<input type="email" name="recruitment_email"/></label><div style={{ marginTop: '24px' }}>
                  <button type="submit" className="button" disabled={companyBusy || !user}>
                    {companyBusy ? 'Submitting…' : 'Submit Company for Approval'}
                  </button>
                </div>
              </form>
            </div>

            {/* Existing Company Submissions */}
            {user && (
              <div>
                <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Your Company Submissions</h3>
                {loadingCompanies ? (
                  <p>Loading your submissions…</p>
                ) : companiesList.length === 0 ? (
                  <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No company registrations found for your account.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {companiesList.map((comp: any) => (
                      <div key={comp.id} className="panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '16px' }}>{comp.name}</h4><OrganizationEvidence kind="company" id={comp.id}/>
                          <span style={{ fontSize: '13px', color: 'var(--muted)' }}>
                            {comp.city || 'Location unlisted'} · {comp.contact_email}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span
                            style={{
                              padding: '4px 10px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: 600,
                              textTransform: 'uppercase',
                              background: comp.approval_status === 'approved' ? '#dcfce7' : comp.approval_status === 'rejected' ? '#fee2e2' : '#fef9c3',
                              color: comp.approval_status === 'approved' ? '#166534' : comp.approval_status === 'rejected' ? '#991b1b' : '#854d0e',
                            }}
                          >
                            {comp.approval_status}
                          </span>
                          {comp.approval_status === 'approved' && (
                            <Link href="/company/" className="button small">
                              Go to Dashboard →
                            </Link>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* College Registration Section */}
        {tab === 'college' && (
          <div>
            <div className="panel" style={{ padding: '32px', marginBottom: '40px' }}>
              <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>Register Your College / Institution</h2>
              <p style={{ color: 'var(--muted)', fontSize: '14px', marginBottom: '24px' }}>
                Join as a recognized academic partner to empower students with verified skill certifications, campus challenges, and recruitment access.
              </p>

              {collegeError && <div className="form-error" role="alert" style={{ marginBottom: '16px' }}>{collegeError}</div>}
              {collegeSuccess && <div className="success-box" role="alert" style={{ marginBottom: '16px' }}>{collegeSuccess}</div>}

              <form onSubmit={handleCollegeSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                  <label>
                    Institution Name *
                    <input
                      required
                      maxLength={200}
                      placeholder="e.g. National Institute of Engineering"
                      value={collegeName}
                      onChange={(e) => setCollegeName(e.target.value)}
                    />
                  </label>
                  <label>
                    City / Campus Location *
                    <input
                      required
                      maxLength={100}
                      placeholder="e.g. Coimbatore, Chennai, Madurai"
                      value={collegeCity}
                      onChange={(e) => setCollegeCity(e.target.value)}
                    />
                  </label>
                  <label>
                    Official Contact Email *
                    <input
                      type="email"
                      required
                      placeholder="principal@institution.edu.in"
                      value={collegeEmail}
                      onChange={(e) => setCollegeEmail(e.target.value)}
                    />
                  </label>
                  <label>
                    Official Website (HTTPS)
                    <input
                      type="url"
                      placeholder="https://institution.edu.in"
                      value={collegeWebsite}
                      onChange={(e) => setCollegeWebsite(e.target.value)}
                    />
                  </label>
                </div>

                <label style={{ marginTop: '16px', display: 'block' }}>
                  Campus Address
                  <textarea
                    rows={3}
                    maxLength={2000}
                    placeholder="Full postal address of the campus…"
                    value={collegeAddress}
                    onChange={(e) => setCollegeAddress(e.target.value)}
                  />
                </label>

                <div className="two-grid"><label>Official contact phone<input name="contact_phone" type="tel"/></label><label>State / region<input name="state"/></label></div><label>Affiliation / institution code<input name="registration_reference"/></label><div style={{ marginTop: '24px' }}>
                  <button type="submit" className="button" disabled={collegeBusy || !user}>
                    {collegeBusy ? 'Submitting…' : 'Submit College for Approval'}
                  </button>
                </div>
              </form>
            </div>

            {/* Existing College Submissions */}
            {user && (
              <div>
                <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Your College Submissions</h3>
                {loadingColleges ? (
                  <p>Loading your submissions…</p>
                ) : collegesList.length === 0 ? (
                  <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No college registrations found for your account.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {collegesList.map((col: any) => (
                      <div key={col.id} className="panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '16px' }}>{col.name}</h4><OrganizationEvidence kind="college" id={col.id}/>
                          <span style={{ fontSize: '13px', color: 'var(--muted)' }}>
                            {col.city} · {col.contact_email}
                          </span>
                        </div>
                        <div>
                          <span
                            style={{
                              padding: '4px 10px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: 600,
                              textTransform: 'uppercase',
                              background: col.approval_status === 'approved' ? '#dcfce7' : col.approval_status === 'rejected' ? '#fee2e2' : '#fef9c3',
                              color: col.approval_status === 'approved' ? '#166534' : col.approval_status === 'rejected' ? '#991b1b' : '#854d0e',
                            }}
                          >
                            {col.approval_status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
