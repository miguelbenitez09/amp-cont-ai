const themes=['ocean','obsidian','forest','amber','light'];
const labels={ocean:'Océano',obsidian:'Obsidiana',forest:'Bosque',amber:'Ámbar',light:'Claro'};
function save(theme){document.documentElement.dataset.theme=theme;try{localStorage.setItem('amp-theme',theme)}catch{};document.querySelectorAll('[data-theme-toggle]').forEach(button=>{button.setAttribute('aria-label','Cambiar tema visual: '+labels[theme]);button.title='Tema activo: '+labels[theme]+' · clic para cambiar';button.innerHTML='<span class="theme-swatch swatch-'+theme+'"></span><span class="theme-button-label">'+labels[theme]+'</span>'})}
export function initializeTheme(){
  if(!document.querySelector('#themes-style')){const style=document.createElement('link');style.id='themes-style';style.rel='stylesheet';style.href='/static/framework/themes.css';document.head.appendChild(style)}
  if(!document.querySelector('#workspace-style')){const style=document.createElement('link');style.id='workspace-style';style.rel='stylesheet';style.href='/static/framework/workspace.css';document.head.appendChild(style)}
  if(!document.querySelector('#logo-style')){const style=document.createElement('link');style.id='logo-style';style.rel='stylesheet';style.href='/static/framework/logo.css';document.head.appendChild(style)}
  if(!document.querySelector('#controls-style')){const style=document.createElement('link');style.id='controls-style';style.rel='stylesheet';style.href='/static/framework/controls.css';document.head.appendChild(style)}
  const cards=document.querySelector('link[href*="/static/css/cards.css"]');
  if(cards)document.head.appendChild(cards);
  let preference='ocean';
  try{preference=localStorage.getItem('amp-theme')||'ocean'}catch{}
  if(!themes.includes(preference))preference='ocean'; save(preference);
  const landingSelect = document.querySelector('#landing-theme-select');
  if(landingSelect){
    landingSelect.value=preference;
    landingSelect.addEventListener('change',()=>save(landingSelect.value));
  } else {
    const host=document.querySelector('.header-actions');
    if(host&&!document.querySelector('#theme-select')){
      const select=document.createElement('select'); select.id='theme-select'; select.className='theme-select';
      select.setAttribute('aria-label','Tema visual');
      select.innerHTML=themes.map(theme=>'<option value="'+theme+'">'+labels[theme]+'</option>').join('');
      select.value=preference; select.addEventListener('change',()=>save(select.value)); host.prepend(select);
    }
  }
  document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
    const label=()=>{const current=document.documentElement.dataset.theme;button.setAttribute('aria-label','Cambiar tema visual: '+labels[current]);button.title='Tema activo: '+labels[current]+' · clic para cambiar';button.innerHTML='<span class="theme-swatch swatch-'+current+'"></span><span class="theme-button-label">'+labels[current]+'</span>'};
    button.classList.add('theme-cycle'); label(); button.addEventListener('click',()=>{const next=themes[(themes.indexOf(document.documentElement.dataset.theme)+1)%themes.length];save(next);const select=document.querySelector('#landing-theme-select')||document.querySelector('#theme-select');if(select)select.value=next;label()});
  });
}
