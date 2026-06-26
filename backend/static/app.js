// Dashboard State Management
const STATE = {
    isAuthenticated: false,
    token: null,
    activeTab: 'active-setups-tab',
    signals: [],
    selectedSignal: null,
    modelStatus: null
};

const API_BASE = '/api';

// DOM Elements
const elements = {
    serverStatus: document.getElementById('server-status'),
    modelStatus: document.getElementById('model-status'),
    currentTime: document.getElementById('current-time'),
    btnLoginLogout: document.getElementById('btn-login-logout'),
    
    // Stats
    statTotal: document.getElementById('stat-total'),
    statWinrate: document.getElementById('stat-winrate'),
    statTpsl: document.getElementById('stat-tpsl'),
    statAccuracy: document.getElementById('stat-accuracy'),
    
    // Tables
    tableActiveSetups: document.getElementById('table-active-setups').getElementsByTagName('tbody')[0],
    tableHistorySetups: document.getElementById('table-history-setups').getElementsByTagName('tbody')[0],
    
    // Simulator
    simulatorForm: document.getElementById('simulator-form'),
    simSymbol: document.getElementById('sim-symbol'),
    simTrigger: document.getElementById('sim-trigger'),
    simAtr: document.getElementById('sim-atr'),
    simSweep: document.getElementById('sim-sweep'),
    simMss: document.getElementById('sim-mss'),
    simSweepDepth: document.getElementById('sim-sweep-depth'),
    simVolume: document.getElementById('sim-volume'),
    simMssStr: document.getElementById('sim-mss-str'),
    simFvgSize: document.getElementById('sim-fvg-size'),
    simFvgLow: document.getElementById('sim-fvg-low'),
    simFvgHigh: document.getElementById('sim-fvg-high'),
    
    // Details Drawer
    signalDetailDrawer: document.getElementById('signal-detail-drawer'),
    btnCloseDetail: document.getElementById('btn-close-detail'),
    detailSymbol: document.getElementById('detail-symbol'),
    detailDirection: document.getElementById('detail-direction'),
    detailTime: document.getElementById('detail-time'),
    detPriceTrigger: document.getElementById('det-price-trigger'),
    detPriceSweep: document.getElementById('det-price-sweep'),
    detPriceMss: document.getElementById('det-price-mss'),
    detFeatDepth: document.getElementById('det-feat-depth'),
    detFeatVolume: document.getElementById('det-feat-volume'),
    detFeatMssStr: document.getElementById('det-feat-mss-str'),
    detFvgSize: document.getElementById('det-fvg-size'),
    detFvgLow: document.getElementById('det-fvg-low'),
    detFvgHigh: document.getElementById('det-fvg-high'),
    detMarketTrend: document.getElementById('det-market-trend'),
    detMarketSession: document.getElementById('det-market-session'),
    detMarketAtr: document.getElementById('det-market-atr'),
    
    // Model Control
    modelTrainedTime: document.getElementById('model-trained-time'),
    modelDatasetVal: document.getElementById('model-dataset-val'),
    modelAccuracyVal: document.getElementById('model-accuracy-val'),
    modelF1Val: document.getElementById('model-f1-val'),
    modelAucVal: document.getElementById('model-auc-val'),
    chkIncludeSynthetic: document.getElementById('chk-include-synthetic'),
    btnRetrain: document.getElementById('btn-retrain'),
    retrainAuthWarning: document.getElementById('retrain-auth-warning'),
    
    // Modals
    loginModal: document.getElementById('login-modal'),
    loginForm: document.getElementById('login-form'),
    btnCloseLogin: document.getElementById('btn-close-login'),
    loginErrorMsg: document.getElementById('login-error-msg'),
    loginUsername: document.getElementById('login-username'),
    loginPassword: document.getElementById('login-password')
};

// --- INITIALIZE & EVENT LISTENERS ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup Time
    updateClock();
    setInterval(updateClock, 1000);
    
    // 2. Load Auth Token
    checkSavedAuth();
    
    // 3. Tab Navigation
    setupTabs();
    
    // 4. API Poll
    pollData();
    setInterval(pollData, 5000); // Poll every 5s
    
    // 5. Simulator Preset Auto-fill on Symbol Change
    elements.simSymbol.addEventListener('change', handleSymbolPreset);
    elements.simTrigger.addEventListener('input', handleTriggerPriceAdjustments);
    
    // 6. Simulator Form submit
    elements.simulatorForm.addEventListener('submit', handleSimulateSubmit);
    
    // 7. Login/Logout actions
    elements.btnLoginLogout.addEventListener('click', handleAuthButton);
    elements.btnCloseLogin.addEventListener('click', () => toggleModal(elements.loginModal, false));
    elements.loginForm.addEventListener('submit', handleLoginSubmit);
    
    // 8. Drawer actions
    elements.btnCloseDetail.addEventListener('click', () => elements.signalDetailDrawer.style.display = 'none');
    
    // 9. Retrain ML Model
    elements.btnRetrain.addEventListener('click', handleRetrain);
});

// Clock UTC Timer
function updateClock() {
    const now = new Date();
    // Emulating the current local time / standard UTC format
    elements.currentTime.innerText = now.toLocaleTimeString('en-US', { hour12: false }) + ' LOCAL';
}

// Check saved Authentication
function checkSavedAuth() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        STATE.isAuthenticated = true;
        STATE.token = token;
        updateAuthUI(true);
    } else {
        STATE.isAuthenticated = false;
        STATE.token = null;
        updateAuthUI(false);
    }
}

function updateAuthUI(isAuthenticated) {
    if (isAuthenticated) {
        elements.btnLoginLogout.innerText = 'Logout Admin';
        elements.btnRetrain.disabled = false;
        elements.retrainAuthWarning.style.display = 'none';
    } else {
        elements.btnLoginLogout.innerText = 'Admin Login';
        elements.btnRetrain.disabled = true;
        elements.retrainAuthWarning.style.display = 'block';
    }
}

// Modal open/close helper
function toggleModal(modalEl, show) {
    modalEl.style.display = show ? 'flex' : 'none';
}

function handleAuthButton() {
    if (STATE.isAuthenticated) {
        // Logout
        localStorage.removeItem('jwt_token');
        STATE.isAuthenticated = false;
        STATE.token = null;
        updateAuthUI(false);
        pollData(); // Refresh to ensure UI locks elements correctly
    } else {
        // Show Login Modal
        elements.loginErrorMsg.style.display = 'none';
        toggleModal(elements.loginModal, true);
    }
}

// Login Form Submit
async function handleLoginSubmit(e) {
    e.preventDefault();
    elements.loginErrorMsg.style.display = 'none';
    
    const username = elements.loginUsername.value;
    const password = elements.loginPassword.value;
    
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        
        const data = await response.json();
        localStorage.setItem('jwt_token', data.access_token);
        STATE.isAuthenticated = true;
        STATE.token = data.access_token;
        updateAuthUI(true);
        toggleModal(elements.loginModal, false);
    } catch (err) {
        elements.loginErrorMsg.style.display = 'block';
    }
}

// Tab navigation helper
function setupTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const targetId = tab.dataset.tab;
            STATE.activeTab = targetId;
            
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// Symbolpreset auto-fill (makes sandbox testing super easy)
function handleSymbolPreset() {
    const symbol = elements.simSymbol.value;
    let trigger = 65400;
    let atr = 120;
    
    if (symbol === 'BTCUSD') {
        trigger = 65400;
        atr = 120;
    } else if (symbol === 'ETHUSD') {
        trigger = 3450;
        atr = 15;
    } else if (symbol === 'XAUUSD') {
        trigger = 2330.5;
        atr = 12.5;
    } else if (symbol === 'EURUSD') {
        trigger = 1.08500;
        atr = 0.00450;
    } else if (symbol === 'GBPUSD') {
        trigger = 1.27200;
        atr = 0.00550;
    }
    
    elements.simTrigger.value = trigger;
    elements.simAtr.value = atr;
    handleTriggerPriceAdjustments();
}

function handleTriggerPriceAdjustments() {
    const triggerPrice = parseFloat(elements.simTrigger.value) || 0;
    const atr = parseFloat(elements.simAtr.value) || 0;
    const direction = elements.simDirection.value;
    
    // Auto-calculate logical prices based on ATR and direction
    let sweepPrice, mssPrice, fvgLow, fvgHigh, fvgSize;
    
    fvgSize = atr * 0.35;
    
    if (direction === 'Bullish') {
        // Bullish sweep: sweep low is below trigger
        sweepPrice = triggerPrice - (atr * 0.8);
        mssPrice = triggerPrice + (atr * 0.6);
        fvgLow = triggerPrice - (fvgSize * 0.5);
        fvgHigh = triggerPrice + (fvgSize * 0.5);
    } else {
        // Bearish sweep: sweep high is above trigger
        sweepPrice = triggerPrice + (atr * 0.8);
        mssPrice = triggerPrice - (atr * 0.6);
        fvgLow = triggerPrice - (fvgSize * 0.5);
        fvgHigh = triggerPrice + (fvgSize * 0.5);
    }
    
    const precision = elements.simSymbol.value.includes('USD') && !elements.simSymbol.value.includes('BTC') && !elements.simSymbol.value.includes('ETH') ? 5 : 2;
    
    elements.simSweep.value = sweepPrice.toFixed(precision);
    elements.simMss.value = mssPrice.toFixed(precision);
    elements.simFvgSize.value = fvgSize.toFixed(precision);
    elements.simFvgLow.value = fvgLow.toFixed(precision);
    elements.simFvgHigh.value = fvgHigh.toFixed(precision);
}

// Form Alert simulation submit
async function handleSimulateSubmit(e) {
    e.preventDefault();
    
    const payload = {
        symbol: elements.simSymbol.value,
        timeframe: elements.simTimeframe.value,
        direction: elements.simDirection.value,
        sweep_price: parseFloat(elements.simSweep.value),
        mss_price: parseFloat(elements.simMss.value),
        trigger_price: parseFloat(elements.simTrigger.value),
        sweep_depth: parseFloat(elements.simSweepDepth.value),
        atr: parseFloat(elements.simAtr.value),
        volume_spike: parseFloat(elements.simVolume.value),
        mss_strength: parseFloat(elements.simMssStr.value),
        trend: document.getElementById('sim-trend').value,
        session: elements.simSession.value,
        fvg_size: parseFloat(elements.simFvgSize.value) || null,
        fvg_low: parseFloat(elements.simFvgLow.value) || null,
        fvg_high: parseFloat(elements.simFvgHigh.value) || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/signals`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit signal');
        }
        
        // Reset/Update
        await pollData();
        
        // Flash animation
        const formBtn = document.getElementById('btn-submit-simulate');
        formBtn.classList.add('btn-primary');
        formBtn.style.background = 'linear-gradient(135deg, var(--accent-green) 0%, #047857 100%)';
        formBtn.style.boxShadow = '0 0 15px rgba(16,185,129,0.5)';
        setTimeout(() => {
            formBtn.style.background = '';
            formBtn.style.boxShadow = '';
        }, 1500);
        
    } catch (err) {
        console.error('Error submitting simulated webhook alert:', err);
    }
}

// --- DATA FETCHING & UI RENDERING ---

async function pollData() {
    try {
        // 1. Server status
        const isHealthy = await checkHealth();
        if (!isHealthy) return;
        
        // 2. Fetch Model status
        await fetchModelStatus();
        
        // 3. Fetch Signals history
        await fetchSignals();
        
    } catch (err) {
        console.error('Data polling failed:', err);
    }
}

async function checkHealth() {
    try {
        // Using get signals as a lightweight check
        const response = await fetch(`${API_BASE}/signals?limit=1`);
        if (response.ok) {
            elements.serverStatus.querySelector('.status-dot').className = 'status-dot dot-green';
            elements.serverStatus.querySelector('.status-label').innerText = 'API: Connected';
            return true;
        }
    } catch (e) {
        elements.serverStatus.querySelector('.status-dot').className = 'status-dot dot-red';
        elements.serverStatus.querySelector('.status-label').innerText = 'API: Offline';
        return false;
    }
    return false;
}

async function fetchModelStatus() {
    try {
        const response = await fetch(`${API_BASE}/model/status`);
        if (response.ok) {
            const data = await response.json();
            STATE.modelStatus = data;
            
            // Update UI indicators
            if (data.model_available) {
                elements.modelStatus.querySelector('.status-dot').className = 'status-dot dot-green';
                elements.modelStatus.querySelector('.status-label').innerText = 'Model: Active';
                elements.statAccuracy.innerText = (data.accuracy * 100).toFixed(1) + '%';
                elements.statAccuracy.className = 'stat-value text-blue';
            } else {
                elements.modelStatus.querySelector('.status-dot').className = 'status-dot dot-yellow';
                elements.modelStatus.querySelector('.status-label').innerText = 'Model: Local Only';
                elements.statAccuracy.innerText = 'Rule-based';
                elements.statAccuracy.className = 'stat-value text-yellow';
            }
            
            // Model tab details
            elements.modelTrainedTime.innerText = data.trained_at ? new Date(data.trained_at).toLocaleString() : 'Never';
            elements.modelDatasetVal.innerText = `${data.dataset_size} setups`;
            elements.modelAccuracyVal.innerText = `${(data.accuracy * 100).toFixed(2)}%`;
            elements.modelF1Val.innerText = data.f1_score.toFixed(4);
            elements.modelAucVal.innerText = data.roc_auc.toFixed(4);
        }
    } catch (err) {
        console.error('Failed to load model status:', err);
    }
}

async function fetchSignals() {
    try {
        const response = await fetch(`${API_BASE}/signals?limit=100`);
        if (response.ok) {
            const data = await response.json();
            STATE.signals = data;
            
            // Calculate stats
            renderStats(data);
            
            // Render tables
            renderTables(data);
            
            // If detail drawer is open, refresh detail
            if (STATE.selectedSignal) {
                const refreshed = data.find(s => s.id === STATE.selectedSignal.id);
                if (refreshed) {
                    showSignalDetails(refreshed);
                }
            }
        }
    } catch (err) {
        console.error('Failed to load signals:', err);
    }
}

function renderStats(signals) {
    const total = signals.length;
    elements.statTotal.innerText = total;
    
    const tpCount = signals.filter(s => s.status === 'TP Hit').length;
    const slCount = signals.filter(s => s.status === 'SL Hit').length;
    
    elements.statTpsl.innerHTML = `<span class="text-green">${tpCount}</span> <span class="text-divider">/</span> <span class="text-red">${slCount}</span>`;
    
    const completedCount = tpCount + slCount;
    const winrate = completedCount > 0 ? (tpCount / completedCount) * 100 : 0.0;
    
    elements.statWinrate.innerText = winrate.toFixed(1) + '%';
}

function renderTables(signals) {
    const activeBody = elements.tableActiveSetups;
    const historyBody = elements.tableHistorySetups;
    
    // Separate into active (Pending) and history (TP Hit, SL Hit)
    const activeList = signals.filter(s => s.status === 'Pending');
    const historyList = signals.filter(s => s.status !== 'Pending');
    
    // Render Active
    activeBody.innerHTML = '';
    if (activeList.length === 0) {
        activeBody.innerHTML = `<tr class="empty-row"><td colspan="9">No active setups found. Use the Webhook Simulator to add some!</td></tr>`;
    } else {
        activeList.forEach(sig => {
            const row = document.createElement('tr');
            row.addEventListener('click', (e) => {
                if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                    showSignalDetails(sig);
                }
            });
            
            const probClass = sig.probability_score >= 70 ? 'prob-high' : (sig.probability_score >= 50 ? 'prob-medium' : 'prob-low');
            const directionClass = sig.direction === 'Bullish' ? 'text-green' : 'text-red';
            
            // Format floats
            const precision = sig.symbol.includes('USD') && !sig.symbol.includes('BTC') && !sig.symbol.includes('ETH') ? 5 : 2;
            
            row.innerHTML = `
                <td class="font-mono text-highlight">${sig.symbol}</td>
                <td class="font-mono">${sig.timeframe}</td>
                <td><span class="${directionClass} font-mono font-semibold">${sig.direction}</span></td>
                <td class="font-mono">${sig.setup_score}/10</td>
                <td><span class="prob-pill ${probClass}">${sig.probability_score}%</span></td>
                <td>${sig.session}</td>
                <td class="font-mono">${sig.trigger_price.toFixed(precision)}</td>
                <td><span class="badge-status status-pending">${sig.status}</span></td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-secondary btn-action-sm text-green" onclick="updateOutcome(${sig.id}, 'TP Hit', event)" ${!STATE.isAuthenticated ? 'disabled title="Requires login"' : ''}>TP</button>
                        <button class="btn btn-secondary btn-action-sm text-red" onclick="updateOutcome(${sig.id}, 'SL Hit', event)" ${!STATE.isAuthenticated ? 'disabled title="Requires login"' : ''}>SL</button>
                    </div>
                </td>
            `;
            activeBody.appendChild(row);
        });
    }
    
    // Render History
    historyBody.innerHTML = '';
    if (historyList.length === 0) {
        historyBody.innerHTML = `<tr class="empty-row"><td colspan="9">No historical setups recorded yet.</td></tr>`;
    } else {
        historyList.forEach(sig => {
            const row = document.createElement('tr');
            row.addEventListener('click', () => showSignalDetails(sig));
            
            const probClass = sig.probability_score >= 70 ? 'prob-high' : (sig.probability_score >= 50 ? 'prob-medium' : 'prob-low');
            const directionClass = sig.direction === 'Bullish' ? 'text-green' : 'text-red';
            const statusClass = sig.status === 'TP Hit' ? 'status-tphit' : 'status-slhit';
            
            const timeStr = new Date(sig.timestamp).toLocaleTimeString() + ' ' + new Date(sig.timestamp).toLocaleDateString();
            
            row.innerHTML = `
                <td class="text-muted font-mono">${timeStr}</td>
                <td class="font-mono text-highlight">${sig.symbol}</td>
                <td class="font-mono">${sig.timeframe}</td>
                <td><span class="${directionClass} font-mono font-semibold">${sig.direction}</span></td>
                <td class="font-mono">${sig.setup_score}/10</td>
                <td><span class="prob-pill ${probClass}">${sig.probability_score}%</span></td>
                <td>${sig.session}</td>
                <td><span class="badge-status ${statusClass}">${sig.status}</span></td>
                <td class="font-mono">${sig.outcome === 1 ? '<span class="text-green">✓ Success</span>' : '<span class="text-red">✗ Fail</span>'}</td>
            `;
            historyBody.appendChild(row);
        });
    }
}

// Display Detail Drawer
function showSignalDetails(sig) {
    STATE.selectedSignal = sig;
    
    const precision = sig.symbol.includes('USD') && !sig.symbol.includes('BTC') && !sig.symbol.includes('ETH') ? 5 : 2;
    
    elements.detailSymbol.innerText = sig.symbol;
    elements.detailDirection.innerText = sig.direction;
    elements.detailDirection.className = `badge ${sig.direction === 'Bullish' ? 'badge-green' : 'badge-red'}`;
    
    const localTime = new Date(sig.timestamp).toLocaleString();
    elements.detailTime.innerText = `${sig.timeframe} TF | Labeled: ${localTime}`;
    
    elements.detPriceTrigger.innerText = sig.trigger_price.toFixed(precision);
    elements.detPriceSweep.innerText = sig.sweep_price.toFixed(precision);
    elements.detPriceMss.innerText = sig.mss_price.toFixed(precision);
    
    elements.detFeatDepth.innerText = `${sig.sweep_depth.toFixed(precision)} (${(sig.sweep_depth / sig.atr * 100).toFixed(1)}% ATR)`;
    elements.detFeatVolume.innerText = `${sig.volume_spike.toFixed(1)}x avg`;
    elements.detFeatMssStr.innerText = `${sig.mss_strength.toFixed(1)}x body`;
    
    elements.detFvgSize.innerText = sig.fvg_size ? sig.fvg_size.toFixed(precision) : 'None';
    elements.detFvgLow.innerText = sig.fvg_low ? sig.fvg_low.toFixed(precision) : '-';
    elements.detFvgHigh.innerText = sig.fvg_high ? sig.fvg_high.toFixed(precision) : '-';
    
    elements.detMarketTrend.innerText = sig.trend;
    elements.detMarketTrend.className = `font-mono ${sig.trend === 'Bullish' ? 'text-green' : (sig.trend === 'Bearish' ? 'text-red' : 'text-muted')}`;
    elements.detMarketSession.innerText = sig.session;
    elements.detMarketAtr.innerText = sig.atr.toFixed(precision);
    
    elements.signalDetailDrawer.style.display = 'block';
    
    // Auto-scroll detail into view if screen is small
    elements.signalDetailDrawer.scrollIntoView({ behavior: 'smooth' });
}

// Action Trigger: Tag Outcome
async function updateOutcome(id, outcomeStatus, event) {
    if (event) {
        event.stopPropagation(); // Don't trigger row click
    }
    
    if (!STATE.isAuthenticated) {
        alert('Requires admin credentials to resolve outcomes.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/signals/${id}/outcome`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${STATE.token}`
            },
            body: JSON.stringify({ status: outcomeStatus })
        });
        
        if (!response.ok) {
            throw new Error('Update failed');
        }
        
        await pollData();
    } catch (err) {
        console.error('Error updating outcome:', err);
    }
}

// Action Trigger: Retrain model
async function handleRetrain() {
    if (!STATE.isAuthenticated) {
        alert('Requires admin credentials to retrain the model.');
        return;
    }
    
    const includeSynthetic = elements.chkIncludeSynthetic.checked;
    elements.btnRetrain.disabled = true;
    elements.btnRetrain.querySelector('span').innerText = 'Retraining Pipeline...';
    
    try {
        const response = await fetch(`${API_BASE}/train`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${STATE.token}`
            },
            body: JSON.stringify({ include_synthetic: includeSynthetic })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Retraining failed');
        }
        
        const data = await response.json();
        alert(`Retraining complete!\nNew Accuracy: ${(data.accuracy * 100).toFixed(2)}%\nTotal Train Samples: ${data.dataset_size}`);
        await pollData();
        
    } catch (err) {
        alert(`Training Error: ${err.message}`);
    } finally {
        elements.btnRetrain.disabled = false;
        elements.btnRetrain.querySelector('span').innerText = 'Retrain ML Engine';
    }
}

// Expose updateOutcome globally so onclick attributes work
window.updateOutcome = updateOutcome;
