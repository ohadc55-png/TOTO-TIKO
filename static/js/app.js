/* ============================================================
   ELITE FOOTBALL TRACKER — Client-side Interactivity
   ============================================================ */

// --- Toast Notifications ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? 'check_circle' : 'error';
    toast.innerHTML = `<span class="material-symbols-outlined" style="font-size:18px">${icon}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// --- Bankroll Modal ---
function toggleBankrollModal() {
    const modal = document.getElementById('bankroll-modal');
    modal.classList.toggle('hidden');
}

async function bankrollAction(action) {
    const amount = parseFloat(document.getElementById('bankroll-amount').value);
    if (!amount || amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/bankroll/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        const data = await res.json();
        if (data.ok) {
            showToast(`${action === 'deposit' ? 'Deposited' : 'Withdrawn'} ₪${amount}`);
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Operation failed', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// --- Add Match ---
async function addMatch(event, competition) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const body = {
        competition: competition,
        home: formData.get('home'),
        away: formData.get('away'),
        odds: parseFloat(formData.get('odds')),
        stake: parseFloat(formData.get('stake')),
        result: formData.get('result') || 'Pending'
    };

    if (!body.home || !body.away) {
        showToast('Please enter both team names', 'error');
        return false;
    }

    try {
        const res = await fetch('/api/match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.ok) {
            showToast(`Added: ${body.home} vs ${body.away}`);
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to add match', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
    return false;
}

// --- Set Match Result (WIN/LOSS) ---
async function setResult(row, result) {
    try {
        const res = await fetch(`/api/match/${row}/result`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ result })
        });
        const data = await res.json();
        if (data.ok) {
            const label = result === 'Draw (X)' ? 'WIN' : 'LOSS';
            showToast(`Match marked as ${label}`);
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to update', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// --- Edit Match Modal ---
function openEditModal(row, home, away, odds, stake, status, date) {
    document.getElementById('edit-row').value = row;
    document.getElementById('edit-home').value = home;
    document.getElementById('edit-away').value = away;
    document.getElementById('edit-odds').value = odds;
    document.getElementById('edit-stake').value = stake;
    document.getElementById('edit-date').value = date;

    // Map status to result value
    let resultValue = 'Pending';
    if (status === 'Won') resultValue = 'Draw (X)';
    else if (status === 'Lost') resultValue = 'No Draw';
    document.getElementById('edit-result').value = resultValue;

    document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
}

async function saveEdit(event) {
    event.preventDefault();
    const row = parseInt(document.getElementById('edit-row').value);
    const body = {
        home: document.getElementById('edit-home').value,
        away: document.getElementById('edit-away').value,
        odds: parseFloat(document.getElementById('edit-odds').value),
        stake: parseFloat(document.getElementById('edit-stake').value),
        result: document.getElementById('edit-result').value,
        date: document.getElementById('edit-date').value
    };

    try {
        const res = await fetch(`/api/match/${row}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.ok) {
            showToast('Match updated');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to update', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
    return false;
}

async function deleteMatch() {
    const row = parseInt(document.getElementById('edit-row').value);
    if (!confirm('Are you sure you want to delete this match?')) return;

    try {
        const res = await fetch(`/api/match/${row}/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.ok) {
            showToast('Match deleted');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to delete', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// --- Create Competition ---
async function createCompetition(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const body = {
        name: formData.get('name'),
        description: formData.get('description') || '',
        default_stake: parseFloat(formData.get('default_stake')) || 30,
        color1: formData.get('color1') || '#3A63DB',
        color2: formData.get('color2') || '#C366F1',
        text_color: formData.get('text_color') || '#FFFFFF',
        logo_url: formData.get('logo_url') || ''
    };

    if (!body.name) {
        showToast('Please enter a competition name', 'error');
        return false;
    }

    try {
        const res = await fetch('/api/competition', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.ok) {
            showToast(`Created: ${body.name}`);
            setTimeout(() => { window.location.href = '/'; }, 800);
        } else {
            showToast(data.error || 'Failed to create', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
    return false;
}

// --- Update Competition Stake ---
async function updateStake(row, newStake) {
    const stake = parseFloat(newStake);
    if (!stake || stake <= 0) {
        showToast('Please enter a valid stake', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/competition/${row}/stake`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stake })
        });
        const data = await res.json();
        if (data.ok) {
            showToast('Stake updated');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to update', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// --- Close Competition ---
async function closeCompetition(row, name) {
    if (!confirm(`Are you sure you want to close "${name}"? This will move it to the archive.`)) return;

    try {
        const res = await fetch(`/api/competition/${row}/close`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.ok) {
            showToast(`"${name}" closed and archived`);
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.error || 'Failed to close', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// --- Close modals on Escape key ---
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const bankrollModal = document.getElementById('bankroll-modal');
        const editModal = document.getElementById('edit-modal');
        if (bankrollModal && !bankrollModal.classList.contains('hidden')) {
            toggleBankrollModal();
        }
        if (editModal && !editModal.classList.contains('hidden')) {
            closeEditModal();
        }
    }
});
