'use strict';
const slides=[...document.querySelectorAll('.slide')];
const links=[...document.querySelectorAll('.slide-links a')];
const port=new URLSearchParams(location.search).get('appPort');
const appPort=port&&/^\d+$/.test(port)&&Number(port)>0&&Number(port)<65536?port:'8000';
document.querySelector('#back').href=`index.html?appPort=${appPort}#0`;
document.querySelector('.brand').href=`index.html?appPort=${appPort}#0`;
document.querySelector('#workflow').href=`http://localhost:${appPort}/workflow-map`;
document.querySelector('#app').href=`http://localhost:${appPort}/agents`;
let current=0;
function show(){const value=Number(location.hash.slice(1));current=Number.isInteger(value)&&value>=1&&value<=slides.length?value-1:0;slides.forEach((s,i)=>{s.hidden=i!==current;});links.forEach((l,i)=>{if(i===current)l.setAttribute('aria-current','page');else l.removeAttribute('aria-current');});document.querySelector('#position').textContent=`${current+1} / ${slides.length}`;document.querySelector('#previous').disabled=current===0;document.querySelector('#next').disabled=current===slides.length-1;document.title=`MobileHeal · Pitch ${current+1} of 5`;window.scrollTo({top:0,behavior:'instant'});}
function move(delta){const next=current+delta;if(next>=0&&next<slides.length){location.hash=String(next+1);window.scrollTo({top:0,behavior:'instant'});}}
document.querySelector('#previous').addEventListener('click',()=>move(-1));document.querySelector('#next').addEventListener('click',()=>move(1));document.addEventListener('keydown',e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.target.closest('input,textarea,select'))return;if(e.key==='ArrowRight'){e.preventDefault();move(1);}if(e.key==='ArrowLeft'){e.preventDefault();move(-1);}});window.addEventListener('hashchange',show);show();
