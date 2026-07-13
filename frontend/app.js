const API_BASE = 'http://127.0.0.1:8004/api/v1';

// Cache DOM elements
const el = {
    stress: document.getElementById('stress-slider'),
    anxiety: document.getElementById('anxiety-slider'),
    fatigue: document.getElementById('fatigue-slider'),
    sleep: document.getElementById('sleep-slider'),
    academic: document.getElementById('academic-slider'),
    social: document.getElementById('social-slider'),
    mood: document.getElementById('mood-slider'),
    resilience: document.getElementById('resilience-slider'),
    focus: document.getElementById('focus-slider'),
    
    time: document.getElementById('time-slider'),
    screentime: document.getElementById('screentime-slider'),
    steps: document.getElementById('steps-slider'),
    availability: document.getElementById('availability-slider'),
    weekend: document.getElementById('weekend-select'),
    completion: document.getElementById('completion-slider'),
    
    stressVal: document.getElementById('stress-val'),
    anxietyVal: document.getElementById('anxiety-val'),
    fatigueVal: document.getElementById('fatigue-val'),
    sleepVal: document.getElementById('sleep-val'),
    academicVal: document.getElementById('academic-val'),
    socialVal: document.getElementById('social-val'),
    moodVal: document.getElementById('mood-val'),
    resilienceVal: document.getElementById('resilience-val'),
    focusVal: document.getElementById('focus-val'),
    
    timeVal: document.getElementById('time-val'),
    screentimeVal: document.getElementById('screentime-val'),
    stepsVal: document.getElementById('steps-val'),
    availabilityVal: document.getElementById('availability-val'),
    
    getRecsBtn: document.getElementById('get-recs-btn'),
    recsContainer: document.getElementById('recs-container'),
    
    simProfile: document.getElementById('sim-profile'),
    simIterations: document.getElementById('sim-iterations'),
    runSimBtn: document.getElementById('run-sim-btn'),
    simResultsSection: document.getElementById('sim-results-section'),
    simRounds: document.getElementById('sim-rounds'),
    simCtr: document.getElementById('sim-ctr'),
    simRegret: document.getElementById('sim-regret'),
    simLogsBox: document.getElementById('sim-logs-box'),
    
    paramsContainer: document.getElementById('params-grid-container'),
    historyContainer: document.getElementById('history-container'),
    serverStatus: document.getElementById('server-status'),
    
    fearedSubject: document.getElementById('feared-subject-input'),
    examSubject: document.getElementById('exam-subject-input'),
    examDate: document.getElementById('exam-date-input'),
    programmingIssue: document.getElementById('programming-issue-input'),
    screentimeHours: document.getElementById('screentime-hours-input'),
    bedtimeTarget: document.getElementById('bedtime-target-input')
};

// State mapping
const activeMissions = new Set();
let currentStudentId = "std-9874";

// Setup event listeners for range inputs
function setupSliderListeners() {
    const sliders = [
        { s: el.stress, v: el.stressVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.anxiety, v: el.anxietyVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.fatigue, v: el.fatigueVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.sleep, v: el.sleepVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.academic, v: el.academicVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.social, v: el.socialVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.mood, v: el.moodVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.resilience, v: el.resilienceVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.focus, v: el.focusVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.screentime, v: el.screentimeVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.steps, v: el.stepsVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.availability, v: el.availabilityVal, f: val => parseFloat(val).toFixed(2) },
        { s: el.time, v: el.timeVal, f: val => {
            const h = parseInt(val);
            const ampm = h >= 12 ? 'PM' : 'AM';
            const displayH = h % 12 === 0 ? 12 : h % 12;
            return `${displayH}:00 ${ampm}`;
        }}
    ];

    sliders.forEach(item => {
        item.s.addEventListener('input', (e) => {
            item.v.textContent = item.f(e.target.value);
        });
    });
}

// Check api health and set status
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/interventions/taxonomy`);
        if (res.ok) {
            el.serverStatus.textContent = "API Online (8004)";
            el.serverStatus.style.background = "rgba(16, 185, 129, 0.15)";
            el.serverStatus.style.borderColor = "rgba(16, 185, 129, 0.3)";
            el.serverStatus.style.color = "var(--success)";
            return true;
        }
    } catch (e) {
        console.error(e);
    }
    el.serverStatus.textContent = "API Offline (8004)";
    el.serverStatus.style.background = "rgba(239, 68, 68, 0.15)";
    el.serverStatus.style.borderColor = "rgba(239, 68, 68, 0.3)";
    el.serverStatus.style.color = "var(--danger)";
    return false;
}

// Fetch and render recommendations
async function getRecommendations() {
    try {
        const payload = {
            student_id: currentStudentId,
            twin_state: {
                stress: parseFloat(el.stress.value),
                anxiety: parseFloat(el.anxiety.value),
                fatigue: parseFloat(el.fatigue.value),
                sleep: parseFloat(el.sleep.value),
                academic: parseFloat(el.academic.value),
                social: parseFloat(el.social.value),
                mood: parseFloat(el.mood.value),
                resilience: parseFloat(el.resilience.value),
                focus: parseFloat(el.focus.value)
            },
            user_context: {
                time_of_day: parseFloat(el.time.value) / 24.0,
                is_weekend: parseFloat(el.weekend.value),
                screen_time_index: parseFloat(el.screentime.value),
                calendar_availability: parseFloat(el.availability.value),
                steps_ratio: parseFloat(el.steps.value),
                past_completion_rate: parseFloat(el.completion.value)
            },
            active_mission_ids: Array.from(activeMissions),
            feared_subjects: el.fearedSubject.value ? [el.fearedSubject.value] : [],
            upcoming_exams: el.examSubject.value ? [{ subject: el.examSubject.value, date: el.examDate.value || null }] : [],
            programming_issues: el.programmingIssue.value ? [el.programmingIssue.value] : [],
            daily_screen_time_hours: el.screentimeHours.value ? parseFloat(el.screentimeHours.value) : null,
            sleep_bedtime_target: el.bedtimeTarget.value || null
        };

        el.recsContainer.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Calculating scores...</p>';

        const response = await fetch(`${API_BASE}/interventions/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("API recommendation failed.");
        const data = await response.json();
        
        renderRecommendations(data.recommendations.slice(0, 5), payload, data.advice);
    } catch (err) {
        console.warn("API recommendation failed. Falling back to local offline mock mode.", err);
        
        // Alert user of mock mode status
        el.serverStatus.textContent = "API Offline (Mock Mode)";
        el.serverStatus.style.background = "rgba(245, 158, 11, 0.15)";
        el.serverStatus.style.borderColor = "rgba(245, 158, 11, 0.3)";
        el.serverStatus.style.color = "var(--warning)";
        
        const mockMissions = [
            {
                mission_id: "academic-pomodoro-focus",
                title: "25-Min Focus: Study session",
                description: "Work on academic objectives using the Pomodoro technique.",
                category: "academic",
                difficulty: 0.5,
                points_value: 50,
                score: 0.985,
                rationale: "Recommended to help prepare for your upcoming exams and reinforce focus."
            },
            {
                mission_id: "sleep-digital-detox",
                title: "Digital Curfew Mode",
                description: "Avoid screens 45 minutes before sleep to protect melatonin cycles.",
                category: "sleep",
                difficulty: 0.4,
                points_value: 60,
                score: 0.942,
                rationale: "Recommended to reduce screen time and improve sleep quality before exams."
            },
            {
                mission_id: "social-chat-friend",
                title: "Peers Study Break",
                description: "Call or check in with a classmate or close friend for 10-15 minutes.",
                category: "social",
                difficulty: 0.3,
                points_value: 40,
                score: 0.895,
                rationale: "Recommended to restore social connectivity and take a productive rest break."
            },
            {
                mission_id: "sleep-bedtime-anchor",
                title: "Anchor Bedtime Sleep",
                description: "Go to bed by your bedtime target to align sleep hygiene.",
                category: "sleep",
                difficulty: 0.3,
                points_value: 45,
                score: 0.880,
                rationale: "Recommended to ensure cognitive recovery and combat academic stress."
            },
            {
                mission_id: "academic-backlog-audit",
                title: "Subject Backlog Review",
                description: "Review concepts and note down sections you struggled with over the last 7 days.",
                category: "academic",
                difficulty: 0.6,
                points_value: 55,
                score: 0.865,
                rationale: "Recommended to identify subject fears and schedule revision hours."
            }
        ];

        // Dynamically customize the mock data based on form inputs!
        const feared = el.fearedSubject.value || "Operating Systems";
        const exam = el.examSubject.value || "Data Structures";
        const examDate = el.examDate.value || "soon";
        const prog = el.programmingIssue.value || "pointers memory leaks";
        const screen = el.screentimeHours.value ? parseFloat(el.screentimeHours.value) : 6.5;
        const bedtime = el.bedtimeTarget.value || "23:00";
        
        // Map personalized values on top of mockMissions
        const personalizedMock = mockMissions.map(m => {
            let customM = { ...m };
            if (customM.mission_id === "academic-pomodoro-focus") {
                customM.title = `25-Min Focus: ${feared}`;
                customM.description = `Work on your struggled subject '${feared}' and debug '${prog}' using the Pomodoro technique.`;
                customM.rationale = `Recommended to prevent academic burnout on feared subject '${feared}' and debug programming blocks.`;
            } else if (customM.mission_id === "sleep-digital-detox") {
                customM.title = `Digital Curfew (${screen}h Screen)`;
                customM.description = `You logged ${screen}h on screens today. Set a strict 45-minute digital curfew to boost rest.`;
                customM.rationale = `Recommended to limit screen time and ensure your brain is rested for upcoming exam: '${exam}'.`;
            } else if (customM.mission_id === "social-chat-friend") {
                customM.title = `Call a Friend (Social Catchup)`;
                customM.description = `Since your social index is low, call a close peer or study partner for 15 minutes to talk about non-academic interests.`;
            } else if (customM.mission_id === "sleep-bedtime-anchor") {
                customM.title = `Anchor Bedtime: ${bedtime}`;
                customM.description = `Head to sleep tonight by your target bedtime of ${bedtime} to recover sleep debt.`;
            } else if (customM.mission_id === "academic-backlog-audit") {
                customM.title = `Audit ${exam} Prep`;
                customM.description = `Review your preparation backlog for your upcoming '${exam}' exam on ${examDate}.`;
            }
            return customM;
        });
        
        const mockAdvice = `Coach Advice (Offline Mock Mode): You need to study '${feared}' for at least 2.5 hours today. Sleep early by your target bedtime ${bedtime} to optimize sleep debt recovery, and limit your ${screen}h daily screen time.`;
        
        renderRecommendations(personalizedMock, payload, mockAdvice);
    }
}

// Render recommendations to DOM
function renderRecommendations(recs, requestPayload, advice = null) {
    if (!recs || recs.length === 0) {
        el.recsContainer.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No recommendations generated.</p>';
        return;
    }

    let html = '';
    if (advice) {
        html += `
            <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%); border: 1px solid var(--card-border-active); padding: 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.8rem; box-shadow: 0 4px 15px rgba(6, 182, 212, 0.15);">
                <div style="font-size: 1.8rem; line-height: 1;">🌟</div>
                <div>
                    <h4 style="font-weight:600; font-size:1rem; margin-bottom:0.2rem; color:var(--secondary);">Coach Advice</h4>
                    <p style="font-size:0.92rem; color:var(--text-primary); line-height:1.4;">${advice}</p>
                </div>
            </div>
        `;
    }

    html += recs.map(rec => `
        <div class="rec-card" id="card-${rec.mission_id}">
            <div class="rec-header">
                <div class="rec-title-group">
                    <h3>${rec.title}</h3>
                    <span class="rec-category category-${rec.category}">${rec.category}</span>
                </div>
                <div class="rec-score-badge" title="Upper Confidence Bound (UCB) Score: combines the predicted reward (exploitation) and uncertainty (exploration). Higher scores indicate more relevant/optimal recommendations.">
                    <span class="score-label">UCB Score ℹ️</span>
                    <span class="score-val">${rec.score.toFixed(3)}</span>
                </div>
            </div>
            <p class="rec-desc">${rec.description}</p>
            <div class="rec-meta">
                <span>Difficulty: <strong>${rec.difficulty.toFixed(1)}</strong></span>
                <span>Value: <strong>${rec.points_value} Points</strong></span>
            </div>
            <div class="rec-rationale">
                💡 ${rec.rationale}
            </div>
            <div class="rec-actions">
                <button class="action-btn action-complete" onclick="submitFeedback('${rec.mission_id}', 1.0, ${encodePayload(requestPayload)})">Complete</button>
                <button class="action-btn action-skip" onclick="submitFeedback('${rec.mission_id}', 0.0, ${encodePayload(requestPayload)})">Skip</button>
            </div>
        </div>
    `).join('');
    el.recsContainer.innerHTML = html;
}

// Base64 helper for JSON parameters passed in onclick handlers
function encodePayload(obj) {
    return `'${btoa(JSON.stringify(obj))}'`;
}

// Submit reward feedback
window.submitFeedback = async function(missionId, reward, encodedRequestPayload) {
    try {
        const requestPayload = JSON.parse(atob(encodedRequestPayload));
        const payload = {
            student_id: currentStudentId,
            mission_id: missionId,
            reward: reward,
            twin_state: requestPayload.twin_state,
            user_context: requestPayload.user_context
        };

        const card = document.getElementById(`card-${missionId}`);
        if (card) {
            card.style.opacity = '0.5';
            card.style.pointerEvents = 'none';
        }

        const res = await fetch(`${API_BASE}/interventions/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Feedback submission failed.");

        // Add to active set to prevent immediate repetition if skipped/started
        activeMissions.add(missionId);
        setTimeout(() => activeMissions.delete(missionId), 60000); // clear after 1 minute for testing

        // Reload data
        await getRecommendations();
        await fetchParameters();
        await fetchHistory();
    } catch (err) {
        alert("Failed to submit feedback: " + err.message);
    }
}

// Fetch bandit parameters summary
async function fetchParameters() {
    try {
        const res = await fetch(`${API_BASE}/interventions/parameters`);
        if (!res.ok) throw new Error();
        const data = await res.ok ? await res.json() : [];
        
        if (data.length === 0) {
            el.paramsContainer.innerHTML = '<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">No model parameters initialized yet. Trigger recommendations first!</p>';
            return;
        }

        el.paramsContainer.innerHTML = data.map(p => {
            const shortId = p.mission_id.length > 25 ? p.mission_id.substring(0, 22) + '...' : p.mission_id;
            return `
                <div class="param-card">
                    <h4 title="${p.mission_id}">${p.mission_id}</h4>
                    <div class="param-row" title="Accumulated user completed (positive) and skipped (negative) feedback.">
                        <span>Feedback Accumulation:</span>
                        <span class="val">${p.b_norm.toFixed(3)}</span>
                    </div>
                    <div class="param-row" title="How strongly this mission matches the active digital twin metrics of the student.">
                        <span>Preference Match:</span>
                        <span class="val">${p.theta_norm.toFixed(3)}</span>
                    </div>
                    <div class="param-row" title="Level of confidence in recommendation (increases as more data is collected).">
                        <span>Confidence Level:</span>
                        <span class="val">${p.diagonal_sum_A.toFixed(1)}</span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.warn("Failed to fetch parameters, loading offline mock parameters.");
        const mockParams = [
            { mission_id: "academic-pomodoro-focus", b_norm: 1.842, theta_norm: 0.953, diagonal_sum_A: 18.0 },
            { mission_id: "sleep-digital-detox", b_norm: 1.564, theta_norm: 0.742, diagonal_sum_A: 17.5 },
            { mission_id: "social-chat-friend", b_norm: 0.891, theta_norm: 0.621, diagonal_sum_A: 16.0 },
            { mission_id: "sleep-bedtime-anchor", b_norm: 1.125, theta_norm: 0.584, diagonal_sum_A: 16.5 },
            { mission_id: "academic-backlog-audit", b_norm: 1.458, theta_norm: 0.880, diagonal_sum_A: 17.0 }
        ];
        el.paramsContainer.innerHTML = mockParams.map(p => `
            <div class="param-card">
                <h4 title="${p.mission_id}">${p.mission_id}</h4>
                <div class="param-row" title="Accumulated user completed (positive) and skipped (negative) feedback.">
                    <span>Feedback Accumulation:</span>
                    <span class="val">${p.b_norm.toFixed(3)}</span>
                </div>
                <div class="param-row" title="How strongly this mission matches the active digital twin metrics of the student.">
                    <span>Preference Match:</span>
                    <span class="val">${p.theta_norm.toFixed(3)}</span>
                </div>
                <div class="param-row" title="Level of confidence in recommendation (increases as more data is collected).">
                    <span>Confidence Level:</span>
                    <span class="val">${p.diagonal_sum_A.toFixed(1)}</span>
                </div>
            </div>
        `).join('');
    }
}

// Fetch recommendation history logs
async function fetchHistory() {
    try {
        const res = await fetch(`${API_BASE}/interventions/history`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        
        if (data.length === 0) {
            el.historyContainer.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No history logs found.</p>';
            return;
        }

        el.historyContainer.innerHTML = data.map(h => {
            const dateStr = new Date(h.created_at).toLocaleTimeString();
            const recTitles = h.recommendations.map(r => r.title).join(', ');
            
            let statusClass = "status-pending";
            let statusText = "Pending";
            if (h.reward === 1.0) {
                statusClass = "status-completed";
                statusText = "Completed";
            } else if (h.reward === 0.0) {
                statusClass = "status-skipped";
                statusText = "Skipped";
            }

            return `
                <div class="history-item">
                    <div class="history-info">
                        <strong>${dateStr}</strong>: ${recTitles.substring(0, 50)}...
                        <br><span style="font-size:0.8rem; color:var(--text-secondary);">Chosen: ${h.chosen_mission_id || 'None'}</span>
                    </div>
                    <span class="history-status ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.warn("Failed to fetch history, loading offline mock history.");
        const mockHistory = [
            { id: 1, student_id: "std-9874", recommendations: [{ title: "25-Min Focus: Study session" }, { title: "Digital Curfew Mode" }], chosen_mission_id: "academic-pomodoro-focus", reward: 1.0, created_at: new Date().toISOString() },
            { id: 2, student_id: "std-9874", recommendations: [{ title: "Call a Friend (Social Catchup)" }], chosen_mission_id: "social-chat-friend", reward: 0.0, created_at: new Date(Date.now() - 3600000).toISOString() }
        ];
        
        el.historyContainer.innerHTML = mockHistory.map(h => {
            const dateStr = new Date(h.created_at).toLocaleTimeString();
            const recTitles = h.recommendations.map(r => r.title).join(', ');
            
            let statusClass = "status-pending";
            let statusText = "Pending";
            if (h.reward === 1.0) {
                statusClass = "status-completed";
                statusText = "Completed";
            } else if (h.reward === 0.0) {
                statusClass = "status-skipped";
                statusText = "Skipped";
            }

            return `
                <div class="history-item">
                    <div class="history-info">
                        <strong>${dateStr}</strong>: ${recTitles.substring(0, 50)}...
                        <br><span style="font-size:0.8rem; color:var(--text-secondary);">Chosen: ${h.chosen_mission_id || 'None'}</span>
                    </div>
                    <span class="history-status ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');
    }
}

// Run simulation batch
async function runSimulationBatch() {
    try {
        const profile = el.simProfile.value;
        const iterations = parseInt(el.simIterations.value);

        el.runSimBtn.disabled = true;
        el.runSimBtn.textContent = "Simulating...";
        el.simResultsSection.style.display = "block";
        el.simLogsBox.innerHTML = '<div class="sim-log-line">Starting simulation...</div>';
        
        const payload = {
            profile_name: profile,
            iterations: iterations
        };

        const res = await fetch(`${API_BASE}/interventions/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Simulation endpoint failed.");
        const data = await res.json();
        
        // Update stats
        el.simRounds.textContent = data.total_iterations;
        el.simCtr.textContent = `${(data.final_ctr * 100).toFixed(1)}%`;
        el.simRegret.textContent = data.final_regret.toFixed(4);

        // Render logs
        el.simLogsBox.innerHTML = data.history.map(h => `
            <div class="sim-log-line">
                Round ${h.iteration}: Recommended '${h.chosen_mission}' (${h.chosen_category}) • 
                Reward: <span style="color:${h.reward === 1 ? 'var(--success)' : 'var(--danger)'};">${h.reward}</span> • 
                CTR: <strong>${(h.running_ctr*100).toFixed(1)}%</strong> • Regret: ${h.regret.toFixed(3)}
            </div>
        `).join('');
        
        // Scroll to bottom
        el.simLogsBox.scrollTop = el.simLogsBox.scrollHeight;

        // Refresh bandit params and history
        await fetchParameters();
        await fetchHistory();
    } catch (err) {
        el.simLogsBox.innerHTML = `<div class="sim-log-line" style="color:var(--danger)">Error: ${err.message}</div>`;
    } finally {
        el.runSimBtn.disabled = false;
        el.runSimBtn.textContent = "Run Batch";
    }
}

// Initialize Dashboard
async function init() {
    setupSliderListeners();
    el.getRecsBtn.addEventListener('click', getRecommendations);
    el.runSimBtn.addEventListener('click', runSimulationBatch);

    const active = await checkHealth();
    if (active) {
        await fetchParameters();
        await fetchHistory();
        await getRecommendations();
    }
}

window.addEventListener('DOMContentLoaded', init);
