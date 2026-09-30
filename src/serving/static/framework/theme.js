const themes=['ocean','obsidian','forest','amber','light'];
const labels={ocean:'Océano',obsidian:'Obsidiana',forest:'Bosque',amber:'Ámbar',light:'Claro'};
function save(theme){document.documentElement.dataset.theme=theme;try{localStorage.setItem('amp-theme',theme)}catch{}}
export function initializeTheme(){
  if(!document.querySelector('#themes-style')){const style=document.createElement('link');style.id='themes-style';style.rel='stylesheet';style.href='/static/framework/themes.css';document.head.appendChild(style)}
  if(!document.querySelector('#workspace-style')){const style=document.createElement('link');style.id='workspace-style';style.rel='stylesheet';style.href='/static/framework/workspace.css';document.head.appendChild(style)}
  if(!document.querySelector('#logo-style')){const style=document.createElement('link');style.id='logo-style';style.rel='stylesheet';style.href='/static/framework/logo.css';document.head.appendChild(style)}
  let preference='ocean';
  try{preference=localStorage.getItem('amp-theme')||'ocean'}catch{}
  if(!themes.includes(preference))preference='ocean'; save(preference);
  const host=document.querySelector('.portal-header nav')||document.querySelector('.header-actions');
  if(host&&!document.querySelector('#theme-select')){
    const select=document.createElement('select'); select.id='theme-select'; select.className='theme-select';
    select.setAttribute('aria-label','Tema visual');
    select.innerHTML=themes.map(theme=>'<option value="'+theme+'">'+labels[theme]+'</option>').join('');
    select.value=preference; select.addEventListener('change',()=>save(select.value)); host.prepend(select);
  }
  document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
    const label=()=>button.setAttribute('aria-label','Cambiar tema visual');
    label(); button.addEventListener('click',()=>{const next=themes[(themes.indexOf(document.documentElement.dataset.theme)+1)%themes.length];save(next);const select=document.querySelector('#theme-select');if(select)select.value=next;label()});
  });
}
