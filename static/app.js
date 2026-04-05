/**
 * DermAI — Skin Detection Agent
 * Frontend JavaScript: handles image upload, camera, API calls, and results rendering
 */

// ===== State =====
const state = {
    currentTab: 'upload',
    imageFile: null,
    imageDataUrl: null,
    cameraStream: null,
    isAnalyzing: false,
    results: null
};

// ===== DOM Elements =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
    // Tabs
    tabBtns: $$('.tab-btn'),
    tabContents: $$('.tab-content'),
    dropZone: $('#drop-zone'),
    fileInput: $('#file-input'),
    userAge: $('#user-age'),
    userSkin: $('#user-skin'),
    // Camera
    cameraVideo: $('#camera-video'),
    cameraCanvas: $('#camera-canvas'),
    btnCapture: $('#btn-capture'),
    // URL
    urlInput: $('#url-input'),
    btnUrlAnalyze: $('#btn-url-analyze'),
    // Preview
    previewContainer: $('#preview-container'),
    previewImage: $('#preview-image'),
    detectionCanvas: $('#detection-canvas'),
    btnClear: $('#btn-clear'),
    btnAnalyze: $('#btn-analyze'),
    // Loading
    loadingSection: $('#loading-section'),
    loadingStep: $('#loading-step'),
    // Results
    resultsSection: $('#results-section'),
    scoreCircle: $('#score-circle'),
    scoreNumber: $('#score-number'),
    scoreTitle: $('#score-title'),
    scoreRecommendation: $('#score-recommendation'),
    statDetections: $('#stat-detections'),
    statConditions: $('#stat-conditions'),
    statTime: $('#stat-time'),
    conditionsList: $('#conditions-list'),
    resultImage: $('#result-image'),
    resultCanvas: $('#result-canvas'),
    tipsList: $('#tips-list'),
    foodCard: $('#food-card'),
    foodContent: $('#food-content'),
    btnNewScan: $('#btn-new-scan'),
    // Sections
    uploadSection: $('#upload-section')
};

// ===== Tab Switching =====
els.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tab) {
    state.currentTab = tab;

    els.tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    els.tabContents.forEach(c => c.classList.toggle('active', c.id === `content-${tab}`));

    // Handle camera
    if (tab === 'camera') {
        startCamera();
    } else {
        stopCamera();
    }
}

// ===== File Upload & Drag/Drop =====
els.dropZone.addEventListener('click', () => els.fileInput.click());

els.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    els.dropZone.classList.add('drag-over');
});

els.dropZone.addEventListener('dragleave', () => {
    els.dropZone.classList.remove('drag-over');
});

els.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    els.dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFile(file);
    }
});

els.fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

function handleFile(file) {
    state.imageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        state.imageDataUrl = e.target.result;
        showPreview(e.target.result);
    };
    reader.readAsDataURL(file);
}

function showPreview(src) {
    els.previewImage.src = src;
    els.previewContainer.classList.remove('hidden');
    els.previewImage.onload = () => {
        // Size canvas to match image display
        const rect = els.previewImage.getBoundingClientRect();
        els.detectionCanvas.width = rect.width;
        els.detectionCanvas.height = rect.height;
    };
}

// ===== Camera =====
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 960 } }
        });
        state.cameraStream = stream;
        els.cameraVideo.srcObject = stream;
    } catch (err) {
        console.error('Camera error:', err);
        alert('تعذر الوصول إلى الكاميرا. يرجى التحقق من الصلاحيات.');
    }
}

function stopCamera() {
    if (state.cameraStream) {
        state.cameraStream.getTracks().forEach(t => t.stop());
        state.cameraStream = null;
    }
}

els.btnCapture.addEventListener('click', () => {
    const video = els.cameraVideo;
    const canvas = els.cameraCanvas;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    state.imageDataUrl = dataUrl;
    state.imageFile = null;

    stopCamera();
    switchTab('upload'); // Switch to show preview
    showPreview(dataUrl);
});

// ===== URL Analysis =====
els.btnUrlAnalyze.addEventListener('click', () => {
    const url = els.urlInput.value.trim();
    if (!url) return;
    analyzeFromUrl(url);
});

els.urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        els.btnUrlAnalyze.click();
    }
});

// ===== Clear =====
els.btnClear.addEventListener('click', () => {
    state.imageFile = null;
    state.imageDataUrl = null;
    els.previewContainer.classList.add('hidden');
    els.fileInput.value = '';
    const ctx = els.detectionCanvas.getContext('2d');
    ctx.clearRect(0, 0, els.detectionCanvas.width, els.detectionCanvas.height);
});

// ===== Analyze =====
els.btnAnalyze.addEventListener('click', () => {
    if (state.imageFile) {
        analyzeFromFile(state.imageFile);
    } else if (state.imageDataUrl) {
        analyzeFromBase64(state.imageDataUrl);
    }
});

async function analyzeFromFile(file) {
    showLoading();

    const formData = new FormData();
    formData.append('image', file);
    if (els.userAge.value) formData.append('age', els.userAge.value);
    if (els.userSkin.value) formData.append('skin_type', els.userSkin.value);

    try {
        updateLoadingStep('جاري إرسال الصورة إلى الذكاء الاصطناعي...');
        const res = await fetch('/api/detect', {
            method: 'POST',
            body: formData
        });

        updateLoadingStep('جاري معالجة النتائج...');
        const data = await res.json();

        if (data.success) {
            showResults(data);
        } else {
            alert('فشل التحليل: ' + (data.error || 'خطأ غير معروف'));
            hideLoading();
        }
    } catch (err) {
        console.error('Error:', err);
        alert('فشل تحليل الصورة. هل الخادم يعمل؟');
        hideLoading();
    }
}

async function analyzeFromBase64(dataUrl) {
    showLoading();

    try {
        updateLoadingStep('جاري إرسال الصورة إلى الذكاء الاصطناعي...');
        const payload = { image: dataUrl };
        if (els.userAge.value) payload.age = els.userAge.value;
        if (els.userSkin.value) payload.skin_type = els.userSkin.value;

        const res = await fetch('/api/detect/base64', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        updateLoadingStep('جاري معالجة النتائج...');
        const data = await res.json();

        if (data.success) {
            showResults(data);
        } else {
            alert('فشل التحليل: ' + (data.error || 'خطأ غير معروف'));
            hideLoading();
        }
    } catch (err) {
        console.error('Error:', err);
        alert('فشل تحليل الصورة. هل الخادم يعمل؟');
        hideLoading();
    }
}

async function analyzeFromUrl(url) {
    showLoading();

    try {
        updateLoadingStep('جاري جلب الصورة من الرابط...');
        const payload = { url: url };
        if (els.userAge.value) payload.age = els.userAge.value;
        if (els.userSkin.value) payload.skin_type = els.userSkin.value;

        const res = await fetch('/api/detect/url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        updateLoadingStep('جاري معالجة النتائج...');
        const data = await res.json();

        if (data.success) {
            // Set preview image from URL
            state.imageDataUrl = url;
            showResults(data);
        } else {
            alert('فشل التحليل: ' + (data.error || 'خطأ غير معروف'));
            hideLoading();
        }
    } catch (err) {
        console.error('Error:', err);
        alert('فشل تحليل الصورة. هل الخادم يعمل؟');
        hideLoading();
    }
}

// ===== Loading =====
function showLoading() {
    state.isAnalyzing = true;
    els.uploadSection.classList.add('hidden');
    els.resultsSection.classList.add('hidden');
    els.loadingSection.classList.remove('hidden');
}

function hideLoading() {
    state.isAnalyzing = false;
    els.loadingSection.classList.add('hidden');
    els.uploadSection.classList.remove('hidden');
}

function updateLoadingStep(text) {
    els.loadingStep.textContent = text;
}

// ===== Results =====
function showResults(data) {
    state.results = data;
    els.loadingSection.classList.add('hidden');
    els.resultsSection.classList.remove('hidden');

    // Animate score
    animateScore(data.health_score);

    // Update stats
    els.scoreRecommendation.textContent = data.overall_recommendation;
    els.statDetections.textContent = data.total_detections;
    els.statConditions.textContent = data.unique_conditions;
    els.statTime.textContent = `${Math.round(data.inference_time_ms)}ms`;

    // Render condition cards
    renderConditions(data.condition_summary);

    // Render detection map
    renderDetectionMap(data);

    // Render tips
    renderTips(data.condition_summary);

    // Render LLM Diet Plan
    if (data.llm_diet_plan) {
        // Simple markdown parsing to HTML since Gemini may return exactly `*` or `**`
        let htmlFood = data.llm_diet_plan
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\* /g, '\n• ')
            .replace(/^- /gm, '• ');
            
        els.foodContent.innerHTML = htmlFood;
        els.foodCard.style.display = 'block';
    } else {
        els.foodCard.style.display = 'none';
    }

    // Scroll to results
    els.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function animateScore(targetScore) {
    const circumference = 2 * Math.PI * 52; // r=52
    const offset = circumference - (targetScore / 100) * circumference;

    // Animate circle
    els.scoreCircle.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    setTimeout(() => {
        els.scoreCircle.style.strokeDashoffset = offset;
    }, 100);

    // Animate number
    let current = 0;
    const step = targetScore / 40;
    const interval = setInterval(() => {
        current += step;
        if (current >= targetScore) {
            current = targetScore;
            clearInterval(interval);
        }
        els.scoreNumber.textContent = Math.round(current);
    }, 30);

    // Update gradient based on score
    const gradientEl = document.querySelector('#score-gradient');
    if (targetScore >= 80) {
        gradientEl.innerHTML = '<stop offset="0%" stop-color="#10B981"/><stop offset="100%" stop-color="#22D3EE"/>';
    } else if (targetScore >= 50) {
        gradientEl.innerHTML = '<stop offset="0%" stop-color="#F59E0B"/><stop offset="100%" stop-color="#EF4444"/>';
    } else {
        gradientEl.innerHTML = '<stop offset="0%" stop-color="#EF4444"/><stop offset="100%" stop-color="#DC2626"/>';
    }
}

function renderConditions(summary) {
    if (!summary || Object.keys(summary).length === 0) {
        els.conditionsList.innerHTML = `
            <div style="text-align:center; padding:40px; color: var(--text-muted); grid-column: 1/-1;">
                <p style="font-size: 2rem; margin-bottom: 12px;">✨</p>
                <p style="font-weight: 600; color: var(--text-primary);">لم يتم اكتشاف أي مشاكل في البشرة!</p>
                <p>بشرتك تبدو صحية. حافظ على روتينك الرائع.</p>
            </div>
        `;
        return;
    }

    let html = '';
    for (const [name, info] of Object.entries(summary)) {
        html += `
            <div class="condition-card animate-in" style="--condition-color: ${info.color}">
                <div style="position:absolute;top:0;left:0;width:4px;height:100%;background:${info.color};border-radius:4px 0 0 4px;"></div>
                <div class="condition-header">
                    <div class="condition-name">
                        <span class="condition-icon-dot" style="background:${info.color}"></span>
                        ${name.replace(/-/g, ' ')}
                    </div>
                    <span class="condition-confidence">${info.max_confidence}%</span>
                </div>
                <div class="condition-count">${info.count} اكتشاف • الحدة: ${info.severity}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="background:${info.color}; width: 0%;" data-width="${info.max_confidence}%"></div>
                </div>
            </div>
        `;
    }
    els.conditionsList.innerHTML = html;

    // Animate confidence bars
    setTimeout(() => {
        $$('.confidence-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    }, 200);
}

function renderDetectionMap(data) {
    const img = els.resultImage;
    const canvas = els.resultCanvas;

    // Set image source
    if (state.imageDataUrl) {
        img.src = state.imageDataUrl;
    }

    img.onload = () => {
        // Calculate displayed dimensions
        const displayWidth = img.clientWidth;
        const displayHeight = img.clientHeight;

        canvas.width = displayWidth;
        canvas.height = displayHeight;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!data.detections || data.detections.length === 0) return;

        // Scale factors
        const scaleX = displayWidth / data.image.width;
        const scaleY = displayHeight / data.image.height;

        // Bounding boxes, labels, and corners have been remvoed as requested.
    };
}

function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

function renderTips(summary) {
    if (!summary || Object.keys(summary).length === 0) {
        els.tipsList.innerHTML = `
            <div style="text-align:center; padding:30px; color: var(--text-muted); grid-column: 1/-1;">
                <p>لا توجد توصيات محددة في هذا الوقت. حافظ على روتينك الرائع للعناية بالبشرة!</p>
            </div>
        `;
        return;
    }

    let html = '';
    for (const [name, info] of Object.entries(summary)) {
        const tipItems = info.tips.map(t => `<li>${t}</li>`).join('');
        html += `
            <div class="tip-card animate-in">
                <div class="tip-card-title">
                    <span>${info.icon}</span>
                    ${name.replace(/-/g, ' ')}
                </div>
                <p class="tip-card-description">${info.description}</p>
                <ul class="tip-list">
                    ${tipItems}
                </ul>
            </div>
        `;
    }
    els.tipsList.innerHTML = html;
}

// ===== New Scan =====
els.btnNewScan.addEventListener('click', () => {
    state.imageFile = null;
    state.imageDataUrl = null;
    state.results = null;

    els.resultsSection.classList.add('hidden');
    els.uploadSection.classList.remove('hidden');
    els.previewContainer.classList.add('hidden');
    els.fileInput.value = '';
    els.urlInput.value = '';

    // Reset score circle
    els.scoreCircle.style.transition = 'none';
    els.scoreCircle.style.strokeDashoffset = '326.73';
    els.scoreNumber.textContent = '0';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ===== Init =====
console.log('🧬 DermAI Skin Detection Agent loaded');
