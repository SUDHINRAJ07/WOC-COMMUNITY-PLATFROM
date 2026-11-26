'use client';



import React, { useState } from 'react';

import Link from 'next/link';

import { useQuery } from '@tanstack/react-query';

import {

  GraduationCap, Users, BookOpen, Briefcase, PlusCircle, CheckCircle, Clock,

  XCircle, AlertCircle, Edit, Trash2, ExternalLink, Globe, Mail, Phone,

  Search, ShieldCheck, HeartHandshake, UserCheck, UserX, Award

} from 'lucide-react';

import { useWoc } from './Platform';

import { api } from '@/lib/api';

import { CollegeEngagementTab } from './EngagementPanels';



export function CollegeDashboard() {

  const { user, toast } = useWoc();

  const [activeTab, setActiveTab] = useState<'overview' | 'profile' | 'students' | 'batches' | 'placements' | 'engagement'>('overview');



  // Queries

  const { data: dashData, refetch: refetchDash, isLoading: loadingDash } = useQuery({

    queryKey: ['college-dashboard', user?.id],

    queryFn: () => api('/college/dashboard/'),

    enabled: !!user,

  });



  const { data: catalogData } = useQuery({

    queryKey: ['college-catalog', user?.id],

    queryFn: () => api('/college/catalog/'),

    enabled: !!user,

  });



  // Students query

  const [studentPage, setStudentPage] = useState(1);

  const [studentStatus, setStudentStatus] = useState('all');

  const [studentSearch, setStudentSearch] = useState('');



  const { data: studentsData, refetch: refetchStudents, isLoading: loadingStudents } = useQuery({

    queryKey: ['college-students', user?.id, studentPage, studentStatus, studentSearch],

    queryFn: () => {

      const q = new URLSearchParams();

      q.set('page', String(studentPage));

      if (studentStatus !== 'all') q.set('status', studentStatus);

      if (studentSearch.trim()) q.set('q', studentSearch.trim());

      return api(`/college/students/?${q.toString()}`);

    },

    enabled: !!user && (activeTab === 'students' || activeTab === 'overview' || activeTab === 'engagement'),

  });



  // Batches query

  const [batchPage, setBatchPage] = useState(1);

  const [batchStatus, setBatchStatus] = useState('all');

  const [batchSearch, setBatchSearch] = useState('');



  const { data: batchesData, refetch: refetchBatches, isLoading: loadingBatches } = useQuery({

    queryKey: ['college-batches', user?.id, batchPage, batchStatus, batchSearch],

    queryFn: () => {

      const q = new URLSearchParams();

      q.set('page', String(batchPage));

      if (batchStatus !== 'all') q.set('status', batchStatus);

      if (batchSearch.trim()) q.set('q', batchSearch.trim());

      return api(`/college/batches/?${q.toString()}`);

    },

    enabled: !!user && (activeTab === 'batches' || activeTab === 'overview'),

  });



  // Placements query

  const [placementPage, setPlacementPage] = useState(1);

  const [placementStatus, setPlacementStatus] = useState('all');

  const [placementType, setPlacementType] = useState('all');



  const { data: placementsData, refetch: refetchPlacements, isLoading: loadingPlacements } = useQuery({

    queryKey: ['college-placements', user?.id, placementPage, placementStatus, placementType],

    queryFn: () => {

      const q = new URLSearchParams();

      q.set('page', String(placementPage));

      if (placementStatus !== 'all') q.set('status', placementStatus);

      if (placementType !== 'all') q.set('placement_type', placementType);

      return api(`/college/placements/?${q.toString()}`);

    },

    enabled: !!user && (activeTab === 'placements' || activeTab === 'overview'),

  });



  // Partnerships query

  const [partnershipPage, setPartnershipPage] = useState(1);

  const { data: partnershipsData, refetch: refetchPartnerships } = useQuery({

    queryKey: ['college-partnerships', user?.id, partnershipPage],

    queryFn: () => api(`/college/partnerships/?page=${partnershipPage}`),

    enabled: !!user && (activeTab === 'placements' || activeTab === 'overview'),

  });



  // Modal & Edit states

  const [batchModalOpen, setBatchModalOpen] = useState(false);

  const [editingBatch, setEditingBatch] = useState<any>(null);

  const [enrollModalBatch, setEnrollModalBatch] = useState<any>(null);



  const [placementModalOpen, setPlacementModalOpen] = useState(false);

  const [partnershipModalOpen, setPartnershipModalOpen] = useState(false);



  // Profile Form state

  const [profileSaving, setProfileSaving] = useState(false);



  const isCollegeAdmin = user?.authorization?.roles?.includes('college_admin') || user?.authorization?.roles?.includes('super_admin');

  const collegeMembership = user?.authorization?.college_memberships?.[0];



  if (!user) {

    return (

      <main id="main" className="section container empty-state">

        <GraduationCap size={44} />

        <h1>College Administrator Portal</h1>

        <p>Please sign in to access your institutional dashboard.</p>

        <Link href="/login/" className="button">Sign In</Link>

      </main>

    );

  }



  if (!isCollegeAdmin) {

    return (

      <main id="main" className="section container narrow">

        <div className="panel" style={{ textAlign: 'center', padding: '40px 24px' }}>

          <Clock size={48} style={{ color: 'var(--gold)', margin: '0 auto 16px' }} />

          <h2>Institutional Verification in Progress</h2>

          <p style={{ color: 'var(--muted)', maxWidth: '480px', margin: '0 auto 24px' }}>

            {collegeMembership?.college_name

              ? `Your affiliation request for "${collegeMembership.college_name}" is currently under review by the WOC platform moderation team.`

              : 'Your institutional onboarding application is awaiting verification.'}

          </p>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>

            <Link href="/onboarding/" className="button outline">View Application Status</Link>

            <Link href="/onboarding/" className="button">View registration status</Link>

          </div>

        </div>

      </main>

    );

  }



  const metrics = dashData?.metrics || {

    total_students: 0,

    active_students: 0,

    pending_requests: 0,

    total_batches: 0,

    active_batches: 0,

    total_placements: 0,

    placed_accepted: 0,

    placed_offered: 0,

    active_partnerships: 0,

  };



  const college = dashData?.college || {};



  // Handlers

  async function handleStudentReview(membershipId: number, action: 'approve' | 'reject' | 'deactivate' | 'reactivate') {

    try {

      await api(`/college/students/${membershipId}/review/`, 'POST', { action });

      toast(`Student membership ${action}d successfully.`);

      refetchStudents();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || `Failed to ${action} student membership.`);

    }

  }



  async function handleSaveProfile(e: React.FormEvent<HTMLFormElement>) {

    e.preventDefault();

    setProfileSaving(true);

    const fd = new FormData(e.currentTarget);

    const body: Record<string, any> = {

      phone: fd.get('phone'),

      principal_name: fd.get('principal_name'),

      website: fd.get('website'),

      contact_email: fd.get('contact_email'),

      address: fd.get('address'),

      description: fd.get('description'),

      city: fd.get('city'),

      logo_url: fd.get('logo_url'),

    };

    try {

      await api('/college/profile/', 'PATCH', body);

      toast('Institution profile updated successfully.');

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to update profile.');

    } finally {

      setProfileSaving(false);

    }

  }



  async function handleSaveBatch(e: React.FormEvent<HTMLFormElement>) {

    e.preventDefault();

    const fd = new FormData(e.currentTarget);

    const payload: Record<string, any> = {

      name: fd.get('name'),

      program_id: fd.get('program_id') || null,

      capacity: Number(fd.get('capacity') || 50),

      start_date: fd.get('start_date') || null,

      end_date: fd.get('end_date') || null,

      status: fd.get('status') || 'upcoming',

      description: fd.get('description') || '',

    };

    try {

      if (editingBatch) {

        await api(`/college/batches/${editingBatch.id}/`, 'PATCH', payload);

        toast('Training batch updated.');

      } else {

        await api('/college/batches/', 'POST', payload);

        toast('New training batch created.');

      }

      setBatchModalOpen(false);

      setEditingBatch(null);

      refetchBatches();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to save batch.');

    }

  }



  async function handleDeleteBatch(id: string) {

    if (!confirm('Are you sure you want to delete this training batch?')) return;

    try {

      await api(`/college/batches/${id}/`, 'DELETE');

      toast('Training batch removed.');

      refetchBatches();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to delete batch.');

    }

  }



  async function handleEnrollToggle(batchId: string, studentId: number, currentlyEnrolled: boolean) {

    try {

      await api(`/college/batches/${batchId}/enroll/`, 'POST', {

        action: currentlyEnrolled ? 'unenroll' : 'enroll',

        student_ids: [studentId],

      });

      toast(currentlyEnrolled ? 'Student unenrolled from batch.' : 'Student enrolled in batch.');

      // Refresh batch detail modal

      const updated = await api(`/college/batches/${batchId}/`);

      setEnrollModalBatch(updated);

      refetchBatches();

    } catch (err: any) {

      toast(err?.message || 'Enrollment update failed.');

    }

  }



  async function handleSavePlacement(e: React.FormEvent<HTMLFormElement>) {

    e.preventDefault();

    const fd = new FormData(e.currentTarget);

    const payload: Record<string, any> = {

      student_id: Number(fd.get('student_id')),

      company_id: fd.get('company_id') || null,

      company_name: fd.get('company_name') || '',

      opportunity_id: fd.get('opportunity_id') || null,

      role_title: fd.get('role_title'),

      placement_type: fd.get('placement_type') || 'job',

      compensation: fd.get('compensation') || '',

      status: fd.get('status') || 'offered',

      placed_at: fd.get('placed_at') || new Date().toISOString().split('T')[0],

    };

    try {

      await api('/college/placements/', 'POST', payload);

      toast('Campus placement record added.');

      setPlacementModalOpen(false);

      refetchPlacements();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to record placement.');

    }

  }



  async function handleDeletePlacement(id: string) {

    if (!confirm('Are you sure you want to delete this placement record?')) return;

    try {

      await api(`/college/placements/${id}/`, 'DELETE');

      toast('Placement record deleted.');

      refetchPlacements();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to delete placement.');

    }

  }



  async function handleSavePartnership(e: React.FormEvent<HTMLFormElement>) {

    e.preventDefault();

    const fd = new FormData(e.currentTarget);

    const payload: Record<string, any> = {

      company_id: fd.get('company_id'),

      partnership_type: fd.get('partnership_type') || 'Recruitment & Training',

      status: fd.get('status') || 'active',

      mou_signed_date: fd.get('mou_signed_date') || null,

      contact_person: fd.get('contact_person') || '',

      notes: fd.get('notes') || '',

    };

    try {

      await api('/college/partnerships/', 'POST', payload);

      toast('Corporate partnership recorded.');

      setPartnershipModalOpen(false);

      refetchPartnerships();

      refetchDash();

    } catch (err: any) {

      toast(err?.message || 'Failed to add partnership.');

    }

  }



  return (

    <main id="main" className="dashboard">

      {/* Side Navigation */}

      <aside className="dashboard-nav">

        <p className="eyebrow">COLLEGE HUB</p>

        <button

          aria-current={activeTab === 'overview' ? 'page' : undefined}

          onClick={() => setActiveTab('overview')}

        >

          Overview

        </button>

        <button

          aria-current={activeTab === 'students' ? 'page' : undefined}

          onClick={() => setActiveTab('students')}

        >

          Students {metrics.pending_requests > 0 && <span className="tab-badge">{metrics.pending_requests}</span>}

        </button>

        <button

          aria-current={activeTab === 'batches' ? 'page' : undefined}

          onClick={() => setActiveTab('batches')}

        >

          Batches & Training

        </button>

        <button

          aria-current={activeTab === 'placements' ? 'page' : undefined}

          onClick={() => setActiveTab('placements')}

        >

          Placements & Partners

        </button>

        <button

          aria-current={activeTab === 'engagement' ? 'page' : undefined}

          onClick={() => setActiveTab('engagement')}

        >

          Events, Clubs & Leaders

        </button>

        <button

          aria-current={activeTab === 'profile' ? 'page' : undefined}

          onClick={() => setActiveTab('profile')}

        >

          College Profile

        </button>

        

      </aside>



      {/* Main Content Area */}

      <div className="dashboard-body">

        {/* Header Banner */}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>

          <div>

            <p className="eyebrow">ACCREDITED INSTITUTION</p>

            <h1 style={{ margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: '10px' }}>

              {activeTab==='overview'?'Your campus, connected.':college.name || 'College Dashboard'}

              {college.verified && (

                <span title="Verified Institution" style={{ color: 'var(--gold)', display: 'inline-flex', verticalAlign: 'middle' }}>

                  <ShieldCheck size={22} />

                </span>

              )}

            </h1>

            <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: '14px' }}>

              {college.name} · {college.city} {college.principal_name && `• Principal: ${college.principal_name}`}

            </p>

          </div>



          <div style={{ display: 'flex', gap: '10px' }}>

            <button className="button small" onClick={() => { setEditingBatch(null); setBatchModalOpen(true); }}>

              <PlusCircle size={15} style={{ marginRight: '6px' }} /> New Training Batch

            </button>

            <button className="button small outline" onClick={() => setPlacementModalOpen(true)}>

              <Award size={15} style={{ marginRight: '6px' }} /> Record Placement

            </button>

          </div>

        </div>



        {/* =========================================================================

            TAB 1: OVERVIEW

           ========================================================================= */}

        {activeTab === 'overview' && (

          <div>

            {/* KPI Cards */}

            <div className="stats-grid" style={{ marginBottom: '32px' }}>

              <div className="stat-card">

                <span className="stat-label"><Users size={16} /> Total Students</span>

                <span className="stat-val">{metrics.total_students}</span>

                <span className="stat-sub">{metrics.active_students} active • {metrics.pending_requests} pending</span>

              </div>

              <div className="stat-card">

                <span className="stat-label"><BookOpen size={16} /> Active Batches</span>

                <span className="stat-val">{metrics.active_batches}</span>

                <span className="stat-sub">{metrics.total_batches} total batches formed</span>

              </div>

              <div className="stat-card">

                <span className="stat-label"><Briefcase size={16} /> Campus Placements</span>

                <span className="stat-val">{metrics.total_placements}</span>

                <span className="stat-sub">{metrics.placed_accepted} accepted • {metrics.placed_offered} offered</span>

              </div>

              <div className="stat-card">

                <span className="stat-label"><HeartHandshake size={16} /> Corporate Partners</span>

                <span className="stat-val">{metrics.active_partnerships}</span>

                <span className="stat-sub">Active MoUs & recruitments</span>

              </div>

            </div>



            {/* Quick Sections */}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>

              {/* Pending Student Requests */}

              <div className="panel">

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>

                  <h3 style={{ margin: 0 }}>Pending Student Requests</h3>

                  <button className="button small outline" onClick={() => setActiveTab('students')}>View All</button>

                </div>

                {dashData?.pending_students?.length === 0 ? (

                  <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No pending student affiliation requests.</p>

                ) : (

                  <div className="record-list">

                    {dashData?.pending_students?.map((s: any) => (

                      <div key={s.membership_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>

                        <div>

                          <strong>{s.name}</strong>

                          <div style={{ fontSize: '13px', color: 'var(--muted)' }}>{s.email}</div>

                        </div>

                        <div style={{ display: 'flex', gap: '6px' }}>

                          <button className="button small" onClick={() => handleStudentReview(s.membership_id, 'approve')}>

                            <UserCheck size={14} style={{ marginRight: '4px' }} /> Approve

                          </button>

                          <button className="button small outline" onClick={() => handleStudentReview(s.membership_id, 'reject')}>

                            <UserX size={14} />

                          </button>

                        </div>

                      </div>

                    ))}

                  </div>

                )}

              </div>



              {/* Active Batches */}

              <div className="panel">

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>

                  <h3 style={{ margin: 0 }}>Recent Training Batches</h3>

                  <button className="button small outline" onClick={() => setActiveTab('batches')}>Manage Batches</button>

                </div>

                {dashData?.recent_batches?.length === 0 ? (

                  <p style={{ color: 'var(--muted)', fontSize: '14px' }}>No training batches created yet.</p>

                ) : (

                  <div className="record-list">

                    {dashData?.recent_batches?.map((b: any) => (

                      <div key={b.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>

                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>

                          <strong>{b.name}</strong>

                          <span className={`status-pill ${b.status}`}>{b.status}</span>

                        </div>

                        <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>

                          Program: {b.program?.title || 'Custom'} • {b.enrolled_count} / {b.capacity} Students Enrolled

                        </div>

                      </div>

                    ))}

                  </div>

                )}

              </div>

            </div>

          </div>

        )}



        {/* =========================================================================

            TAB 2: STUDENTS ROSTER & MANAGEMENT

           ========================================================================= */}

        {activeTab === 'students' && (

          <div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>

              {/* Search & Filters */}

              <div style={{ display: 'flex', gap: '10px', flex: 1, minWidth: '280px' }}>

                <div style={{ position: 'relative', flex: 1 }}>

                  <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--muted)' }} />

                  <input

                    type="search"

                    placeholder="Search students by name, email or phone..."

                    value={studentSearch}

                    onChange={(e) => { setStudentSearch(e.target.value); setStudentPage(1); }}

                    style={{ paddingLeft: '34px', width: '100%' }}

                  />

                </div>

                <select

                  value={studentStatus}

                  onChange={(e) => { setStudentStatus(e.target.value); setStudentPage(1); }}

                  style={{ width: '150px' }}

                >

                  <option value="all">All Statuses</option>

                  <option value="active">Active Members</option>

                  <option value="pending">Pending Approval</option>

                  <option value="inactive">Inactive</option>

                  <option value="rejected">Rejected</option>

                </select>

              </div>

            </div>



            {loadingStudents ? (

              <p>Loading student roster...</p>

            ) : studentsData?.results?.length === 0 ? (

              <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

                <Users size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />

                <h3>No students found</h3>

                <p style={{ color: 'var(--muted)' }}>No student affiliation records match your current filters.</p>

              </div>

            ) : (

              <div className="panel" style={{ overflowX: 'auto', padding: 0 }}>

                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>

                  <thead>

                    <tr style={{ borderBottom: '2px solid var(--border)', background: 'var(--surface-alt)' }}>

                      <th style={{ padding: '12px 16px' }}>Student</th>

                      <th style={{ padding: '12px 16px' }}>Contact</th>

                      <th style={{ padding: '12px 16px' }}>Status</th>

                      <th style={{ padding: '12px 16px' }}>Batches</th>

                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>

                    </tr>

                  </thead>

                  <tbody>

                    {studentsData?.results?.map((s: any) => (

                      <tr key={s.membership_id} style={{ borderBottom: '1px solid var(--border)' }}>

                        <td style={{ padding: '12px 16px' }}>

                          <strong>{s.name}</strong>

                          <div style={{ fontSize: '12px', color: 'var(--muted)' }}>ID: #{s.user_id}</div>

                        </td>

                        <td style={{ padding: '12px 16px', fontSize: '13px' }}>

                          <div>{s.email}</div>

                          {s.phone && <div style={{ color: 'var(--muted)' }}>{s.phone}</div>}

                        </td>

                        <td style={{ padding: '12px 16px' }}>

                          <span className={`status-pill ${s.status}`}>{s.status}</span>

                        </td>

                        <td style={{ padding: '12px 16px', fontSize: '13px' }}>

                          {s.enrolled_batches_count} enrolled

                        </td>

                        <td style={{ padding: '12px 16px', textAlign: 'right' }}>

                          {s.status === 'pending' && (

                            <div style={{ display: 'inline-flex', gap: '6px' }}>

                              <button className="button small" onClick={() => handleStudentReview(s.membership_id, 'approve')}>

                                Approve

                              </button>

                              <button className="button small outline" onClick={() => handleStudentReview(s.membership_id, 'reject')}>

                                Reject

                              </button>

                            </div>

                          )}

                          {s.status === 'active' && (

                            <button className="button small outline" onClick={() => handleStudentReview(s.membership_id, 'deactivate')}>

                              Deactivate

                            </button>

                          )}

                          {(s.status === 'inactive' || s.status === 'rejected') && (

                            <button className="button small outline" onClick={() => handleStudentReview(s.membership_id, 'reactivate')}>

                              Reactivate

                            </button>

                          )}

                        </td>

                      </tr>

                    ))}

                  </tbody>

                </table>



                {/* Pagination */}

                {studentsData?.count > 20 && (

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>

                    <span style={{ fontSize: '13px', color: 'var(--muted)' }}>

                      Total {studentsData.count} students

                    </span>

                    <div style={{ display: 'flex', gap: '8px' }}>

                      <button

                        className="button small outline"

                        disabled={!studentsData.previous}

                        onClick={() => setStudentPage(p => Math.max(1, p - 1))}

                      >

                        Previous

                      </button>

                      <button

                        className="button small outline"

                        disabled={!studentsData.next}

                        onClick={() => setStudentPage(p => p + 1)}

                      >

                        Next

                      </button>

                    </div>

                  </div>

                )}

              </div>

            )}

          </div>

        )}



        {/* =========================================================================

            TAB 3: TRAINING & BATCH MANAGEMENT

           ========================================================================= */}

        {activeTab === 'batches' && (

          <div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>

              <div style={{ display: 'flex', gap: '10px', flex: 1, minWidth: '280px' }}>

                <input

                  type="search"

                  placeholder="Search batches..."

                  value={batchSearch}

                  onChange={(e) => { setBatchSearch(e.target.value); setBatchPage(1); }}

                  style={{ flex: 1 }}

                />

                <select

                  value={batchStatus}

                  onChange={(e) => { setBatchStatus(e.target.value); setBatchPage(1); }}

                  style={{ width: '150px' }}

                >

                  <option value="all">All Batches</option>

                  <option value="upcoming">Upcoming</option>

                  <option value="in_progress">In Progress</option>

                  <option value="completed">Completed</option>

                  <option value="cancelled">Cancelled</option>

                </select>

              </div>

              <button className="button" onClick={() => { setEditingBatch(null); setBatchModalOpen(true); }}>

                <PlusCircle size={16} style={{ marginRight: '6px' }} /> Create Batch

              </button>

            </div>



            {loadingBatches ? (

              <p>Loading training batches...</p>

            ) : batchesData?.results?.length === 0 ? (

              <div className="panel" style={{ textAlign: 'center', padding: '36px' }}>

                <BookOpen size={40} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />

                <h3>No training batches created yet</h3>

                <p style={{ color: 'var(--muted)', marginBottom: '16px' }}>

                  Create batches to organize students and assign curriculum from the WOC academy catalog.

                </p>

                <button className="button" onClick={() => { setEditingBatch(null); setBatchModalOpen(true); }}>

                  Create Your First Batch

                </button>

              </div>

            ) : (

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>

                {batchesData?.results?.map((b: any) => (

                  <div key={b.id} className="panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>

                    <div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>

                        <h3 style={{ margin: 0, fontSize: '18px' }}>{b.name}</h3>

                        <span className={`status-pill ${b.status}`}>{b.status}</span>

                      </div>

                      <p style={{ fontSize: '13px', color: 'var(--gold)', fontWeight: 600, margin: '0 0 10px' }}>

                        {b.program?.title ? `${b.program.title} (${b.program.module})` : 'General Training'}

                      </p>

                      {b.description && (

                        <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '12px' }}>

                          {b.description.slice(0, 100)}{b.description.length > 100 ? '...' : ''}

                        </p>

                      )}

                      <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '16px' }}>

                        <div>Dates: {b.start_date || 'TBD'} to {b.end_date || 'TBD'}</div>

                        <div style={{ marginTop: '4px' }}>

                          <strong>Capacity:</strong> {b.enrolled_count} / {b.capacity} Students Enrolled

                        </div>

                      </div>

                    </div>



                    <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>

                      <button

                        className="button small"

                        style={{ flex: 1 }}

                        onClick={async () => {

                          const detailed = await api(`/college/batches/${b.id}/`);

                          setEnrollModalBatch(detailed);

                        }}

                      >

                        <Users size={14} style={{ marginRight: '4px' }} /> Students ({b.enrolled_count})

                      </button>

                      <button

                        className="button small outline"

                        onClick={() => {

                          setEditingBatch(b);

                          setBatchModalOpen(true);

                        }}

                      >

                        <Edit size={14} />

                      </button>

                      <button

                        className="button small outline"

                        onClick={() => handleDeleteBatch(b.id)}

                      >

                        <Trash2 size={14} />

                      </button>

                    </div>

                  </div>

                ))}

              </div>

            )}

          </div>

        )}



        {/* =========================================================================

            TAB 4: PLACEMENTS & CORPORATE PARTNERSHIPS

           ========================================================================= */}

        {activeTab === 'placements' && (

          <div>

            {/* Campus Placements Section */}

            <div style={{ marginBottom: '40px' }}>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>

                <div>

                  <h2 style={{ margin: 0 }}>Campus Placement Records</h2>

                  <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 0' }}>

                    Track full-time employment offers and internships secured by institutional students.

                  </p>

                </div>

                <button className="button" onClick={() => setPlacementModalOpen(true)}>

                  <PlusCircle size={15} style={{ marginRight: '6px' }} /> Record Placement

                </button>

              </div>



              {loadingPlacements ? (

                <p>Loading placements...</p>

              ) : placementsData?.results?.length === 0 ? (

                <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

                  <Award size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />

                  <h3>No placement records found</h3>

                  <p style={{ color: 'var(--muted)' }}>Record student offers to monitor institutional placement statistics.</p>

                </div>

              ) : (

                <div className="panel" style={{ overflowX: 'auto', padding: 0 }}>

                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>

                    <thead>

                      <tr style={{ borderBottom: '2px solid var(--border)', background: 'var(--surface-alt)' }}>

                        <th style={{ padding: '12px 16px' }}>Student</th>

                        <th style={{ padding: '12px 16px' }}>Role & Company</th>

                        <th style={{ padding: '12px 16px' }}>Type</th>

                        <th style={{ padding: '12px 16px' }}>Package / Stipend</th>

                        <th style={{ padding: '12px 16px' }}>Status</th>

                        <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>

                      </tr>

                    </thead>

                    <tbody>

                      {placementsData?.results?.map((p: any) => (

                        <tr key={p.id} style={{ borderBottom: '1px solid var(--border)' }}>

                          <td style={{ padding: '12px 16px' }}>

                            <strong>{p.student.name}</strong>

                            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{p.student.email}</div>

                          </td>

                          <td style={{ padding: '12px 16px' }}>

                            <strong>{p.role_title}</strong>

                            <div style={{ fontSize: '13px', color: 'var(--muted)' }}>{p.company_name}</div>

                          </td>

                          <td style={{ padding: '12px 16px', textTransform: 'capitalize' }}>

                            {p.placement_type}

                          </td>

                          <td style={{ padding: '12px 16px' }}>

                            {p.compensation || '—'}

                          </td>

                          <td style={{ padding: '12px 16px' }}>

                            <span className={`status-pill ${p.status}`}>{p.status}</span>

                          </td>

                          <td style={{ padding: '12px 16px', textAlign: 'right' }}>

                            <button

                              className="button small outline"

                              onClick={() => handleDeletePlacement(p.id)}

                            >

                              <Trash2 size={14} />

                            </button>

                          </td>

                        </tr>

                      ))}

                    </tbody>

                  </table>

                </div>

              )}

            </div>



            {/* Corporate Partnerships Section */}

            <div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>

                <div>

                  <h2 style={{ margin: 0 }}>Corporate Partnerships & MoUs</h2>

                  <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 0' }}>

                    Connect with approved WOC enterprise employers for campus recruitment and guest lectures.

                  </p>

                </div>

                <button className="button small outline" onClick={() => setPartnershipModalOpen(true)}>

                  <HeartHandshake size={15} style={{ marginRight: '6px' }} /> Add Partner Company

                </button>

              </div>



              {partnershipsData?.results?.length === 0 ? (

                <div className="panel" style={{ textAlign: 'center', padding: '32px' }}>

                  <HeartHandshake size={36} style={{ color: 'var(--muted)', margin: '0 auto 12px' }} />

                  <h3>No corporate partners added yet</h3>

                  <p style={{ color: 'var(--muted)' }}>Establish partnerships with companies hiring from WOC.</p>

                </div>

              ) : (

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>

                  {partnershipsData?.results?.map((part: any) => (

                    <div key={part.id} className="panel">

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>

                        <div>

                          <h3 style={{ margin: 0 }}>{part.company.name}</h3>

                          <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '2px 0 6px' }}>

                            {part.company.city} {part.company.website && `• ${part.company.website}`}

                          </p>

                        </div>

                        <span className={`status-pill ${part.status}`}>{part.status}</span>

                      </div>

                      <div style={{ fontSize: '13px', marginTop: '10px' }}>

                        <div><strong>Type:</strong> {part.partnership_type}</div>

                        {part.contact_person && <div><strong>Contact:</strong> {part.contact_person}</div>}

                        {part.mou_signed_date && <div><strong>MoU Date:</strong> {part.mou_signed_date}</div>}

                        {part.notes && <div style={{ color: 'var(--muted)', marginTop: '4px' }}>{part.notes}</div>}

                      </div>

                    </div>

                  ))}

                </div>

              )}

            </div>

          </div>

        )}



        {/* =========================================================================

            TAB 5: COLLEGE PROFILE

           ========================================================================= */}

        {activeTab === 'engagement' && (

          <CollegeEngagementTab

            activeStudents={(studentsData?.results || []).filter((s: any) => s.status === 'active')}

          />

        )}



        {activeTab === 'profile' && (

          <div className="panel" style={{ maxWidth: '780px' }}>

            <h2 style={{ marginTop: 0 }}>Institution Profile</h2>

            <p style={{ color: 'var(--muted)', marginBottom: '24px' }}>

              Keep institutional contact details, leadership information and profile updated for students and partners.

            </p>



            <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                <label>

                  College / Institution Name

                  <input type="text" value={college.name || ''} disabled style={{ background: 'var(--surface-alt)' }} />

                  <small style={{ color: 'var(--muted)' }}>Name changes require Super Admin approval.</small>

                </label>

                <label>

                  Campus City / Location

                  <input type="text" name="city" defaultValue={college.city || ''} />

                </label>

              </div>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                <label>

                  Principal / Director Name

                  <input type="text" name="principal_name" defaultValue={college.principal_name || ''} placeholder="e.g. Dr. A. Ramanathan" />

                </label>

                <label>

                  Official Contact Phone

                  <input type="text" name="phone" defaultValue={college.phone || ''} placeholder="+91 9876543210" />

                </label>

              </div>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                <label>

                  Contact Email

                  <input type="email" name="contact_email" defaultValue={college.contact_email || ''} />

                </label>

                <label>

                  Official Website (HTTPS)

                  <input type="url" name="website" defaultValue={college.website || ''} placeholder="https://college.edu" />

                </label>

              </div>



              <label>

                Logo Image URL (HTTPS)

                <input type="url" name="logo_url" defaultValue={college.logo_url || ''} placeholder="https://college.edu/logo.png" />

              </label>



              <label>

                Campus Address

                <textarea name="address" defaultValue={college.address || ''} rows={2} />

              </label>



              <label>

                About Institution / Description

                <textarea name="description" defaultValue={college.description || ''} rows={4} placeholder="Brief summary of departments, strengths, facilities..." />

              </label>



              <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>

                <button className="button" type="submit" disabled={profileSaving}>

                  {profileSaving ? 'Saving Changes...' : 'Save Profile'}

                </button>

              </div>

            </form>

          </div>

        )}

      </div>



      {/* =========================================================================

          MODAL: CREATE / EDIT BATCH

         ========================================================================= */}

      {batchModalOpen && (

        <div className="modal-backdrop" onClick={() => setBatchModalOpen(false)}>

          <div className="modal" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>

            <h2>{editingBatch ? 'Edit Training Batch' : 'Create Training Batch'}</h2>

            <form onSubmit={handleSaveBatch} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

              <label>

                Batch Name

                <input type="text" name="name" required defaultValue={editingBatch?.name || ''} placeholder="e.g. AI & Cloud 2026 Batch" />

              </label>



              <label>

                Curriculum / Program

                <select name="program_id" defaultValue={editingBatch?.program?.id || ''}>

                  <option value="">-- Standalone Training / Institutional Module --</option>

                  {catalogData?.programs?.map((p: any) => (

                    <option key={p.id} value={p.id}>

                      {p.title} ({p.module})

                    </option>

                  ))}

                </select>

              </label>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Start Date

                  <input type="date" name="start_date" defaultValue={editingBatch?.start_date || ''} />

                </label>

                <label>

                  End Date

                  <input type="date" name="end_date" defaultValue={editingBatch?.end_date || ''} />

                </label>

              </div>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Max Capacity

                  <input type="number" name="capacity" min={1} max={2000} defaultValue={editingBatch?.capacity || 50} />

                </label>

                <label>

                  Status

                  <select name="status" defaultValue={editingBatch?.status || 'upcoming'}>

                    <option value="upcoming">Upcoming</option>

                    <option value="in_progress">In Progress</option>

                    <option value="completed">Completed</option>

                    <option value="cancelled">Cancelled</option>

                  </select>

                </label>

              </div>



              <label>

                Batch Description / Notes

                <textarea name="description" rows={3} defaultValue={editingBatch?.description || ''} placeholder="Batch objectives, venue or timings..." />

              </label>



              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>

                <button type="button" className="button outline" onClick={() => setBatchModalOpen(false)}>

                  Cancel

                </button>

                <button type="submit" className="button">

                  {editingBatch ? 'Update Batch' : 'Create Batch'}

                </button>

              </div>

            </form>

          </div>

        </div>

      )}



      {/* =========================================================================

          MODAL: MANAGE BATCH STUDENTS

         ========================================================================= */}

      {enrollModalBatch && (

        <div className="modal-backdrop" onClick={() => setEnrollModalBatch(null)}>

          <div className="modal" style={{ maxWidth: '640px', maxHeight: '80vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>

            <h2>Enrolled Students — {enrollModalBatch.name}</h2>

            <p style={{ color: 'var(--muted)', fontSize: '13px' }}>

              Capacity: {enrollModalBatch.students?.length || 0} / {enrollModalBatch.capacity} enrolled

            </p>



            <h4 style={{ margin: '16px 0 8px' }}>Currently Enrolled Students</h4>

            {enrollModalBatch.students?.length === 0 ? (

              <p style={{ color: 'var(--muted)', fontSize: '13px' }}>No students enrolled in this batch yet.</p>

            ) : (

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>

                {enrollModalBatch.students?.map((s: any) => (

                  <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--surface-alt)', borderRadius: '6px' }}>

                    <div>

                      <strong>{s.name}</strong>

                      <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{s.email}</div>

                    </div>

                    <button

                      className="button small outline"

                      onClick={() => handleEnrollToggle(enrollModalBatch.id, s.id, true)}

                    >

                      Remove

                    </button>

                  </div>

                ))}

              </div>

            )}



            <h4 style={{ margin: '20px 0 8px' }}>Add Active College Students</h4>

            {studentsData?.results?.filter((m: any) => m.status === 'active' && !enrollModalBatch.students?.some((es: any) => es.id === m.user_id)).length === 0 ? (

              <p style={{ color: 'var(--muted)', fontSize: '13px' }}>No other active students available to enroll.</p>

            ) : (

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>

                {studentsData?.results

                  ?.filter((m: any) => m.status === 'active' && !enrollModalBatch.students?.some((es: any) => es.id === m.user_id))

                  .map((m: any) => (

                    <div key={m.membership_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', border: '1px solid var(--border)', borderRadius: '6px' }}>

                      <div>

                        <strong>{m.name}</strong>

                        <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{m.email}</div>

                      </div>

                      <button

                        className="button small"

                        disabled={(enrollModalBatch.students?.length || 0) >= enrollModalBatch.capacity}

                        onClick={() => handleEnrollToggle(enrollModalBatch.id, m.user_id, false)}

                      >

                        Enroll

                      </button>

                    </div>

                  ))}

              </div>

            )}



            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>

              <button className="button" onClick={() => setEnrollModalBatch(null)}>Done</button>

            </div>

          </div>

        </div>

      )}



      {/* =========================================================================

          MODAL: RECORD PLACEMENT

         ========================================================================= */}

      {placementModalOpen && (

        <div className="modal-backdrop" onClick={() => setPlacementModalOpen(false)}>

          <div className="modal" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>

            <h2>Record Campus Placement</h2>

            <form onSubmit={handleSavePlacement} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

              <label>

                Select Student

                <select name="student_id" required>

                  <option value="">-- Choose active college student --</option>

                  {studentsData?.results?.filter((s: any) => s.status === 'active').map((s: any) => (

                    <option key={s.user_id} value={s.user_id}>

                      {s.name} ({s.email})

                    </option>

                  ))}

                </select>

              </label>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Partner Company (Optional)

                  <select name="company_id">

                    <option value="">-- Select or type below --</option>

                    {catalogData?.companies?.map((c: any) => (

                      <option key={c.id} value={c.id}>{c.name}</option>

                    ))}

                  </select>

                </label>

                <label>

                  Company Name (if not in list)

                  <input type="text" name="company_name" placeholder="e.g. Infosys, TCS" />

                </label>

              </div>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Role Title

                  <input type="text" name="role_title" required placeholder="e.g. Associate Software Engineer" />

                </label>

                <label>

                  Placement Type

                  <select name="placement_type" defaultValue="job">

                    <option value="job">Full-time Job</option>

                    <option value="internship">Internship</option>

                  </select>

                </label>

              </div>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Compensation / CTC / Stipend

                  <input type="text" name="compensation" placeholder="e.g. 7.5 LPA or ₹25,000/mo" />

                </label>

                <label>

                  Placement Status

                  <select name="status" defaultValue="offered">

                    <option value="offered">Offer Made</option>

                    <option value="accepted">Offer Accepted</option>

                    <option value="declined">Declined</option>

                  </select>

                </label>

              </div>



              <label>

                Offer / Placement Date

                <input type="date" name="placed_at" defaultValue={new Date().toISOString().split('T')[0]} />

              </label>



              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>

                <button type="button" className="button outline" onClick={() => setPlacementModalOpen(false)}>

                  Cancel

                </button>

                <button type="submit" className="button">

                  Save Placement

                </button>

              </div>

            </form>

          </div>

        </div>

      )}



      {/* =========================================================================

          MODAL: ADD PARTNERSHIP

         ========================================================================= */}

      {partnershipModalOpen && (

        <div className="modal-backdrop" onClick={() => setPartnershipModalOpen(false)}>

          <div className="modal" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>

            <h2>Add Corporate Partner</h2>

            <form onSubmit={handleSavePartnership} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

              <label>

                Partner Company

                <select name="company_id" required>

                  <option value="">-- Choose approved WOC company --</option>

                  {catalogData?.companies?.map((c: any) => (

                    <option key={c.id} value={c.id}>{c.name} ({c.city})</option>

                  ))}

                </select>

              </label>



              <label>

                Partnership Type

                <input

                  type="text"

                  name="partnership_type"

                  required

                  defaultValue="Campus Recruitment & Training Partner"

                  placeholder="e.g. Hiring Partner, Guest Lecture Series, Co-op Internship"

                />

              </label>



              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>

                <label>

                  Status

                  <select name="status" defaultValue="active">

                    <option value="active">Active</option>

                    <option value="pending">Pending Signing</option>

                    <option value="ended">Ended</option>

                  </select>

                </label>

                <label>

                  MoU Signed Date

                  <input type="date" name="mou_signed_date" />

                </label>

              </div>



              <label>

                Company Contact Person

                <input type="text" name="contact_person" placeholder="e.g. HR Manager / Campus Recruiter" />

              </label>



              <label>

                Partnership Notes

                <textarea name="notes" rows={3} placeholder="Key terms, campus drive timelines, notes..." />

              </label>



              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>

                <button type="button" className="button outline" onClick={() => setPartnershipModalOpen(false)}>

                  Cancel

                </button>

                <button type="submit" className="button">

                  Add Partner

                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </main>

  );

}

