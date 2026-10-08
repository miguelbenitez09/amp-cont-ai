/* The server owns workflow state; this guard cannot grant permissions. */
document.addEventListener('DOMContentLoaded', () => {
 "use strict";
 const mandatory=()=>!!window.activeSession?.user?.must_change_password;
 const originalClose=window.closeAuthModal;
 window.closeAuthModal=function(){if(mandatory()){enforce();return;}return originalClose?.();};
 const originalSync=window.syncSessionUI;
 let enforcing=false;
 let workflowRequest=false;
 let operationCapabilities=null;
 let capabilityActor=null;
 const tabCapabilities={'tab-cot-swarm':'agents.write','tab-customs-lakehouse':'datasets.read','tab-forecast':'forecast.read',
  'tab-benchmark':'models.read','tab-diagnostics':'models.read','tab-simulation':'simulation.run',
  'tab-data-platform':'datasets.read','tab-security-iam':'audit.read'};
 function applyRoleInterface(){
  if(!window.activeSession?.user){operationCapabilities=null;capabilityActor=null;delete document.body.dataset.roleReady;for(const element of document.querySelectorAll('.tabs-nav > .tab-btn,.overview-nav-card'))element.hidden=false;return;}
  if(capabilityActor!==window.activeSession.user.username){operationCapabilities=null;delete document.body.dataset.roleReady;}
  if(!operationCapabilities){for(const button of document.querySelectorAll('.tabs-nav > .tab-btn'))button.hidden=!!tabCapabilities[button.dataset.tab];return;}
  const actor=document.getElementById('sim-user-select');if(actor){actor.replaceChildren(new Option(window.activeSession.user.username,window.activeSession.user.username));actor.disabled=true;actor.title='La identidad de ejecución procede de la sesión autenticada.';}
  for(const button of document.querySelectorAll('.tabs-nav > .tab-btn')){
   const cap=tabCapabilities[button.dataset.tab];button.hidden=!!cap&&!operationCapabilities.includes(cap);
   if(button.dataset.tab==='tab-security-iam')button.hidden=!operationCapabilities.includes('audit.read')&&!operationCapabilities.includes('iam.write');
   if(button.hidden&&button.classList.contains('active'))document.querySelector('[data-tab="tab-landing"]')?.click();
  }
  for(const card of document.querySelectorAll('.overview-nav-card')){
   const target=card.getAttribute('onclick')?.match(/data-tab=(tab-[a-z-]+)/)?.[1];
   const button=target&&document.querySelector(`[data-tab="${target}"]`);if(button)card.hidden=button.hidden;
  }
 }
 async function resumeWorkflow(){
  if(workflowRequest||!window.activeSession?.user||mandatory())return;
  workflowRequest=true;
  const actor=window.activeSession.user.username;
  try{
   const response=await fetch('/api/workspace/session');const state=await response.json();
   if(window.activeSession?.user?.username!==actor)return;
   if(response.ok&&state.authenticated){capabilityActor=actor;operationCapabilities=state.capabilities;applyRoleInterface();document.body.dataset.roleReady='true';}
   if(response.ok&&state.authenticated&&!state.user.must_change_password&&state.workflow.current_step!=='ready')location.replace('/static/workspace/index.html');
  }catch(error){console.warn('No se pudo comprobar la etapa de configuración.',error.message);}
  finally{workflowRequest=false;}
 }
 function enforce(){
  if(enforcing)return;
  enforcing=true;
  const blocked=mandatory();
  document.body.classList.toggle('password-rotation-required',blocked);
  const modal=document.getElementById('auth-iam-modal');
  if(blocked&&modal){
   modal.classList.add('open');Object.assign(modal.style,{display:'flex',visibility:'visible',opacity:'1',pointerEvents:'auto'});
   window.switchAuthTab?.('atab-password');
   const status=document.getElementById('pwd-change-status');
   if(status&&!status.textContent.includes('Error'))status.textContent='Cambio obligatorio pendiente. Completa este paso o cierra la sesiÃ³n; cerrar la ventana no habilita el acceso.';
   modal.querySelectorAll('.modal-close').forEach(button=>{button.disabled=true;button.title='Cambia la contraseÃ±a o cierra la sesiÃ³n';});
   if(!document.getElementById('mandatory-logout')){
    const logout=document.createElement('button');logout.id='mandatory-logout';logout.type='button';logout.className='btn btn-secondary';logout.textContent='Cerrar sesiÃ³n';logout.onclick=()=>window.executeLogout?.();
    document.getElementById('atab-password')?.append(logout);
   }
   window.focusPortOpsAuthDialog?.();
  }else if(modal){modal.querySelectorAll('.modal-close').forEach(button=>button.disabled=false);}
  const link=document.getElementById('workspace-access');
  if(link){link.hidden=!window.activeSession?.user;link.setAttribute('aria-disabled',String(blocked));}
  enforcing=false;
  applyRoleInterface();
  resumeWorkflow();
 }
 window.syncSessionUI=function(){originalSync?.();enforce();};
 window.openFirstRunModal=()=>location.assign('/static/workspace/index.html');
 document.addEventListener('click',event=>{if(event.target.closest('#btn-settings-gear')&&window.activeSession?.user&&!mandatory()){event.preventDefault();event.stopImmediatePropagation();location.assign('/static/workspace/index.html');}},true);
 document.addEventListener('click',event=>{const button=event.target.closest('.tab-btn');if(!button||!window.activeSession?.user)return;if(button.hidden){event.preventDefault();event.stopImmediatePropagation();return;}if(button.dataset.tab==='tab-security-iam'&&!mandatory()){event.preventDefault();event.stopImmediatePropagation();location.assign('/static/workspace/index.html#'+(operationCapabilities?.includes('audit.read')?'security':'identity'));}},true);
 const activate=window.activateAuthenticatedSession;
 window.activateAuthenticatedSession=async function(...args){await activate?.(...args);await window.refreshPortOpsSession?.();enforce();};
 const change=window.executeChangePassword;
 window.executeChangePassword=async function(...args){await change?.(...args);await window.refreshPortOpsSession?.();enforce();};
 const authTab=window.switchAuthTab;
 window.switchAuthTab=function(id){return authTab?.(mandatory()?'atab-password':id);};
 enforce();
});
