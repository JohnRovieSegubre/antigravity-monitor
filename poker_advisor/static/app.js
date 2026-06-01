console.log("Antigravity Poker Advisor v3 — EV Tracker connecting...");

// ─── Chart.js EV Graph Setup ──────────────────────────────────────
let evChart = null;

function initChart() {
    const ctx = document.getElementById('ev-chart').getContext('2d');
    evChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Expected Value (EV)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointBackgroundColor: '#06b6d4',
                    pointBorderColor: '#0a0e1a',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Actual P/L',
                    data: [],
                    borderColor: '#eab308',
                    backgroundColor: 'rgba(234, 179, 8, 0.05)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointBackgroundColor: '#eab308',
                    pointBorderColor: '#0a0e1a',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6,
                    borderDash: [5, 3],
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400, easing: 'easeOutQuart' },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#141929',
                    titleColor: '#f0f2f8',
                    bodyColor: '#b0b8d4',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y >= 0 ? '+' : ''}${context.parsed.y.toFixed(2)} BB`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Hand #', color: '#6b7394', font: { size: 11, weight: 600 } },
                    ticks: { color: '#4a5170', font: { size: 10 } },
                    grid: { color: 'rgba(255,255,255,0.03)' },
                },
                y: {
                    title: { display: true, text: 'BB', color: '#6b7394', font: { size: 11, weight: 600 } },
                    ticks: {
                        color: '#4a5170',
                        font: { size: 10 },
                        callback: v => (v >= 0 ? '+' : '') + v.toFixed(1)
                    },
                    grid: { color: 'rgba(255,255,255,0.03)' },
                }
            }
        }
    });
}

// ─── SSE Stream ───────────────────────────────────────────────────
const eventSource = new EventSource('/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Update title
    if (data.client) {
        document.getElementById('advisor-title').innerText = "♠ " + data.client + " Advisor";
    }

    // ── Hero Cards ──
    const heroCardsDiv = document.getElementById('hero-cards');
    heroCardsDiv.innerHTML = `
        <div class="card ${data.hero_cards[0].color}">${data.hero_cards[0].rank}${data.hero_cards[0].suit}</div>
        <div class="card ${data.hero_cards[1].color}">${data.hero_cards[1].rank}${data.hero_cards[1].suit}</div>
    `;

    // ── Board Cards ──
    const boardCardsDiv = document.getElementById('board-cards');
    if (data.board_cards && data.board_cards.length > 0) {
        let html = '';
        for (let i = 0; i < 5; i++) {
            if (i < data.board_cards.length) {
                const c = data.board_cards[i];
                html += `<div class="card ${c.color}">${c.rank}${c.suit}</div>`;
            } else {
                html += `<div class="card placeholder"></div>`;
            }
        }
        boardCardsDiv.innerHTML = html;
    } else {
        boardCardsDiv.innerHTML = Array(5).fill('<div class="card placeholder"></div>').join('');
    }

    // ── Stack, Pot, To Call ──
    document.getElementById('stack-display').innerText = data.stack;
    document.getElementById('pot').innerText = data.pot;
    document.getElementById('to-call').innerText = data.to_call;

    // ── Equity ──
    const equityPercent = document.getElementById('equity-percent');
    const equityFill = document.querySelector('.equity-fill');
    const eq = data.equity || 0;

    equityPercent.innerText = `${eq}% Equity`;
    equityFill.style.width = `${eq}%`;

    if (eq > 60) equityFill.style.background = 'linear-gradient(90deg, #22c55e, #4ade80)';
    else if (eq > 40) equityFill.style.background = 'linear-gradient(90deg, #eab308, #facc15)';
    else equityFill.style.background = 'linear-gradient(90deg, #f43f5e, #fb7185)';

    // ── Hand class & stage ──
    const handClassEl = document.getElementById('hand-class');
    const stageEl = document.getElementById('stage-badge');
    if (handClassEl) handClassEl.innerText = data.hand_class || '—';
    if (stageEl) stageEl.innerText = data.stage || '';

    // ── Action Card ──
    const actionCard = document.getElementById('recommended-action');
    const actionText = actionCard.querySelector('.action-text');
    const action = (data.action || 'WAITING').replace('...', '');
    actionCard.className = 'action-card ' + action.toLowerCase();
    actionText.innerText = action;

    // ── Strategy Metrics ──
    const evEl = document.getElementById('ev-estimate');
    const evVal = data.ev_estimate || 0;
    evEl.innerText = (evVal >= 0 ? '+' : '') + evVal.toFixed(2) + ' BB';
    evEl.style.color = evVal >= 0 ? '#22c55e' : '#f43f5e';

    document.getElementById('pot-odds').innerText = (data.pot_odds || 0).toFixed(1) + '%';

    const sprVal = data.spr || 0;
    document.getElementById('spr-value').innerText = sprVal > 100 ? '∞' : sprVal.toFixed(1);

    // ── Reasoning ──
    const reasonText = document.getElementById('reasoning-text');
    if (data.reasoning) {
        reasonText.innerText = data.reasoning;
    } else {
        reasonText.innerText = 'Waiting for cards to be dealt...';
    }

    // ── Session Stats Bar ──
    const stats = data.session_stats;
    if (stats) {
        document.getElementById('stat-hands').innerText = stats.hands_played;

        const pnlEl = document.getElementById('stat-pnl');
        const pnl = stats.total_pnl;
        pnlEl.innerText = (pnl >= 0 ? '+' : '') + pnl.toFixed(1) + ' BB';
        pnlEl.className = 'stat-value pnl ' + (pnl >= 0 ? 'positive' : 'negative');

        document.getElementById('stat-winrate').innerText = stats.win_rate.toFixed(2) + ' BB/h';
        document.getElementById('stat-vpip').innerText = stats.vpip.toFixed(0) + '%';
        document.getElementById('stat-fold').innerText = stats.fold_pct.toFixed(0) + '%';

        const bestEl = document.getElementById('stat-best');
        bestEl.innerText = '+' + stats.biggest_win.toFixed(1) + ' BB';

        const worstEl = document.getElementById('stat-worst');
        worstEl.innerText = stats.biggest_loss.toFixed(1) + ' BB';

        // ── Update EV Chart ──
        if (evChart && stats.ev_history && stats.ev_history.length > 0) {
            evChart.data.labels = stats.ev_history.map(h => '#' + h.hand_id);
            evChart.data.datasets[0].data = stats.ev_history.map(h => h.cumulative_ev);

            if (stats.pnl_history && stats.pnl_history.length > 0) {
                evChart.data.datasets[1].data = stats.pnl_history.map(h => h.cumulative_pnl);
            }
            evChart.update('none'); // No animation for smooth updates
        }
    }

    // ── Hand History Feed ──
    const historyFeed = document.getElementById('history-feed');
    const lastHands = data.last_hands;
    if (lastHands && lastHands.length > 0) {
        let html = '';
        // Show newest first
        for (let i = lastHands.length - 1; i >= 0; i--) {
            const h = lastHands[i];
            const actionLower = (h.action || 'fold').toLowerCase();
            const result = h.result_bb || 0;
            const resultClass = result > 0 ? 'positive' : result < 0 ? 'negative' : 'neutral';
            const resultStr = result > 0 ? '+' + result.toFixed(1) : result.toFixed(1);
            const cards = (h.hero_cards || []).join(' ');

            html += `
                <div class="history-item ${actionLower}">
                    <span class="history-hand-id">#${h.hand_id}</span>
                    <span class="history-cards">${cards}</span>
                    <span class="history-action ${actionLower}">${h.action}</span>
                    <span class="history-result ${resultClass}">${resultStr} BB</span>
                </div>
            `;
        }
        historyFeed.innerHTML = html;
    }
};

eventSource.onerror = function() {
    console.log("Lost connection to live feed.");
    const status = document.getElementById('connection-status');
    status.innerText = "Connection Lost";
    status.classList.remove('online');
    status.style.color = "#f43f5e";
};

// ─── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initChart);
