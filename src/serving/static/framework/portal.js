import {initializeTheme} from './theme.js';
initializeTheme();
if (!document.querySelector('link[href*="portal.css"]')) {
  const portalStyle = document.createElement('link');
  portalStyle.rel = 'stylesheet';
  portalStyle.href = '/static/framework/portal.css';
  document.head.appendChild(portalStyle);
}
if (!document.querySelector('link[href*="formulas.css"]')) {
  const formulaStyle = document.createElement('link');
  formulaStyle.rel = 'stylesheet';
  formulaStyle.href = '/static/framework/formulas.css';
  document.head.appendChild(formulaStyle);
}

const translations = {
  en: {
    'Capacidades': 'Capabilities',
    'Puertos & Canal': 'Ports & Canal',
    'Proyecto & Visión': 'Project & Vision',
    'Metodología MLOps': 'MLOps Methodology',
    'Arancel SAC & Datos': 'SAC Tariff & Data',
    'Abrir mi instancia': 'Open my instance',
    'Abrir mi instancia ↗': 'Open my instance ↗',
    'Entrar a la Estación de Trabajo Operativa (/app) →': 'Enter Operational Workstation (/app) →',
    'Explorar Análisis Macroeconómico & Aranceles 📊': 'Explore Macroeconomic Analysis & Tariffs 📊',
    'Ver Metodología Científica & MLOps 🔬': 'View Scientific Methodology & MLOps 🔬',
    'DEL DATO A LA DECISIÓN': 'FROM DATA TO DECISION',
    'EL PROYECTO': 'THE PROJECT',
    'LOOP ENGINEERING': 'LOOP ENGINEERING',
    'DATOS Y PRIVACIDAD': 'DATA & PRIVACY',
    'Observar': 'Observe',
    'Implementar': 'Implement',
    'Verificar': 'Verify',
    'Aprender': 'Learn',
    'Compartir conocimiento.': 'Share knowledge.',
    'Proteger la información.': 'Protect information.',
    '5 Puertos de Transbordo': '5 Transshipment Ports',
    '27,716 Fracciones SAC': '27,716 SAC Tariff Lines',
    'Inferencia Cuantiles P10/P50/P90': 'Quantile Inference P10/P50/P90',
    'Libro Mayor WORM Inmutable': 'Immutable WORM Ledger'
  },
  pt: {
    'Capacidades': 'Capacidades',
    'Puertos & Canal': 'Portos & Canal',
    'Proyecto & Visión': 'Projeto & Visão',
    'Metodología MLOps': 'Metodologia MLOps',
    'Arancel SAC & Datos': 'Tarifa SAC & Dados',
    'Abrir mi instancia': 'Abrir minha instância',
    'Abrir mi instancia ↗': 'Abrir minha instância ↗',
    'Entrar a la Estación de Trabajo Operativa (/app) →': 'Entrar na Estação de Trabalho Operacional (/app) →',
    'Explorar Análisis Macroeconómico & Aranceles 📊': 'Explorar Análise Macroeconômica & Tarifas 📊',
    'Ver Metodología Científica & MLOps 🔬': 'Ver Metodologia Científica & MLOps 🔬',
    'DEL DATO A LA DECISIÓN': 'DO DADO À DECISÃO',
    'EL PROYECTO': 'O PROJETO',
    'LOOP ENGINEERING': 'LOOP ENGINEERING',
    'DATOS Y PRIVACIDAD': 'DADOS E PRIVACIDADE',
    'Observar': 'Observar',
    'Implementar': 'Implementar',
    'Verificar': 'Verificar',
    'Aprender': 'Aprender',
    'Compartir conocimiento.': 'Compartilhar conhecimento.',
    'Proteger la información.': 'Proteger a informação.',
    '5 Puertos de Transbordo': '5 Portos de Transbordo',
    '27,716 Fracciones SAC': '27.716 Linhas SAC',
    'Inferencia Cuantiles P10/P50/P90': 'Inferência de Quantis P10/P50/P90',
    'Libro Mayor WORM Inmutable': 'Livro-Razão WORM Imutável'
  }
};
const originalText = new WeakMap();
function translate(locale){
  document.documentElement.lang = locale === 'pt' ? 'pt' : locale === 'en' ? 'en' : 'es';
  document.querySelectorAll('a,button,h3,strong,summary,.eyebrow,.pill-tag').forEach(node => {
    if (!originalText.has(node)) originalText.set(node, node.textContent.trim());
    const source = originalText.get(node);
    if ((translations[locale]||{})[source]) {
      node.textContent = translations[locale][source];
    }
  });
  localStorage.setItem('amp-locale', locale);
}

const landingLangSelect = document.querySelector('#landing-lang-select');
if (landingLangSelect) {
  landingLangSelect.value = localStorage.getItem('amp-locale') || 'es';
  landingLangSelect.addEventListener('change', () => translate(landingLangSelect.value));
  translate(landingLangSelect.value);
} else {
  const host = document.querySelector('.portal-header nav') || document.querySelector('.header-actions');
  if (host && !document.querySelector('.language-select')) {
    const language = document.createElement('select');
    language.className = 'language-select';
    language.setAttribute('aria-label', 'Idioma / Language / Idioma');
    language.innerHTML = '<option value="es">ES</option><option value="en">EN</option><option value="pt">PT</option>';
    language.value = localStorage.getItem('amp-locale') || 'es';
    language.addEventListener('change', () => translate(language.value));
    host.prepend(language);
    translate(language.value);
  }
}

