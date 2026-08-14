/**
 * SecureVault — Professional Background Particle Network
 * Adaptive theme per page: Dashboard=emerald, Encrypt=cyan-green, Decrypt=teal, others=green
 * Shows on all non-landing pages behind all content.
 */
(function () {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    /* ── Canvas setup ─────────────────────────────────────────── */
    const canvas = document.createElement('canvas');
    canvas.id = 'sv-bg-canvas';
    canvas.style.cssText = [
        'position:fixed',
        'top:0', 'left:0',
        'width:100vw', 'height:100vh',
        'z-index:0',
        'pointer-events:none',
        'display:block',
    ].join(';');
    document.body.insertBefore(canvas, document.body.firstChild);

    const ctx = canvas.getContext('2d');
    let W = canvas.width  = window.innerWidth;
    let H = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    });

    /* ── Adaptive colour per page ─────────────────────────────── */
    const path = window.location.pathname;
    let PRIMARY_RGB, GLOW_RGB, BG_TOP, BG_BOT;

    if (path.includes('/encrypt')) {
        PRIMARY_RGB = '0,220,255';   // cyan-green
        GLOW_RGB    = '0,180,220';
        BG_TOP = '#010a0d';
        BG_BOT = '#020804';
    } else if (path.includes('/decrypt')) {
        PRIMARY_RGB = '0,255,180';   // teal-green
        GLOW_RGB    = '0,210,150';
        BG_TOP = '#01100a';
        BG_BOT = '#020804';
    } else if (path.includes('/vault')) {
        PRIMARY_RGB = '0,255,140';
        GLOW_RGB    = '0,200,110';
        BG_TOP = '#010d06';
        BG_BOT = '#020804';
    } else if (path.includes('/security')) {
        PRIMARY_RGB = '0,255,100';
        GLOW_RGB    = '0,200,80';
        BG_TOP = '#010c05';
        BG_BOT = '#020804';
    } else {
        PRIMARY_RGB = '0,255,153';   // emerald (dashboard default)
        GLOW_RGB    = '0,229,163';
        BG_TOP = '#010d07';
        BG_BOT = '#020804';
    }

    /* ── Background gradient ──────────────────────────────────── */
    function drawBG() {
        const grad = ctx.createLinearGradient(0, 0, 0, H);
        grad.addColorStop(0, BG_TOP);
        grad.addColorStop(1, BG_BOT);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, W, H);
    }

    /* ── Subtle radial glow in center-left ───────────────────── */
    function drawGlow(t) {
        const pulse = 0.5 + Math.sin(t * 0.4) * 0.08;
        const grd = ctx.createRadialGradient(W * 0.3, H * 0.4, 0, W * 0.3, H * 0.4, W * 0.55);
        grd.addColorStop(0, `rgba(${GLOW_RGB},${0.055 * pulse})`);
        grd.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, W, H);

        // Second ambient glow top-right
        const grd2 = ctx.createRadialGradient(W * 0.78, H * 0.18, 0, W * 0.78, H * 0.18, W * 0.38);
        grd2.addColorStop(0, `rgba(${PRIMARY_RGB},${0.035 * pulse})`);
        grd2.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grd2;
        ctx.fillRect(0, 0, W, H);
    }

    /* ── Particles ────────────────────────────────────────────── */
    const PCOUNT = 70;
    const particles = Array.from({ length: PCOUNT }, () => ({
        x:    Math.random() * W,
        y:    Math.random() * H,
        r:    0.8 + Math.random() * 2,
        vx:   (Math.random() - 0.5) * 0.4,
        vy:   (Math.random() - 0.5) * 0.4,
        o:    0.25 + Math.random() * 0.55,
        phi:  Math.random() * Math.PI * 2,
        pulseSpeed: 0.4 + Math.random() * 0.8,
    }));

    const CONN = 170;

    /* ── Horizontal scan line (subtle) ───────────────────────── */
    let scanY = 0;
    function drawScan(t) {
        scanY = ((t * 25) % (H + 40)) - 20;
        const grad = ctx.createLinearGradient(0, scanY - 6, 0, scanY + 6);
        grad.addColorStop(0, 'rgba(0,0,0,0)');
        grad.addColorStop(0.5, `rgba(${PRIMARY_RGB},0.03)`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, scanY - 6, W, 12);
    }

    /* ── Grid overlay (very faint perspective-style) ─────────── */
    function drawGrid() {
        ctx.strokeStyle = `rgba(${PRIMARY_RGB},0.022)`;
        ctx.lineWidth = 0.5;

        // Horizontal lines
        const hStep = 55;
        for (let y = hStep; y < H; y += hStep) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(W, y);
            ctx.stroke();
        }
        // Vertical lines
        const vStep = 75;
        for (let x = vStep; x < W; x += vStep) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, H);
            ctx.stroke();
        }
    }

    /* ── Main animation loop ──────────────────────────────────── */
    let startTime = null;

    function tick(ts) {
        if (!startTime) startTime = ts;
        const t = (ts - startTime) / 1000;

        ctx.clearRect(0, 0, W, H);

        drawBG();
        drawGlow(t);
        drawGrid();
        drawScan(t);

        /* Update particles */
        for (const p of particles) {
            p.x += p.vx; p.y += p.vy;
            if (p.x < -10) p.x = W + 10;
            else if (p.x > W + 10) p.x = -10;
            if (p.y < -10) p.y = H + 10;
            else if (p.y > H + 10) p.y = -10;

            const pulse = p.o * (0.8 + Math.sin(t * p.pulseSpeed + p.phi) * 0.2);

            /* Glow halo */
            const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 5);
            grd.addColorStop(0, `rgba(${PRIMARY_RGB},${pulse * 0.5})`);
            grd.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r * 5, 0, Math.PI * 2);
            ctx.fillStyle = grd;
            ctx.fill();

            /* Core dot */
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${PRIMARY_RGB},${pulse})`;
            ctx.fill();
        }

        /* Connection lines */
        for (let i = 0; i < PCOUNT; i++) {
            for (let j = i + 1; j < PCOUNT; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const d2 = dx * dx + dy * dy;
                if (d2 < CONN * CONN) {
                    const alpha = (1 - Math.sqrt(d2) / CONN) * 0.18;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(${PRIMARY_RGB},${alpha})`;
                    ctx.lineWidth = 0.7;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
})();
