'use client';

import React, { useState,useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Calendar, Users, Award, Megaphone, PlusCircle, CheckCircle,
  XCircle, Shield, Trash2, ShieldAlert, UserCheck, MapPin
} from 'lucide-react';
import { api,getApiBase } from '@/lib/api';
import { useWoc } from './Platform';

function eventBannerSrc(ev:any){
 if(ev.poster_url)return getApiBase().replace(/\/api$/,'')+ev.poster_url;
 const title=String(ev.title||'').toLowerCase();
 if(title.includes('innovation')&&title.includes('workshop'))return '/images/campus-events/innovation-skills-workshop-2026.jpg?v=2';
 if(title.includes('prompt')||title.includes('bootcamp'))return '/images/campus-events/ai-prompt-bootcamp-2026.jpg?v=2';
 if(title.includes('startup')||title.includes('pitch'))return '/images/campus-events/startup-pitch-arena-2026.jpg?v=2';
 if(title.includes('ui/ux')||title.includes('design jam'))return '/images/campus-events/uiux-design-jam-2026.jpg?v=2';
 if(title.includes('cybersecurity')||title.includes('defense lab'))return '/images/campus-events/cybersecurity-lab-2026.jpg?v=2';
 if(title.includes('design challenge'))return '/images/campus-events/campus-design-challenge-2026.jpg';
 if(title.includes('cultural showcase'))return '/images/campus-events/annual-cultural-showcase-2026.jpg';
 if(title.includes('sports')&&title.includes('teamwork'))return '/images/campus-events/sports-teamwork-day-2026.jpg';
 if(/\b(marathon|run)\b/.test(title))return '/images/campus-events/marathon-2026.png';
 if(/\bcricket\b/.test(title))return '/images/sports-cricket.webp';
 if(/\bfootball\b/.test(title))return '/images/sports-football.webp';
 if(/\bbadminton\b/.test(title))return '/images/sports-badminton.webp';
 if(/\bdance\b/.test(title))return '/images/campus-events/dance-fest-2026.png';
 if(/\bmusic\b/.test(title))return '/images/music-performance.webp';
 if(/\btally/.test(title))return '/images/campus-events/tallyprime-workshop-2026.png';
 if(/\bhackathon\b/.test(title))return '/images/campus-events/hackathon-2026.png';
 if(/\b(energy|expo)\b/.test(title))return '/images/campus-events/renewable-energy-expo-2026.png';
 if(title.includes('artificial intelligence')||/\bai\b/.test(title))return '/images/artificial-intelligence-v2.webp';
 const byType:Record<string,string>={
  workshop:'/images/campus-events/innovation-skills-workshop-2026.jpg',
  technical:'/images/campus-events/hackathon-2026.png',
  competition:'/images/campus-events/campus-design-challenge-2026.jpg',
  webinar:'/images/learning-access.webp',
  seminar:'/images/careers-conversation.webp',
  symposium:'/images/campus-events/renewable-energy-expo-2026.png',
  sports:'/images/campus-events/sports-teamwork-day-2026.jpg',
  cultural:'/images/campus-events/annual-cultural-showcase-2026.jpg',
 };
 return byType[ev.event_type]||'/images/campus-hero.webp';
}

function EventPostMedia({event}:{event:any}){return <>{event.poster_url&&<img src={getApiBase().replace(/\/api$/,'')+event.poster_url} alt={`${event.title} event poster`} loading="lazy" className="campus-event-poster"/>}{event.organizer_name&&<p className="campus-event-organizer"><strong>Organized by:</strong> {event.organizer_name}{event.organizer_contact&&<> · {event.organizer_contact}</>}</p>}{event.end_date&&<p className="campus-event-meta">Ends: {new Date(event.end_date).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</p>}{event.registration_deadline&&<p className="campus-event-meta">Register by: {new Date(event.registration_deadline).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</p>}</>}
function localEventDate(value?:string){if(!value)return '';const date=new Date(value);return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16)}

// ============================================================================
// 1. STUDENT ENGAGEMENT TAB (Events, Clubs, Leadership, Achievements)
// ============================================================================
export function StudentEngagementTab() {
  const { user, demo, toast } = useWoc();
  const [subTab, setSubTab] = useState<'events' | 'clubs' | 'leadership' | 'history'>('events');
  const [annClubId, setAnnClubId] = useState('');
  const [annTitle, setAnnTitle] = useState('');
  const [annContent, setAnnContent] = useState('');
  const [busy, setBusy] = useState(false);

  const [requestedEvent,setRequestedEvent]=useState('');
  useEffect(()=>{setRequestedEvent(new URLSearchParams(window.location.search).get('event')||'')},[]);
  const { data, refetch, isLoading } = useQuery({
    queryKey: ['student-engagement', user?.id,requestedEvent],
    queryFn: () => api('/student/engagement/'+(requestedEvent?'?event='+encodeURIComponent(requestedEvent):'')),
    enabled: !!user && !demo,
  });

  if (demo) {
    return (
      <div className="panel">
        <p>Campus events, clubs, and leadership assignments require the local Django backend.</p>
      </div>
    );
  }

  if (isLoading) return <p>Loading campus engagement...</p>;

  const stats = data?.stats || {
    registered_events: 0,
    attended_events: 0,
    approved_clubs: 0,
    active_leadership_roles: 0,
    achievements_count: 0,
  };

  async function registerEvent(id: string) {
    try {
      await api(`/student/events/${id}/register/`, 'POST', {});
      toast('Event registration confirmed.');
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Could not register for event.');
    }
  }

  async function cancelEvent(id: string) {
    if (!confirm('Cancel your registration for this event?')) return;
    try {
      await api(`/student/events/${id}/cancel/`, 'POST', {});
      toast('Event registration cancelled.');
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Could not cancel registration.');
    }
  }

  async function joinClub(id: string) {
    try {
      await api(`/student/clubs/${id}/join/`, 'POST', {});
      toast('Club membership request submitted.');
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Could not submit club request.');
    }
  }

  async function leaveClub(id: string) {
    if (!confirm('Leave this club or withdraw your request?')) return;
    try {
      await api(`/student/clubs/${id}/leave/`, 'POST', {});
      toast('Club membership updated.');
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Could not update club membership.');
    }
  }

  async function postClubAnnouncement(e: React.FormEvent) {
    e.preventDefault();
    if (!annClubId) return;
    setBusy(true);
    try {
      await api('/student/leadership/announcements/', 'POST', {
        club_id: annClubId,
        title: annTitle,
        content: annContent,
      });
      toast('Club announcement published.');
      setAnnTitle('');
      setAnnContent('');
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Failed to post announcement.');
    } finally {
      setBusy(false);
    }
  }

  const leaderClubs = (data?.leadership_roles || []).filter(
    (l: any) => l.club && Array.isArray(l.permissions) && l.permissions.includes('post_club_announcement')
  );

  return (
    <div>
      {/* Engagement Stats */}
      <div className="stats-grid" style={{ marginBottom: '20px' }}>
        <div className="stat-card">
          <span className="stat-label"><Calendar size={15} /> Registered Events</span>
          <span className="stat-val">{stats.registered_events}</span>
          <span className="stat-sub">{stats.attended_events} attended</span>
        </div>
        <div className="stat-card">
          <span className="stat-label"><Users size={15} /> My Clubs</span>
          <span className="stat-val">{stats.approved_clubs}</span>
          <span className="stat-sub">{data?.affiliated_college?.name || 'No college affiliated'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label"><Shield size={15} /> Leadership Roles</span>
          <span className="stat-val">{stats.active_leadership_roles}</span>
          <span className="stat-sub">Active campus responsibilities</span>
        </div>
        <div className="stat-card">
          <span className="stat-label"><Award size={15} /> Achievements</span>
          <span className="stat-val">{stats.achievements_count}</span>
          <span className="stat-sub">Verified event recognitions</span>
        </div>
      </div>

      {/* Sub-navigation */}
      <div className="lesson-tabs" style={{ marginBottom: '20px' }}>
        <button aria-pressed={subTab === 'events'} onClick={() => setSubTab('events')}>Upcoming Events</button>
        <button aria-pressed={subTab === 'clubs'} onClick={() => setSubTab('clubs')}>Clubs & Chapters</button>
        <button aria-pressed={subTab === 'leadership'} onClick={() => setSubTab('leadership')}>Leadership</button>
        <button aria-pressed={subTab === 'history'} onClick={() => setSubTab('history')}>History & Announcements</button>
      </div>

      {/* Upcoming Events */}
      {subTab === 'events' && (
        <div>
          {!data?.upcoming_events?.length ? (
            <div className="panel student-engagement-empty"><Calendar size={32} aria-hidden="true"/><h3>No upcoming events yet</h3><p>Campus and public events will appear here when available.</p></div>
          ) : (
            <div className="campus-event-grid">
              {data.upcoming_events.map((ev:any)=>{
                const isReg=ev.my_registration?.status==='registered';
                const full=ev.registered_count>=ev.capacity;
                const date=new Date(ev.event_date);
                return <article key={ev.id} className={`campus-post-card ${requestedEvent===ev.id?'notification-target-event':''}`} id={`event-${ev.id}`}>
                  <div className="campus-post-banner"><img src={eventBannerSrc(ev)} alt={`${ev.title} event banner`} loading="lazy"/><div className="campus-post-date"><strong>{date.getDate()}</strong><span>{date.toLocaleDateString('en-IN',{month:'short'})}</span></div></div>
                  <div className="campus-post-content">
                    <div className="campus-post-badges"><span>{ev.event_type.replaceAll('_',' ')}</span><span>{ev.visibility==='public'?'Open to all colleges':'College event'}</span>{isReg&&<span>Registered</span>}</div>
                    <p className="campus-post-college">{ev.institution_name}</p>
                    <h3>{ev.title}</h3>
                    <div className="campus-post-info"><p><Calendar size={15}/><span>{date.toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})} · {date.toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'})}</span></p><p><MapPin size={15}/><span>{ev.venue}</span></p>{ev.organizer_name&&<p><Users size={15}/><span>{ev.organizer_name}</span></p>}</div>
                    <p className="campus-post-description">{ev.description}</p>
                    <details className="campus-post-details"><summary>Event details</summary><p>{ev.description}</p>{ev.organizer_contact&&<p><strong>Organizer contact:</strong> {ev.organizer_contact}</p>}{ev.end_date&&<p><strong>Ends:</strong> {new Date(ev.end_date).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</p>}{ev.registration_deadline&&<p><strong>Register by:</strong> {new Date(ev.registration_deadline).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</p>}{ev.eligibility&&<p><strong>Eligibility:</strong> {ev.eligibility}</p>}</details>
                  </div>
                  <footer className="campus-post-footer"><span><Users size={15}/>{ev.registered_count} / {ev.capacity} registered</span>{isReg?<button className="button small outline" onClick={()=>cancelEvent(ev.id)}>Cancel registration</button>:<button className="button small" disabled={full} onClick={()=>registerEvent(ev.id)}>{full?'Full':'Register'}</button>}</footer>
                </article>;
              })}
            </div>
          )}
        </div>
      )}

      {/* Clubs & Chapters */}
      {subTab === 'clubs' && (
        <div>
          {!data?.affiliated_college ? (
            <div className="panel">
              <p style={{ color: 'var(--muted)' }}>Affiliate with an approved college in <strong>My College</strong> to join campus clubs and chapters.</p>
            </div>
          ) : !data?.clubs?.length ? (
            <div className="panel"><p style={{ color: 'var(--muted)' }}>No active clubs listed at {data.affiliated_college.name} yet.</p></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: '16px' }}>
              {data.clubs.map((c: any) => (
                <div key={c.id} className="panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <span className="label">{c.category}</span>
                    {c.my_membership_status && <span className={`status-pill ${c.my_membership_status}`}>{c.my_membership_status}</span>}
                  </div>
                  <h3 style={{ margin: '8px 0 4px' }}>{c.name}</h3>
                  <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 12px' }}>{c.description}</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <small style={{ color: 'var(--muted)' }}>{c.members_count} members</small>
                    {c.my_membership_status === 'approved' || c.my_membership_status === 'pending' ? (
                      <button className="button small outline" onClick={() => leaveClub(c.id)}>
                        {c.my_membership_status === 'pending' ? 'Withdraw' : 'Leave Club'}
                      </button>
                    ) : (
                      <button className="button small" onClick={() => joinClub(c.id)}>Request to Join</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Leadership */}
      {subTab === 'leadership' && (
        <div>
          {!data?.leadership_roles?.length ? (
            <div className="panel"><p style={{ color: 'var(--muted)' }}>You do not have any active campus leadership assignments.</p></div>
          ) : (
            <div className="record-list" style={{ marginBottom: '24px' }}>
              {data.leadership_roles.map((l: any) => (
                <div key={l.id} className="record">
                  <div>
                    <span className="label">{l.role.replace('_', ' ')}</span>
                    <h3 style={{ margin: '4px 0' }}>{l.title || l.role.replace('_', ' ')}</h3>
                    <p style={{ margin: '0 0 6px', fontSize: '13px', color: 'var(--muted)' }}>
                      {l.institution_name} {l.club ? `• Club: ${l.club.name}` : ''}
                    </p>
                    {l.responsibilities && <p style={{ margin: '0 0 6px', fontSize: '13px' }}>{l.responsibilities}</p>}
                    <small style={{ color: 'var(--muted)' }}>
                      Permissions: {(l.permissions || []).join(', ') || 'Standard'}
                    </small>
                  </div>
                  <span className="status-pill active">Active</span>
                </div>
              ))}
            </div>
          )}

          {leaderClubs.length > 0 && (
            <form onSubmit={postClubAnnouncement} className="panel form-stack">
              <h3 style={{ marginTop: 0 }}><Megaphone size={16} style={{ marginRight: '6px' }} /> Post Club Announcement</h3>
              <label>
                Club
                <select value={annClubId} onChange={(e) => setAnnClubId(e.target.value)} required>
                  <option value="">-- Select your assigned club --</option>
                  {leaderClubs.map((l: any) => (
                    <option key={l.club.id} value={l.club.id}>{l.club.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Title
                <input required value={annTitle} onChange={(e) => setAnnTitle(e.target.value)} placeholder="Announcement title" />
              </label>
              <label>
                Message
                <textarea required rows={3} value={annContent} onChange={(e) => setAnnContent(e.target.value)} placeholder="Share club updates or meeting details..." />
              </label>
              <button className="button small" disabled={busy}>{busy ? 'Publishing...' : 'Publish Club Announcement'}</button>
            </form>
          )}
        </div>
      )}

      {/* Participation History, Achievements & Announcements */}
      {subTab === 'history' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Participation & Achievements</h3>
            {!data?.my_registrations?.length ? (
              <p style={{ color: 'var(--muted)', fontSize: '13px' }}>No event participation recorded yet.</p>
            ) : (
              <div className="record-list">
                {data.my_registrations.map((r: any) => (
                  <div key={r.registration_id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{r.event.title}</strong>
                      <span className={`status-pill ${r.status}`}>{r.status}</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                      {r.event.institution_name} • {new Date(r.event.event_date).toLocaleDateString('en-IN')}
                    </div>
                    {r.achievement && (
                      <div style={{ fontSize: '13px', color: 'var(--crimson)', fontWeight: 600, marginTop: '4px' }}>
                        <Award size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> {r.achievement}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Campus & Club Announcements</h3>
            {!data?.announcements?.length ? (
              <p style={{ color: 'var(--muted)', fontSize: '13px' }}>No recent campus announcements.</p>
            ) : (
              <div className="record-list">
                {data.announcements.map((a: any) => (
                  <div key={a.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{a.title}</strong>
                      <span className="label">{a.club ? a.club.name : 'Campus'}</span>
                    </div>
                    <p style={{ fontSize: '13px', margin: '4px 0' }}>{a.content}</p>
                    <small style={{ color: 'var(--muted)' }}>{new Date(a.created_at).toLocaleDateString('en-IN')}</small>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 2. COLLEGE ADMIN ENGAGEMENT TAB
// ============================================================================
export function CollegeEngagementTab({ activeStudents }: { activeStudents: any[] }) {
  const { toast } = useWoc();
  const [subTab, setSubTab] = useState<'events' | 'clubs' | 'leadership' | 'announcements'>('events');
  const [eventModal, setEventModal] = useState(false);
  const [editingEvent,setEditingEvent]=useState<any>(null);
  const [eventBusy,setEventBusy]=useState(false);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);
  const [clubModal, setClubModal] = useState(false);
  const [selectedClub, setSelectedClub] = useState<any>(null);
  const [leaderModal, setLeaderModal] = useState(false);

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['college-engagement-stats'],
    queryFn: () => api('/college/engagement/stats/'),
  });
  const { data: eventsData, refetch: refetchEvents } = useQuery({
    queryKey: ['college-events'],
    queryFn: () => api('/college/events/'),
  });
  const { data: clubsData, refetch: refetchClubs } = useQuery({
    queryKey: ['college-clubs'],
    queryFn: () => api('/college/clubs/'),
  });
  const { data: leaderData, refetch: refetchLeaders } = useQuery({
    queryKey: ['college-leadership'],
    queryFn: () => api('/college/leadership/'),
  });
  const { data: annData, refetch: refetchAnns } = useQuery({
    queryKey: ['college-announcements'],
    queryFn: () => api('/college/announcements/'),
  });

  async function createEvent(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();if(eventBusy)return;setEventBusy(true);
    const fd=new FormData(e.currentTarget);
    try{
      for(const key of ['event_date','end_date','registration_deadline']){const value=String(fd.get(key)||'');fd.set(key,value?new Date(value).toISOString():'')}
      const poster=fd.get('poster_image');if(!(poster instanceof File)||!poster.size)fd.delete('poster_image');
      if(poster instanceof File&&poster.size>5*1024*1024)throw new Error('Poster must be up to 5 MB.');
      await api(editingEvent?`/college/events/${editingEvent.id}/`:'/college/events/',editingEvent?'PATCH':'POST',fd);
      toast(editingEvent?'Campus event updated.':'Campus event published.');setEventModal(false);setEditingEvent(null);refetchEvents();refetchStats();
    }catch(err:any){toast(err?.message||'Could not save event.')}finally{setEventBusy(false)}
  }

  async function updateParticipant(eventId: string, regId: string, statusVal: string, achievement?: string) {
    try {
      await api(`/college/events/${eventId}/participants/${regId}/`, 'POST', {
        status: statusVal,
        achievement: achievement || '',
      });
      toast('Participant updated.');
      setSelectedEvent(await api(`/college/events/${eventId}/`));
      refetchStats();
    } catch (err: any) {
      toast(err?.message || 'Failed to update participant.');
    }
  }

  async function createClub(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api('/college/clubs/', 'POST', {
        name: fd.get('name'),
        category: fd.get('category'),
        description: fd.get('description'),
      });
      toast('Club created.');
      setClubModal(false);
      refetchClubs();
      refetchStats();
    } catch (err: any) {
      toast(err?.message || 'Failed to create club.');
    }
  }

  async function reviewClubMember(clubId: string, membershipId: string, action: 'approve' | 'reject') {
    try {
      await api(`/college/clubs/${clubId}/members/${membershipId}/review/`, 'POST', { action });
      toast(`Club membership ${action}d.`);
      setSelectedClub(await api(`/college/clubs/${clubId}/`));
      refetchClubs();
      refetchStats();
    } catch (err: any) {
      toast(err?.message || 'Failed to review club membership.');
    }
  }

  async function assignLeadership(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api('/college/leadership/', 'POST', {
        student_id: Number(fd.get('student_id')),
        role: fd.get('role'),
        club_id: fd.get('club_id') || null,
        title: fd.get('title') || '',
        responsibilities: fd.get('responsibilities') || '',
      });
      toast('Leadership role assigned.');
      setLeaderModal(false);
      refetchLeaders();
      refetchStats();
    } catch (err: any) {
      toast(err?.message || 'Failed to assign leadership.');
    }
  }

  async function revokeLeadership(id: string) {
    if (!confirm('Revoke this leadership assignment?')) return;
    try {
      await api(`/college/leadership/${id}/revoke/`, 'POST', {});
      toast('Leadership role revoked.');
      refetchLeaders();
      refetchStats();
    } catch (err: any) {
      toast(err?.message || 'Failed to revoke leadership.');
    }
  }

  async function postAnnouncement(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api('/college/announcements/', 'POST', {
        title: fd.get('title'),
        content: fd.get('content'),
        club_id: fd.get('club_id') || null,
      });
      toast('Announcement published.');
      e.currentTarget.reset();
      refetchAnns();
    } catch (err: any) {
      toast(err?.message || 'Failed to post announcement.');
    }
  }

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '20px' }}>
        <div className="stat-card">
          <span className="stat-label"><Calendar size={15} /> Campus Events</span>
          <span className="stat-val">{stats?.total_events || 0}</span>
          <span className="stat-sub">{stats?.upcoming_events || 0} upcoming • {stats?.total_attended || 0} attended</span>
        </div>
        <div className="stat-card">
          <span className="stat-label"><Users size={15} /> Clubs & Chapters</span>
          <span className="stat-val">{stats?.active_clubs || 0}</span>
          <span className="stat-sub">{stats?.pending_club_requests || 0} pending join requests</span>
        </div>
        <div className="stat-card">
          <span className="stat-label"><Shield size={15} /> Campus Leaders</span>
          <span className="stat-val">{stats?.active_leaders || 0}</span>
          <span className="stat-sub">Ambassadors, coordinators & leads</span>
        </div>
      </div>

      <div className="lesson-tabs" style={{ marginBottom: '20px' }}>
        <button aria-pressed={subTab === 'events'} onClick={() => setSubTab('events')}>Events & Attendance</button>
        <button aria-pressed={subTab === 'clubs'} onClick={() => setSubTab('clubs')}>Clubs & Chapters</button>
        <button aria-pressed={subTab === 'leadership'} onClick={() => setSubTab('leadership')}>Leadership</button>
        <button aria-pressed={subTab === 'announcements'} onClick={() => setSubTab('announcements')}>Announcements</button>
      </div>

      {subTab === 'events' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ margin: 0 }}>Campus Events</h3>
            <button className="button small" onClick={() => {setEditingEvent(null);setEventModal(true)}}><PlusCircle size={15} style={{ marginRight: '6px' }} /> Create Event</button>
          </div>
          <div className="record-list">
            {(eventsData?.results || []).map((ev: any) => (
              <div key={ev.id} className="record" style={{ flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ flex: 1 }}>
                  <span className="label">{ev.event_type} • {ev.visibility}</span>
                  <h3 style={{ margin: '4px 0' }}>{ev.title}</h3><EventPostMedia event={ev}/>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                    {ev.venue} • {new Date(ev.event_date).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })} • {ev.registered_count}/{ev.capacity} registered
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span className={`status-pill ${ev.status}`}>{ev.status}</span>
                  <button className="button small outline" disabled={ev.status==='suspended'} onClick={()=>{setEditingEvent(ev);setEventModal(true)}}>Edit event</button>
                  <button className="button small outline" onClick={async () => setSelectedEvent(await api(`/college/events/${ev.id}/`))}>
                    Participants ({ev.registered_count})
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === 'clubs' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ margin: 0 }}>Student Clubs & Chapters</h3>
            <button className="button small" onClick={() => setClubModal(true)}><PlusCircle size={15} style={{ marginRight: '6px' }} /> Create Club</button>
          </div>
          <div className="record-list">
            {(clubsData?.results || []).map((c: any) => (
              <div key={c.id} className="record">
                <div>
                  <span className="label">{c.category}</span>
                  <h3 style={{ margin: '4px 0' }}>{c.name}</h3>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                    {c.members_count} members • {c.pending_count} pending requests
                  </p>
                </div>
                <button className="button small outline" onClick={async () => setSelectedClub(await api(`/college/clubs/${c.id}/`))}>
                  Manage Members
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === 'leadership' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ margin: 0 }}>Campus Leadership Assignments</h3>
            <button className="button small" onClick={() => setLeaderModal(true)}><PlusCircle size={15} style={{ marginRight: '6px' }} /> Assign Leader</button>
          </div>
          <div className="record-list">
            {(leaderData?.results || []).map((l: any) => (
              <div key={l.id} className="record">
                <div>
                  <span className="label">{l.role.replace('_', ' ')}</span>
                  <h3 style={{ margin: '4px 0' }}>{l.student.name} {l.title ? `— ${l.title}` : ''}</h3>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                    {l.club ? `Club: ${l.club.name} • ` : ''}Permissions: {(l.permissions || []).join(', ')}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span className={`status-pill ${l.status}`}>{l.status}</span>
                  {l.status === 'active' && (
                    <button className="button small outline" onClick={() => revokeLeadership(l.id)}>Revoke</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === 'announcements' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <form onSubmit={postAnnouncement} className="panel form-stack">
            <h3 style={{ marginTop: 0 }}>Publish Campus Announcement</h3>
            <label>
              Target Audience
              <select name="club_id">
                <option value="">College-wide (All active students)</option>
                {(clubsData?.results || []).map((c: any) => <option key={c.id} value={c.id}>Club: {c.name}</option>)}
              </select>
            </label>
            <label>Title<input name="title" required /></label>
            <label>Content<textarea name="content" rows={3} required /></label>
            <button className="button small">Publish</button>
          </form>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Recent Announcements</h3>
            {(annData?.results || []).map((a: any) => (
              <div key={a.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <strong>{a.title}</strong>
                <p style={{ fontSize: '13px', margin: '4px 0' }}>{a.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      {eventModal && (
        <div className="modal-backdrop" onClick={() => setEventModal(false)}>
          <div className="modal" style={{ maxWidth: '540px' }} onClick={(e) => e.stopPropagation()}>
            <h2>{editingEvent?'Edit Campus Event':'Create Campus Event'}</h2>
            <form key={editingEvent?.id||'new-event'} onSubmit={createEvent} className="form-stack">
              <label>Title<input name="title" defaultValue={editingEvent?.title||''} required /></label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <label>Type
                  <select name="event_type" defaultValue={editingEvent?.event_type||'technical'}>
                    <option value="symposium">Symposium</option><option value="technical">Technical</option><option value="workshop">Workshop</option>
                    <option value="webinar">Webinar</option><option value="seminar">Seminar</option>
                    <option value="competition">Competition</option><option value="sports">Sports</option>
                    <option value="cultural">Cultural</option>
                  </select>
                </label>
                <label>Visibility
                  <select name="visibility" defaultValue={editingEvent?.visibility||'college'}><option value="college">College Only</option><option value="public">Public</option></select>
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <label>Date & Time<input type="datetime-local" name="event_date" defaultValue={localEventDate(editingEvent?.event_date)} required /></label>
                <label>Capacity<input type="number" name="capacity" min={1} defaultValue={editingEvent?.capacity||100} /></label>
              </div>
              <label>End date & time<input type="datetime-local" name="end_date" defaultValue={localEventDate(editingEvent?.end_date)}/></label>
              <label>Registration closes<input type="datetime-local" name="registration_deadline" defaultValue={localEventDate(editingEvent?.registration_deadline)}/></label>
              <label>Organized by<input name="organizer_name" maxLength={200} required defaultValue={editingEvent?.organizer_name||''} placeholder="College, department, club or organizing team"/></label>
              <label>Organizer contact<input name="organizer_contact" maxLength={150} defaultValue={editingEvent?.organizer_contact||''} placeholder="Contact email or phone number"/></label>
              <label>Event poster<input type="file" name="poster_image" accept="image/jpeg,image/png,image/webp"/><small>JPG, PNG or WebP · Maximum 5 MB. Uploading replaces the existing poster.</small></label>
              {editingEvent&&<EventPostMedia event={editingEvent}/>}
              <label>Status<select name="status" defaultValue={editingEvent?.status||'upcoming'}><option value="upcoming">Upcoming</option><option value="ongoing">Ongoing</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select></label>
              <label>Venue<input name="venue" defaultValue={editingEvent?.venue||''} required /></label>
              <label>Eligibility<input name="eligibility" defaultValue={editingEvent?.eligibility||''} placeholder="Who can participate?" /></label>
              <label>Description<textarea name="description" defaultValue={editingEvent?.description||''} rows={3} required /></label>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="button outline" onClick={() => setEventModal(false)}>Cancel</button>
                <button className="button" disabled={eventBusy}>{eventBusy?'Saving…':editingEvent?'Save changes':'Publish event'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedEvent && (
        <div className="modal-backdrop" onClick={() => setSelectedEvent(null)}>
          <div className="modal" style={{ maxWidth: '640px', maxHeight: '80vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
            <h2>Participants — {selectedEvent.title}</h2>
            {!selectedEvent.participants?.length ? <p>No participants registered yet.</p> : (
              <div className="record-list">
                {selectedEvent.participants.map((p: any) => (
                  <div key={p.registration_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)', gap: '8px' }}>
                    <div>
                      <strong>{p.name}</strong> <span className={`status-pill ${p.status}`}>{p.status}</span>
                      <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{p.email} {p.achievement ? `• 🏆 ${p.achievement}` : ''}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="button small" onClick={() => updateParticipant(selectedEvent.id, p.registration_id, 'attended', p.achievement)}>Attended</button>
                      <button className="button small outline" onClick={() => {
                        const ach = prompt('Enter achievement / award (e.g. 1st Place):', p.achievement || '');
                        if (ach !== null) updateParticipant(selectedEvent.id, p.registration_id, 'attended', ach);
                      }}>Award</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div style={{ marginTop: '16px', textAlign: 'right' }}><button className="button" onClick={() => setSelectedEvent(null)}>Close</button></div>
          </div>
        </div>
      )}

      {clubModal && (
        <div className="modal-backdrop" onClick={() => setClubModal(false)}>
          <div className="modal" style={{ maxWidth: '480px' }} onClick={(e) => e.stopPropagation()}>
            <h2>Create Student Club</h2>
            <form onSubmit={createClub} className="form-stack">
              <label>Club Name<input name="name" required /></label>
              <label>Category
                <select name="category">
                  <option value="technical">Technical</option><option value="cultural">Cultural</option>
                  <option value="sports">Sports</option><option value="entrepreneurship">Entrepreneurship</option>
                  <option value="professional">Professional Development</option>
                </select>
              </label>
              <label>Description<textarea name="description" rows={3} required /></label>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="button outline" onClick={() => setClubModal(false)}>Cancel</button>
                <button className="button">Create Club</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedClub && (
        <div className="modal-backdrop" onClick={() => setSelectedClub(null)}>
          <div className="modal" style={{ maxWidth: '600px', maxHeight: '80vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
            <h2>Members — {selectedClub.name}</h2>
            {!selectedClub.members?.length ? <p>No membership requests yet.</p> : (
              <div className="record-list">
                {selectedClub.members.map((m: any) => (
                  <div key={m.membership_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <div><strong>{m.name}</strong> <span className={`status-pill ${m.status}`}>{m.status}</span><div style={{ fontSize: '12px', color: 'var(--muted)' }}>{m.email}</div></div>
                    {m.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button className="button small" onClick={() => reviewClubMember(selectedClub.id, m.membership_id, 'approve')}>Approve</button>
                        <button className="button small outline" onClick={() => reviewClubMember(selectedClub.id, m.membership_id, 'reject')}>Reject</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            <div style={{ marginTop: '16px', textAlign: 'right' }}><button className="button" onClick={() => setSelectedClub(null)}>Close</button></div>
          </div>
        </div>
      )}

      {leaderModal && (
        <div className="modal-backdrop" onClick={() => setLeaderModal(false)}>
          <div className="modal" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
            <h2>Assign Campus Leadership</h2>
            <form onSubmit={assignLeadership} className="form-stack">
              <label>Student
                <select name="student_id" required>
                  <option value="">-- Choose active student --</option>
                  {activeStudents.map((s: any) => <option key={s.user_id} value={s.user_id}>{s.name} ({s.email})</option>)}
                </select>
              </label>
              <label>Role
                <select name="role">
                  <option value="campus_ambassador">Campus Ambassador</option>
                  <option value="student_coordinator">Student Coordinator</option>
                  <option value="club_leader">Club Leader</option>
                </select>
              </label>
              <label>Assigned Club (Optional)
                <select name="club_id">
                  <option value="">-- None --</option>
                  {(clubsData?.results || []).map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </label>
              <label>Role Title<input name="title" placeholder="e.g. Tech Fest Coordinator" /></label>
              <label>Responsibilities<textarea name="responsibilities" rows={2} /></label>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="button outline" onClick={() => setLeaderModal(false)}>Cancel</button>
                <button className="button">Assign Role</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 3. SUPER ADMIN ENGAGEMENT OVERSIGHT TAB
// ============================================================================
export function SuperAdminEngagementTab() {
  const { toast } = useWoc();
  const { data, refetch, isLoading } = useQuery({
    queryKey: ['super-admin-engagement'],
    queryFn: () => api('/super-admin/engagement/'),
  });

  async function moderate(kind: 'event' | 'club' | 'announcement', targetId: string, action: 'suspend' | 'restore') {
    const note = action === 'suspend' ? (prompt('Moderation reason:') || 'Suspended by platform moderator.') : '';
    try {
      await api('/super-admin/engagement/moderate/', 'POST', { kind, target_id: targetId, action, note });
      toast(`${kind} ${action}ed.`);
      refetch();
    } catch (err: any) {
      toast(err?.message || 'Moderation failed.');
    }
  }

  if (isLoading) return <p>Loading platform-wide engagement oversight...</p>;
  const summary = data?.summary || {};

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <div className="stat-card"><span className="stat-label">Total Events</span><span className="stat-val">{summary.total_events || 0}</span><span className="stat-sub">{summary.suspended_events || 0} suspended</span></div>
        <div className="stat-card"><span className="stat-label">Total Clubs</span><span className="stat-val">{summary.total_clubs || 0}</span><span className="stat-sub">{summary.suspended_clubs || 0} suspended</span></div>
        <div className="stat-card"><span className="stat-label">Active Leaders</span><span className="stat-val">{summary.active_leadership_roles || 0}</span></div>
      </div>

      <h3>Platform Campus Events</h3>
      <div className="record-list" style={{ marginBottom: '28px' }}>
        {(data?.events || []).map((ev: any) => (
          <div key={ev.id} className="record">
            <div>
              <strong>{ev.title}</strong> <span className={`status-pill ${ev.status}`}>{ev.status}</span>
              <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{ev.institution_name} • {ev.event_type} • {ev.visibility}</div>
            </div>
            {ev.status === 'suspended' ? (
              <button className="button small outline" onClick={() => moderate('event', ev.id, 'restore')}>Restore</button>
            ) : (
              <button className="button small outline" onClick={() => moderate('event', ev.id, 'suspend')}>Suspend</button>
            )}
          </div>
        ))}
      </div>

      <h3>Platform Student Clubs</h3>
      <div className="record-list">
        {(data?.clubs || []).map((c: any) => (
          <div key={c.id} className="record">
            <div>
              <strong>{c.name}</strong> <span className={`status-pill ${c.status}`}>{c.status}</span>
              <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{c.institution_name} • {c.category} • {c.members_count} members</div>
            </div>
            {c.status === 'suspended' ? (
              <button className="button small outline" onClick={() => moderate('club', c.id, 'restore')}>Restore</button>
            ) : (
              <button className="button small outline" onClick={() => moderate('club', c.id, 'suspend')}>Suspend</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
