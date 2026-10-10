'use strict';
(()=>{
const NS='http://www.w3.org/2000/svg';
const sources=['New change request','Firebase crash','Issue email','Internal Jira defect','BA new requirement'];
const defs=[...sources.map((s,i)=>({id:'source'+i,x:25,y:40+i*97,w:180,label:s,sub:i===0?'User-submitted signal':'Mock connector · unconfigured',icon:['↗','⌁','✉','◇','＋'][i]})),
{id:'intake',x:275,y:235,w:150,label:'Intake & classify',sub:'Normalize signal · assign owner',icon:'≡'},
{id:'diagnose',x:475,y:235,w:170,label:'Requirements & diagnosis',sub:'Context · scope · root cause',icon:'⌕'},
{id:'plan',x:700,y:235,w:145,label:'Design & plan',sub:'Proposed change · acceptance',icon:'▧'},
{id:'implement',x:905,y:235,w:175,label:'Implement',sub:'Isolated local change',icon:'⌘'},
{id:'correct',x:850,y:375,w:180,label:'Correctness reviewer',sub:'Independent agent · behavior',icon:'✓'},
{id:'security',x:595,y:375,w:180,label:'Security reviewer',sub:'Independent agent · risk',icon:'◇'},
{id:'qa',x:340,y:375,w:180,label:'QA reviewer',sub:'Independent agent · coverage',icon:'◎'},
{id:'join',x:595,y:500,w:180,label:'Join review results',sub:'All three must pass',icon:'⋈'},
{id:'tests',x:275,y:650,w:180,label:'Run tests',sub:'Checks · regression evidence',icon:'▷'},
{id:'approval',x:475,y:650,w:180,label:'Human approval',sub:'Review evidence · decide',icon:'♙',gate:true},
{id:'merge',x:700,y:650,w:180,label:'LOCAL merge',sub:'Approved change in local repo',icon:'⑂'},
{id:'monitor',x:905,y:650,w:180,label:'Monitor',sub:'Mock signals · follow-up',icon:'⌁'}];
const nodeMap=Object.fromEntries(defs.map(n=>[n.id,n]));
function element(tag,attrs,parent,text){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text)e.textContent=text;parent.appendChild(e);return e;}
const edges=document.querySelector('#edges'),nodes=document.querySelector('#nodes');
const paths=[];
function path(d,rework=false){paths.push(element('path',{d,class:'edge'+(rework?' rework':'')},edges));}
defs.slice(0,5).forEach(n=>path(`M205 ${n.y+33} H240 V268 H275`));
path('M425 268 H475');path('M645 268 H700');path('M845 268 H905');
path('M992 301 V345 H940 V375');path('M992 345 H685 V375');path('M685 345 H430 V375');
path('M940 441 V478 H685 V500');path('M685 441 V500');path('M430 441 V478 H685 V500');
path('M685 566 V600 H365 V650');path('M455 683 H475');path('M655 683 H700');path('M880 683 H905');
path('M775 533 H1092 V268 H1080',true);path('M275 683 H250 V757 H1118 V268 H1080',true);
element('text',{x:805,y:522,class:'rework-label'},edges,'Review failure → rework');element('text',{x:650,y:776,class:'rework-label'},edges,'Test failure → revise implementation');
for(const n of defs){const g=element('g',{class:'node'+(n.gate?' gate':''),id:n.id},nodes);element('rect',{x:n.x,y:n.y,width:n.w,height:66,rx:10},g);element('text',{x:n.x+13,y:n.y+24,class:'icon'},g,n.icon);element('text',{x:n.x+13,y:n.y+43,class:'label'},g,n.label);element('text',{x:n.x+13,y:n.y+57,class:'sub'},g,n.sub);}
const labels=[[25,20,'01  SIGNALS'],[275,213,'02  UNDERSTAND & BUILD'],[340,326,'03  PARALLEL INDEPENDENT REVIEW'],[275,630,'04  VERIFY & DECIDE']];labels.forEach(([x,y,t])=>element('text',{x,y,class:'section-label'},nodes,t));
const stages=[['source0','Starting signal','A mock starting signal enters the workflow.'],['intake','Signal received','The sample normalizes the signal and classifies its intent, urgency, and owner.'],['diagnose','Build a shared understanding','An agent gathers requirements and diagnosis evidence to define a bounded change.'],['plan','Make the change reviewable','Design, implementation steps, and acceptance criteria become a concrete plan.'],['implement','Implement in isolation','The sample agent makes a local change with a clear record of its reasoning.'],['correct security qa','Three independent perspectives','Correctness, security, and QA reviewers work in parallel. Each evaluates the change independently.'],['join','Every review must pass','The review gate joins all three results. A failure sends the change back to implementation.'],['tests','Verify the behavior','Tests and regression checks provide evidence. Failed checks return to implementation.'],['approval','A human makes the decision','The sample simulates approval. In a real run, a human must review the evidence before merge.'],['merge','Merge locally','The approved sample change merges into a local repository. This is not a production deployment.'],['monitor','Close the loop','Mock monitoring looks for follow-up signals that can start another work item.']];
let selected=0,index=-1,timer=null,running=false,reworked=false,returning=false;const scenario=document.querySelector('#scenario');const sourceDetails=['Clarify the requested change, scope, and acceptance criteria.','Inspect the mock Firebase stack trace, affected build, and reproduction conditions.','Extract the reported symptoms, impact, and reproduction steps from the mock issue email.','Inspect the mock Jira defect, linked acceptance criteria, and reproduction evidence.','Translate the business analyst’s requirement into behavior, constraints, and acceptance criteria.'];const play=document.querySelector('#play'),staticBox=document.querySelector('#static');const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;staticBox.checked=reduced;
function stop(){clearTimeout(timer);timer=null;running=false;play.innerHTML=index>=stages.length-1?'Replay sample <span>↻</span>':index<0?'Start sample <span>▶</span>':'Continue <span>▶</span>';}
function render(){play.disabled=staticBox.checked;document.querySelector('#replay').disabled=staticBox.checked;document.querySelector('.run-panel').classList.toggle('is-empty',index<0);defs.forEach(n=>document.getElementById(n.id).classList.remove('active','done'));document.getElementById('source'+selected).classList.add(index>=0?'done':'active');for(let i=0;i<=index;i++)(i===0?'source'+selected:stages[i][0]).split(' ').forEach(id=>document.getElementById(id).classList.add(i===index?'active':'done'));const stage=stages[index];document.querySelector('#step-title').textContent=stage?(index===0?sources[selected]+' received':stage[1]):'Ready when you are.';document.querySelector('#step-detail').textContent=stage?(index===2?sourceDetails[selected]:stage[2]):'Choose a signal and start the sample to explore each checkpoint.';document.querySelector('#counter').textContent=`${index<0?0:index+1} / 11 checkpoints`;document.querySelector('#progress-fill').style.width=((index<0?0:index+1)/11*100)+'%';}
function tick(){if(staticBox.checked){stop();return;}if(returning){returning=false;index=5;paths.forEach(p=>p.classList.remove('branch-active'));}else if(!reworked&&((scenario.value==='review'&&index===6)||(scenario.value==='test'&&index===7))){reworked=true;returning=true;index=4;render();paths[paths.length-(scenario.value==='review'?2:1)].classList.add('branch-active');document.querySelector('#step-title').textContent=scenario.value==='review'?'Review gate failed → rework':'Test gate failed → rework';document.querySelector('#step-detail').textContent='This mock scenario returns to implementation to revise the change, then repeats the required verification.';timer=setTimeout(tick,2800);return;}else{if(index>=stages.length-1){stop();return;}index++;}render();running=true;play.innerHTML='Pause <span>Ⅱ</span>';timer=setTimeout(tick,2800);}
function reset(){stop();index=staticBox.checked?stages.length-1:-1;reworked=false;returning=false;paths.forEach(p=>p.classList.remove('branch-active'));render();}
scenario.addEventListener('change',reset);
play.addEventListener('click',()=>{if(running){stop();return;}if(index>=stages.length-1){reset();}tick();});
document.querySelector('#replay').addEventListener('click',()=>{reset();tick();});
document.querySelectorAll('[data-source]').forEach(b=>b.addEventListener('click',()=>{reset();selected=Number(b.dataset.source);index=staticBox.checked?stages.length-1:-1;document.querySelectorAll('[data-source]').forEach(s=>{s.classList.toggle('selected',s===b);s.setAttribute('aria-pressed',String(s===b));});render();}));
staticBox.addEventListener('change',()=>{reset();if(staticBox.checked){document.querySelector('#step-title').textContent='The complete workflow';document.querySelector('#step-detail').textContent='Explore the full path at rest. Every independent review and test must pass; human approval precedes a local merge.';}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&running)stop();});
render();if(reduced){index=stages.length-1;render();}
})();
