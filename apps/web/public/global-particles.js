'use strict';

(function () {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  if (document.querySelector('.global-particle-canvas')) {
    return;
  }

  function getPageType() {
    var path = (window.location && window.location.pathname ? window.location.pathname : '').toLowerCase();
    if (!path || path === '/' || path.endsWith('/index.html')) return 'home';
    if (path.indexOf('/crm') !== -1) return 'crm';
    if (path.indexOf('/blog/') !== -1 || path.endsWith('/blog')) return 'reading';
    if (path.indexOf('privacidade') !== -1) return 'reading';
    if (path.indexOf('/lp/') !== -1) return 'lp';
    return 'default';
  }

  function createProfile(type) {
    var profiles = {
      home: {
        className: 'gp-home',
        counts: [24, 32, 40],
        connection: [126, 148, 172],
        speed: [0.085, 0.105, 0.125],
        radius: [1.7, 1.95, 2.2],
        radiusJitter: [1.35, 1.5, 1.7],
        bloom: [2.2, 2.35, 2.55],
        lineAlpha: [0.095, 0.115, 0.135],
        lineWidth: [0.82, 0.94, 1.02],
        glow: [22, 26, 30],
        alphaBase: [0.22, 0.245, 0.27],
        alphaJitter: [0.18, 0.19, 0.21],
        pointerDistance: 118,
        pointerForce: 0.0032
      },
      crm: {
        className: 'gp-crm',
        counts: [22, 30, 36],
        connection: [120, 140, 156],
        speed: [0.085, 0.105, 0.12],
        radius: [1.6, 1.85, 2.05],
        radiusJitter: [1.3, 1.42, 1.55],
        bloom: [2.12, 2.24, 2.36],
        lineAlpha: [0.09, 0.105, 0.12],
        lineWidth: [0.82, 0.92, 0.98],
        glow: [21, 24, 27],
        alphaBase: [0.2, 0.225, 0.245],
        alphaJitter: [0.17, 0.18, 0.19],
        pointerDistance: 112,
        pointerForce: 0.003
      },
      lp: {
        className: 'gp-lp',
        counts: [18, 24, 30],
        connection: [108, 124, 138],
        speed: [0.072, 0.09, 0.108],
        radius: [1.4, 1.62, 1.82],
        radiusJitter: [1.2, 1.28, 1.42],
        bloom: [2.02, 2.12, 2.24],
        lineAlpha: [0.074, 0.088, 0.102],
        lineWidth: [0.78, 0.86, 0.92],
        glow: [18, 20, 22],
        alphaBase: [0.18, 0.2, 0.22],
        alphaJitter: [0.16, 0.17, 0.18],
        pointerDistance: 102,
        pointerForce: 0.0024
      },
      reading: {
        className: 'gp-reading',
        counts: [8, 12, 16],
        connection: [84, 94, 104],
        speed: [0.045, 0.05, 0.06],
        radius: [1.1, 1.2, 1.3],
        radiusJitter: [0.9, 0.95, 1],
        bloom: [1.7, 1.78, 1.86],
        lineAlpha: [0.035, 0.045, 0.055],
        lineWidth: [0.65, 0.7, 0.75],
        glow: [12, 14, 16],
        alphaBase: [0.12, 0.13, 0.15],
        alphaJitter: [0.1, 0.1, 0.12],
        pointerDistance: 74,
        pointerForce: 0.0012
      },
      default: {
        className: 'gp-default',
        counts: [14, 20, 26],
        connection: [98, 114, 128],
        speed: [0.06, 0.08, 0.1],
        radius: [1.25, 1.45, 1.6],
        radiusJitter: [1.05, 1.15, 1.22],
        bloom: [1.9, 2, 2.1],
        lineAlpha: [0.06, 0.075, 0.09],
        lineWidth: [0.72, 0.82, 0.88],
        glow: [16, 18, 20],
        alphaBase: [0.16, 0.18, 0.2],
        alphaJitter: [0.14, 0.14, 0.16],
        pointerDistance: 92,
        pointerForce: 0.002
      }
    };

    return profiles[type] || profiles.default;
  }

  var pageType = getPageType();
  var profile = createProfile(pageType);

  var style = document.createElement('style');
  style.textContent = [
    'body.global-particles-enabled { position: relative; isolation: isolate; }',
    'body.global-particles-enabled > :not(.global-particle-canvas) { position: relative; z-index: 1; }',
    '.global-particle-canvas {',
    '  position: fixed;',
    '  inset: 0;',
    '  width: 100%;',
    '  height: 100%;',
    '  pointer-events: none;',
    '  z-index: 0;',
    '  opacity: 0.4;',
    '  mix-blend-mode: screen;',
    '}',
    '.global-particle-canvas.gp-home { opacity: 0.44; }',
    '.global-particle-canvas.gp-crm { opacity: 0.38; }',
    '.global-particle-canvas.gp-lp { opacity: 0.3; }',
    '.global-particle-canvas.gp-reading { opacity: 0.12; }',
    '.global-particle-canvas.gp-default { opacity: 0.22; }',
    '@media (max-width: 768px) {',
    '  .global-particle-canvas.gp-home { opacity: 0.3; }',
    '  .global-particle-canvas.gp-crm { opacity: 0.28; }',
    '  .global-particle-canvas.gp-lp { opacity: 0.22; }',
    '  .global-particle-canvas.gp-reading { opacity: 0.08; }',
    '  .global-particle-canvas.gp-default { opacity: 0.18; }',
    '}'
  ].join('');
  document.head.appendChild(style);

  var canvas = document.createElement('canvas');
  canvas.className = 'global-particle-canvas ' + profile.className;
  canvas.setAttribute('aria-hidden', 'true');
  document.body.appendChild(canvas);
  document.body.classList.add('global-particles-enabled');

  var ctx = canvas.getContext('2d');
  if (!ctx) {
    return;
  }

  var particles = [];
  var pointer = { x: null, y: null };
  var palette = ['#00f0ff', '#ff2d78', '#a855f7', '#00ff88'];
  var rafId = 0;
  var isVisible = true;
  var connectionDistance = 170;
  var pulseWaves = [];
  var lastFrame = 0;
  function targetFrameMs() {
    return window.innerWidth < 768 ? 33 : 16;
  }

  function viewportTier() {
    if (window.innerWidth < 640) return 0;
    if (window.innerWidth < 1180) return 1;
    return 2;
  }

  function tierValue(values, tier) {
    return values[Math.max(0, Math.min(values.length - 1, tier))];
  }

  function resize() {
    var tier = viewportTier();
    var ratio = Math.min(window.devicePixelRatio || 1, 1.75);
    canvas.width = Math.floor(window.innerWidth * ratio);
    canvas.height = Math.floor(window.innerHeight * ratio);
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    connectionDistance = tierValue(profile.connection, tier);
    rebuildParticles();
  }

  function rebuildParticles() {
    var tier = viewportTier();
    var total = tierValue(profile.counts, tier);
    particles = [];
    for (var i = 0; i < total; i++) {
      particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * tierValue(profile.speed, tier),
        vy: (Math.random() - 0.5) * tierValue(profile.speed, tier),
        radius: Math.random() * tierValue(profile.radiusJitter, tier) + tierValue(profile.radius, tier),
        alpha: Math.random() * tierValue(profile.alphaJitter, tier) + tierValue(profile.alphaBase, tier),
        color: palette[i % palette.length],
        pulse: Math.random() * Math.PI * 2,
        // 1 em ~6 partículas é "sparkle" — flash neon ocasional
        sparkle: Math.random() < 0.16,
        sparklePhase: Math.random() * Math.PI * 2
      });
    }
  }

  // Onda expansiva: cria pulso de repulsão centrado em (x,y) que decai em ~700ms.
  function spawnWave(x, y) {
    if (pulseWaves.length > 6) pulseWaves.shift();
    pulseWaves.push({ x: x, y: y, life: 1, born: performance.now() });
  }

  function drawConnections() {
    for (var i = 0; i < particles.length; i++) {
      for (var j = i + 1; j < particles.length; j++) {
        var a = particles[i];
        var b = particles[j];
        var dx = a.x - b.x;
        var dy = a.y - b.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > connectionDistance) continue;
        var gradient = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
        gradient.addColorStop(0, a.color);
        gradient.addColorStop(1, b.color);
        ctx.beginPath();
        ctx.strokeStyle = gradient;
        ctx.globalAlpha = (1 - dist / connectionDistance) * tierValue(profile.lineAlpha, viewportTier());
        ctx.lineWidth = tierValue(profile.lineWidth, viewportTier());
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }

  function step(now) {
    if (!isVisible) return;
    rafId = requestAnimationFrame(step);

    // Throttle adaptativo: ~30fps em mobile, ~60fps em desktop. Economia
    // significativa de bateria em devices móveis sem perda visual perceptível.
    if (now && lastFrame && (now - lastFrame) < targetFrameMs() - 1) return;
    lastFrame = now || performance.now();

    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

    // Render onda(s) de pulso e atualiza decay.
    if (pulseWaves.length) {
      var nowMs = performance.now();
      for (var w = pulseWaves.length - 1; w >= 0; w--) {
        var wave = pulseWaves[w];
        var age = (nowMs - wave.born) / 700; // 700ms de vida
        if (age >= 1) { pulseWaves.splice(w, 1); continue; }
        wave.life = 1 - age;
        var radius = age * 280;
        ctx.beginPath();
        ctx.strokeStyle = '#00f0ff';
        ctx.globalAlpha = wave.life * 0.45;
        ctx.lineWidth = 2;
        ctx.shadowBlur = 24;
        ctx.shadowColor = '#00f0ff';
        ctx.arc(wave.x, wave.y, radius, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      ctx.shadowBlur = 0;
    }

    drawConnections();

    var tier = viewportTier();
    var glow = tierValue(profile.glow, tier);
    var bloomFactor = tierValue(profile.bloom, tier);

    particles.forEach(function (particle) {
      particle.pulse += 0.012;
      if (particle.sparkle) particle.sparklePhase += 0.06;
      particle.x += particle.vx;
      particle.y += particle.vy;

      if (particle.x < -12 || particle.x > window.innerWidth + 12) particle.vx *= -1;
      if (particle.y < -12 || particle.y > window.innerHeight + 12) particle.vy *= -1;

      if (pointer.x !== null) {
        var dx = pointer.x - particle.x;
        var dy = pointer.y - particle.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < profile.pointerDistance) {
          particle.x -= dx * profile.pointerForce;
          particle.y -= dy * profile.pointerForce;
        }
      }

      // Pulso expansivo empurra partículas para fora da onda.
      for (var w2 = 0; w2 < pulseWaves.length; w2++) {
        var pw = pulseWaves[w2];
        var pdx = particle.x - pw.x;
        var pdy = particle.y - pw.y;
        var pdist = Math.sqrt(pdx * pdx + pdy * pdy);
        if (pdist > 0 && pdist < 220) {
          var force = pw.life * 0.6 / pdist;
          particle.x += pdx * force;
          particle.y += pdy * force;
        }
      }

      // Sparkle ocasional: brilho extra a cada ciclo.
      var sparkleBoost = particle.sparkle
        ? Math.max(0, Math.sin(particle.sparklePhase)) * 0.6
        : 0;

      var bloom = particle.radius * (bloomFactor + Math.sin(particle.pulse) * 0.2 + sparkleBoost);
      ctx.beginPath();
      ctx.fillStyle = particle.color;
      ctx.globalAlpha = particle.alpha * (0.22 + sparkleBoost * 0.4);
      ctx.shadowBlur = glow * (1 + sparkleBoost);
      ctx.shadowColor = particle.color;
      ctx.arc(particle.x, particle.y, bloom, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.globalAlpha = particle.alpha * (0.9 + Math.sin(particle.pulse) * 0.16 + sparkleBoost * 0.4);
      ctx.shadowBlur = glow * 0.65;
      ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
      ctx.fill();
    });

    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
  }

  window.addEventListener('mousemove', function (event) {
    pointer.x = event.clientX;
    pointer.y = event.clientY;
  }, { passive: true });

  window.addEventListener('touchmove', function (event) {
    if (!event.touches[0]) return;
    pointer.x = event.touches[0].clientX;
    pointer.y = event.touches[0].clientY;
  }, { passive: true });

  // Click/tap em qualquer lugar dispara onda expansiva. Ignora eventos
  // sobre elementos interativos (links, botões, inputs) — não deve
  // disparar ao confirmar um clique de navegação.
  function isInteractiveTarget(el) {
    if (!el || !el.closest) return false;
    return !!el.closest('a, button, input, textarea, select, label, [role="button"], [role="link"], [contenteditable]');
  }
  window.addEventListener('pointerdown', function (event) {
    if (isInteractiveTarget(event.target)) return;
    spawnWave(event.clientX, event.clientY);
  }, { passive: true });

  document.addEventListener('visibilitychange', function () {
    isVisible = document.visibilityState === 'visible';
    if (!isVisible) {
      cancelAnimationFrame(rafId);
      return;
    }
    step();
  });

  window.addEventListener('resize', resize, { passive: true });

  resize();
  step();
})();
