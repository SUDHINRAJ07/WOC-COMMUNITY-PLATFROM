'use client';
import {ProfileFiles} from './ProfileFiles';

import React, { useState, useEffect, ReactNode } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  User as UserIcon, GraduationCap, BookOpen, Layers, Briefcase,
  Bookmark, ClipboardList, Award, Bell, CheckCircle, Clock,
  ExternalLink, Search, PlayCircle, Sparkles, ShieldCheck, XCircle
} from 'lucide-react';
import { useWoc, Registration } from './Platform';
import { api } from '@/lib/api';
import { StudentEngagementTab } from './EngagementPanels';

type TabKey =
  | 'Overview'
  | 'My Profile'
  | 'My College'
  | 'My Learning'
  | 'My Batches'
  | 'Campus Engagement'
  | 'Jobs & Internships'
  | 'Saved Opportunities'
  | 'Application History'
  | 'Certificates'
  | 'Notifications';

const NAV_TABS: TabKey[] = [
  'Overview',
  'My Profile',
  'My College',
  'My Learning',
  'My Batches',
  'Campus Engagement',
  'Jobs & Internships',
  'Saved Opportunities',
  'Application History',
  'Certificates',
  'Notifications',
];

interface StudentDashboardProps {
  renderLearning: (record: Registration, close: () => void) => ReactNode;
  renderNotifications: (notifications: any, refetch: () => void) => ReactNode;
  renderPhoneVerification: () => ReactNode;
}

export function StudentDashboard({
  renderLearning,
  renderNotifications,
  renderPhoneVerification,
}: StudentDashboardProps) {
  const { user, demo, records, refresh, setUser, toast } = useWoc();
  const [tab, setTab] = useState<TabKey>('Overview');
  const [selectedRecord, setSelectedRecord] = useState<Registration | null>(null);
  const [otherModuleFilter, setOtherModuleFilter] = useState<string>('all');

  // Search & Filter states
  const [collegeQuery, setCollegeQuery] = useState('');
  const [batchFilter, setBatchFilter] = useState('all');
  const [oppSearch, setOppSearch] = useState('');
  const [oppType, setOppType] = useState('all');
  const [oppWorkMode, setOppWorkMode] = useState('');
  const [oppPage, setOppPage] = useState(1);
  const [appStatusFilter, setAppStatusFilter] = useState('all');

  // Modals & Busy states
  const [profileBusy, setProfileBusy] = useState(false);
  const [skillsInput, setSkillsInput] = useState('');
  const [interestsInput, setInterestsInput] = useState('');
  const [trackModalOpp, setTrackModalOpp] = useState<any>(null);
  const [trackBusy, setTrackBusy] = useState(false);

  useEffect(() => {
    if (user) {
      refresh();
      setSkillsInput((user.skills || []).join(', '));
      setInterestsInput((user.interests || []).join(', '));
    }
  }, [user?.id]);

  // Queries (enabled only when logged in & non-demo)
  const { data: notifications, refetch: refetchNotifications } = useQuery({
    queryKey: ['notifications', user?.id],
    queryFn: () => api('/notifications/'),
    enabled: !!user && !demo,
  });

  const { data: dashData, refetch: refetchDash, isLoading: loadingDash } = useQuery({
    queryKey: ['student-dashboard', user?.id],
    queryFn: () => api('/student/dashboard/'),
    enabled: !!user && !demo,
  });

  const { data: collegesData, refetch: refetchColleges, isLoading: loadingColleges } = useQuery({
    queryKey: ['student-colleges', user?.id, collegeQuery],
    queryFn: () => {
      const q = new URLSearchParams();
      if (collegeQuery.trim()) q.set('q', collegeQuery.trim());
      return api(`/student/colleges/?${q.toString()}`);
    },
    enabled: !!user && !demo && tab === 'My College',
  });

  const { data: batchesData, isLoading: loadingBatches } = useQuery({
    queryKey: ['student-batches', user?.id, batchFilter],
    queryFn: () => {
      const q = new URLSearchParams();
      if (batchFilter !== 'all') q.set('status', batchFilter);
      return api(`/student/batches/?${q.toString()}`);
    },
    enabled: !!user && !demo && tab === 'My Batches',
  });

  const { data: oppsData, isLoading: loadingOpps } = useQuery({
    queryKey: ['student-opps', oppType, oppWorkMode, oppSearch, oppPage],
    queryFn: () => {
      const q = new URLSearchParams();
      if (oppType !== 'all') q.set('type', oppType);
      if (oppWorkMode) q.set('work_mode', oppWorkMode);
      if (oppSearch.trim()) q.set('q', oppSearch.trim());
      q.set('page', String(oppPage));
      return api(`/opportunities/?${q.toString()}`);
    },
    enabled: !!user && !demo && tab === 'Jobs & Internships',
  });

  const { data: savedOppsData, refetch: refetchSaved, isLoading: loadingSaved } = useQuery({
    queryKey: ['student-saved-opps', user?.id],
    queryFn: () => api('/student/opportunities/saved/'),
    enabled: !!user && !demo && (tab === 'Saved Opportunities' || tab === 'Jobs & Internships'),
  });

  const { data: appsData, refetch: refetchApps, isLoading: loadingApps } = useQuery({
    queryKey: ['student-opp-apps', user?.id, appStatusFilter],
    queryFn: () => {
      const q = new URLSearchParams();
      if (appStatusFilter !== 'all') q.set('status', appStatusFilter);
      return api(`/student/opportunities/applications/?${q.toString()}`);
    },
    enabled: !!user && !demo && (tab === 'Application History' || tab === 'Jobs & Internships'),
  });

  const { data: certsData, isLoading: loadingCerts } = useQuery({
    queryKey: ['student-certs', user?.id],
    queryFn: () => api('/student/certificates/'),
    enabled: !!user && !demo && tab === 'Certificates',
  });

  if (!user) {
    return (
      <main id="main" className="section container empty-state">
        <UserIcon size={40} />
        <h1>Your WOC account.</h1>
        <p>Sign in to view your courses, college affiliation, batches, and career opportunities.</p>
        <Link href="/login/" className="button">Sign in</Link>
      </main>
    );
  }

  const savedIdSet = new Set<string>([
    ...(dashData?.opportunities?.saved_ids || []),
    ...((savedOppsData?.results || []).map((x: any) => x.opportunity?.id)),
  ]);

  const completion = dashData?.profile_completion || { percentage: demo ? 50 : 0, missing: [], completed: [] };
  const affiliation = dashData?.college_affiliation;
  const learningSummary = dashData?.learning || {
    enrolled_count: records.filter((r) => r.program.module === 'academy').length,
    completed_count: records.filter((r) => r.program.module === 'academy' && r.status === 'completed').length,
    average_progress: 0,
    resume_target: null,
    courses: [],
  };
  const batchesSummary = dashData?.batches || { total: 0, upcoming: 0, in_progress: 0, completed: 0, recent: [] };
  const oppSummary = dashData?.opportunities || {
    saved_count: 0,
    confirmed_applications_count: 0,
    external_clicks_count: 0,
    recommended: [],
  };

  const academyRecords = records.filter((r) => r.program.module === 'academy');
  const otherRecords = records.filter(
    (r) => r.program.module !== 'academy' && (otherModuleFilter === 'all' || r.program.module === otherModuleFilter)
  );

  // Handlers
  async function handleSaveProfile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setProfileBusy(true);
    const fd = new FormData(e.currentTarget);
    const skills = skillsInput.split(',').map((s) => s.trim()).filter(Boolean);
    const interests = interestsInput.split(',').map((s) => s.trim()).filter(Boolean);
    const payload = {
      name: String(fd.get('name') || ''),
      graduation_year: fd.get('graduation_year') ? Number(fd.get('graduation_year')) : null,
      institution: String(fd.get('institution') || ''),
      city: String(fd.get('city') || ''),
      qualification: String(fd.get('qualification') || ''),
      bio: String(fd.get('bio') || ''),
      career_goals: String(fd.get('career_goals') || ''),
      resume_url: String(fd.get('resume_url') || ''),
      linkedin_url: String(fd.get('linkedin_url') || ''),
      github_url: String(fd.get('github_url') || ''),
      skills,
      interests,
    };
    try {
      if (demo) {
        setUser({ ...user!, ...payload });
        toast('Profile updated in demo mode.');
      } else {
        const res = await api('/student/profile/', 'PATCH', payload);
        setUser(res.user);
        refetchDash();
        toast('Student profile updated.');
      }
    } catch (err: any) {
      toast(err?.message || 'Failed to update profile.');
    } finally {
      setProfileBusy(false);
    }
  }

  async function handleRequestCollege(institutionId: number) {
    try {
      await api('/student/colleges/request/', 'POST', { institution_id: institutionId });
      toast('College membership request submitted for review.');
      refetchColleges();
      refetchDash();
    } catch (err: any) {
      toast(err?.message || 'Could not submit college request.');
    }
  }

  async function handleLeaveCollege(membershipId?: number) {
    if (!confirm('Are you sure you want to withdraw or deactivate this college affiliation?')) return;
    try {
      await api('/student/colleges/leave/', 'POST', membershipId ? { membership_id: membershipId } : {});
      toast('College affiliation updated.');
      refetchColleges();
      refetchDash();
    } catch (err: any) {
      toast(err?.message || 'Could not update college affiliation.');
    }
  }

  async function handleToggleBookmark(oppId: string) {
    if (demo) {
      toast('Bookmarking requires the local Django backend.');
      return;
    }
    try {
      const res = await api(`/student/opportunities/${oppId}/save/`, 'POST', { action: 'toggle' });
      toast(res.saved ? 'Opportunity saved to bookmarks.' : 'Removed from saved opportunities.');
      refetchDash();
      refetchSaved();
    } catch (err: any) {
      toast(err?.message || 'Could not update bookmark.');
    }
  }

  async function handleExternalClick(opp: any) {
    if (!demo) {
      try {
        await api(`/student/opportunities/${opp.id}/track/`, 'POST', { action: 'click' });
        refetchApps();
        refetchDash();
      } catch {
        // Non-blocking log
      }
    }
    if (opp.careers_url) {
      window.open(opp.careers_url, '_blank', 'noopener,noreferrer');
    } else if (opp.recruitment_email) {
      window.location.href = `mailto:${opp.recruitment_email}?subject=${encodeURIComponent(`Application: ${opp.title}`)}`;
    }
  }

  async function handleSubmitApplicationStatus(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!trackModalOpp) return;
    setTrackBusy(true);
    const fd = new FormData(e.currentTarget);
    try {
      await api(`/student/opportunities/${trackModalOpp.id}/track/`, 'POST', {
        action: 'update_status',
        status: fd.get('status'),
        applied_at: fd.get('applied_at') || null,
        notes: fd.get('notes') || '',
      });
      toast('Application status recorded.');
      setTrackModalOpp(null);
      refetchApps();
      refetchDash();
    } catch (err: any) {
      toast(err?.message || 'Failed to update application status.');
    } finally {
      setTrackBusy(false);
    }
  }

  function openResumeLearning(recordId?: string) {
    if (recordId) {
      const found = records.find((r) => r.id === recordId);
      if (found) {
        setTab('My Learning');
        setSelectedRecord(found);
        return;
      }
    }
    setTab('My Learning');
  }

  return (
    <main id="main" className="dashboard">
      {/* Side Navigation */}
      <aside className="dashboard-nav">
        <p className="eyebrow">MY WOC</p>
        {NAV_TABS.map((t) => (
          <button
            key={t}
            aria-current={tab === t ? 'page' : undefined}
            onClick={() => {
              setTab(t);
              setSelectedRecord(null);
            }}
          >
            {t}
            {t === 'Notifications' && (notifications?.unread_count || 0) > 0 && (
              <span className="tab-badge">{notifications.unread_count}</span>
            )}
          </button>
        ))}
        {user.authorization?.roles?.includes('college_admin') && <Link href="/college/">College Portal</Link>}
        {user.authorization?.roles?.includes('company_admin') && <Link href="/company/">Company Hub</Link>}
        {user.authorization?.roles?.includes('super_admin') && <Link href="/super-admin/">Super Admin</Link>}
        {user.is_staff && <Link href="/admin/">Django Admin</Link>}
        <button
          onClick={async () => {
            if (!demo) await api('/logout/', 'POST');
            setUser(null);
            toast('Signed out.');
          }}
        >
          Sign out
        </button>
      </aside>

      {/* Main Content */}
      <div className="dashboard-body">
        <p className="eyebrow">{demo ? 'BROWSER DEMO ACCOUNT' : 'STUDENT DASHBOARD'}</p>
        <h1 style={{ marginTop: '4px' }}>
          {tab === 'Overview' ? `Hello, ${user.name.split(' ')[0]}.` : tab}
        </h1>
        <p style={{ color: 'var(--muted)', marginBottom: '24px' }}>
          Your learning progress, college affiliation, training batches, and career journey in one place.
        </p>

        {selectedRecord ? (
          renderLearning(selectedRecord, () => setSelectedRecord(null))
        ) : (
          <>
            {/* ================================================================
                1. OVERVIEW TAB
               ================================================================ */}
            {tab === 'Overview' && (
              <div>
                {/* Top KPIs */}
                <div className="stats-grid" style={{ marginBottom: '24px' }}>
                  <div className="stat-card">
                    <span className="stat-label"><UserIcon size={15} /> Profile Completion</span>
                    <span className="stat-val">{completion.percentage}%</span>
                    <span className="stat-sub">
                      {completion.percentage < 100
                        ? `${completion.missing.length} item${completion.missing.length === 1 ? '' : 's'} remaining`
                        : 'Profile complete'}
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label"><BookOpen size={15} /> Academy Learning</span>
                    <span className="stat-val">{learningSummary.average_progress}%</span>
                    <span className="stat-sub">
                      {learningSummary.enrolled_count} enrolled • {learningSummary.completed_count} completed
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label"><Layers size={15} /> Training Batches</span>
                    <span className="stat-val">{batchesSummary.total}</span>
                    <span className="stat-sub">
                      {batchesSummary.in_progress} ongoing • {batchesSummary.upcoming} upcoming
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label"><Award size={15} /> Certificates & Careers</span>
                    <span className="stat-val">{dashData?.certificates_count ?? records.filter((r) => r.certificate).length}</span>
                    <span className="stat-sub">
                      {oppSummary.saved_count} saved • {oppSummary.confirmed_applications_count} applied
                    </span>
                  </div>
                </div>

                {/* Profile Completion Bar + College Status */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                  <div className="panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <h3 style={{ margin: 0 }}>Profile Completeness</h3>
                      <strong>{completion.percentage}%</strong>
                    </div>
                    <div style={{ height: '8px', background: 'var(--border)', borderRadius: '999px', overflow: 'hidden', marginBottom: '12px' }}>
                      <div style={{ width: `${completion.percentage}%`, height: '100%', background: 'var(--navy)' }} />
                    </div>
                    {completion.missing.length > 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 12px' }}>
                        Add: {completion.missing.slice(0, 3).join(', ')}
                        {completion.missing.length > 3 ? ` (+${completion.missing.length - 3} more)` : ''}
                      </p>
                    ) : (
                      <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 12px' }}>
                        Your student profile is complete and ready for opportunities.
                      </p>
                    )}
                    <button className="button small outline" onClick={() => setTab('My Profile')}>
                      Update Profile
                    </button>
                  </div>

                  <div className="panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <h3 style={{ margin: 0 }}>College Affiliation</h3>
                      {affiliation && <span className={`status-pill ${affiliation.status}`}>{affiliation.status}</span>}
                    </div>
                    {affiliation ? (
                      <div>
                        <p style={{ margin: '0 0 6px', fontWeight: 600 }}>
                          {affiliation.institution_name}
                          {affiliation.institution_verified && (
                            <ShieldCheck size={15} style={{ marginLeft: '6px', verticalAlign: 'middle', color: 'var(--gold)' }} />
                          )}
                        </p>
                        <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 12px' }}>
                          {affiliation.institution_city}
                        </p>
                      </div>
                    ) : (
                      <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 12px' }}>
                        Not affiliated with a verified institution yet.
                      </p>
                    )}
                    <button className="button small outline" onClick={() => setTab('My College')}>
                      {affiliation ? 'Manage Affiliation' : 'Find Your College'}
                    </button>
                  </div>
                </div>

                {/* Resume Learning Banner */}
                {learningSummary.resume_target && (
                  <div className="panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
                    <div>
                      <span className="label">RESUME LEARNING</span>
                      <h3 style={{ margin: '6px 0 4px' }}>{learningSummary.resume_target.program_title}</h3>
                      <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                        {learningSummary.resume_target.lessons_completed} of 3 lessons completed ({learningSummary.resume_target.percentage}%)
                      </p>
                    </div>
                    <button
                      className="button small"
                      onClick={() => openResumeLearning(learningSummary.resume_target.record_id)}
                    >
                      <PlayCircle size={15} style={{ marginRight: '6px' }} /> Resume Course
                    </button>
                  </div>
                )}

                {/* Recommended Opportunities + Recent Batches */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
                  <div className="panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h3 style={{ margin: 0 }}><Sparkles size={16} style={{ marginRight: '6px' }} /> Recommended Opportunities</h3>
                      <button className="button small outline" onClick={() => setTab('Jobs & Internships')}>Browse All</button>
                    </div>
                    {oppSummary.recommended?.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                        Add your skills and interests in your profile to see matched opportunities.
                      </p>
                    ) : (
                      <div className="record-list">
                        {oppSummary.recommended.map((o: any) => (
                          <div key={o.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                              <strong>{o.title}</strong>
                              <span className="label">{o.opportunity_type}</span>
                            </div>
                            <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>
                              {o.company_name} • {o.work_mode.replace('_', '-')}
                            </div>
                            {o.matched_keywords?.length > 0 && (
                              <div style={{ fontSize: '12px', color: 'var(--navy)', marginTop: '4px' }}>
                                Matched: {o.matched_keywords.join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h3 style={{ margin: 0 }}>Assigned Training Batches</h3>
                      <button className="button small outline" onClick={() => setTab('My Batches')}>View Batches</button>
                    </div>
                    {batchesSummary.recent?.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                        No training batches assigned yet. Batches assigned by your college admin will appear here.
                      </p>
                    ) : (
                      <div className="record-list">
                        {batchesSummary.recent.map((b: any) => (
                          <div key={b.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <strong>{b.name}</strong>
                              <span className={`status-pill ${b.status}`}>{b.status}</span>
                            </div>
                            <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>
                              {b.institution_name} • {b.program?.title || 'Institutional Training'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ================================================================
                2. MY PROFILE TAB
               ================================================================ */}
            {tab === 'My Profile' && (
              <div style={{ maxWidth: '780px' }}>
                <ProfileFiles onChanged={()=>{refetchDash();}}/>
                <form className="panel form-stack" onSubmit={handleSaveProfile}>
                  <h2 style={{ marginTop: 0 }}>Student Profile & Career Readiness</h2>
 <p>Complete your profile after signup. Your profile is {completion.percentage}% complete.</p>
 <label>Graduation year<input name="graduation_year" type="number" min={1950} max={2100} defaultValue={user.graduation_year || ''}/></label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <label>
                      Full Name
                      <input name="name" defaultValue={user.name} required />
                    </label>
                    <label>
                      City / Location
                      <input name="city" defaultValue={user.city || ''} placeholder="e.g. Chennai" />
                    </label>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <label>
                      Educational Qualification
                      <input name="qualification" defaultValue={user.qualification || ''} placeholder="e.g. B.Tech CSE, Final Year" />
                    </label>
                    <label>
                      Institution Name (Display)
                      <input name="institution" defaultValue={user.institution || ''} placeholder="College / University" />
                    </label>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <label>
                      Skills (comma-separated)
                      <input
                        value={skillsInput}
                        onChange={(e) => setSkillsInput(e.target.value)}
                        placeholder="e.g. Python, React, SQL, UI Design"
                      />
                    </label>
                    <label>
                      Interests (comma-separated)
                      <input
                        value={interestsInput}
                        onChange={(e) => setInterestsInput(e.target.value)}
                        placeholder="e.g. Backend, AI, Product"
                      />
                    </label>
                  </div>

                  <label>
                    Career Goals
                    <textarea name="career_goals" defaultValue={user.career_goals || ''} rows={2} placeholder="What roles or domains are you aiming for?" />
                  </label>

                  <label>
                    About You / Bio
                    <textarea name="bio" defaultValue={user.bio || ''} maxLength={2000} rows={3} />
                  </label>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                    <label>
                      Resume URL (HTTPS)
                      <input type="url" name="resume_url" defaultValue={user.resume_url || ''} placeholder="https://..." />
                    </label>
                    <label>
                      LinkedIn URL (HTTPS)
                      <input type="url" name="linkedin_url" defaultValue={user.linkedin_url || ''} placeholder="https://linkedin.com/in/..." />
                    </label>
                    <label>
                      GitHub URL (HTTPS)
                      <input type="url" name="github_url" defaultValue={user.github_url || ''} placeholder="https://github.com/..." />
                    </label>
                  </div>

                  <button className="button" disabled={profileBusy}>
                    {profileBusy ? 'Saving...' : 'Save Student Profile'}
                  </button>
                </form>

                {renderPhoneVerification()}
              </div>
            )}

            {/* ================================================================
                3. MY COLLEGE TAB
               ================================================================ */}
            {tab === 'My College' && (
              <div>
                {demo ? (
                  <div className="panel"><p>College affiliation requests require the local Django backend.</p></div>
                ) : (
                  <>
                    {/* Current & Past Memberships */}
                    <div className="panel" style={{ marginBottom: '24px' }}>
                      <h2 style={{ marginTop: 0 }}>Your College Affiliation</h2>
                      {loadingColleges ? (
                        <p>Loading affiliation status...</p>
                      ) : collegesData?.memberships?.length === 0 ? (
                        <p style={{ color: 'var(--muted)' }}>
                          You have not submitted a college membership request yet. Search approved institutions below to request affiliation.
                        </p>
                      ) : (
                        <div className="record-list">
                          {collegesData?.memberships?.map((m: any) => (
                            <div key={m.membership_id} className="record">
                              <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <h3 style={{ margin: 0 }}>{m.institution_name}</h3>
                                  <span className={`status-pill ${m.status}`}>{m.status}</span>
                                </div>
                                <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--muted)' }}>
                                  {m.institution_city} • Requested {new Date(m.created_at).toLocaleDateString('en-IN')}
                                </p>
                              </div>
                              {(m.status === 'active' || m.status === 'pending') && (
                                <button
                                  className="button small outline"
                                  onClick={() => handleLeaveCollege(m.membership_id)}
                                >
                                  {m.status === 'pending' ? 'Withdraw Request' : 'Leave College'}
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Search Approved Colleges */}
                    <div className="panel">
                      <h3 style={{ marginTop: 0 }}>Find & Request Approved College</h3>
                      <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                        Only one active college affiliation is allowed at a time. Requests are reviewed by the college administrator.
                      </p>
                      <div style={{ position: 'relative', maxWidth: '460px', marginBottom: '16px' }}>
                        <Search size={16} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--muted)' }} />
                        <input
                          type="search"
                          placeholder="Search approved colleges by name or city..."
                          value={collegeQuery}
                          onChange={(e) => setCollegeQuery(e.target.value)}
                          style={{ paddingLeft: '34px', width: '100%' }}
                        />
                      </div>

                      {collegesData?.colleges?.length === 0 ? (
                        <p style={{ color: 'var(--muted)' }}>No approved colleges match your search.</p>
                      ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                          {collegesData?.colleges?.map((c: any) => {
                            const hasPendingOrActive = collegesData?.memberships?.some(
                              (m: any) => m.institution_id === c.id && (m.status === 'active' || m.status === 'pending')
                            );
                            return (
                              <div key={c.id} style={{ border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <strong>{c.name}</strong>
                                  {c.verified && <ShieldCheck size={16} style={{ color: 'var(--gold)' }} />}
                                </div>
                                <div style={{ fontSize: '13px', color: 'var(--muted)', margin: '4px 0 12px' }}>
                                  {c.city}
                                </div>
                                <button
                                  className="button small"
                                  disabled={hasPendingOrActive}
                                  onClick={() => handleRequestCollege(c.id)}
                                >
                                  {hasPendingOrActive ? 'Requested / Active' : 'Request Membership'}
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ================================================================
                4. MY LEARNING TAB (Academy Courses + Other Module Registrations)
               ================================================================ */}
            {tab === 'My Learning' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h2 style={{ margin: 0 }}>Enrolled Academy Courses</h2>
                  <Link href="/academy/" className="button small">Explore Academy Programs</Link>
                </div>

                {academyRecords.length === 0 ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '32px', marginBottom: '32px' }}>
                    <BookOpen size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No Academy enrollments yet</h3>
                    <p style={{ color: 'var(--muted)' }}>Enroll in an Academy program to track lessons, complete projects, and earn certificates.</p>
                    <Link href="/academy/" className="button">Browse Academy</Link>
                  </div>
                ) : (
                  <div className="record-list" style={{ marginBottom: '32px' }}>
                    {academyRecords.map((r) => {
                      const lessons = Array.isArray(r.data?.lessons) ? r.data.lessons : [];
                      const pct = r.status === 'completed' ? 100 : r.status === 'awaiting_review' ? 90 : Math.min(80, Math.round((lessons.length / 3) * 80));
                      return (
                        <div className="record" key={r.id}>
                          <div style={{ flex: 1 }}>
                            <span className="label">{r.program.category}</span>
                            <h3 style={{ margin: '4px 0' }}>{r.program.title}</h3>
                            <p style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--muted)' }}>
                              Status: {r.status.replaceAll('_', ' ')} • {lessons.length}/3 lessons completed ({pct}%)
                            </p>
                            <div style={{ height: '6px', maxWidth: '280px', background: 'var(--border)', borderRadius: '999px', overflow: 'hidden' }}>
                              <div style={{ width: `${pct}%`, height: '100%', background: 'var(--navy)' }} />
                            </div>
                          </div>
                          <button className="button small" onClick={() => setSelectedRecord(r)}>
                            <PlayCircle size={14} style={{ marginRight: '6px' }} />
                            {r.status === 'completed' ? 'Review Course' : 'Resume Learning'}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Other WOC Registrations (Events, Sports, Culturals, Chapters, Incubation) */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                  <h3 style={{ margin: 0 }}>Campus Activities & Other Registrations</h3>
                  <select value={otherModuleFilter} onChange={(e) => setOtherModuleFilter(e.target.value)} style={{ width: '180px' }}>
                    <option value="all">All Activities</option>
                    <option value="events">Events</option>
                    <option value="sports">Sports</option>
                    <option value="culturals">Culturals</option>
                    <option value="association">Chapters</option>
                    <option value="incubation">Incubation</option>
                    <option value="partnerships">Partnerships</option>
                  </select>
                </div>
                {otherRecords.length === 0 ? (
                  <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No other campus activity registrations yet.</p>
                ) : (
                  <div className="record-list">
                    {otherRecords.map((r) => (
                      <div className="record" key={r.id}>
                        <div>
                          <span className="label">{r.program.module}</span>
                          <h3>{r.program.title}</h3>
                          <p>{r.status.replaceAll('_', ' ')} · {new Date(r.created_at).toLocaleDateString('en-IN')}</p>
                        </div>
                        <Link className="text-link" href={`/${r.program.module}/${r.program.slug}/`}>View details</Link>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ================================================================
                5. MY BATCHES TAB
               ================================================================ */}
            {tab === 'My Batches' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h2 style={{ margin: 0 }}>Assigned Training Batches</h2>
                  <select value={batchFilter} onChange={(e) => setBatchFilter(e.target.value)} style={{ width: '160px' }}>
                    <option value="all">All Statuses</option>
                    <option value="upcoming">Upcoming</option>
                    <option value="in_progress">Ongoing</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>

                {loadingBatches ? (
                  <p>Loading your training batches...</p>
                ) : !batchesData?.results?.length ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>
                    <Layers size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No assigned training batches</h3>
                    <p style={{ color: 'var(--muted)' }}>
                      Once affiliated with a college, training batches assigned by your college administrator will appear here.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
                    {batchesData.results.map((b: any) => (
                      <div key={b.id} className="panel">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <h3 style={{ margin: 0 }}>{b.name}</h3>
                          <span className={`status-pill ${b.status}`}>{b.status}</span>
                        </div>
                        <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 8px' }}>
                          {b.institution_name} ({b.institution_city})
                        </p>
                        <p style={{ fontSize: '13px', fontWeight: 600, margin: '0 0 8px' }}>
                          Program: {b.program?.title || 'Institutional Training'}
                        </p>
                        <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '0 0 12px' }}>
                          Dates: {b.start_date || 'TBD'} to {b.end_date || 'TBD'}
                        </p>
                        {b.progress ? (
                          <div>
                            <div style={{ fontSize: '12px', marginBottom: '4px' }}>
                              Course Progress: {b.progress.percentage}% ({b.progress.lessons_completed}/3 lessons)
                            </div>
                            <button
                              className="button small outline"
                              onClick={() => openResumeLearning(b.progress.record_id)}
                            >
                              Resume Learning
                            </button>
                          </div>
                        ) : b.program?.slug ? (
                          <Link href={`/${b.program.module}/${b.program.slug}/`} className="button small outline">
                            View Program
                          </Link>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ================================================================
                5B. CAMPUS ENGAGEMENT TAB (Events, Clubs, Leadership, Achievements)
               ================================================================ */}
            {tab === 'Campus Engagement' && <StudentEngagementTab />}

            {/* ================================================================
                6. JOBS & INTERNSHIPS TAB
               ================================================================ */}
            {tab === 'Jobs & Internships' && (
              <div>
                <div className="catalogue-toolbar" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                  <label className="search-input" style={{ gridColumn: 'span 2' }}>
                    <Search size={16} />
                    <input
                      placeholder="Search jobs, internships, companies, skills..."
                      value={oppSearch}
                      onChange={(e) => { setOppSearch(e.target.value); setOppPage(1); }}
                    />
                  </label>
                  <select value={oppType} onChange={(e) => { setOppType(e.target.value); setOppPage(1); }}>
                    <option value="all">All Types</option>
                    <option value="job">Full-time Jobs</option>
                    <option value="internship">Internships</option>
                  </select>
                  <select value={oppWorkMode} onChange={(e) => { setOppWorkMode(e.target.value); setOppPage(1); }}>
                    <option value="">All Work Modes</option>
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="on_site">On-site</option>
                  </select>
                </div>

                {loadingOpps ? (
                  <p>Loading opportunities...</p>
                ) : !oppsData?.results?.length ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>
                    <Briefcase size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No opportunities match your filters</h3>
                    <p style={{ color: 'var(--muted)' }}>Try adjusting your search or visit the public Careers portal.</p>
                  </div>
                ) : (
                  <>
                    <div className="record-list">
                      {oppsData.results.map((o: any) => {
                        const isSaved = savedIdSet.has(o.id);
                        return (
                          <div key={o.id} className="record" style={{ alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ flex: 1, minWidth: '260px' }}>
                              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                                <span className="label">{o.opportunity_type}</span>
                                <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{o.work_mode.replace('_', '-')}</span>
                                {o.compensation && <span style={{ fontSize: '12px', fontWeight: 600 }}>{o.compensation}</span>}
                              </div>
                              <h3 style={{ margin: '4px 0' }}>
                                <Link href={`/careers/opportunity/?id=${o.id}`}>{o.title}</Link>
                              </h3>
                              <p style={{ margin: '0 0 6px', fontSize: '13px', color: 'var(--muted)' }}>
                                {o.company_name} • {o.location || o.company_city || 'India'}
                              </p>
                              {o.required_skills?.length > 0 && (
                                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                                  Skills: {o.required_skills.slice(0, 5).join(', ')}
                                </div>
                              )}
                            </div>

                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                              <button
                                className="button small outline"
                                onClick={() => handleToggleBookmark(o.id)}
                                title={isSaved ? 'Remove bookmark' : 'Save opportunity'}
                              >
                                <Bookmark size={14} style={{ marginRight: '4px', fill: isSaved ? 'currentColor' : 'none' }} />
                                {isSaved ? 'Saved' : 'Save'}
                              </button>
                              <button className="button small" onClick={() => handleExternalClick(o)}>
                                <ExternalLink size={14} style={{ marginRight: '4px' }} />
                                Apply Externally
                              </button>
                              <button className="button small outline" onClick={() => setTrackModalOpp(o)}>
                                Track Status
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {oppsData.count > 20 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                        <span style={{ fontSize: '13px', color: 'var(--muted)' }}>Total {oppsData.count} opportunities</span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="button small outline" disabled={!oppsData.previous} onClick={() => setOppPage((p) => Math.max(1, p - 1))}>Previous</button>
                          <button className="button small outline" disabled={!oppsData.next} onClick={() => setOppPage((p) => p + 1)}>Next</button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* ================================================================
                7. SAVED OPPORTUNITIES TAB
               ================================================================ */}
            {tab === 'Saved Opportunities' && (
              <div>
                {loadingSaved ? (
                  <p>Loading saved opportunities...</p>
                ) : !savedOppsData?.results?.length ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>
                    <Bookmark size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No saved opportunities yet</h3>
                    <p style={{ color: 'var(--muted)' }}>Bookmark jobs or internships while browsing to review and apply later.</p>
                    <button className="button" onClick={() => setTab('Jobs & Internships')}>Browse Opportunities</button>
                  </div>
                ) : (
                  <div className="record-list">
                    {savedOppsData.results.map((item: any) => {
                      const o = item.opportunity;
                      return (
                        <div key={item.saved_id} className="record" style={{ flexWrap: 'wrap', gap: '12px' }}>
                          <div style={{ flex: 1 }}>
                            <span className="label">{o.opportunity_type}</span>
                            <h3 style={{ margin: '4px 0' }}>
                              <Link href={`/careers/opportunity/?id=${o.id}`}>{o.title}</Link>
                            </h3>
                            <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                              {o.company_name} • Saved {new Date(item.saved_at).toLocaleDateString('en-IN')}
                            </p>
                          </div>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="button small" onClick={() => handleExternalClick(o)}>
                              <ExternalLink size={14} style={{ marginRight: '4px' }} /> Apply Externally
                            </button>
                            <button className="button small outline" onClick={() => setTrackModalOpp(o)}>
                              Track Status
                            </button>
                            <button className="button small outline" onClick={() => handleToggleBookmark(o.id)}>
                              Remove
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* ================================================================
                8. APPLICATION HISTORY TAB
               ================================================================ */}
            {tab === 'Application History' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                    External link clicks are logged separately from applications you confirm manually.
                  </p>
                  <select value={appStatusFilter} onChange={(e) => setAppStatusFilter(e.target.value)} style={{ width: '190px' }}>
                    <option value="all">All Activity</option>
                    <option value="clicked">External Link Clicked</option>
                    <option value="applied">Applied (Confirmed)</option>
                    <option value="interviewing">Interviewing</option>
                    <option value="offer_received">Offer Received</option>
                    <option value="rejected">Rejected</option>
                    <option value="withdrawn">Withdrawn</option>
                  </select>
                </div>

                {loadingApps ? (
                  <p>Loading application history...</p>
                ) : !appsData?.results?.length ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>
                    <ClipboardList size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No application activity recorded</h3>
                    <p style={{ color: 'var(--muted)' }}>Click an external application link or manually log your application status.</p>
                  </div>
                ) : (
                  <div className="record-list">
                    {appsData.results.map((log: any) => (
                      <div key={log.id} className="record" style={{ flexWrap: 'wrap', gap: '12px' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span className={`status-pill ${log.status}`}>{log.status.replaceAll('_', ' ')}</span>
                            <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
                              {log.external_click_count} external link click{log.external_click_count === 1 ? '' : 's'}
                            </span>
                          </div>
                          <h3 style={{ margin: '6px 0 4px' }}>{log.opportunity.title}</h3>
                          <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                            {log.opportunity.company_name}
                            {log.applied_at && ` • Applied ${log.applied_at}`}
                          </p>
                          {log.notes && <p style={{ margin: '6px 0 0', fontSize: '13px' }}>{log.notes}</p>}
                        </div>
                        <button
                          className="button small outline"
                          onClick={() => setTrackModalOpp({ ...log.opportunity, _existingLog: log })}
                        >
                          Update Status
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ================================================================
                9. CERTIFICATES TAB
               ================================================================ */}
            {tab === 'Certificates' && (
              <div>
                {loadingCerts ? (
                  <p>Loading your certificates...</p>
                ) : (certsData?.results?.length || records.filter((r) => r.certificate).length) === 0 ? (
                  <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>
                    <Award size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />
                    <h3>No certificates earned yet</h3>
                    <p style={{ color: 'var(--muted)' }}>
                      Certificates are issued after completing all lessons, passing the assessment, and staff approval.
                    </p>
                  </div>
                ) : (
                  <div className="record-list">
                    {(certsData?.results || records.filter((r) => r.certificate).map((r) => ({
                      id: r.certificate,
                      program_title: r.program.title,
                      issued_at: r.created_at,
                      sample: r.program.sample,
                    }))).map((c: any) => (
                      <div className="record" key={c.id}>
                        <div>
                          <span className="label">{c.sample ? 'SAMPLE CREDENTIAL' : 'VERIFIED CREDENTIAL'}</span>
                          <h3 style={{ margin: '4px 0' }}>{c.program_title}</h3>
                          <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                            Issued {new Date(c.issued_at).toLocaleDateString('en-IN')} • ID: {c.id}
                          </p>
                        </div>
                        <Link className="button small outline" href={`/certificate/?id=${c.id}`}>
                          Verify & Print
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ================================================================
                10. NOTIFICATIONS TAB
               ================================================================ */}
            {tab === 'Notifications' && renderNotifications(notifications, refetchNotifications)}
          </>
        )}
      </div>

      {/* ====================================================================
          MODAL: MANUAL APPLICATION STATUS TRACKING
         ==================================================================== */}
      {trackModalOpp && (
        <div className="modal-backdrop" onClick={() => setTrackModalOpp(null)}>
          <div className="modal" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
            <h2>Track Application Status</h2>
            <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: 0 }}>
              {trackModalOpp.title} — {trackModalOpp.company_name}
            </p>
            <form onSubmit={handleSubmitApplicationStatus} className="form-stack">
              <label>
                Application Status
                <select
                  name="status"
                  defaultValue={
                    trackModalOpp._existingLog?.status && trackModalOpp._existingLog.status !== 'clicked'
                      ? trackModalOpp._existingLog.status
                      : 'applied'
                  }
                  required
                >
                  <option value="applied">Applied (Submitted externally)</option>
                  <option value="interviewing">Interviewing</option>
                  <option value="offer_received">Offer Received</option>
                  <option value="rejected">Rejected</option>
                  <option value="withdrawn">Withdrawn</option>
                </select>
              </label>

              <label>
                Application Date
                <input
                  type="date"
                  name="applied_at"
                  defaultValue={trackModalOpp._existingLog?.applied_at || new Date().toISOString().split('T')[0]}
                />
              </label>

              <label>
                Personal Notes
                <textarea
                  name="notes"
                  rows={3}
                  defaultValue={trackModalOpp._existingLog?.notes || ''}
                  placeholder="Interview dates, recruiter contact, follow-up reminders..."
                />
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button type="button" className="button outline" onClick={() => setTrackModalOpp(null)}>
                  Cancel
                </button>
                <button type="submit" className="button" disabled={trackBusy}>
                  {trackBusy ? 'Saving...' : 'Save Status'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
