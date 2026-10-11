/* Local demonstration of Jira intake. No Jira or LLM network calls are made. */
function mockTicket(input, type='story') {
  const key=String(input).trim().toUpperCase();
  if(!/^[A-Z][A-Z0-9_]*-[1-9]\d*$/.test(key)) throw new Error('Enter a Jira key such as MHEAL-104.');
  if(!['story','defect'].includes(type)) throw new Error('Choose a story or defect.');
  const defect=type==='defect';
  return {
    key, mode:'mock', type:defect?'Defect':'Story', status:'Ready for development',
    priority:defect?'High':'Medium', owner:defect?'Support engineering':'Customer experience',
    title:defect?'Require a callback number before saving a profile':'Make customer profiles easier to complete',
    description:defect?'Support cannot call customers back because the profile form accepts an empty phone number. The phone number must be required before the customer can save.':'As a customer, I want to complete my profile without sharing my date of birth, so I can save my contact details quickly. The notification banner should feel calm and welcoming.',
    criteria:defect?['Phone number is required before saving.','Saving without a phone number is blocked.','A profile with a phone number saves successfully.']:['Date of birth is optional.','The notification banner uses light blue (#E8F0FE).','The save button reads “Save changes”.'],
    steps:defect?['Open the customer profile screen.','Fill in name and email; leave phone number empty.','Save the profile. It currently succeeds without a callback number.']:[],
    requirement:defect?'Make phone number required.':'Make date of birth optional. Set the notification banner to light blue (#E8F0FE) and label the save button “Save changes”.',
  };
}
if(typeof module !== 'undefined') module.exports={mockTicket};
let jiraImportRun=0, jiraImportedTicket=null;
function jiraIntakeMarkup(){
  jiraImportRun++; jiraImportedTicket=null;
  return `<div class="intake-tabs" role="tablist" aria-label="Requirement source">
    <button type="button" role="tab" id="intake-write" aria-selected="true" aria-controls="requirement-panel" onclick="jiraIntakeTab('write')">✎ Requirement</button>
    <button type="button" role="tab" id="intake-jira" aria-selected="false" aria-controls="jira-panel" tabindex="-1" onclick="jiraIntakeTab('jira')">◆ Import from Jira <span>MOCK</span></button>
  </div><section id="jira-panel" role="tabpanel" aria-labelledby="intake-jira" hidden>
    <div class="ji-intro"><div class="ji-logo" aria-hidden="true">◆</div><div><h2>Start with the story you already have.</h2><p>Bring a Jira story or defect into a reviewable change request.</p></div></div>
    <div class="ji-disclosure"><b>Mock import · Simulated LLM</b><span>Uses sample ticket content. Any valid Jira key receives the selected sample; no connection or model call is made.</span></div>
    <div class="ji-inputs"><div class="field"><label for="jira-key">Jira issue key</label><input class="input" id="jira-key" placeholder="MHEAL-104" autocomplete="off" spellcheck="false" aria-describedby="jira-error" onkeydown="if(event.key==='Enter'){event.preventDefault();jiraReadTicket()}"></div>
    <div class="field"><label for="jira-type">Ticket type</label><select class="input" id="jira-type"><option value="story">Story · requirement</option><option value="defect">Defect · bug fix</option></select></div>
    <button type="button" class="btn primary" id="jira-read" onclick="jiraReadTicket()">Read ticket →</button></div>
    <div id="jira-error" class="err" role="alert"></div>
    <div class="ji-samples"><span>Try a sample</span><button type="button" class="btn sm" onclick="jiraSample('MHEAL-104','story')">▤ MHEAL-104 · Profile story</button><button type="button" class="btn sm" onclick="jiraSample('MHEAL-208','defect')">⊙ MHEAL-208 · Callback defect</button></div>
    <div id="jira-result" aria-live="polite"><div class="ji-empty"><span aria-hidden="true">▤ → ✦ → ✓</span><b>Your ticket, translated into a clear next step.</b><p>Preview the source, review the extracted requirement, then use it in your request.</p></div></div>
  </section>`;
}
function jiraIntakeTab(tab){
  const write=tab==='write';
  for(const [id,active] of [['intake-write',write],['intake-jira',!write]]){
    const el=document.getElementById(id); el.setAttribute('aria-selected',String(active)); el.tabIndex=active?0:-1;
  }
  document.getElementById('jira-panel').hidden=write;
  document.getElementById('requirement-panel').hidden=!write;
  document.getElementById('requirement-actions').hidden=!write;
  document.getElementById('request-grid').classList.toggle('jira-intake-open',!write);
  document.getElementById('request-live-preview').hidden=!write;
}
function jiraSample(key,type){
  document.getElementById('jira-key').value=key;document.getElementById('jira-type').value=type;jiraReadTicket();
}
async function jiraReadTicket(){
  const error=document.getElementById('jira-error'), result=document.getElementById('jira-result');
  let ticket;
  try{ ticket=mockTicket(document.getElementById('jira-key').value,document.getElementById('jira-type').value); }
  catch(e){error.textContent=e.message;document.getElementById('jira-key').setAttribute('aria-invalid','true');return;}
  error.textContent='';document.getElementById('jira-key').removeAttribute('aria-invalid');
  const run=++jiraImportRun; jiraImportedTicket=null;
  const button=document.getElementById('jira-read');button.disabled=true;
  const stages=['Reading sample ticket','Extracting requirements','Preparing your review'];
  try{
    for(let stage=0;stage<3;stage++){
      if(run!==jiraImportRun||!result.isConnected)return;
      result.innerHTML=`<div class="ji-progress" role="status"><div class="ji-orbit" aria-hidden="true">✦</div><b>${stages[stage]}…</b><span>Simulated LLM interpretation</span><div class="ji-track">${stages.map((s,i)=>`<span class="${i<=stage?'active':''}">${i<stage?'✓':i+1} ${s}</span>`).join('')}</div></div>`;
      await new Promise(resolve=>setTimeout(resolve,450));
    }
    if(run!==jiraImportRun||!result.isConnected)return;
    jiraImportedTicket=ticket;
    result.innerHTML=`<div class="ji-review"><div class="ji-ready"><span>✓ Ready to review</span><small>Mock ticket · no external changes</small></div>
    <div class="ji-columns"><section class="ji-source"><div class="ji-caption">SOURCE TICKET</div><div class="ji-meta"><b>${esc(ticket.key)}</b><span class="ji-type ${ticket.type==='Defect'?'defect':''}">${ticket.type}</span><span>${ticket.priority} priority</span></div>
      <h3>${esc(ticket.title)}</h3><p>${esc(ticket.description)}</p><div class="ji-owner">${esc(ticket.owner)} · ${esc(ticket.status)}</div>
      ${ticket.steps.length?`<h4>Steps to reproduce</h4><ol>${ticket.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>`:''}
      <h4>Acceptance criteria</h4><ul>${ticket.criteria.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></section>
    <section class="ji-extract"><div class="ji-caption">✦ SIMULATED LLM EXTRACTION</div><h3>A requirement you can refine.</h3><p>Review the interpretation before it becomes a change request.</p><label for="jira-extracted">Extracted requirement</label><textarea id="jira-extracted" class="input" rows="7">${esc(ticket.requirement)}</textarea><div class="ji-note">Jira key, ticket type, original description and acceptance criteria will be preserved in Business context.</div><button type="button" class="btn primary" onclick="jiraUseTicket()">Use this ticket →</button></section></div></div>`;
  } finally {if(button.isConnected&&run===jiraImportRun)button.disabled=false;}
}
function jiraUseTicket(){
  const ticket=jiraImportedTicket, text=document.getElementById('jira-extracted')?.value.trim();
  if(!ticket||!text){document.getElementById('jira-error').textContent='Add an extracted requirement before continuing.';return;}
  if(document.getElementById('f-eng').value.trim() && !confirm('Replace the typed requirement with this imported ticket?'))return;
  const context=`Imported from Jira ${ticket.key} · ${ticket.type} · Mock import / simulated LLM\n\n${ticket.description}\n\nAcceptance criteria:\n${ticket.criteria.map(s=>'- '+s).join('\n')}${ticket.steps.length?'\n\nSteps to reproduce:\n'+ticket.steps.map((s,i)=>`${i+1}. ${s}`).join('\n'):''}`;
  document.getElementById('f-eng').value=text;
  document.getElementById('f-title').value=`[${ticket.key}] ${ticket.title}`;
  const desc=document.getElementById('f-desc');desc.value=context+(desc.value.trim()?'\n\nAdditional context:\n'+desc.value:'');
  clearTimeout(state.engT);
  state.translation=null;state.lastTranslated=null;state.manualRules=false;state.answers=[];state.agreed=false;
  document.getElementById('f-trout').replaceChildren();document.getElementById('f-submit').disabled=false;
  jiraIntakeTab('write');document.getElementById('f-eng').focus();toast(`${ticket.key} imported — review the requirement, then preview the change`);
}
if(typeof document!=='undefined')document.addEventListener('keydown',event=>{
  if(!event.target.closest('.intake-tabs')||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  event.preventDefault();const next=event.key==='Home'?'write':event.key==='End'?'jira':event.target.id==='intake-write'?'jira':'write';
  jiraIntakeTab(next);document.getElementById(next==='write'?'intake-write':'intake-jira').focus();
});
