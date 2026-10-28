'use strict';
const slides=[...document.querySelectorAll('.slide')];
const stage=document.getElementById('stage'), viewport=document.getElementById('viewport');
const prev=document.getElementById('prev'), next=document.getElementById('next');
const count=document.getElementById('count'),bar=document.getElementById('bar');
const toc=document.getElementById('toc'), helpDialog=document.getElementById('helpDialog'), licenseDialog=document.getElementById('licenseDialog');
let current=-1;
function fit(){if(innerWidth<=700){stage.style.transform='none';return;}const scale=Math.min(viewport.clientWidth/1440,viewport.clientHeight/810);stage.style.transform=`scale(${scale})`;}
function go(n){n=Math.max(0,Math.min(slides.length-1,n));if(n===current)return;slides.forEach((s,i)=>{s.classList.toggle('active',i===n);s.setAttribute('aria-hidden',i===n?'false':'true');s.inert=i!==n;});current=n;count.textContent=String(n+1).padStart(2,'0');bar.style.width=((n+1)/slides.length*100)+'%';prev.disabled=n===0;next.disabled=n===slides.length-1;viewport.scrollTop=0;document.querySelectorAll('[data-slide]').forEach(b=>b.classList.toggle('current',Number(b.dataset.slide)===n));history.replaceState(null,'',`#slide-${n+1}`);document.title=`${n+1}/40 · ${slides[n].querySelector('h1').textContent} · QA agentizada`;}
function fromHash(){const m=location.hash.match(/^#slide-(\d+)$/);return m?Number(m[1])-1:0;}
function openDialog(d){d.showModal();}
function closeAll(){[toc,helpDialog,licenseDialog].forEach(d=>{if(d.open)d.close();});}
async function fullscreen(){try{if(document.fullscreenElement){await document.exitFullscreen();}else if(document.documentElement.requestFullscreen){await document.documentElement.requestFullscreen();}else{showStatus('Usá la opción de pantalla completa de tu navegador.');}}catch{showStatus('La pantalla completa no está disponible. Podés activarla desde el menú del navegador.');}}
function showStatus(t){const s=document.getElementById('status');s.textContent=t;s.classList.add('shown');setTimeout(()=>s.classList.remove('shown'),5000);}
prev.addEventListener('click',()=>go(current-1));next.addEventListener('click',()=>go(current+1));
document.getElementById('index').addEventListener('click',()=>openDialog(toc));document.getElementById('help').addEventListener('click',()=>openDialog(helpDialog));document.getElementById('full').addEventListener('click',fullscreen);
document.querySelectorAll('[data-slide]').forEach(b=>b.addEventListener('click',()=>{toc.close();go(Number(b.dataset.slide));}));document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));document.querySelector('[data-license]').addEventListener('click',()=>openDialog(licenseDialog));
[toc,helpDialog,licenseDialog].forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
document.addEventListener('keydown',e=>{if([toc,helpDialog,licenseDialog].some(d=>d.open))return;const interactive=e.target.closest('button,a,input,textarea,select');if(interactive&&[' ','Enter'].includes(e.key))return;if(e.ctrlKey||e.altKey||e.metaKey)return;switch(e.key){case 'ArrowRight':case 'PageDown':case ' ':e.preventDefault();go(current+1);break;case 'ArrowLeft':case 'PageUp':e.preventDefault();go(current-1);break;case 'Home':e.preventDefault();go(0);break;case 'End':e.preventDefault();go(slides.length-1);break;case 'i':case 'I':e.preventDefault();openDialog(toc);break;case 'f':case 'F':e.preventDefault();fullscreen();break;case '?':openDialog(helpDialog);break;}});
window.addEventListener('resize',fit);window.addEventListener('hashchange',()=>go(fromHash()));document.addEventListener('fullscreenchange',()=>{fit();const f=document.getElementById('full');f.setAttribute('aria-label',document.fullscreenElement?'Salir de pantalla completa':'Activar pantalla completa');});
// Public hooks support navigation and local QA without network or imports.
window.presentation={go,get current(){return current;},count:slides.length};
go(fromHash());fit();document.fonts.ready.then(fit);
