const test = require('node:test');
const assert = require('node:assert/strict');
const {mockTicket} = require('../app/static/jira-import.js');
test('normalizes Jira keys and returns an editable story requirement',()=>{
 const t=mockTicket(' mheal-104 ','story');
 assert.equal(t.key,'MHEAL-104'); assert.equal(t.type,'Story');
 assert.match(t.requirement,/date of birth/i); assert.ok(t.criteria.length);
});
test('defects include reproduction steps and a corrective requirement',()=>{
 const t=mockTicket('MHEAL-208','defect');
 assert.equal(t.type,'Defect'); assert.ok(t.steps.length); assert.match(t.requirement,/phone/i);
});
test('invalid keys and unsupported types are rejected',()=>{
 for(const key of ['', '104', 'MH-0', '<script>-12']) assert.throws(()=>mockTicket(key,'story'));
 assert.throws(()=>mockTicket('MH-1','other'));
});
test('each import is independent and explicitly simulated',()=>{
 const a=mockTicket('TEAM-42','story'); a.criteria.push('edit');
 const b=mockTicket('TEAM-42','story'); assert.ok(!b.criteria.includes('edit')); assert.equal(b.mode,'mock');
});
