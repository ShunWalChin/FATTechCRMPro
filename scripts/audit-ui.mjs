/**
 * Mede o site contra as regras objetivas de UI/UX, em vez de opinar sobre ele.
 *
 * As recomendacoes vem da base local da skill ui-ux-pro-max (nextlevelbuilder/ui-ux-pro-max-skill),
 * clonada em .local/references. Aqui so entram criterios **verificaveis no navegador** -- contraste
 * calculado, tamanho de alvo medido, atributo presente ou ausente. Julgamento estetico nao entra:
 * "o site ficaria melhor com outra paleta" nao e uma medida, e a identidade cyberpunk do original e
 * uma decisao do dono, nao um defeito a corrigir.
 *
 * Como todo verificador deste projeto, ele reporta o denominador. Saber que ha 3 problemas nao vale
 * nada sem saber que foram 1.240 elementos conferidos em 49 paginas -- um checador que olha pouco
 * tambem termina sem achar problema.
 *
 * Uso: node scripts/audit-ui.mjs [http://127.0.0.1:3200]
 */
import {chromium} from '@playwright/test';
import {readdirSync, statSync} from 'node:fs';
import {join, relative} from 'node:path';

const RAIZ = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const PUBLICO = join(RAIZ, 'apps', 'web', 'public');
const BASE = process.argv[2] || 'http://127.0.0.1:3200';

function paginas(dir = PUBLICO) {
  return readdirSync(dir).flatMap(nome => {
    const caminho = join(dir, nome);
    if (statSync(caminho).isDirectory()) return paginas(caminho);
    return nome.endsWith('.html') ? [relative(PUBLICO, caminho).split('\\').join('/')] : [];
  });
}

// Executado dentro da pagina. Tudo aqui e medido, nunca inferido do codigo-fonte.
const MEDIR = () => {
  const achados = [];
  const contagem = {texto: 0, alvos: 0, imagens: 0, botoes: 0, campos: 0, titulos: 0, naoMedivel: 0};

  const canal = v => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  const luminancia = ([r, g, b]) => 0.2126 * canal(r / 255) + 0.7152 * canal(g / 255) + 0.0722 * canal(b / 255);
  const rgb = cor => (cor.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
  const razao = (frente, fundo) => {
    const [a, b] = [luminancia(frente) + 0.05, luminancia(fundo) + 0.05].sort((x, y) => y - x);
    return a / b;
  };
  // O fundo efetivo. Ignorar background-image foi o primeiro defeito deste medidor: um botao com
  // gradiente tem background-color transparente, e subir ate o pai escuro dava 1.10:1 num CTA que
  // na verdade e texto preto sobre ciano. Agora o gradiente e lido, e cada parada vira um fundo
  // candidato -- vale a pior delas, porque o texto atravessa o gradiente inteiro.
  // Imagem que nao e gradiente nao da para medir daqui: devolve null e o trecho e contado a parte.
  const paradasDe = imagem => {
    if (!imagem || imagem === 'none') return [];
    if (!/gradient\(/.test(imagem)) return null;
    return [...imagem.matchAll(/rgba?\(([^)]+)\)/g)]
      .map(m => m[1].split(',').map(Number))
      .filter(p => p.length < 4 || p[3] > 0.85)
      .map(p => p.slice(0, 3));
  };
  const fundoDe = el => {
    for (let no = el; no && no !== document.documentElement; no = no.parentElement) {
      const estilo = getComputedStyle(no);
      const paradas = paradasDe(estilo.backgroundImage);
      if (paradas === null) return null;
      if (paradas.length) return paradas;
      const partes = (estilo.backgroundColor.match(/[\d.]+/g) || []).map(Number);
      if (partes.length === 3 || (partes.length === 4 && partes[3] > 0.85)) return [partes.slice(0, 3)];
    }
    const partes = (getComputedStyle(document.documentElement).backgroundColor.match(/[\d.]+/g) || []).map(Number);
    return [partes.length >= 3 ? partes.slice(0, 3) : [0, 0, 0]];
  };
  const visivel = el => {
    const r = el.getBoundingClientRect();
    const e = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && e.visibility !== 'hidden' && e.display !== 'none'
      && Number(e.opacity) > 0.1;
  };
  const onde = el => {
    const marca = el.tagName.toLowerCase();
    const classe = typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '';
    return marca + classe;
  };

  // 1. Contraste do texto — WCAG AA: 4.5:1 normal, 3:1 para texto grande.
  for (const el of document.querySelectorAll('p, a, span, li, h1, h2, h3, h4, h5, h6, button, label, td, th, small, strong, em')) {
    if (!visivel(el)) continue;
    const texto = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
    if (texto.length < 2) continue;
    const estilo = getComputedStyle(el);
    const frente = rgb(estilo.color);
    if (frente.length < 3) continue;
    contagem.texto++;
    const tamanho = parseFloat(estilo.fontSize);
    const grande = tamanho >= 24 || (tamanho >= 18.66 && Number(estilo.fontWeight) >= 700);
    const minimo = grande ? 3 : 4.5;
    const fundos = fundoDe(el);
    if (fundos === null) { contagem.naoMedivel++; continue; }
    // A pior parada manda: se o texto fica ilegivel em parte do gradiente, fica ilegivel.
    const r = Math.min(...fundos.map(f => razao(frente, f)));
    if (r < minimo) {
      achados.push({regra: 'contraste', gravidade: 'alta', onde: onde(el),
        detalhe: `${r.toFixed(2)}:1 (mínimo ${minimo}:1) em ${Math.round(tamanho)}px`,
        amostra: texto.slice(0, 40)});
    }
  }

  // 2. Tamanho de alvo — WCAG 2.2 AA: 24×24 CSS px, ou espacamento equivalente.
  for (const el of document.querySelectorAll('a[href], button, [role="button"], input:not([type="hidden"]), select, textarea')) {
    if (!visivel(el)) continue;
    contagem.alvos++;
    const r = el.getBoundingClientRect();
    // Link dentro de bloco de texto e excecao explicita da norma: nao e alvo isolado.
    const emTexto = el.tagName === 'A' && el.closest('p, li, td, small');
    if (!emTexto && (r.width < 24 || r.height < 24)) {
      achados.push({regra: 'alvo-pequeno', gravidade: 'alta', onde: onde(el),
        detalhe: `${Math.round(r.width)}×${Math.round(r.height)}px (mínimo 24×24)`,
        amostra: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40)});
    }
  }

  // 3. Imagem sem texto alternativo, e imagem abaixo da dobra sem carregamento tardio.
  for (const img of document.querySelectorAll('img')) {
    contagem.imagens++;
    if (img.getAttribute('alt') === null) {
      achados.push({regra: 'alt-ausente', gravidade: 'alta', onde: onde(img),
        detalhe: 'sem atributo alt', amostra: (img.getAttribute('src') || '').slice(-40)});
    }
    const topo = img.getBoundingClientRect().top + window.scrollY;
    if (topo > window.innerHeight && img.loading !== 'lazy') {
      achados.push({regra: 'sem-lazy', gravidade: 'media', onde: onde(img),
        detalhe: `${Math.round(topo)}px abaixo do topo, sem loading="lazy"`,
        amostra: (img.getAttribute('src') || '').slice(-40)});
    }
  }

  // 4. Botao sem nome acessivel: icone sozinho nao diz o que faz.
  for (const el of document.querySelectorAll('button, a[href], [role="button"]')) {
    if (!visivel(el)) continue;
    contagem.botoes++;
    const nome = (el.getAttribute('aria-label') || el.getAttribute('title')
      || el.textContent || '').replace(/\s+/g, ' ').trim();
    if (!nome) {
      achados.push({regra: 'sem-nome', gravidade: 'alta', onde: onde(el),
        detalhe: 'sem texto, aria-label ou title', amostra: el.outerHTML.slice(0, 60)});
    }
  }

  // 5. Campo de formulario sem rotulo visivel associado.
  for (const el of document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]), select, textarea')) {
    if (!visivel(el)) continue;
    contagem.campos++;
    const rotulado = (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`))
      || el.closest('label') || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
    if (!rotulado) {
      achados.push({regra: 'campo-sem-rotulo', gravidade: 'alta', onde: onde(el),
        detalhe: 'sem label, aria-label nem aria-labelledby',
        amostra: el.getAttribute('placeholder') || el.getAttribute('name') || ''});
    }
  }

  // 6. Ordem de titulos: pular nivel quebra a navegacao por cabecalho.
  let anterior = 0;
  for (const el of document.querySelectorAll('h1, h2, h3, h4, h5, h6')) {
    if (!visivel(el)) continue;
    contagem.titulos++;
    const nivel = Number(el.tagName[1]);
    if (anterior && nivel > anterior + 1) {
      achados.push({regra: 'titulo-pulado', gravidade: 'media', onde: onde(el),
        detalhe: `h${anterior} seguido de h${nivel}`, amostra: el.textContent.trim().slice(0, 40)});
    }
    anterior = nivel;
  }

  // 7. Rolagem horizontal: conteudo mais largo que a viewport.
  const largura = document.documentElement.scrollWidth;
  if (largura > window.innerWidth + 1) {
    const culpados = [...document.querySelectorAll('body *')]
      .filter(el => el.getBoundingClientRect().right > window.innerWidth + 1 && visivel(el))
      .slice(0, 3).map(onde);
    achados.push({regra: 'rolagem-horizontal', gravidade: 'alta', onde: culpados.join(', ') || 'body',
      detalhe: `${largura}px de conteúdo em ${window.innerWidth}px de tela`, amostra: ''});
  }

  return {achados, contagem};
};

const larguras = [{nome: 'desktop', width: 1280, height: 900}, {nome: 'celular', width: 375, height: 812}];
const navegador = await chromium.launch();
const todos = [];
const totais = {paginas: 0, texto: 0, alvos: 0, imagens: 0, botoes: 0, campos: 0, titulos: 0, naoMedivel: 0};
const lista = paginas().sort();

console.log(`Auditando ${lista.length} páginas em ${BASE}, em ${larguras.length} larguras\n`);
for (const {nome, width, height} of larguras) {
  const contexto = await navegador.newContext({viewport: {width, height}, reducedMotion: 'no-preference'});
  const pagina = await contexto.newPage();
  for (const arquivo of lista) {
    const resposta = await pagina.goto(`${BASE}/${arquivo}`, {waitUntil: 'load', timeout: 45000}).catch(() => null);
    if (!resposta || !resposta.ok()) {
      todos.push({pagina: arquivo, largura: nome, regra: 'nao-carregou', gravidade: 'alta',
        onde: '', detalhe: String(resposta?.status() ?? 'sem resposta'), amostra: ''});
      continue;
    }
    // O conteudo do original aparece por animacao de revelacao; medir antes dela mede o que ninguem ve.
    await pagina.waitForTimeout(700);
    const {achados, contagem} = await pagina.evaluate(MEDIR);
    if (nome === 'desktop') {
      totais.paginas++;
      for (const chave of Object.keys(contagem)) totais[chave] += contagem[chave];
    }
    todos.push(...achados.map(a => ({pagina: arquivo, largura: nome, ...a})));
  }
  await contexto.close();
}
await navegador.close();

console.log('Denominador — o que foi conferido');
console.log(`   páginas            : ${totais.paginas} (× ${larguras.length} larguras)`);
console.log(`   trechos de texto   : ${totais.texto}`);
console.log(`   alvos clicáveis    : ${totais.alvos}`);
console.log(`   imagens            : ${totais.imagens}`);
console.log(`   botões e links     : ${totais.botoes}`);
console.log(`   campos de formulário: ${totais.campos}`);
console.log(`   títulos            : ${totais.titulos}\n`);

const porRegra = {};
for (const a of todos) (porRegra[a.regra] ??= []).push(a);
const ordem = ['nao-carregou', 'contraste', 'alvo-pequeno', 'sem-nome', 'alt-ausente',
  'campo-sem-rotulo', 'rolagem-horizontal', 'titulo-pulado', 'sem-lazy'];

console.log('Achados por regra');
for (const regra of ordem) {
  const lista = porRegra[regra];
  if (!lista) continue;
  const paginasAfetadas = new Set(lista.map(a => a.pagina)).size;
  console.log(`\n   ${regra.toUpperCase()} — ${lista.length} ocorrência(s) em ${paginasAfetadas} página(s)`);
  // Uma amostra por assinatura: cinquenta paginas com o mesmo defeito sao um defeito, nao cinquenta.
  const vistos = new Set();
  for (const a of lista) {
    const chave = `${a.onde}|${a.detalhe}`;
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    if (vistos.size > 6) { console.log(`      ... e mais ${lista.length - 6} ocorrência(s)`); break; }
    console.log(`      ${a.onde} — ${a.detalhe}${a.amostra ? ` — "${a.amostra}"` : ''} [${a.largura}, ${a.pagina}]`);
  }
}

const altas = todos.filter(a => a.gravidade === 'alta').length;
console.log(`\n${'='.repeat(70)}`);
console.log(`${todos.length} achado(s): ${altas} de gravidade alta, ${todos.length - altas} média.`);
process.exit(altas > 0 ? 1 : 0);
