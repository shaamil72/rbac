// Thin wrapper around fetch — injects Bearer token and handles 401

function getToken() {
    return sessionStorage.getItem('token');
}

async function apiFetch(path, options = {}) {
    const token = getToken();
    if (!token) { window.location.href = '/'; return null; }

    const headers = { 'Content-Type': 'application/json', ...options.headers };
    headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(path, { ...options, headers });

    if (res.status === 401) {
        sessionStorage.clear();
        window.location.href = '/';
        return null;
    }
    return res;
}

const apiGet    = (path)       => apiFetch(path);
const apiPost   = (path, body) => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) });
const apiPatch  = (path, body) => apiFetch(path, { method: 'PATCH',  body: JSON.stringify(body) });
const apiDelete = (path)       => apiFetch(path, { method: 'DELETE' });
