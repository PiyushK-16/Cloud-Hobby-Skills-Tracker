const CATS = ['Photography', 'Music', 'Coding', 'Art', 'Fitness', 'Cooking', 'Other'];
const LEVELS = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'];
const $view = document.getElementById('view'), $nav = document.getElementById('nav');
const PAGES = { Dashboard: dashboard, Skills: skills, Practice: practice, Goals: goals, Community: community, Profile: profile };
let current = 'Dashboard';

function go(name) { current = name; nav(); PAGES[name](); }
function nav() {
  $nav.replaceChildren(h('b', {}, 'Skill Tracker'), ...(localStorage.getItem('token') ? [
    ...Object.keys(PAGES).map(n => h('button', { class: n === current ? 'on' : '', onclick: () => go(n) }, n)),
    h('button', { onclick: guard(async () => { await api('/api/logout', { method: 'POST' }); localStorage.removeItem('token'); start(); }) }, 'Logout')] : []));
}

/* ---------- auth ---------- */
function authPage() {
  let register = false;
  const draw = () => {
    const f = h('form', { onsubmit: guard(async e => {
      e.preventDefault(); const d = Object.fromEntries(new FormData(f));
      if (register) { await api('/api/register', { method: 'POST', body: d }); toast('Registered! Logging in...'); }
      const r = await api('/api/login', { method: 'POST', body: { email: d.email, password: d.password } });
      localStorage.setItem('token', r.access_token); start();
    }) },
      ...(register ? [field('Name', h('input', { name: 'name', required: true })), field('Username', h('input', { name: 'username', required: true, pattern: '[A-Za-z0-9_]{3,30}' }))] : []),
      field('Email', h('input', { name: 'email', type: 'email', required: true })),
      field('Password (min 8)', h('input', { name: 'password', type: 'password', minlength: 8, required: true })),
      h('button', { class: 'btn' }, register ? 'Create account' : 'Log in'),
      h('button', { type: 'button', class: 'btn alt', onclick: () => { register = !register; draw(); } }, register ? 'I have an account' : 'Need an account?'));
    $view.replaceChildren(h('div', { class: 'card narrow' }, h('h2', {}, register ? 'Register' : 'Login'), f));
  };
  draw();
}

/* ---------- dashboard ---------- */
async function dashboard() {
  const d = await guard(() => api('/api/analytics/dashboard'))(); if (!d) return;
  const stat = (n, l) => h('div', { class: 'card stat' }, h('div', { class: 'n' }, n), h('small', {}, l));
  $view.replaceChildren(h('h2', {}, `Welcome, ${d.welcome}`),
    h('div', { class: 'grid' }, stat(d.active_skills, 'Active skills'), stat(d.total_practice_hours + ' h', 'Total practice'), stat(d.weekly_hours + ' h', 'Last 7 days'),
      stat(d.monthly_hours + ' h', 'This month'), stat(d.current_streak + ' 🔥', `Streak (best ${d.longest_streak})`), stat(d.goals_completed + '/' + (d.goals_completed + d.active_goals), 'Goals done'),
      stat(d.milestones_achieved, 'Milestones'), stat(d.posts, 'Posts'), stat(d.likes_received, 'Likes'), stat(d.comments_received, 'Comments')),
    h('div', { class: 'card' }, h('h3', {}, 'Practice hours by skill'), barChart(d.hours_by_skill.map(x => ({ label: x.skill, value: x.hours })))),
    h('div', { class: 'card' }, h('h3', {}, 'Weekly practice trend (8 weeks)'), barChart(d.weekly_trend.map(x => ({ label: x.week_start.slice(5), value: x.hours })))),
    h('div', { class: 'card' }, h('h3', {}, 'Monthly progress'), barChart(d.monthly_progress.map(x => ({ label: x.month, value: x.hours })))),
    h('div', { class: 'card' }, h('h3', {}, 'Goal completion'), barChart(d.goal_completion.map(x => ({ label: x.title, value: x.progress_pct })), '%')),
    h('div', { class: 'card' }, h('h3', {}, 'Skill distribution'), barChart(d.skill_distribution.map(x => ({ label: x.category, value: x.count })), '')),
    h('div', { class: 'card' }, h('h3', {}, 'Recent activity'), d.recent_activity.length ? d.recent_activity.map(a => h('p', {}, `${a.practiced_at} · ${a.skill_name} · ${a.duration_minutes} min · ${a.activity}`)) : h('p', { class: 'muted' }, 'Log a practice session to see it here.')));
}

/* ---------- skills ---------- */
async function skills() {
  const list = await guard(() => api('/api/skills'))() || [];
  const f = h('form', { onsubmit: guard(async e => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(f));
    Object.keys(d).forEach(k => d[k] === '' && delete d[k]);
    await api('/api/skills', { method: 'POST', body: d }); toast('Skill added'); skills();
  }) },
    field('Skill name', h('input', { name: 'skill_name', required: true })),
    field('Category', h('select', { name: 'category' }, CATS.map(c => h('option', {}, c)))),
    h('div', { class: 'row' }, field('Current level', h('select', { name: 'current_level' }, LEVELS.map(l => h('option', {}, l)))),
      field('Target level', h('select', { name: 'target_level' }, LEVELS.map(l => h('option', { selected: l === 'INTERMEDIATE' }, l)))),
      field('Start', h('input', { name: 'start_date', type: 'date' })), field('Target date', h('input', { name: 'target_date', type: 'date' }))),
    field('Description', h('textarea', { name: 'description', maxlength: 500 })), h('button', { class: 'btn' }, 'Add skill'));
  $view.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'Add a hobby / skill'), f),
    ...list.map(s => h('div', { class: 'card' }, h('div', { class: 'row' }, h('h3', {}, s.skill_name), h('span', { class: 'tag' }, s.category), h('span', { class: 'chip' }, s.status)),
      h('p', { class: 'muted' }, `${s.current_level} → ${s.target_level}`, s.description ? ' · ' + s.description : ''),
      h('div', { class: 'row' },
        h('select', { onchange: guard(async e => { await api('/api/skills/' + s.skill_id, { method: 'PUT', body: { status: e.target.value } }); toast('Status updated'); }) },
          ['ACTIVE', 'PAUSED', 'COMPLETED'].map(x => h('option', { selected: x === s.status }, x))),
        h('button', { class: 'btn del', onclick: guard(async () => { if (confirm('Delete this skill and all its sessions/goals?')) { await api('/api/skills/' + s.skill_id, { method: 'DELETE' }); skills(); } }) }, 'Delete')))));
}

/* ---------- practice ---------- */
async function practice() {
  const [list, sessions] = await Promise.all([api('/api/skills').catch(() => []), api('/api/practice?limit=15').catch(() => [])]);
  const f = h('form', { onsubmit: guard(async e => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(f)); d.duration_minutes = +d.duration_minutes; if (!d.practiced_at) delete d.practiced_at;
    const r = await api('/api/practice', { method: 'POST', body: d });
    toast(r.milestones_achieved.length ? '🎉 Milestone: ' + r.milestones_achieved.join(', ') : 'Session logged'); practice();
  }) },
    field('Skill', h('select', { name: 'skill_id', required: true }, list.map(s => h('option', { value: s.skill_id }, s.skill_name)))),
    h('div', { class: 'row' }, field('Duration (minutes)', h('input', { name: 'duration_minutes', type: 'number', min: 1, max: 1440, required: true })), field('Date', h('input', { name: 'practiced_at', type: 'date' }))),
    field('Activity', h('input', { name: 'activity', required: true, maxlength: 200 })), field('Notes', h('textarea', { name: 'notes', maxlength: 1000 })), h('button', { class: 'btn' }, 'Log session'));
  $view.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'Log practice'), list.length ? f : h('p', {}, 'Add a skill first.')),
    h('div', { class: 'card' }, h('h3', {}, 'Recent sessions'), sessions.map(s => h('p', {}, `${s.practiced_at} · ${s.skill_name} · ${s.duration_minutes} min · ${s.activity}`))));
}

/* ---------- goals ---------- */
async function goals() {
  const [list, gs] = await Promise.all([api('/api/skills').catch(() => []), api('/api/goals').catch(() => [])]);
  const f = h('form', { onsubmit: guard(async e => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(f)); d.target_value = +d.target_value;
    if (d.milestones) d.milestones = d.milestones.split(',').map(Number).filter(Boolean); else delete d.milestones;
    if (!d.deadline) delete d.deadline;
    await api('/api/goals', { method: 'POST', body: d }); toast('Goal created'); goals();
  }) },
    field('Skill', h('select', { name: 'skill_id', required: true }, list.map(s => h('option', { value: s.skill_id }, s.skill_name)))),
    field('Title', h('input', { name: 'title', required: true, placeholder: 'Practice 30 hours' })),
    h('div', { class: 'row' }, field('Target', h('input', { name: 'target_value', type: 'number', step: 'any', min: 0.1, required: true })),
      field('Unit', h('select', { name: 'unit' }, ['hours', 'minutes', 'sessions'].map(u => h('option', {}, u)))), field('Deadline', h('input', { name: 'deadline', type: 'date' }))),
    field('Milestones (comma separated, optional)', h('input', { name: 'milestones', placeholder: '5,10,20,30' })), h('button', { class: 'btn' }, 'Create goal'));
  $view.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'New goal'), list.length ? f : h('p', {}, 'Add a skill first.')),
    ...gs.map(g => h('div', { class: 'card' }, h('div', { class: 'row' }, h('h3', {}, g.title), h('span', { class: 'chip' }, g.skill_name), h('span', { class: 'chip' }, g.status)),
      h('div', { class: g.progress_pct >= 100 ? 'bar ok' : 'bar' }, h('i', { style: `width:${g.progress_pct}%` })),
      h('p', { class: 'muted' }, `${+g.current_value.toFixed(2)} / ${g.target_value} ${g.unit} · ${g.progress_pct}%`),
      h('div', { class: 'row' }, g.milestones.map(m => h('span', { class: 'chip' }, (m.achieved ? '✅ ' : '⬜ ') + m.title))))));
}

/* ---------- community ---------- */
async function community() {
  const state = { category: 'All', q: '', sort: 'recent', following: false };
  const [mine, trending] = await Promise.all([api('/api/skills').catch(() => []), api('/api/community/trending').catch(() => [])]);
  const feedBox = h('div');
  const load = guard(async () => {
    const qs = new URLSearchParams({ category: state.category, q: state.q, sort: state.sort, following: state.following });
    const posts = await api('/api/feed?' + qs);
    feedBox.replaceChildren(...(posts.length ? posts.map(postCard) : [h('p', { class: 'muted' }, 'No posts match.')]));
  });
  const pf = h('form', { onsubmit: guard(async e => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(pf)); const body = { content: d.content };
    if (d.skill_id) body.skill_id = d.skill_id;
    const file = pf.querySelector('input[type=file]').files[0];
    if (file) { const fd = new FormData(); fd.append('file', file); fd.append('purpose', 'post'); body.file_id = (await api('/api/files/upload', { method: 'POST', form: fd })).file_id; }
    await api('/api/posts', { method: 'POST', body }); pf.reset(); toast('Posted!'); load();
  }) },
    field('Share an achievement', h('textarea', { name: 'content', required: true, maxlength: 1000, placeholder: 'Completed 30 hours of guitar practice! 🎸' })),
    h('div', { class: 'row' }, h('select', { name: 'skill_id' }, h('option', { value: '' }, '(no skill)'), mine.map(s => h('option', { value: s.skill_id }, s.skill_name))),
      h('input', { type: 'file', accept: 'image/png,image/jpeg,image/gif,image/webp' }), h('button', { class: 'btn' }, 'Post')));
  const filters = h('div', { class: 'row' },
    h('select', { onchange: e => { state.category = e.target.value; load(); } }, ['All', ...CATS].map(c => h('option', {}, c))),
    h('input', { type: 'search', placeholder: 'Search skills/posts', oninput: e => { state.q = e.target.value; clearTimeout(filters.t); filters.t = setTimeout(load, 300); } }),
    h('select', { onchange: e => { state.sort = e.target.value; load(); } }, h('option', { value: 'recent' }, 'Most recent'), h('option', { value: 'liked' }, 'Most liked')),
    h('label', {}, h('input', { type: 'checkbox', onchange: e => { state.following = e.target.checked; load(); } }), ' Following only'));
  $view.replaceChildren(h('div', { class: 'card' }, pf),
    h('div', { class: 'card' }, h('h3', {}, 'Trending skills'), h('div', { class: 'row' }, trending.length ? trending.map(t => h('span', { class: 'tag' }, `${t.skill} (${t.posts})`)) : h('span', { class: 'muted' }, 'Nothing yet'))),
    h('div', { class: 'card' }, filters), feedBox);
  load();
}
function postCard(p) {
  const cbox = h('div');
  const likeBtn = h('button', { class: 'btn alt' }, `${p.liked_by_me ? '❤️' : '🤍'} ${p.like_count}`);
  likeBtn.onclick = guard(async () => { const r = await api(`/api/posts/${p.post_id}/like`, { method: p.liked_by_me ? 'DELETE' : 'POST' }); p.liked_by_me = r.liked; p.like_count = r.like_count; likeBtn.textContent = `${r.liked ? '❤️' : '🤍'} ${r.like_count}`; });
  const loadComments = guard(async () => {
    const cs = await api(`/api/posts/${p.post_id}/comments`);
    cbox.replaceChildren(...cs.map(c => h('p', {}, h('b', {}, c.username + ': '), c.content, ' ', c.is_mine ? h('a', { href: '#', onclick: guard(async e => { e.preventDefault(); await api('/api/comments/' + c.comment_id, { method: 'DELETE' }); loadComments(); }) }, '✕') : null)));
  });
  const cf = h('form', { class: 'row', onsubmit: guard(async e => { e.preventDefault(); const i = cf.querySelector('input'); await api(`/api/posts/${p.post_id}/comments`, { method: 'POST', body: { content: i.value } }); i.value = ''; loadComments(); }) },
    h('input', { placeholder: 'Write a comment', required: true, maxlength: 500 }), h('button', { class: 'btn alt' }, 'Send'));
  loadComments();
  return h('div', { class: 'card post' },
    h('div', { class: 'row' }, p.avatar_url ? h('img', { class: 'avatar', src: p.avatar_url, alt: '' }) : h('div', { class: 'avatar' }), h('b', {}, '@' + p.username),
      p.skill_name ? h('span', { class: 'tag' }, p.skill_name) : null, h('small', { class: 'muted' }, ago(p.created_at))),
    h('p', {}, p.content), p.media_url ? h('img', { src: p.media_url, alt: 'Achievement proof' }) : null,
    h('div', { class: 'row' }, likeBtn, p.is_mine ? h('button', { class: 'btn del', onclick: guard(async () => { await api('/api/posts/' + p.post_id, { method: 'DELETE' }); community(); }) }, 'Delete') :
      h('button', { class: 'btn alt', onclick: guard(async () => { const r = prompt('Why are you reporting this post?'); if (r) toast((await api(`/api/posts/${p.post_id}/report`, { method: 'POST', body: { reason: r } })).message); }) }, 'Report')),
    cbox, cf);
}

/* ---------- profile ---------- */
async function profile() {
  const p = await guard(() => api('/api/profile'))(); if (!p) return;
  const f = h('form', { onsubmit: guard(async e => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(f)); d.is_public = f.querySelector('[name=is_public]').checked;
    const file = f.querySelector('input[type=file]').files[0];
    if (file) { const fd = new FormData(); fd.append('file', file); fd.append('purpose', 'profile'); d.profile_picture_file_id = (await api('/api/files/upload', { method: 'POST', form: fd })).file_id; }
    await api('/api/profile', { method: 'PUT', body: d }); toast('Profile saved'); profile();
  }) },
    field('Name', h('input', { name: 'name', value: p.name, required: true })), field('Bio', h('textarea', { name: 'bio', maxlength: 500 }, p.bio || '')),
    field('Interests', h('input', { name: 'interests', value: p.interests || '' })), field('Profile picture', h('input', { type: 'file', accept: 'image/*' })),
    h('label', {}, h('input', { type: 'checkbox', name: 'is_public', checked: p.is_public ? 'checked' : false }), ' Public profile'), h('button', { class: 'btn' }, 'Save'));
  $view.replaceChildren(h('div', { class: 'card' }, h('div', { class: 'row' }, p.profile_picture_url ? h('img', { class: 'avatar', src: p.profile_picture_url, alt: '' }) : null, h('h2', {}, '@' + p.username)),
    h('p', { class: 'muted' }, p.email), f));
}

function start() { nav(); localStorage.getItem('token') ? go('Dashboard') : authPage(); }
start();
