const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../app/static/workflow.html'),'utf8');
const context=vm.createContext({state:{info:{live_spec:'name: required'},tests:null},esc:s=>String(s??'').replaceAll('<','&lt;'),isInc:cr=>cr.kind==='incident'});
vm.runInContext(html.slice(html.indexOf('function md(src)'),html.indexOf('/* ---------------- sync hub')),context);
vm.runInContext(html.slice(html.indexOf('function headerActions(cr)'),html.indexOf('function headerActions(cr)')+html.slice(html.indexOf('function headerActions(cr)')).indexOf('\nfunction ')),context);
const cr={id:1,kind:'incident',status:'pr_open',tested:true,pr:{number:1,branch:'fix',base:'main',git:true},stats:{files:1,additions:1,deletions:1},checks_summary:{fail:0},branch_state:{up_to_date:false,changed_files:['android/app/src/main/java/com/mobileheal/app/MainActivity.kt']}};
test('stale incident exposes Update branch and disables merge',()=>{
 const out=context.tPR(cr);
 assert.match(out,/Update branch/);
 assert.match(out,/disabled[^>]*onclick="merge\(\)"/);
 assert.match(out,/MainActivity.kt/);
});
test('fresh incident permits the existing merge flow',()=>{
 const out=context.tPR({...cr,branch_state:{up_to_date:true,changed_files:[]}});
 assert.doesNotMatch(out,/Update branch/);
 assert.doesNotMatch(out,/disabled[^>]*onclick="merge\(\)"/);
});

test('incident header offers regeneration instead of a stale merge shortcut',()=>{
 assert.match(context.headerActions(cr),/Update branch/);
 assert.doesNotMatch(context.headerActions(cr),/Merge fix/);
});

vm.runInContext(html.slice(html.indexOf('async function markTested('),html.indexOf('\nasync function merge()',html.indexOf('async function markTested('))),context);
test('saving test results retains current source freshness before rendering',async()=>{
 context.state.cr=cr;
 context.act=async(fn)=>fn();
 context.api=async(url,options)=>options ? {...cr,branch_state:undefined} : cr;
 context.refreshList=async()=>{};
 context.renderCR=()=>assert.equal(context.state.cr.branch_state.up_to_date,false);
 await context.markTested(true,false,'verified');
 assert.match(context.headerActions(context.state.cr),/Update branch/);
});
