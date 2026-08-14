/* Integrated Encrypt + Share Flow Logic & Web Share API */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Drag & Drop File Upload Dropzone
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const selectedFileText = document.getElementById('selected-file-text');
    const encryptForm = document.getElementById('encrypt-form');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressFill = document.getElementById('upload-progress-fill');
    const animBox = document.getElementById('encryption-animation-box');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', (e) => {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                if (selectedFileText) {
                    selectedFileText.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
                }
            }
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                if (selectedFileText) {
                    selectedFileText.textContent = `Selected: ${files[0].name} (${(files[0].size / (1024 * 1024)).toFixed(2)} MB)`;
                }
            }
        });
    }

    if (encryptForm) {
        encryptForm.addEventListener('submit', () => {
            if (animBox) animBox.style.display = 'block';
            if (progressBar && progressFill) {
                progressBar.style.display = 'block';
                let progress = 0;
                const interval = setInterval(() => {
                    progress += 10;
                    if (progress <= 90) {
                        progressFill.style.width = `${progress}%`;
                    } else {
                        clearInterval(interval);
                    }
                }, 120);
            }
        });
    }

    // 2. Post-Encryption Copy Link Button
    const copyBtn = document.getElementById('copy-share-btn');
    const shareInput = document.getElementById('share-url-input');

    if (copyBtn && shareInput) {
        copyBtn.addEventListener('click', () => {
            const shareUrl = shareInput.value;
            
            // Clipboard API
            if (navigator.clipboard) {
                navigator.clipboard.writeText(shareUrl).then(() => {
                    showCopiedFeedback(copyBtn);
                }).catch(() => {
                    fallbackCopyText(shareInput, copyBtn);
                });
            } else {
                fallbackCopyText(shareInput, copyBtn);
            }
        });
    }

    // 3. Native Web Share API Button
    const shareBtn = document.getElementById('native-share-btn');
    if (shareBtn && shareInput) {
        shareBtn.addEventListener('click', async () => {
            const shareUrl = shareInput.value;
            
            if (navigator.share) {
                try {
                    await navigator.share({
                        title: 'SecureVault Encrypted File',
                        text: 'Decrypt and download this protected file on SecureVault.',
                        url: shareUrl
                    });
                } catch (err) {
                    // Fallback to Copy Link if share action was cancelled or failed
                    if (copyBtn) copyBtn.click();
                }
            } else {
                // Fallback for browsers without Web Share API
                if (copyBtn) copyBtn.click();
            }
        });
    }
});

function showCopiedFeedback(btn) {
    const originalText = btn.textContent;
    btn.textContent = '✓ Copied';
    btn.style.background = 'var(--success)';
    btn.style.color = '#050816';
    btn.style.boxShadow = '0 0 15px rgba(0, 255, 153, 0.4)';

    setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = '';
        btn.style.color = '';
        btn.style.boxShadow = '';
    }, 2500);
}

function fallbackCopyText(input, btn) {
    input.select();
    input.setSelectionRange(0, 99999);
    document.execCommand('copy');
    showCopiedFeedback(btn);
}
