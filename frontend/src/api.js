// services layer: every call to the REST API goes through here.
async function api(path, { method = 'GET', body, form } = {}) {
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) headers['Authorization'] = 'Bearer ' + token;
  let payload;
  if (form) payload = form;
  else if (body) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }
  let res;
  try { res = await fetch(path, { method, headers, body: payload }); }
  catch (e) { throw new Error('Network problem - check your connection and try again.'); }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && token) { localStorage.removeItem('token'); location.reload(); }
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map(x => x.msg).join('; ') : 'Request failed');
  }
  return data;
}
