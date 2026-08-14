/**
 * SecureVault — Professional 3D Glass Cube Vault
 * Matches reference image: solid dark emerald filled cubes,
 * glowing green edges, volumetric center light, particle depth, grid floor.
 */

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('hero-3d-canvas-container');
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        initStaticFallback(container);
        return;
    }

    if (typeof THREE !== 'undefined') {
        initScene(container);
    }
});

function initScene(container) {
    let W = window.innerWidth;
    let H = window.innerHeight;

    /* ── Renderer ──────────────────────────────────────────────── */
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    /* ── Scene & Camera ────────────────────────────────────────── */
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x010703);
    scene.fog = new THREE.FogExp2(0x010703, 0.028);

    const camera = new THREE.PerspectiveCamera(52, W / H, 0.1, 200);
    camera.position.set(0, 1.5, 16);

    /* ── Lights ────────────────────────────────────────────────── */
    // Ambient
    scene.add(new THREE.AmbientLight(0x003311, 1.5));

    // Central hero glow — this is what makes the cubes look lit from behind the title
    const heroLight = new THREE.PointLight(0x00FF88, 18, 28, 1.8);
    heroLight.position.set(0, 0.5, 1);
    scene.add(heroLight);

    // Left fill
    const leftLight = new THREE.PointLight(0x00cc66, 6, 35, 2);
    leftLight.position.set(-10, 2, 0);
    scene.add(leftLight);

    // Right fill
    const rightLight = new THREE.PointLight(0x00aa55, 5, 35, 2);
    rightLight.position.set(10, -2, -4);
    scene.add(rightLight);

    // Deep back light (creates depth glow)
    const backLight = new THREE.PointLight(0x00FF88, 4, 50, 1.5);
    backLight.position.set(0, -1, -15);
    scene.add(backLight);

    /* ── MATERIALS ─────────────────────────────────────────────── */
    // Solid filled dark green glass — this is the key fix
    // We use MeshStandardMaterial (NOT MeshPhysicalMaterial with transmission)
    // so the cube FACES are visibly filled with dark green, not transparent wireframe.
    const makeCubeMaterial = (seed) => {
        const brightness = 0.06 + (seed % 7) * 0.018;
        return new THREE.MeshStandardMaterial({
            color: new THREE.Color(0, brightness * 2.2, brightness),
            emissive: new THREE.Color(0, brightness * 1.1, brightness * 0.4),
            emissiveIntensity: 0.9,
            roughness: 0.15,
            metalness: 0.6,
            transparent: true,
            opacity: 0.72 + (seed % 5) * 0.04,
            side: THREE.FrontSide,
        });
    };

    /* ── CUBES ─────────────────────────────────────────────────── */
    const cubes = [];
    const CUBE_COUNT = 72;

    // Zone helpers — keep a clear tunnel in the center for text
    const clearRadius = (x, y) => (Math.abs(x) < 5.5 && Math.abs(y) < 3.2);

    for (let i = 0; i < CUBE_COUNT; i++) {
        const size = 0.55 + Math.random() * 1.05;
        const geo = new THREE.BoxGeometry(size, size, size);

        // Filled faces
        const mat = makeCubeMaterial(i);
        const mesh = new THREE.Mesh(geo, mat);

        // Glowing green edge wireframe on top
        const edgeGeo = new THREE.EdgesGeometry(geo);
        const edgeMat = new THREE.LineBasicMaterial({
            color: 0x00FF99,
            transparent: true,
            opacity: 0.9,
        });
        mesh.add(new THREE.LineSegments(edgeGeo, edgeMat));

        // Position: spread across full viewport depth
        let hx, hy;
        let attempts = 0;
        do {
            hx = (Math.random() - 0.5) * 30;
            hy = (Math.random() - 0.5) * 18;
            attempts++;
        } while (clearRadius(hx, hy) && attempts < 40);

        const hz = (Math.random() - 0.5) * 22;

        mesh.position.set(hx, hy, hz);
        mesh.rotation.set(
            Math.random() * Math.PI,
            Math.random() * Math.PI,
            Math.random() * Math.PI * 0.5
        );
        mesh.castShadow = true;

        scene.add(mesh);
        cubes.push({
            mesh,
            hx, hy, hz,
            rx: (Math.random() - 0.5) * 0.0045,
            ry: (Math.random() - 0.5) * 0.0045,
            phi: Math.random() * Math.PI * 2,
            floatAmp: 0.18 + Math.random() * 0.25,
            floatSpeed: 0.35 + Math.random() * 0.45,
        });
    }

    /* ── PERSPECTIVE GRID FLOOR ────────────────────────────────── */
    // Matches reference: glowing green grid lines converging to horizon
    const gridLines = new THREE.GridHelper(80, 60, 0x00FF99, 0x003d1a);
    gridLines.position.set(0, -6, -8);
    gridLines.material.transparent = true;
    gridLines.material.opacity = 0.45;
    scene.add(gridLines);

    // Floor reflection plane (dark glossy)
    const floorMat = new THREE.MeshStandardMaterial({
        color: 0x010a04,
        roughness: 0.05,
        metalness: 0.9,
        transparent: true,
        opacity: 0.8,
    });
    const floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.set(0, -6.05, -8);
    scene.add(floorMesh);

    /* ── PARTICLES ─────────────────────────────────────────────── */
    const PAR = 220;
    const parPos = new Float32Array(PAR * 3);
    for (let i = 0; i < PAR * 3; i += 3) {
        parPos[i]     = (Math.random() - 0.5) * 40;
        parPos[i + 1] = (Math.random() - 0.5) * 24;
        parPos[i + 2] = (Math.random() - 0.5) * 26;
    }
    const parGeo = new THREE.BufferGeometry();
    parGeo.setAttribute('position', new THREE.BufferAttribute(parPos, 3));
    const parMesh = new THREE.Points(parGeo, new THREE.PointsMaterial({
        color: 0x00FF99,
        size: 0.09,
        transparent: true,
        opacity: 0.65,
        sizeAttenuation: true,
    }));
    scene.add(parMesh);

    /* ── CENTRAL GLOW SPRITE (volumetric radial behind headline) ── */
    // Canvas-drawn soft radial sprite
    const spriteCvs = document.createElement('canvas');
    spriteCvs.width = spriteCvs.height = 256;
    const sCtx = spriteCvs.getContext('2d');
    const grad = sCtx.createRadialGradient(128, 128, 0, 128, 128, 128);
    grad.addColorStop(0, 'rgba(0,255,140,0.55)');
    grad.addColorStop(0.4, 'rgba(0,200,100,0.2)');
    grad.addColorStop(1, 'rgba(0,50,20,0)');
    sCtx.fillStyle = grad;
    sCtx.fillRect(0, 0, 256, 256);
    const spriteTex = new THREE.CanvasTexture(spriteCvs);
    const glowSprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: spriteTex,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    }));
    glowSprite.scale.set(18, 14, 1);
    glowSprite.position.set(0, 0.5, -2);
    scene.add(glowSprite);

    /* ── MOUSE PARALLAX ────────────────────────────────────────── */
    let mx = 0, my = 0, tx = 0, ty = 0;
    window.addEventListener('mousemove', e => {
        mx = (e.clientX / W - 0.5) * 2;
        my = (e.clientY / H - 0.5) * 2;
    });

    /* ── RESIZE ────────────────────────────────────────────────── */
    window.addEventListener('resize', () => {
        W = window.innerWidth;
        H = window.innerHeight;
        camera.aspect = W / H;
        camera.updateProjectionMatrix();
        renderer.setSize(W, H);
    });

    /* ── ANIMATE ───────────────────────────────────────────────── */
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const t = clock.getElapsedTime();

        // Hero light pulse — makes center glow breathe
        heroLight.intensity = 16 + Math.sin(t * 1.8) * 3.5;

        // Glow sprite breathe
        const s = 1 + Math.sin(t * 1.4) * 0.07;
        glowSprite.scale.set(18 * s, 14 * s, 1);

        // Cubes slow float + rotate
        cubes.forEach(c => {
            c.mesh.rotation.x += c.rx;
            c.mesh.rotation.y += c.ry;
            c.mesh.position.y = c.hy + Math.sin(t * c.floatSpeed + c.phi) * c.floatAmp;
            c.mesh.position.z = c.hz + Math.cos(t * c.floatSpeed * 0.7 + c.phi) * 0.18;
        });

        // Particles drift
        parMesh.rotation.y = t * 0.018;

        // Smooth mouse parallax
        tx += (mx * 0.22 - tx) * 0.05;
        ty += (-my * 0.18 - ty) * 0.05;
        camera.rotation.y = tx * 0.06;
        camera.rotation.x = ty * 0.05;
        camera.position.x = tx * 0.35;
        camera.position.y = 1.5 + ty * 0.25;

        renderer.render(scene, camera);
    }

    animate();
}

function initStaticFallback(container) {
    container.style.background = '#010703';
    container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:5rem;">🛡️</div>`;
}
