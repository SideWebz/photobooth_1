const state = {
    isCapturing: false,
    isSessionRunning: false,
    photoCount: 0,
    sessionStarted: false,
    countdownTimer: null,
    nextCaptureId: 1,
};

const overlay = document.getElementById('uiOverlay');
const startMessage = document.getElementById('startMessage');
const countdownEl = document.getElementById('countdown');
const statusText = document.getElementById('statusText');
const progress = document.getElementById('progress');
const dots = [...document.querySelectorAll('.dot')];
const flash = document.getElementById('flash');
const cameraFeed = document.getElementById('cameraFeed');
const cameraLayer = document.getElementById('cameraLayer');
const printScreen = document.getElementById('printScreen');
const printCountdown = document.getElementById('printCountdown');
const clock = document.getElementById('clock');

const updateClock = () => {
    clock.textContent = new Intl.DateTimeFormat('nl-BE', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    }).format(new Date());
};

const updateProgress = () => {
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index < state.photoCount);
    });
};

const setStatus = (message, visible = true) => {
    statusText.textContent = message;
    statusText.classList.toggle('visible', visible);
};

const clearCountdown = () => {
    if (state.countdownTimer) {
        clearTimeout(state.countdownTimer);
        state.countdownTimer = null;
    }
    countdownEl.classList.remove('show');
    countdownEl.textContent = '';
};

const showFlash = () => {
    flash.classList.remove('active');
    void flash.offsetWidth;
    flash.classList.add('active');
};

const updateCamera = () => {
    cameraFeed.src = '/video_feed?ts=' + Date.now();
};

const requestCapture = async () => {
    const res = await fetch('/api/capture', { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
        throw new Error(data.error || 'Capture failed');
    }
    return data;
};

const showCameraError = (message) => {
    clearCountdown();
    state.isCapturing = false;
    state.isSessionRunning = false;
    state.sessionStarted = false;
    state.photoCount = 0;
    updateProgress();
    progress.classList.remove('visible');
    startMessage.classList.remove('hidden');
    startMessage.innerHTML = 'CAMERA NIET GEVONDEN<br /><span class="start-subtitle">' + message + '</span>';
    setStatus(message, true);
};

const startSession = async () => {
    if (state.isSessionRunning) return;
    state.isSessionRunning = true;
    state.photoCount = 0;
    state.sessionStarted = true;

    overlay.classList.remove('hidden');
    startMessage.classList.add('hidden');
    progress.classList.add('visible');
    updateProgress();
    setStatus('EVEN GEDULD...', false);

    try {
        const startRes = await fetch('/api/start', { method: 'POST' });
        const startData = await startRes.json();
        if (!startData.success) {
            showCameraError(startData.message || 'Gebruik alleen een GoPro/V4L2 USB-camera. Geen laptopwebcam fallback actief.');
            return;
        }

        await runCaptureSequence();
    } catch (error) {
        showCameraError(error.message || 'Camera-opname mislukt. Controleer de GoPro-verbinding.');
    }
};

const runCountdown = (value) => new Promise((resolve) => {
    clearCountdown();
    countdownEl.textContent = value;
    countdownEl.classList.remove('show');
    void countdownEl.offsetWidth;
    countdownEl.classList.add('show');

    state.countdownTimer = setTimeout(resolve, 1000);
});

const runPrintCountdown = () => new Promise((resolve) => {
    let remaining = 20;
    printCountdown.textContent = remaining;
    printScreen.classList.add('visible');

    const timer = setInterval(() => {
        remaining -= 1;
        printCountdown.textContent = remaining;
        if (remaining === 0) {
            clearInterval(timer);
            resolve();
        }
    }, 1000);
});

const runCaptureSequence = async () => {
    state.isCapturing = true;
    for (let i = 1; i <= 3; i += 1) {
        state.photoCount = i;
        updateProgress();
        await runCountdown(5);
        await runCountdown(4);
        await runCountdown(3);
        await runCountdown(2);
        await runCountdown(1);
        showFlash();
        await requestCapture();
        await new Promise((resolve) => setTimeout(resolve, 350));
    }

    state.isCapturing = false;

    progress.classList.remove('visible');

    try {
        const [res] = await Promise.all([
            fetch('/api/finish', { method: 'POST' }),
            runPrintCountdown(),
        ]);
        const data = await res.json();
        if (!data.success) {
            throw new Error(data.error || 'Finish failed');
        }

    } catch (error) {
    } finally {
        printScreen.classList.remove('visible');
    }

    setTimeout(() => {
        state.photoCount = 0;
        updateProgress();
        state.isSessionRunning = false;
        state.sessionStarted = false;
        startMessage.classList.remove('hidden');
        setStatus('EVEN GEDULD...', false);
        progress.classList.remove('visible');
        clearCountdown();
        updateCamera();
    }, 2200);
};

cameraLayer.addEventListener('click', startSession);
cameraLayer.addEventListener('touchstart', (event) => {
    event.preventDefault();
    startSession();
}, { passive: false });

window.addEventListener('load', () => {
    updateCamera();
    updateClock();
    setInterval(updateClock, 1000);
    setStatus('EVEN GEDULD...', false);
    updateProgress();
});

