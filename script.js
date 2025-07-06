// DOM Elements
const fileUpload = document.getElementById('fileUpload');
const videoFile = document.getElementById('videoFile');
const videoUrl = document.getElementById('videoUrl');
const analyzeUrlBtn = document.getElementById('analyzeUrl');
const uploadStatus = document.getElementById('uploadStatus');
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

// Mobile Navigation
hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
});

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// File Upload Functionality
fileUpload.addEventListener('click', () => {
    videoFile.click();
});

fileUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUpload.classList.add('dragover');
});

fileUpload.addEventListener('dragleave', (e) => {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
});

fileUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

videoFile.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// URL Analysis
analyzeUrlBtn.addEventListener('click', () => {
    const url = videoUrl.value.trim();
    if (url) {
        if (isValidURL(url)) {
            handleUrlAnalysis(url);
        } else {
            showError('Please enter a valid URL');
        }
    } else {
        showError('Please enter a video URL');
    }
});

videoUrl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        analyzeUrlBtn.click();
    }
});

// File Upload Handler
function handleFileUpload(file) {
    // Validate file type
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'];
    const maxSize = 2 * 1024 * 1024 * 1024; // 2GB in bytes
    
    if (!allowedTypes.includes(file.type)) {
        showError('Please upload a valid video file (MP4, AVI, MOV, MKV)');
        return;
    }
    
    if (file.size > maxSize) {
        showError('File size must be less than 2GB');
        return;
    }
    
    // Show upload status
    showUploadProgress();
    
    // Simulate file processing (in real app, this would be API call)
    simulateFileProcessing(file);
}

// URL Analysis Handler
function handleUrlAnalysis(url) {
    showUploadProgress();
    
    // Simulate URL processing (in real app, this would be API call)
    simulateUrlProcessing(url);
}

// Show Upload Progress
function showUploadProgress() {
    uploadStatus.style.display = 'block';
    const progressFill = uploadStatus.querySelector('.progress-fill');
    const statusText = uploadStatus.querySelector('.status-text');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) {
            progress = 100;
            clearInterval(interval);
            showSuccess();
        }
        progressFill.style.width = progress + '%';
        
        if (progress < 30) {
            statusText.textContent = 'Uploading video...';
        } else if (progress < 70) {
            statusText.textContent = 'Analyzing gameplay...';
        } else if (progress < 95) {
            statusText.textContent = 'Generating insights...';
        } else {
            statusText.textContent = 'Almost done...';
        }
    }, 200);
}

// Simulate File Processing
function simulateFileProcessing(file) {
    console.log('Processing file:', file.name);
    // In a real application, this would upload the file to your server
    // and process it with AI/ML algorithms
}

// Simulate URL Processing
function simulateUrlProcessing(url) {
    console.log('Processing URL:', url);
    // In a real application, this would download the video from URL
    // and process it with AI/ML algorithms
}

// Show Success Message
function showSuccess() {
    const statusText = uploadStatus.querySelector('.status-text');
    statusText.textContent = 'Analysis complete! Redirecting to results...';
    statusText.style.color = '#00d4ff';
    
    // Hide after 3 seconds
    setTimeout(() => {
        uploadStatus.style.display = 'none';
        showResultsModal();
    }, 3000);
}

// Show Error Message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff4444;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(255, 68, 68, 0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Show Results Modal (Demo)
function showResultsModal() {
    const modal = document.createElement('div');
    modal.className = 'results-modal';
    modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Analysis Results</h2>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="results-grid">
                        <div class="result-card">
                            <div class="result-icon">📊</div>
                            <h3>Performance Score</h3>
                            <p class="result-value">87%</p>
                        </div>
                        <div class="result-card">
                            <div class="result-icon">⚽</div>
                            <h3>Key Plays</h3>
                            <p class="result-value">23</p>
                        </div>
                        <div class="result-card">
                            <div class="result-icon">👥</div>
                            <h3>Players Tracked</h3>
                            <p class="result-value">22</p>
                        </div>
                        <div class="result-card">
                            <div class="result-icon">🎯</div>
                            <h3>Success Rate</h3>
                            <p class="result-value">72%</p>
                        </div>
                    </div>
                    <div class="analysis-preview">
                        <h3>Analysis Preview</h3>
                        <div class="preview-content">
                            <p>✅ Formation analysis completed</p>
                            <p>✅ Player movement patterns identified</p>
                            <p>✅ Tactical insights generated</p>
                            <p>✅ Performance metrics calculated</p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-primary">View Full Report</button>
                    <button class="btn-secondary close-modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    document.body.appendChild(modal);
    
    // Close modal functionality
    const closeButtons = modal.querySelectorAll('.close-modal');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.remove();
        });
    });
    
    // Close on overlay click
    modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
        if (e.target === modal.querySelector('.modal-overlay')) {
            modal.remove();
        }
    });
}

// URL Validation
function isValidURL(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

// Add CSS for dynamic elements
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .dragover {
        border-color: #00d4ff !important;
        background: rgba(0, 212, 255, 0.1) !important;
    }
    
    .error-message {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    .results-modal .modal-overlay {
        background: rgba(0, 0, 0, 0.8);
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    
    .results-modal .modal-content {
        background: #1a1a1a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        max-width: 600px;
        width: 100%;
        max-height: 80vh;
        overflow-y: auto;
        animation: fadeInUp 0.3s ease-out;
    }
    
    .results-modal .modal-header {
        padding: 30px 30px 0 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 30px;
        padding-bottom: 20px;
    }
    
    .results-modal .modal-header h2 {
        color: #ffffff;
        font-size: 1.8rem;
        margin: 0;
    }
    
    .results-modal .close-modal {
        background: none;
        border: none;
        color: #cccccc;
        font-size: 2rem;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }
    
    .results-modal .close-modal:hover {
        color: #00d4ff;
    }
    
    .results-modal .modal-body {
        padding: 0 30px 30px 30px;
    }
    
    .results-modal .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .results-modal .result-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    .results-modal .result-icon {
        font-size: 2rem;
        margin-bottom: 10px;
    }
    
    .results-modal .result-card h3 {
        color: #cccccc;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    
    .results-modal .result-value {
        color: #00d4ff;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .results-modal .analysis-preview {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 20px;
    }
    
    .results-modal .analysis-preview h3 {
        color: #ffffff;
        margin-bottom: 15px;
    }
    
    .results-modal .preview-content p {
        color: #cccccc;
        margin-bottom: 8px;
    }
    
    .results-modal .modal-footer {
        padding: 20px 30px 30px 30px;
        display: flex;
        gap: 15px;
        justify-content: flex-end;
    }
    
    .hamburger.active span:nth-child(1) {
        transform: rotate(-45deg) translate(-5px, 6px);
    }
    
    .hamburger.active span:nth-child(2) {
        opacity: 0;
    }
    
    .hamburger.active span:nth-child(3) {
        transform: rotate(45deg) translate(-5px, -6px);
    }
    
    @media (max-width: 768px) {
        .nav-menu.active {
            display: flex;
            flex-direction: column;
            position: absolute;
            top: 100%;
            left: 0;
            width: 100%;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            gap: 15px;
        }
        
        .nav-menu.active .dropdown-menu {
            position: static;
            opacity: 1;
            visibility: visible;
            transform: none;
            background: rgba(255, 255, 255, 0.05);
            margin-top: 10px;
        }
        
        .results-modal .modal-content {
            margin: 20px;
            max-height: calc(100vh - 40px);
        }
        
        .results-modal .results-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .results-modal .modal-footer {
            flex-direction: column;
        }
    }
`;

document.head.appendChild(style);

// Initialize animations on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'fadeInUp 0.8s ease-out forwards';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .sport-card, .upload-card').forEach(el => {
    observer.observe(el);
});

// Add loading state management
let isProcessing = false;

function setProcessingState(processing) {
    isProcessing = processing;
    const buttons = document.querySelectorAll('.btn-analyze, .btn-primary');
    buttons.forEach(btn => {
        btn.disabled = processing;
        if (processing) {
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
        } else {
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    });
}

// Enhanced file upload with processing state
function handleFileUpload(file) {
    if (isProcessing) return;
    
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'];
    const maxSize = 2 * 1024 * 1024 * 1024;
    
    if (!allowedTypes.includes(file.type)) {
        showError('Please upload a valid video file (MP4, AVI, MOV, MKV)');
        return;
    }
    
    if (file.size > maxSize) {
        showError('File size must be less than 2GB');
        return;
    }
    
    setProcessingState(true);
    showUploadProgress();
    simulateFileProcessing(file);
}

// Enhanced URL analysis with processing state
function handleUrlAnalysis(url) {
    if (isProcessing) return;
    
    if (!isValidURL(url)) {
        showError('Please enter a valid URL');
        return;
    }
    
    setProcessingState(true);
    showUploadProgress();
    simulateUrlProcessing(url);
}

// Enhanced success handler
function showSuccess() {
    const statusText = uploadStatus.querySelector('.status-text');
    statusText.textContent = 'Analysis complete! Redirecting to results...';
    statusText.style.color = '#00d4ff';
    
    setTimeout(() => {
        uploadStatus.style.display = 'none';
        setProcessingState(false);
        showResultsModal();
    }, 3000);
}

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // ESC to close modal
    if (e.key === 'Escape') {
        const modal = document.querySelector('.results-modal');
        if (modal) {
            modal.remove();
        }
    }
    
    // Ctrl/Cmd + U to focus upload
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
    }
});

console.log('Pro Factory - Sports Video Analysis Platform initialized');