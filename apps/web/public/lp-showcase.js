'use strict';

(function () {
  var config = window.__fatShowcaseConfig;
  if (!config) {
    var slug = '';
    if (document.body) {
      slug = document.body.getAttribute('data-fat-lp') || '';
    }
    if (!slug && window.location && window.location.pathname) {
      slug = window.location.pathname.split('/').pop().replace(/\.html$/i, '');
    }
    if (window.__fatShowcaseConfigs && slug) {
      config = window.__fatShowcaseConfigs[slug];
    }
  }
  if (!config) return;
  var basePath = config.basePath || '.';

  var root = document.getElementById('lp-root');
  if (!root) return;

  // Defesa em profundidade: escapa caracteres HTML de strings antes de
  // interpolar em template strings. Os configs vêm de lp/data.js (estático,
  // controlado pelo dev), mas escapar aqui evita XSS caso alguém edite o
  // arquivo com aspas/HTML não intencionais — e também serve como contrato
  // para qualquer fonte futura de dados (CMS, API).
  function esc(value) {
    if (value == null) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
  // Aplica esc em cada campo string do config. Mantém URLs intactas (já são
  // tratadas pelo browser; whatsApp é montada com encodeURIComponent no data.js).
  (function sanitizeConfig(obj) {
    if (!obj || typeof obj !== 'object') return;
    for (var k in obj) {
      if (!Object.prototype.hasOwnProperty.call(obj, k)) continue;
      if (k === 'whatsApp' || k === 'basePath' || k === 'canonical') continue; // URLs/paths
      var v = obj[k];
      if (typeof v === 'string') {
        obj[k] = esc(v);
      } else if (Array.isArray(v)) {
        v.forEach(function (item) { sanitizeConfig(item); });
      } else if (v && typeof v === 'object') {
        sanitizeConfig(v);
      }
    }
  })(config);

  function block(items, renderer) {
    return items.map(renderer).join('');
  }

  root.innerHTML = [
    '<div class="lp-shell">',
    '  <header class="lp-nav">',
    '    <div class="lp-nav-inner">',
    '      <div class="lp-brand">',
    '        <span class="lp-brand-mark">[FATTECH]</span>',
    '        <div>',
    '          <div>' + config.navLabel + '</div>',
    '          <div class="lp-brand-meta">' + config.navMeta + '</div>',
    '        </div>',
    '      </div>',
    '      <nav class="lp-nav-links" aria-label="Atalhos da landing page">',
    '        <a href="' + basePath + '/index.html">Site Principal</a>',
    '        <a href="' + basePath + '/crm.html">CRM IA</a>',
    '        <a href="#preco">Preco</a>',
    '        <a href="' + config.whatsApp + '" target="_blank" rel="noopener noreferrer">WhatsApp</a>',
    '      </nav>',
    '    </div>',
    '  </header>',
    '',
    '  <section class="lp-section lp-section--hero">',
    '    <div class="lp-section-inner lp-hero">',
    '      <div class="lp-reveal">',
    '        <div class="lp-kicker">' + config.kicker + '</div>',
    '        <h1>' + config.title + '</h1>',
    '        <p class="lp-lead">' + config.lead + '</p>',
    '        <div class="lp-hero-actions">',
    '          <a class="lp-btn" href="' + config.whatsApp + '" target="_blank" rel="noopener noreferrer">' + config.primaryCta + '</a>',
    '          <a class="lp-btn-secondary" href="#prova">' + config.secondaryCta + '</a>',
    '        </div>',
    '        <div class="lp-metrics">',
              block(config.metrics, function (metric) {
                return '<div class="lp-metric"><strong>' + metric.value + '</strong><span>' + metric.label + '</span></div>';
              }),
    '        </div>',
    '      </div>',
    '      <aside class="lp-hero-card lp-reveal">',
    '        <div class="lp-kicker">' + config.sideTag + '</div>',
    '        <h3>' + config.sideTitle + '</h3>',
    '        <p>' + config.sideBody + '</p>',
    '        <ul class="lp-price-list">',
              block(config.sideBullets, function (item) {
                return '<li>' + item + '</li>';
              }),
    '        </ul>',
    '      </aside>',
    '    </div>',
    '  </section>',
    '',
    '  <section class="lp-section" id="dor">',
    '    <div class="lp-section-inner">',
    '      <div class="lp-section-header lp-reveal">',
    '        <div class="lp-kicker">Diagnostico operacional</div>',
    '        <h2 class="lp-section-title">' + config.problemTitle + '</h2>',
    '        <p class="lp-section-sub">' + config.problemLead + '</p>',
    '      </div>',
    '      <div class="lp-card-grid">',
              block(config.pains, function (pain, index) {
                return '<article class="lp-card lp-reveal"><div class="lp-card-number">Ponto ' + String(index + 1).padStart(2, '0') + '</div><h3>' + pain.title + '</h3><p>' + pain.body + '</p></article>';
              }),
    '      </div>',
    '    </div>',
    '  </section>',
    '',
    '  <section class="lp-section" id="solucao">',
    '    <div class="lp-section-inner">',
    '      <div class="lp-section-header lp-reveal">',
    '        <div class="lp-kicker">A virada de chave</div>',
    '        <h2 class="lp-section-title">' + config.solutionTitle + '</h2>',
    '        <p class="lp-section-sub">' + config.solutionLead + '</p>',
    '      </div>',
    '      <div class="lp-proof-grid">',
              block(config.modules, function (module, index) {
                return '<article class="lp-proof-card lp-reveal"><div class="lp-card-number">Modulo ' + String(index + 1).padStart(2, '0') + '</div><h3>' + module.title + '</h3><p>' + module.body + '</p></article>';
              }),
    '      </div>',
    '    </div>',
    '  </section>',
    '',
    '  <section class="lp-section" id="prova">',
    '    <div class="lp-section-inner">',
    '      <div class="lp-section-header lp-reveal">',
    '        <div class="lp-kicker">Impacto esperado</div>',
    '        <h2 class="lp-section-title">' + config.proofTitle + '</h2>',
    '        <p class="lp-section-sub">' + config.proofLead + '</p>',
    '      </div>',
    '      <div class="lp-result-grid">',
              block(config.outcomes, function (outcome) {
                return '<article class="lp-proof-card lp-reveal"><h3>' + outcome.title + '</h3><p>' + outcome.body + '</p></article>';
              }),
    '      </div>',
    '    </div>',
    '  </section>',
    '',
    '  <section class="lp-section" id="preco">',
    '    <div class="lp-section-inner lp-price-grid">',
    '      <div class="lp-price lp-reveal">',
    '        <div class="lp-price-tag">' + config.price.tag + '</div>',
    '        <h3>' + config.price.title + '</h3>',
    '        <p class="lp-section-sub">' + config.price.subtitle + '</p>',
    '        <div class="lp-price-main">',
    '          <div class="lp-price-value">' + config.price.setup + '</div>',
    '          <div class="lp-price-caption">' + config.price.setupCaption + '</div>',
    '        </div>',
    '        <div class="lp-price-main">',
    '          <div class="lp-price-value">' + config.price.recurring + '</div>',
    '          <div class="lp-price-caption">' + config.price.recurringCaption + '</div>',
    '        </div>',
    '        <div class="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, volume de demanda, maturidade comercial e velocidade de execucao.</div>',
    '      </div>',
    '      <div class="lp-price lp-reveal">',
    '        <div class="lp-price-tag">Inclui</div>',
    '        <h3>' + config.offerTitle + '</h3>',
    '        <ul class="lp-price-list">',
              block(config.offerItems, function (item) {
                return '<li>' + item + '</li>';
              }),
    '        </ul>',
    '        <div class="lp-hero-actions" style="margin-top:24px;">',
    '          <a class="lp-btn" href="' + config.whatsApp + '" target="_blank" rel="noopener noreferrer">' + config.offerCta + '</a>',
    '        </div>',
    '      </div>',
    '    </div>',
    '  </section>',
    '',
    '  <section class="lp-section" id="faq">',
    '    <div class="lp-section-inner">',
    '      <div class="lp-section-header lp-reveal">',
    '        <div class="lp-kicker">FAQ comercial</div>',
    '        <h2 class="lp-section-title">' + config.faqTitle + '</h2>',
    '      </div>',
    '      <div class="lp-faq-list">',
              block(config.faq, function (item) {
                return '<article class="lp-faq-item lp-reveal"><h3>' + item.q + '</h3><p>' + item.a + '</p></article>';
              }),
    '      </div>',
    '    </div>',
    '  </section>',
    '',
    '  <footer class="lp-footer">',
    '    <div class="lp-footer-inner">',
    '      <span>FAT Tech — IA aplicada ao comercial, atendimento e operacao.</span>',
    '      <span><a href="' + basePath + '/privacidade.html">Politica de Privacidade</a> · <a href="' + basePath + '/blog/index.html">Blog</a></span>',
    '    </div>',
    '  </footer>',
    '</div>'
  ].join('');

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
      entry.target.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.lp-reveal').forEach(function (node) {
    observer.observe(node);
  });
})();
