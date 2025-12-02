// API Configuration
const API_BASE_URL = window.location.origin;

// State
let currentUser = null;
let authToken = localStorage.getItem('authToken');
let callTimer = null;
let callDuration = 0;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadCrops();
    loadStates();
    loadExperts();
    checkAuthStatus();
    initEventListeners();
});

// Event Listeners
function initEventListeners() {
    const yieldForm = document.getElementById('yieldForm');
    const recommendForm = document.getElementById('recommendForm');
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    
    if (yieldForm) yieldForm.onsubmit = handleYieldPrediction;
    if (recommendForm) recommendForm.onsubmit = handleCropRecommendation;
    if (loginBtn) loginBtn.onclick = () => { showLogin(); openModal('authModal'); };
    if (signupBtn) signupBtn.onclick = () => { showSignup(); openModal('authModal'); };
}

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// Load Data
async function loadCrops() {
    const select = document.getElementById('yieldCrop');
    if (!select) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/yield/crops`);
        const data = await response.json();
        
        if (data.success) {
            select.innerHTML = '<option value="">Select Crop</option>';
            data.crops.forEach(crop => {
                select.innerHTML += `<option value="${crop.value}">${crop.name} (Avg: ${crop.avg_yield} kg/ha)</option>`;
            });
        }
    } catch (error) {
        console.error('Error loading crops:', error);
    }
}

async function loadStates() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/yield/states`);
        const data = await response.json();
        
        if (data.success) {
            const selects = ['yieldState', 'recState', 'signupState'];
            selects.forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    select.innerHTML = '<option value="">Select State</option>';
                    data.states.forEach(state => {
                        select.innerHTML += `<option value="${state}">${state}</option>`;
                    });
                }
            });
        }
    } catch (error) {
        console.error('Error loading states:', error);
        // Fallback: populate signupState with hardcoded states if API fails
        const signupState = document.getElementById('signupState');
        if (signupState) {
            const states = ['Punjab', 'Haryana', 'Uttar Pradesh', 'West Bengal', 'Andhra Pradesh', 'Tamil Nadu', 'Karnataka', 'Maharashtra', 'Madhya Pradesh', 'Gujarat', 'Rajasthan', 'Bihar', 'Odisha', 'Assam', 'Jharkhand', 'Chhattisgarh', 'Kerala', 'Telangana'];
            signupState.innerHTML = '<option value="">Select State</option>';
            states.forEach(state => {
                signupState.innerHTML += `<option value="${state}">${state}</option>`;
            });
        }
    }
}

async function loadExperts() {
    const container = document.getElementById('expertsList');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/livekit/experts`);
        const data = await response.json();
        
        if (data.success) {
            container.innerHTML = '';
            
            data.experts.forEach(expert => {
                container.innerHTML += `
                    <div class="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition">
                        <div class="flex items-center space-x-4 mb-4">
                            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-3xl">👨‍🌾</div>
                            <div>
                                <h4 class="text-lg font-bold text-gray-800">${expert.name}</h4>
                                <p class="text-green-600">${expert.specialization}</p>
                            </div>
                        </div>
                        <p class="text-gray-600 mb-2">⭐ ${expert.rating} | ${expert.experience}</p>
                        <span class="inline-block px-3 py-1 rounded-full text-sm mb-4 ${expert.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${expert.available ? '🟢 Available' : '🔴 Busy'}
                        </span>
                        <button onclick="initiateCall('${expert.id}')" 
                                class="w-full py-3 rounded-xl font-semibold transition ${expert.available ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}"
                                ${!expert.available ? 'disabled' : ''}>
                            ${expert.available ? '📞 Call Now (₹' + expert.price_per_min + '/min)' : 'Unavailable'}
                        </button>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error('Error loading experts:', error);
    }
}

// Yield Prediction
async function handleYieldPrediction(e) {
    e.preventDefault();
    
    const resultDiv = document.getElementById('yieldResult');
    resultDiv.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent"></div><span class="ml-4 text-gray-600">Analyzing...</span></div>';
    
    const data = {
        crop: document.getElementById('yieldCrop').value,
        state: document.getElementById('yieldState').value,
        season: document.getElementById('yieldSeason').value,
        area: parseFloat(document.getElementById('yieldArea').value),
        nitrogen: parseFloat(document.getElementById('nitrogen').value),
        phosphorus: parseFloat(document.getElementById('phosphorus').value),
        potassium: parseFloat(document.getElementById('potassium').value),
        ph: parseFloat(document.getElementById('ph').value),
        rainfall: parseFloat(document.getElementById('rainfall').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        humidity: parseFloat(document.getElementById('humidity').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/yield/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            const p = result.prediction;
            const categoryColor = p.category === 'Excellent' ? 'bg-green-500' : p.category === 'Good' ? 'bg-blue-500' : p.category === 'Average' ? 'bg-yellow-500' : 'bg-red-500';
            
            resultDiv.innerHTML = `
                <div class="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 mt-4">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <p class="text-4xl font-bold text-green-600">${p.predicted_yield.toLocaleString()} kg/ha</p>
                            <p class="text-gray-600">Total Yield: <strong class="text-gray-800">${p.total_yield.toLocaleString()} kg</strong> for ${data.area} hectares</p>
                        </div>
                        <span class="px-4 py-2 ${categoryColor} text-white rounded-full font-semibold">${p.category} Yield</span>
                    </div>
                    
                    <div class="grid grid-cols-3 gap-4 mb-4">
                        <div class="bg-white rounded-lg p-3 text-center">
                            <p class="text-2xl font-bold text-gray-800">${p.confidence}%</p>
                            <p class="text-sm text-gray-500">Confidence</p>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <p class="text-2xl font-bold text-gray-800">${p.base_yield.toLocaleString()}</p>
                            <p class="text-sm text-gray-500">Base (kg/ha)</p>
                        </div>
                        <div class="bg-white rounded-lg p-3 text-center">
                            <p class="text-2xl font-bold text-gray-800">${p.factors.soil_factor}</p>
                            <p class="text-sm text-gray-500">Soil Factor</p>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-800 mb-2">💡 Insights</h4>
                        <ul class="space-y-1">
                            ${p.insights.map(i => `<li class="text-gray-600 flex items-start"><span class="text-green-500 mr-2">✓</span>${i}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div>
                        <h4 class="font-semibold text-gray-800 mb-2">📋 Recommendations</h4>
                        <ul class="space-y-1">
                            ${p.recommendations.map(r => `<li class="text-gray-600 flex items-start"><span class="text-blue-500 mr-2">→</span>${r}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div class="bg-red-50 text-red-600 p-4 rounded-xl mt-4">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="bg-red-50 text-red-600 p-4 rounded-xl mt-4">Error connecting to server</div>`;
        console.error('Error:', error);
    }
}

// Crop Recommendation
async function handleCropRecommendation(e) {
    e.preventDefault();
    
    const resultDiv = document.getElementById('recommendResult');
    resultDiv.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent"></div><span class="ml-4 text-gray-600">Finding best crops...</span></div>';
    
    const data = {
        state: document.getElementById('recState').value,
        season: document.getElementById('recSeason').value,
        soil_type: document.getElementById('soilType').value,
        water_availability: document.getElementById('waterAvailability').value,
        farm_size: parseFloat(document.getElementById('recFarmSize').value),
        budget: parseFloat(document.getElementById('recBudget').value),
        ph: parseFloat(document.getElementById('recPh').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/recommend/get`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            let html = '<h3 class="text-xl font-bold text-gray-800 mb-4 mt-4">🌱 Top Recommended Crops</h3><div class="space-y-4">';
            
            result.recommendations.forEach((rec, index) => {
                const scoreColor = rec.score >= 80 ? 'bg-green-500' : rec.score >= 60 ? 'bg-blue-500' : 'bg-yellow-500';
                
                html += `
                    <div class="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-5 border border-green-100">
                        <div class="flex justify-between items-start mb-3">
                            <h4 class="text-xl font-bold text-gray-800">#${index + 1} ${rec.crop}</h4>
                            <span class="px-3 py-1 ${scoreColor} text-white rounded-full text-sm font-semibold">${rec.suitability} (${rec.score}%)</span>
                        </div>
                        
                        <div class="grid grid-cols-3 gap-3 mb-3">
                            <div class="bg-white rounded-lg p-3 text-center">
                                <p class="text-lg font-bold text-gray-800">₹${rec.financials.investment_per_ha.toLocaleString()}</p>
                                <p class="text-xs text-gray-500">Investment/ha</p>
                            </div>
                            <div class="bg-white rounded-lg p-3 text-center">
                                <p class="text-lg font-bold text-green-600">₹${rec.financials.expected_profit_per_ha.toLocaleString()}</p>
                                <p class="text-xs text-gray-500">Profit/ha</p>
                            </div>
                            <div class="bg-white rounded-lg p-3 text-center">
                                <p class="text-lg font-bold text-blue-600">${rec.financials.roi_percent}%</p>
                                <p class="text-xs text-gray-500">ROI</p>
                            </div>
                        </div>
                        
                        <p class="text-gray-600 text-sm mb-2">
                            <span class="font-medium">Duration:</span> ${rec.details.duration_days} days | 
                            <span class="font-medium">Water:</span> ${rec.details.water_need} | 
                            <span class="font-medium">Risk:</span> ${rec.details.risk_level}
                        </p>
                        
                        <ul class="space-y-1">
                            ${rec.reasons.map(r => `<li class="text-gray-600 text-sm flex items-start"><span class="text-green-500 mr-2">✓</span>${r}</li>`).join('')}
                        </ul>
                    </div>
                `;
            });
            
            html += '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="bg-red-50 text-red-600 p-4 rounded-xl mt-4">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="bg-red-50 text-red-600 p-4 rounded-xl mt-4">Error connecting to server</div>`;
        console.error('Error:', error);
    }
}

// LiveKit Call Functions
async function initiateCall(expertId) {
    const userName = currentUser?.username || 'Farmer';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/livekit/create-room`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                expert_id: expertId,
                user_name: userName,
                call_type: 'video'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('expertsList').classList.add('hidden');
            document.getElementById('callInterface').classList.remove('hidden');
            document.getElementById('callExpertName').textContent = `Calling ${data.expert.name}...`;
            
            // Start timer
            callDuration = 0;
            callTimer = setInterval(() => {
                callDuration++;
                const mins = Math.floor(callDuration / 60).toString().padStart(2, '0');
                const secs = (callDuration % 60).toString().padStart(2, '0');
                document.getElementById('callTimer').textContent = `${mins}:${secs}`;
            }, 1000);
            
            // In production, connect to LiveKit here
            console.log('LiveKit Room:', data.room.name);
            console.log('Token:', data.user_token);
        }
    } catch (error) {
        console.error('Error initiating call:', error);
        alert('Failed to connect. Please try again.');
    }
}

function toggleMic() {
    // Toggle microphone in LiveKit
    console.log('Toggle mic');
}

function toggleVideo() {
    // Toggle video in LiveKit
    console.log('Toggle video');
}

async function endCall() {
    clearInterval(callTimer);
    
    // Reset UI
    document.getElementById('callInterface').classList.add('hidden');
    document.getElementById('expertsList').classList.remove('hidden');
    
    alert(`Call ended. Duration: ${Math.floor(callDuration / 60)}m ${callDuration % 60}s`);
}

// Auth Functions
function showLogin() {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('signupForm').classList.add('hidden');
    document.getElementById('authTitle').textContent = '🔐 Login';
}

function showSignup() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('signupForm').classList.remove('hidden');
    document.getElementById('authTitle').textContent = '📝 Sign Up';
}

async function handleLogin(e) {
    e.preventDefault();
    
    const data = {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            localStorage.setItem('authToken', result.token);
            authToken = result.token;
            currentUser = result.user;
            updateAuthUI();
            closeModal('authModal');
            alert('Login successful!');
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const data = {
        username: document.getElementById('signupUsername').value,
        email: document.getElementById('signupEmail').value,
        password: document.getElementById('signupPassword').value,
        phone: document.getElementById('signupPhone').value,
        state: document.getElementById('signupState').value,
        farm_size: parseFloat(document.getElementById('signupFarmSize').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            localStorage.setItem('authToken', result.token);
            authToken = result.token;
            currentUser = result.user;
            updateAuthUI();
            closeModal('authModal');
            alert('Registration successful!');
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Signup error:', error);
        alert('Registration failed');
    }
}

function checkAuthStatus() {
    if (authToken) {
        // Verify token and get user info
        updateAuthUI();
    }
}

function updateAuthUI() {
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    
    if (currentUser) {
        loginBtn.textContent = currentUser.username;
        signupBtn.textContent = 'Logout';
        signupBtn.onclick = logout;
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    
    document.getElementById('loginBtn').textContent = 'Login';
    document.getElementById('signupBtn').textContent = 'Sign Up';
    document.getElementById('signupBtn').onclick = () => { showSignup(); openModal('authModal'); };
    
    alert('Logged out');
}
