import {initializeTheme} from './theme.js';
initializeTheme();
const portalStyle = document.createElement('link');
portalStyle.rel = 'stylesheet';
portalStyle.href = '/static/framework/portal.css';
document.head.appendChild(portalStyle);
const formulaStyle = document.createElement('link');
formulaStyle.rel = 'stylesheet';
formulaStyle.href = '/static/framework/formulas.css';
document.head.appendChild(formulaStyle);

const translations = {
  en: {'Proyecto':'Project','Metodología':'Methodology','Datos y privacidad':'Data & privacy','Abrir mi instancia ↗':'Open my instance ↗','Explorar mi instancia →':'Explore my instance →','Conocer el proceso':'See the process','EL PROYECTO':'THE PROJECT','LOOP ENGINEERING':'LOOP ENGINEERING','DATOS Y PRIVACIDAD':'DATA & PRIVACY','Observar':'Observe','Implementar':'Implement','Verificar':'Verify','Aprender':'Learn','Compartir conocimiento.':'Share knowledge.','Proteger la información.':'Protect information.'},
  pt: {'Proyecto':'Projeto','Metodología':'Metodologia','Datos y privacidad':'Dados e privacidade','Abrir mi instancia ↗':'Abrir minha instância ↗','Explorar mi instancia →':'Explorar minha instância →','Conocer el proceso':'Conhecer o processo','EL PROYECTO':'O PROJETO','LOOP ENGINEERING':'LOOP ENGINEERING','DATOS Y PRIVACIDAD':'DADOS E PRIVACIDADE','Observar':'Observar','Implementar':'Implementar','Verificar':'Verificar','Aprender':'Aprender','Compartir conocimiento.':'Compartilhar conhecimento.','Proteger la información.':'Proteger a informação.'}
};
const originalText = new WeakMap();
function translate(locale){
  document.documentElement.lang = locale === 'pt' ? 'pt' : locale === 'en' ? 'en' : 'es';
  document.querySelectorAll('a,button,h3,strong,summary,.eyebrow').forEach(node => {
    if (!originalText.has(node)) originalText.set(node,node.textContent);
    const source=originalText.get(node);
    node.textContent=(translations[locale]||{})[source]||source;
  });
  localStorage.setItem('amp-locale',locale);
}
const language = document.createElement('select');
language.className='language-select';
language.setAttribute('aria-label','Idioma / Language / Idioma');
language.innerHTML='<option value="es">ES</option><option value="en">EN</option><option value="pt">PT</option>';
language.value=localStorage.getItem('amp-locale')||'es';
language.addEventListener('change',()=>translate(language.value));
document.querySelector('.portal-header nav')?.prepend(language);
language.style.cssText='background:#102a3e;color:#edf5ff;border:1px solid #2a5368;border-radius:8px;padding:8px 10px;font-weight:700;';
translate(language.value);
const methodology=document.querySelector('#metodologia');
if(methodology){const analysis=document.createElement('div');analysis.className='analysis-grid';analysis.innerHTML='<article class="formula-card"><div class="eyebrow">MÉTRICA VERIFICABLE</div><h3>Error absoluto medio</h3><code>MAE = (1 / n) · Σ |yᵢ − ŷᵢ|</code><p>El valor se calcula sobre el conjunto de validación real. Un resultado menor indica menor error promedio, pero no prueba causalidad ni estabilidad fuera del período evaluado.</p></article><article class="signal-card positive"><h3>Señal positiva</h3><p>La evaluación mejora cuando el dataset, la división temporal, la receta y el checksum del artefacto quedan registrados en la misma ejecución.</p></article><article class="signal-card negative"><h3>Señal de alerta</h3><p>Una métrica sin procedencia, un dato simulado o una variable disponible sólo después de la predicción invalida la interpretación del resultado.</p></article></div>';methodology.appendChild(analysis)}
