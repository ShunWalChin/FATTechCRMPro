/* ╔══════════════════════════════════════════════════════════╗
   ║         FAT TECH — JAVASCRIPT PRINCIPAL v2.1            ║
   ║         Todos os elementos interativos do site          ║
   ║──────────────────────────────────────────────────────────║
   ║  Módulos:                                               ║
   ║  1.  Init (ativa reveal CSS, remove no-js class)        ║
   ║  2.  Navbar (scroll, mobile menu, active link)          ║
   ║  3.  Particle Canvas (partículas interativas no hero)   ║
   ║  4.  Scroll Reveal (fade-in ao entrar na viewport)      ║
   ║  5.  Counter Animation (contadores do hero)             ║
   ║  6.  Formulário → WhatsApp                              ║
   ║  7.  Smooth Scroll (ancoras suaves)                     ║
   ║  8.  Cursor Trail (rastro neon no mouse)                ║
   ║  9.  Efeitos visuais (glitch logo, flicker tags)        ║
   ║  10. Todos os Cards clicáveis (WhatsApp contextual)     ║
   ║                                                         ║
   ║  Dependências: NENHUMA (JS puro, sem frameworks)        ║
   ║  Compatibilidade: Chrome/Edge/Firefox/Safari modernos   ║
   ╚══════════════════════════════════════════════════════════╝ */

'use strict';

/* ════════════════════════════════════════════════════
   Aguarda o DOM estar completamente carregado
   antes de inicializar qualquer coisa.
   Isso evita erros de "elemento não encontrado".
════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {


  /* ══════════════════════════════════════════════
     1. INIT — Ativa os estilos que dependem de JS
  ══════════════════════════════════════════════ */
  // Remove a classe .no-js do <html> e adiciona .js-ready
  // Isso permite que CSS saiba se JS está disponível
  document.documentElement.classList.remove('no-js');
  document.documentElement.classList.add('js-ready');


  /* ══════════════════════════════════════════════
     2. NAVBAR
     - Fundo sólido ao rolar
     - Menu mobile (hamburger)
     - Link ativo conforme seção visível
     - Contrato unificado entre home, CRM e privacidade
     - Breakpoint compacto em 1080px para cobrir tablets
  ══════════════════════════════════════════════ */
  const navbar    = document.getElementById('navbar');
  const navLinks  = document.getElementById('navLinks');
  const hamburger = document.getElementById('hamburger');
  const allLinks  = document.querySelectorAll('.nav-link');

  if (!navbar || !navLinks || !hamburger) {
    console.warn('[FAT Tech] Elementos da navbar não encontrados.');
  } else {
    // Em 1080px a navegação principal deixa de caber com conforto.
    // A partir daqui, todas as páginas que usam a navbar principal
    // entram no mesmo modo drawer/hamburger.
    const compactNavQuery = window.matchMedia('(max-width: 1080px)');
    let backdrop = document.getElementById('navBackdrop');
    const navLogo = navbar.querySelector('.nav-logo');

    // Backdrop é opcional no HTML. Se a página principal esquecer
    // de declarar o elemento, o JS cria automaticamente para manter
    // o contrato visual e de acessibilidade consistente.
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'navBackdrop';
      backdrop.className = 'nav-backdrop';
      backdrop.setAttribute('aria-hidden', 'true');
      navbar.insertAdjacentElement('afterend', backdrop);
    }

    function isCompactNav () {
      return compactNavQuery.matches;
    }

    /* ── Função centralizada: abre/fecha menu ──
       v3.0 — Aplica classe em DOIS lugares (navLinks + body) por
       redundância, garantindo abertura mesmo se um seletor falhar.
       Salva scrollY antes de travar pra restaurar ao fechar. */
    var scrollYBeforeOpen = 0;

    function openMenu () {
      if (!isCompactNav()) return;
      scrollYBeforeOpen = window.scrollY || window.pageYOffset || 0;
      hamburger.classList.add('open');
      navLinks.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      hamburger.setAttribute('aria-expanded', 'true');
      document.body.classList.add('nav-menu-open');
      // Trava posição do body (iOS evita "bounce")
      document.body.style.top = '-' + scrollYBeforeOpen + 'px';
    }

    function closeMenu () {
      hamburger.classList.remove('open');
      navLinks.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('nav-menu-open');
      document.body.style.top = '';
      // Restaura scroll que estava antes de abrir
      if (scrollYBeforeOpen > 0) {
        window.scrollTo(0, scrollYBeforeOpen);
      }
    }

    // Ao sair do breakpoint compacto, qualquer estado aberto é limpo.
    // Isso evita menu "preso" ao girar a tela ou redimensionar a janela.
    function syncMenuMode () {
      if (!isCompactNav()) closeMenu();
    }

    /* ── Scroll: adiciona classe .scrolled ao rolar 40px ── */
    function onScroll () {
      navbar.classList.toggle('scrolled', window.scrollY > 40);
      updateActiveLink();
    }

    window.addEventListener('scroll', onScroll, { passive: true });

    /* ── Hamburger: toggle ── */
    hamburger.addEventListener('click', function () {
      if (!isCompactNav()) return;
      navLinks.classList.contains('open') ? closeMenu() : openMenu();
    });

    /* ── Fecha ao clicar em qualquer link ── */
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', closeMenu);
    });

    if (navLogo) {
      navLogo.addEventListener('click', closeMenu);
    }

    /* ── Fecha ao tocar no backdrop (fora do menu) ── */
    if (backdrop) {
      backdrop.addEventListener('click', closeMenu);
    }

    /* ── Fecha ao pressionar Escape ── */
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navLinks.classList.contains('open')) closeMenu();
    });

    /* ── Fecha ao redimensionar para desktop (evita menu preso após girar tela) ── */
    if (typeof compactNavQuery.addEventListener === 'function') {
      compactNavQuery.addEventListener('change', syncMenuMode);
    } else if (typeof compactNavQuery.addListener === 'function') {
      compactNavQuery.addListener(syncMenuMode);
    }

    var resizeMenuTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeMenuTimer);
      resizeMenuTimer = setTimeout(syncMenuMode, 100);
    });

    /* ── Marca link ativo conforme seção visível ── */
    function updateActiveLink () {
      var sections = document.querySelectorAll('section[id]');
      var current = '';
      sections.forEach(function (sec) {
        if (window.scrollY >= sec.offsetTop - 130) current = sec.id;
      });
      allLinks.forEach(function (link) {
        link.classList.toggle('active', link.getAttribute('href') === '#' + current);
      });
    }

    syncMenuMode();
    updateActiveLink();

  } /* /navbar */


  /* ══════════════════════════════════════════════
     3. PARTICLE CANVAS
     Partículas coloridas que flutuam no hero.
     - Reagem ao movimento do mouse (repulsão suave)
     - Linhas de conexão entre partículas próximas
     - Quantidade adaptada ao tamanho da tela
  ══════════════════════════════════════════════ */
  const canvas = document.getElementById('particleCanvas');

  if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let mouse = { x: null, y: null };
    let heroParticleConfig = null;

    function getHeroParticleConfig () {
      if (window.innerWidth < 768) {
        return {
          sizeMin: 1.4,
          sizeRange: 2.8,
          speed: 0.32,
          glow: 26,
          bloom: 2.8,
          pulseSpeed: 0.022,
          lineDistance: 165,
          lineAlpha: 0.20,
          lineWidth: 1.15,
          repelDistance: 145,
          repelForce: 0.022,
          countFactor: 13000,
          maxCount: 56
        };
      }

      if (window.innerWidth < 1280) {
        return {
          sizeMin: 1.55,
          sizeRange: 3.2,
          speed: 0.26,
          glow: 38,
          bloom: 3.4,
          pulseSpeed: 0.020,
          lineDistance: 185,
          lineAlpha: 0.24,
          lineWidth: 1.2,
          repelDistance: 165,
          repelForce: 0.018,
          countFactor: 18000,
          maxCount: 78
        };
      }

      return {
        sizeMin: 1.75,
        sizeRange: 4.0,
        speed: 0.22,
        glow: 50,
        bloom: 4.2,
        pulseSpeed: 0.018,
        lineDistance: 215,
        lineAlpha: 0.30,
        lineWidth: 1.3,
        repelDistance: 180,
        repelForce: 0.014,
        countFactor: 22000,
        maxCount: 95
      };
    }

    /* ── Redimensiona canvas para preencher o pai ── */
    function resizeCanvas () {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      heroParticleConfig = getHeroParticleConfig();
    }

    resizeCanvas();

    // Redimensiona ao mudar tamanho da janela (debounce 200ms)
    let resizeTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        resizeCanvas();
        initParticles();
      }, 200);
    });

    /* ── Rastreia posição do mouse dentro do canvas ── */
    canvas.addEventListener('mousemove', function (e) {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });

    canvas.addEventListener('mouseleave', function () {
      mouse.x = null;
      mouse.y = null;
    });

    // Touch: suporte para dispositivos móveis
    canvas.addEventListener('touchmove', function (e) {
      const rect  = canvas.getBoundingClientRect();
      const touch = e.touches[0];
      mouse.x = touch.clientX - rect.left;
      mouse.y = touch.clientY - rect.top;
    }, { passive: true });

    /* ── Classe Particle ── */
    function Particle () {
      this.reset();
    }

    Particle.prototype.reset = function () {
      this.x      = Math.random() * canvas.width;
      this.y      = Math.random() * canvas.height;
      this.size   = Math.random() * heroParticleConfig.sizeRange + heroParticleConfig.sizeMin;
      this.speedX = (Math.random() - 0.5) * heroParticleConfig.speed;
      this.speedY = (Math.random() - 0.5) * heroParticleConfig.speed;
      this.opacity = Math.random() * 0.32 + 0.24;
      this.pulse   = Math.random() * Math.PI * 2;

      // Cores do design system
      var colors = ['#00f0ff', '#ff2d78', '#a855f7', '#00ff88'];
      this.color = colors[Math.floor(Math.random() * colors.length)];
    };

    Particle.prototype.update = function () {
      // Pulso de opacidade
      this.pulse += heroParticleConfig.pulseSpeed;

      // Movimento
      this.x += this.speedX;
      this.y += this.speedY;

      // Ricochete nas bordas
      if (this.x < 0 || this.x > canvas.width)  this.speedX *= -1;
      if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;

      // Repulsão suave do mouse (raio de 120px)
      if (mouse.x !== null) {
        var dx   = mouse.x - this.x;
        var dy   = mouse.y - this.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < heroParticleConfig.repelDistance) {
          this.x -= dx * heroParticleConfig.repelForce;
          this.y -= dy * heroParticleConfig.repelForce;
        }
      }
    };

    Particle.prototype.draw = function () {
      // Opacidade com pulso senoidal
      var op = this.opacity * (0.76 + 0.24 * Math.sin(this.pulse));
      var bloomSize = this.size * (heroParticleConfig.bloom + Math.sin(this.pulse) * 0.16);

      ctx.fillStyle   = this.color;
      ctx.shadowColor = this.color;
      ctx.globalAlpha = op * 0.22;
      ctx.shadowBlur  = heroParticleConfig.glow;

      ctx.beginPath();
      ctx.arc(this.x, this.y, bloomSize, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.globalAlpha = op;
      ctx.shadowBlur  = heroParticleConfig.glow * 0.45;
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();

      ctx.shadowBlur  = 0;
      ctx.globalAlpha = 1;
    };

    /* ── Cria as partículas baseado no tamanho da tela ── */
    function initParticles () {
      heroParticleConfig = getHeroParticleConfig();
      var count = Math.floor((canvas.width * canvas.height) / heroParticleConfig.countFactor);
      count = Math.max(count, 22);
      count = Math.min(count, heroParticleConfig.maxCount);

      particles = [];
      for (var i = 0; i < count; i++) {
        particles.push(new Particle());
      }
    }

    /* ── Desenha linhas entre partículas próximas ── */
    function drawConnections () {
      for (var i = 0; i < particles.length; i++) {
        for (var j = i + 1; j < particles.length; j++) {
          var dx   = particles[i].x - particles[j].x;
          var dy   = particles[i].y - particles[j].y;
          var dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < heroParticleConfig.lineDistance) {
            var gradient = ctx.createLinearGradient(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
            gradient.addColorStop(0, particles[i].color);
            gradient.addColorStop(1, particles[j].color);
            ctx.globalAlpha = (1 - dist / heroParticleConfig.lineDistance) * heroParticleConfig.lineAlpha;
            ctx.strokeStyle = gradient;
            ctx.lineWidth   = heroParticleConfig.lineWidth;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
            ctx.globalAlpha = 1;
          }
        }
      }
    }

    /* ── Loop de animação (requestAnimationFrame) ── */
    var animating = true;

    function animateParticles () {
      if (!animating) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawConnections();
      particles.forEach(function (p) {
        p.update();
        p.draw();
      });
      requestAnimationFrame(animateParticles);
    }

    // Pausa animação quando aba não está visível (economiza CPU)
    document.addEventListener('visibilitychange', function () {
      animating = !document.hidden;
      if (animating) animateParticles();
    });

    initParticles();
    animateParticles();

  } /* /canvas */


  /* ══════════════════════════════════════════════
     4. SCROLL REVEAL
     Elementos com [data-reveal] entram suavemente
     quando cruzam a viewport.
     Usa IntersectionObserver (performance nativa).
  ══════════════════════════════════════════════ */
  var revealElements = document.querySelectorAll('[data-reveal]');

  if (revealElements.length > 0 && 'IntersectionObserver' in window) {

    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            // Para de observar após revelar (performance)
            revealObserver.unobserve(entry.target);
          }
        });
      },
      {
        threshold:  0.1,
        rootMargin: '0px 0px -30px 0px'
      }
    );

    revealElements.forEach(function (el) {
      revealObserver.observe(el);
    });

    /* ── Stagger: cards de grid revelam em cascata ── */
    var staggerParents = document.querySelectorAll(
      '.services-grid, .solucoes-grid, .cases-grid, .niveis-grid'
    );

    if (staggerParents.length > 0) {
      var staggerObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              var children = entry.target.querySelectorAll('[data-reveal]');
              children.forEach(function (child, i) {
                setTimeout(function () {
                  child.classList.add('revealed');
                }, i * 80); // 80ms de delay entre cada card
              });
              staggerObserver.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.05 }
      );

      staggerParents.forEach(function (parent) {
        staggerObserver.observe(parent);
      });
    }

  } else {
    // Fallback: revela tudo imediatamente se não há IntersectionObserver
    revealElements.forEach(function (el) {
      el.classList.add('revealed');
    });
  }


  /* ══════════════════════════════════════════════
     5. COUNTER ANIMATION
     Conta de 0 até o valor de data-target quando
     a seção de estatísticas entra na viewport.
     Usa easing ease-out cúbico para suavidade.
  ══════════════════════════════════════════════ */

  /* ── Função de animação de um contador ── */
  function animateCounter (el) {
    var target   = parseInt(el.dataset.target, 10);
    var duration = 2000; // 2 segundos
    var start    = performance.now();

    if (isNaN(target)) return;

    function step (timestamp) {
      var progress = Math.min((timestamp - start) / duration, 1);
      // Easing: ease-out cubic
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target; // garante valor final exato
      }
    }

    requestAnimationFrame(step);
  }

  /* ── Dispara os contadores quando o hero-stats fica visível ── */
  var statsSection = document.querySelector('.hero-stats');

  if (statsSection && 'IntersectionObserver' in window) {
    var counterObserver = new IntersectionObserver(
      function (entries) {
        if (entries[0].isIntersecting) {
          document.querySelectorAll('.stat-num[data-target]').forEach(animateCounter);
          counterObserver.unobserve(statsSection);
        }
      },
      { threshold: 0.4 }
    );

    counterObserver.observe(statsSection);
  }


  /* ══════════════════════════════════════════════
     6. FORMULÁRIO → WHATSAPP
     Coleta os dados do formulário e abre o WhatsApp
     com uma mensagem pré-formatada.
  ══════════════════════════════════════════════ */
  var contactForm = document.getElementById('contactForm');

  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();

      // Coleta os valores
      var nome      = (document.getElementById('nome')      || {}).value || '';
      var email     = (document.getElementById('email')     || {}).value || '';
      var whatsapp  = (document.getElementById('whatsapp')  || {}).value || '';
      var interesse = (document.getElementById('interesse') || {}).value || '';
      var mensagem  = (document.getElementById('mensagem')  || {}).value || '';

      nome      = nome.trim();
      email     = email.trim();
      whatsapp  = whatsapp.trim();
      mensagem  = mensagem.trim();

      // Mapeia valor do select para uma descrição mais natural
      var interesseMap = {
        'agentes':    'agentes de IA para atendimento e vendas',
        'whatsapp':   'automação de WhatsApp',
        'marketing':  'marketing digital com IA',
        'crm':        'CRM com IA',
        'site':       'site ou landing page',
        'consultoria':'consultoria estratégica',
        'outro':      'uma solução que faça sentido para o meu negócio',
        '':           ''
      };

      var interesseTexto = interesseMap[interesse] || interesse;

      // Monta uma mensagem mais humana, incluindo apenas o que o lead informou.
      var linhas = [];
      linhas.push('Olá! Vim pelo site da FAT Tech e gostaria de entender melhor como vocês podem me ajudar.');

      if (nome) {
        linhas.push('Meu nome é ' + nome + '.');
      }

      if (interesseTexto) {
        linhas.push('Tenho interesse em ' + interesseTexto + '.');
      }

      if (mensagem) {
        linhas.push(mensagem);
      }

      if (email) {
        linhas.push('Meu e-mail para contato é ' + email + '.');
      }

      if (whatsapp) {
        linhas.push('Você também pode falar comigo por este WhatsApp: ' + whatsapp + '.');
      }

      var text = linhas.join('\n');

      var url = 'https://wa.me/5535998491017?text=' + encodeURIComponent(text);
      window.open(url, '_blank', 'noopener,noreferrer');
    });
  }


  /* ══════════════════════════════════════════════
     7. SMOOTH SCROLL
     Rolagem suave ao clicar em links âncora (#).
     Compensa a altura fixa da navbar.
  ══════════════════════════════════════════════ */
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href   = link.getAttribute('href');
      var target = document.querySelector(href);

      if (target) {
        e.preventDefault();
        var navHeight = navbar ? navbar.offsetHeight : 80;
        var top       = target.getBoundingClientRect().top + window.scrollY - navHeight - 16;

        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });


  /* ══════════════════════════════════════════════
     8. CURSOR TRAIL
     Rastro neon que segue o mouse (desktop only).
     8 pontos com tamanhos e opacidades decrescentes.
  ══════════════════════════════════════════════ */

  // Não criar cursor trail em dispositivos touch (mobile/tablet)
  var isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

  if (!isTouchDevice) {
    var trailLength = 14;
    var trail       = [];

    // Paleta cromática: cyan → pink → purple ciclando pelos pontos
    var trailPalette = [
      '0,240,255',   // cyan
      '255,45,120',  // pink
      '168,85,247'   // purple
    ];

    for (var i = 0; i < trailLength; i++) {
      var dot = document.createElement('div');
      dot.className = 'cursor-trail';

      // Tamanho e opacidade decrescentes do head (12px) até a cauda (3px)
      var t       = i / (trailLength - 1);
      var size    = (12 - t * 9).toFixed(1);
      var opacity = (0.85 - t * 0.65).toFixed(2);
      var glow    = (16 - t * 10).toFixed(1);
      var rgb     = trailPalette[i % trailPalette.length];

      dot.style.cssText = [
        'position:fixed',
        'pointer-events:none',
        'z-index:9997',
        'width:'  + size + 'px',
        'height:' + size + 'px',
        'border-radius:50%',
        'background:rgba(' + rgb + ',' + opacity + ')',
        'box-shadow:0 0 ' + glow + 'px rgba(' + rgb + ',0.95), 0 0 ' + (glow * 2) + 'px rgba(' + rgb + ',0.4)',
        'top:-30px',
        'left:-30px',
        'will-change:transform',
        'transition:none',
        'mix-blend-mode:screen'
      ].join(';');

      document.body.appendChild(dot);
      trail.push({ el: dot, x: 0, y: 0, half: parseFloat(size) / 2 });
    }

    var mouseX = 0;
    var mouseY = 0;

    document.addEventListener('mousemove', function (e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    /* ── Halo expandindo no clique (anel cyan) ── */
    document.addEventListener('click', function (e) {
      var ring = document.createElement('div');
      ring.style.cssText = [
        'position:fixed',
        'pointer-events:none',
        'z-index:9996',
        'left:' + (e.clientX - 5) + 'px',
        'top:'  + (e.clientY - 5) + 'px',
        'width:10px',
        'height:10px',
        'border-radius:50%',
        'border:2px solid rgba(0,240,255,0.9)',
        'box-shadow:0 0 18px rgba(0,240,255,0.7)',
        'transition:transform .55s ease-out, opacity .55s ease-out',
        'transform:scale(1)',
        'opacity:1',
        'mix-blend-mode:screen'
      ].join(';');
      document.body.appendChild(ring);
      requestAnimationFrame(function () {
        ring.style.transform = 'scale(7)';
        ring.style.opacity = '0';
      });
      setTimeout(function () { if (ring.parentNode) ring.parentNode.removeChild(ring); }, 600);
    });

    /* ── Animação do rastro ── */
    function animateTrail () {
      // Cada ponto segue o anterior com suavização (lerp)
      for (var k = 0; k < trail.length; k++) {
        var prev = k === 0 ? { x: mouseX, y: mouseY } : trail[k - 1];
        trail[k].x += (prev.x - trail[k].x) * 0.35;
        trail[k].y += (prev.y - trail[k].y) * 0.35;
        trail[k].el.style.transform =
          'translate(' + (trail[k].x - trail[k].half).toFixed(1) + 'px,' +
                         (trail[k].y - trail[k].half).toFixed(1) + 'px)';
      }
      rafId = requestAnimationFrame(animateTrail);
    }

    var rafId = requestAnimationFrame(animateTrail);
    window.addEventListener('pagehide', function () { cancelAnimationFrame(rafId); });

  } /* /cursor trail */


  /* ══════════════════════════════════════════════
     9. EFEITOS VISUAIS EXTRA
  ══════════════════════════════════════════════ */

  /* ── Glitch no logo ao passar o mouse ── */
  var logo = document.querySelector('.nav-logo');
  if (logo) {
    logo.addEventListener('mouseenter', function () {
      logo.style.textShadow = '2px 0 #ff2d78, -2px 0 #00f0ff';
      logo.style.letterSpacing = '0.1em';
      setTimeout(function () {
        logo.style.textShadow   = '';
        logo.style.letterSpacing = '';
      }, 180);
    });
  }

  /* ── Flicker aleatório nas section-tags ──
     Simula instabilidade de sinal (efeito cyberpunk)
  ── */
  function randomFlicker () {
    var tags = document.querySelectorAll('.section-tag');
    if (tags.length > 0) {
      var tag = tags[Math.floor(Math.random() * tags.length)];
      var origOpacity = tag.style.opacity;
      tag.style.opacity = '0.2';
      setTimeout(function () {
        tag.style.opacity = origOpacity || '';
      }, 80);
    }
    // Agenda próximo flicker entre 2s e 6s
    setTimeout(randomFlicker, 2000 + Math.random() * 4000);
  }

  // Inicia com 3s de delay para não distrair ao carregar
  setTimeout(randomFlicker, 3000);

  /* hero-subtitle: entrada controlada pelo [data-reveal] + IntersectionObserver acima */


  /* ══════════════════════════════════════════════
     10. CARDS CLICÁVEIS — Card inteiro abre WhatsApp
     Cobre 4 tipos de cards:
     - .service-card  → link interno .service-link
     - .solucao-card  → link interno .solucao-link
     - .nivel-card    → link interno .nivel-cta
     - .case-card     → link interno .case-link
     Ao clicar no card (fora do próprio link),
     dispara o mesmo href do link interno.
  ══════════════════════════════════════════════ */
  var cardDefs = [
    { card: '.service-card', link: '.service-link' },
    { card: '.solucao-card', link: '.solucao-link' },
    { card: '.nivel-card',   link: '.nivel-cta'    },
    { card: '.case-card',    link: '.case-link'     }
  ];

  cardDefs.forEach(function (def) {
    document.querySelectorAll(def.card).forEach(function (card) {
      var link = card.querySelector(def.link);
      if (!link) return;

      card.addEventListener('click', function (e) {
        // Se o clique foi diretamente no link interno, deixa o browser tratar
        if (e.target.closest(def.link)) return;
        window.open(link.href, '_blank', 'noopener,noreferrer');
      });
    });
  });

  /* ══════════════════════════════════════════════
     EXIT-INTENT — Detecta intenção de saída
     Dispara 1× por sessão ao mover o mouse para
     fora da janela pela borda superior (clientY ≤ 5).
     Não dispara em mobile (sem evento mouseleave confiável).
     Não dispara se usuário já viu nesta sessão.
  ══════════════════════════════════════════════ */
  (function initExitIntent () {
    var popup    = document.getElementById('exitPopup');
    var closeBtn = document.getElementById('exitPopupClose');
    if (!popup || !closeBtn) return;

    var SESSION_KEY = 'fattech_exit_shown';
    var shown       = false;

    try {
      if (sessionStorage.getItem(SESSION_KEY)) return;
    } catch (e) {
      /* segue sem persistência de sessão */
    }

    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;

    function openPopup () {
      if (shown) return;
      shown = true;
      try {
        sessionStorage.setItem(SESSION_KEY, '1');
      } catch (e) {
        /* sessionStorage indisponível */
      }
      popup.hidden = false;
      popup.style.pointerEvents = 'auto';
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          popup.style.opacity = '1';
        });
      });
      document.body.style.overflow = 'hidden';
      setTimeout(function () { closeBtn.focus(); }, 350);
      popup.dispatchEvent(new CustomEvent('ft:opened'));
    }

    function closePopup () {
      popup.style.opacity = '0';
      popup.style.pointerEvents = 'none';
      document.body.style.overflow = '';
      setTimeout(function () { popup.hidden = true; }, 340);
    }

    document.addEventListener('mouseleave', function (e) {
      if (e.clientY <= 5) openPopup();
    });

    closeBtn.addEventListener('click', closePopup);

    popup.addEventListener('click', function (e) {
      if (e.target === popup) closePopup();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !popup.hidden) closePopup();
    });

    popup.addEventListener('ft:opened', function () {
      if (window.gtag) {
        gtag('event', 'exit_intent_shown', { event_category: 'engagement' });
      }
    });
  }());


}); /* /DOMContentLoaded */


/* ════════════════════════════════════════════════════
   11. CONSENT MANAGER — LGPD / COOKIES
   ─────────────────────────────────────────────────
   Gerencia o consentimento de cookies conforme a
   Lei nº 13.709/2018 (LGPD), Art. 7º, I.

   Comportamento:
   - Na primeira visita: exibe o banner
   - "Aceitar todos": salva consentimento + carrega GA
   - "Apenas essenciais": salva recusa + NÃO carrega GA
   - Em visitas seguintes: relê localStorage e age
   - Consentimento expira em 180 dias (renovação obrigatória)

   Dados salvos em localStorage (não cookies):
   {
     "status": "accepted" | "rejected",
     "timestamp": <ISO 8601>,
     "expires": <ISO 8601 + 180 dias>
   }
════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var CONSENT_KEY    = 'fattech_cookie_consent';
  var CONSENT_DAYS   = 180; /* Validade do consentimento em dias */
  var banner         = document.getElementById('cookieBanner');
  var btnAccept      = document.getElementById('cookieAccept');
  var btnReject      = document.getElementById('cookieReject');

  /* ── Lê o consentimento salvo ── */
  function readConsent () {
    try {
      var raw  = localStorage.getItem(CONSENT_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      /* Verifica se ainda está dentro do prazo */
      if (data.expires && new Date() > new Date(data.expires)) {
        localStorage.removeItem(CONSENT_KEY);
        return null;
      }
      return data;
    } catch (e) {
      return null;
    }
  }

  /* ── Salva o consentimento ── */
  function saveConsent (status) {
    var now     = new Date();
    var expires = new Date(now.getTime() + CONSENT_DAYS * 24 * 60 * 60 * 1000);
    try {
      localStorage.setItem(CONSENT_KEY, JSON.stringify({
        status:    status,
        timestamp: now.toISOString(),
        expires:   expires.toISOString()
      }));
    } catch (e) {
      /* localStorage indisponível — segue sem salvar */
    }
  }

  /* ── Oculta o banner com animação ── */
  function hideBanner () {
    if (!banner) return;
    banner.classList.remove('visible');
    /* Remove do DOM após a transição para não impactar leitores de tela */
    setTimeout(function () {
      banner.hidden = true;
    }, 420);
  }

  /* ── Exibe o banner com animação ── */
  function showBanner () {
    if (!banner) return;
    banner.hidden = false;
    /* requestAnimationFrame garante que o browser pinte o estado inicial
       (hidden = display:none removido) antes de adicionar .visible */
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        banner.classList.add('visible');
      });
    });
  }

  /* ── Carrega o Google Analytics de forma condicional ──
     Lê o ID do <script id="ga-config" data-ga-id="G-XXXXXXXX">
     Deixe data-ga-id vazio se ainda não tiver o ID configurado.
  ── */
  function loadAnalytics () {
    var gaConfig = document.getElementById('ga-config');
    var gaId     = gaConfig ? gaConfig.getAttribute('data-ga-id') : '';

    /* Só carrega se o ID estiver configurado e não for placeholder */
    if (!gaId || gaId === '' || gaId.indexOf('XXXXXXXXXX') !== -1) return;

    /* Evita carregar duas vezes */
    if (window._gaLoaded) return;
    window._gaLoaded = true;

    /* Injeta o script do GTM/GA4 */
    var script  = document.createElement('script');
    script.async = true;
    script.src  = 'https://www.googletagmanager.com/gtag/js?id=' + gaId;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    function gtag () { window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', gaId, {
      anonymize_ip:          true,   /* Anonimiza IP (melhor prática LGPD) */
      allow_google_signals:  false,  /* Sem remarketing sem consentimento */
      allow_ad_personalization_signals: false
    });

    /* ── Meta Pixel — carregamento condicional pós-consentimento ── */
    (function loadMetaPixel () {
      var pixelConfig  = document.getElementById('meta-pixel-config');
      if (!pixelConfig) return;
      var pixelId      = pixelConfig.getAttribute('data-pixel-id') || '';
      var pixelEnabled = pixelConfig.getAttribute('data-pixel-enabled') || 'false';

      if (!pixelId || pixelEnabled !== 'true' || window._pixelLoaded) return;
      window._pixelLoaded = true;

      !function(f,b,e,v,n,t,s){
        if(f.fbq)return;n=f.fbq=function(){n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s);
      }(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');

      fbq('init', pixelId);
      fbq('track', 'PageView');

      document.querySelectorAll('a[href*="wa.me"]').forEach(function (link) {
        link.addEventListener('click', function () {
          if (window.fbq) fbq('track', 'Contact');
        });
      });

      var form = document.querySelector('form');
      if (form) {
        form.addEventListener('submit', function () {
          if (window.fbq) fbq('track', 'Lead');
        });
      }
    }());
  }

  /* ── Inicialização ── */
  var consent = readConsent();

  if (consent === null) {
    /* Primeira visita ou consentimento expirado: mostra o banner */
    /* Pequeno delay para não competir com o carregamento da página */
    setTimeout(showBanner, 800);
  } else if (consent.status === 'accepted') {
    /* Já aceitou: carrega analytics silenciosamente */
    loadAnalytics();
  }
  /* Se rejeitou: não exibe banner nem carrega analytics */

  /* ── Eventos dos botões ── */
  if (btnAccept) {
    btnAccept.addEventListener('click', function () {
      saveConsent('accepted');
      loadAnalytics();
      hideBanner();
    });
  }

  if (btnReject) {
    btnReject.addEventListener('click', function () {
      saveConsent('rejected');
      hideBanner();
    });
  }

  /* ── Acessibilidade: fecha com Escape ── */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && banner && !banner.hidden) {
      saveConsent('rejected');
      hideBanner();
    }
  });

}()); /* /consent manager */



