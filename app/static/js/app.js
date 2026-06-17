// ─── Toast ────────────────────────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const el   = document.getElementById('toast');
    const body = document.getElementById('toast-body');
    el.className = `toast align-items-center text-bg-${type} border-0`;
    body.textContent = message;
    bootstrap.Toast.getOrCreateInstance(el, { delay: 3000 }).show();
}

// ─── Navigation ───────────────────────────────────────────────────────────────

function showSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link[data-section]').forEach(l => l.classList.remove('active'));
    document.getElementById('section-' + name).classList.add('active');
    document.querySelector(`.nav-link[data-section="${name}"]`).classList.add('active');
    ({ users: loadUsers, roles: loadRoles, permissions: loadPermissions, logs: loadLogs })[name]?.();
}

function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}

// ─── Bootstrap ────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    if (!getToken()) { window.location.href = '/'; return; }
    document.getElementById('current-user').textContent = sessionStorage.getItem('username') || '';
    document.querySelectorAll('.nav-link[data-section]').forEach(link => {
        link.addEventListener('click', e => { e.preventDefault(); showSection(link.dataset.section); });
    });
    showSection('users');
});

// ─── Users ────────────────────────────────────────────────────────────────────

async function loadUsers() {
    const res = await apiGet('/users');
    if (!res?.ok) return;
    const users = await res.json();

    document.getElementById('users-tbody').innerHTML = users.length ? users.map(u => `
        <tr>
            <td class="text-muted">${u.id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.email}</td>
            <td>
                <span class="badge ${u.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${u.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${u.roles.map(r => `<span class="badge bg-primary badge-role">${r.name}</span>`).join('') || '<span class="text-muted">—</span>'}</td>
            <td>
                <button class="btn btn-sm btn-outline-${u.is_active ? 'warning' : 'success'}"
                    onclick="toggleUser(${u.id}, ${u.is_active})">
                    ${u.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button class="btn btn-sm btn-outline-secondary ms-1"
                    onclick="viewPerms(${u.id}, '${u.username}')">
                    Permissions
                </button>
            </td>
        </tr>`).join('')
    : '<tr><td colspan="6" class="text-center text-muted py-4">No users found</td></tr>';
}

async function toggleUser(userId, isActive) {
    const res = await apiPatch(`/users/${userId}`, { is_active: !isActive });
    if (res?.ok) { showToast(`User ${isActive ? 'deactivated' : 'activated'}`); loadUsers(); }
    else showToast('Failed to update user', 'danger');
}

async function viewPerms(userId, username) {
    const res = await apiGet(`/users/${userId}/permissions`);
    if (!res?.ok) return;
    const data = await res.json();

    document.getElementById('perms-modal-title').textContent = `${username}'s Permissions`;
    document.getElementById('perms-modal-body').innerHTML = data.permissions.length
        ? data.permissions.map(p => `<span class="perm-badge">${p.name}</span>`).join('')
        : '<span class="text-muted">No permissions assigned</span>';
    new bootstrap.Modal(document.getElementById('permsModal')).show();
}

async function createUser() {
    const username = document.getElementById('new-username').value.trim();
    const email    = document.getElementById('new-email').value.trim();
    const password = document.getElementById('new-password').value;

    if (!username || !email || !password) return;

    const res = await apiPost('/users', { username, email, password });
    if (res?.ok) {
        bootstrap.Modal.getInstance(document.getElementById('createUserModal')).hide();
        document.getElementById('createUserForm').reset();
        document.getElementById('create-user-error').classList.add('d-none');
        showToast('User created successfully');
        loadUsers();
    } else {
        const err = await res.json();
        const errDiv = document.getElementById('create-user-error');
        errDiv.textContent = err.detail || 'Error creating user';
        errDiv.classList.remove('d-none');
    }
}

// ─── Roles ────────────────────────────────────────────────────────────────────

async function loadRoles() {
    const res = await apiGet('/roles');
    if (!res?.ok) return;
    const roles = await res.json();

    document.getElementById('roles-tbody').innerHTML = roles.length ? roles.map(r => `
        <tr>
            <td class="text-muted">${r.id}</td>
            <td><strong>${r.name}</strong></td>
            <td>${r.description || '<span class="text-muted">—</span>'}</td>
            <td>${r.permissions.map(p => `<span class="badge bg-secondary badge-role">${p.name}</span>`).join('') || '<span class="text-muted">—</span>'}</td>
        </tr>`).join('')
    : '<tr><td colspan="4" class="text-center text-muted py-4">No roles found</td></tr>';
}

// ─── Permissions ──────────────────────────────────────────────────────────────

async function loadPermissions() {
    const res = await apiGet('/permissions');
    if (!res?.ok) return;
    const perms = await res.json();

    document.getElementById('permissions-tbody').innerHTML = perms.length ? perms.map(p => `
        <tr>
            <td class="text-muted">${p.id}</td>
            <td><code>${p.name}</code></td>
            <td><span class="badge bg-light text-dark border">${p.resource}</span></td>
        </tr>`).join('')
    : '<tr><td colspan="3" class="text-center text-muted py-4">No permissions found</td></tr>';
}

async function createPermission() {
    const name     = document.getElementById('new-perm-name').value.trim();
    const resource = document.getElementById('new-perm-resource').value.trim();

    if (!name || !resource) return;

    const res = await apiPost('/permissions', { name, resource });
    if (res?.ok) {
        bootstrap.Modal.getInstance(document.getElementById('createPermModal')).hide();
        document.getElementById('createPermForm').reset();
        document.getElementById('create-perm-error').classList.add('d-none');
        showToast('Permission created');
        loadPermissions();
    } else {
        const err = await res.json();
        const errDiv = document.getElementById('create-perm-error');
        errDiv.textContent = err.detail || 'Error';
        errDiv.classList.remove('d-none');
    }
}

// ─── Logs ─────────────────────────────────────────────────────────────────────

async function loadLogs() {
    const res = await apiGet('/logs?limit=100');
    if (!res?.ok) return;
    const logs = await res.json();

    document.getElementById('logs-tbody').innerHTML = logs.length ? logs.map(l => `
        <tr>
            <td class="text-muted">${l.id}</td>
            <td>${l.user_id ?? '<span class="text-muted">—</span>'}</td>
            <td><code>${l.action}</code></td>
            <td class="status-${l.status}">${l.status === 'success' ? '✓' : '✗'} ${l.status}</td>
            <td class="text-muted">${new Date(l.timestamp + 'Z').toLocaleString()}</td>
        </tr>`).join('')
    : '<tr><td colspan="5" class="text-center text-muted py-4">No log entries</td></tr>';
}
