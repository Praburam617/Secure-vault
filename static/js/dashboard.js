/* Subtle Atmospheric Dark Background Shader/Canvas */
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    let time = 0;
    function renderBackground() {
        time += 0.005;
        ctx.clearRect(0, 0, width, height);

        // Soft volumetric cyan/blue radial gradient breathing glow
        const cx = width * 0.5 + Math.sin(time) * 40;
        const cy = height * 0.4 + Math.cos(time * 0.8) * 30;

        const radGrad = ctx.createRadialGradient(cx, cy, 50, cx, cy, Math.max(width, height) * 0.7);
        radGrad.addColorStop(0, 'rgba(0, 191, 255, 0.07)');
        radGrad.addColorStop(0.5, 'rgba(0, 229, 255, 0.03)');
        radGrad.addColorStop(1, 'rgba(3, 7, 18, 0)');

        ctx.fillStyle = radGrad;
        ctx.fillRect(0, 0, width, height);

        requestAnimationFrame(renderBackground);
    }

    renderBackground();
});
