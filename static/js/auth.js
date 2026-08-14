/* Password Strength & Visibility Control */
document.addEventListener('DOMContentLoaded', () => {
    // Password Visibility Toggle
    const toggleBtns = document.querySelectorAll('.toggle-password');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.textContent = 'Hide';
                } else {
                    input.type = 'password';
                    btn.textContent = 'Show';
                }
            }
        });
    });

    // Password Strength Meter
    const passwordInput = document.getElementById('password');
    const strengthProgress = document.getElementById('strength-progress');
    const strengthLabel = document.getElementById('strength-label');

    if (passwordInput && strengthProgress) {
        passwordInput.addEventListener('input', () => {
            const val = passwordInput.value;
            let score = 0;

            if (val.length >= 8) score += 25;
            if (/[A-Z]/.test(val)) score += 25;
            if (/[a-z]/.test(val)) score += 25;
            if (/\d/.test(val) || /[^A-Za-z0-9]/.test(val)) score += 25;

            strengthProgress.className = 'password-strength-progress';

            if (val.length === 0) {
                strengthProgress.style.width = '0%';
                if (strengthLabel) strengthLabel.textContent = '';
            } else if (score < 50) {
                strengthProgress.classList.add('strength-weak');
                if (strengthLabel) strengthLabel.textContent = 'Weak';
            } else if (score < 100) {
                strengthProgress.classList.add('strength-medium');
                if (strengthLabel) strengthLabel.textContent = 'Medium';
            } else {
                strengthProgress.classList.add('strength-strong');
                if (strengthLabel) strengthLabel.textContent = 'Strong';
            }
        });
    }
});
