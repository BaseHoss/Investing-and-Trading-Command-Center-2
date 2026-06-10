#!/usr/bin/env python3
"""One-shot Explorer dropdown patch (2.6.0): per-row add/remove (fixed 6 each), selection
persisted in localStorage, drawn from the full position pool; CLASSMAP for the 20-name
universe. Playbook/consultant already iterate the full pool. Idempotent + self-verifying."""
import json, sys
t = open('dashboard_template_beta.html').read()
def rep(o, n, tag):
    global t
    if o in t: t = t.replace(o, n); print('ok', tag)
    elif n in t: print('already', tag)
    else: print('FAIL anchor', tag); sys.exit(1)

rep('.exprow{display:grid;grid-template-columns:64px 1fr;gap:8px;margin-top:8px;align-items:center}',
    '.exprow{display:grid;grid-template-columns:64px 1fr 92px;gap:8px;margin-top:8px;align-items:center}'
    '.rowadd{display:flex;align-items:center}'
    '.rowadd select{width:100%;background:var(--card2);border:1px solid var(--line);color:var(--muted);border-radius:9px;padding:7px 6px;font-size:10.5px;font-weight:800;font-family:var(--font);cursor:pointer}'
    '.rowadd select:disabled{opacity:.4;cursor:not-allowed}'
    '.aset-x{position:absolute;top:2px;right:4px;border:0;background:transparent;color:var(--muted);font-size:13px;font-weight:800;line-height:1;cursor:pointer;padding:0 2px;opacity:.55}'
    '.aset-x:hover{opacity:1;color:var(--red)}', 'css-exprow')

rep('.aset{border:1px solid var(--line);background:var(--card2);border-radius:10px;padding:7px 9px;cursor:pointer;text-align:left;transition:.12s;min-width:0;min-height:56px;',
    '.aset{border:1px solid var(--line);background:var(--card2);border-radius:10px;padding:7px 9px;cursor:pointer;text-align:left;transition:.12s;position:relative;min-width:0;min-height:56px;', 'css-aset-rel')

rep('function asetChip(x){const up=x.day>=0;',
    r'''function asetChip(x,row){const up=x.day>=0;const xb=row?'<button class="aset-x" title="remove" onclick="event.stopPropagation();explRemove('+row+',\''+x.id+'\')">×</button>':'';''', 'asetchip-sig')
rep('''return '<div class="aset '+cls+'" data-id="'+x.id+'"><div class="t">''',
    '''return '<div class="aset '+cls+'" data-id="'+x.id+'">'+xb+'<div class="t">''', 'asetchip-x')

old_render = '''document.getElementById('assets-live').innerHTML=LIVE.slice(0,6).map(id=>asetChip({...A[id],live:true,ref:false})).join('');
document.getElementById('assets-quote').innerHTML=[...LIVE.slice(6).map(id=>({...A[id],live:true,ref:false})),...Q.map(q=>({...q,live:false,ref:false})),...GCCREF].map(asetChip).join('');'''
new_render = r'''const POOL=[].concat(LIVE.map(function(id){return Object.assign({},A[id],{live:true,ref:false});}),Q.map(function(q){return Object.assign({},q,{live:false,ref:false});}),GCCREF.map(function(g){return Object.assign({},g,{live:false,ref:true});}));
function poolById(id){for(var i=0;i<POOL.length;i++){if(POOL[i].id===id)return POOL[i];}return null;}
var DEF1=['NVDA','MSFT','AAPL','AMZN','META','GOOGL'];
var DEF2=['SPY','QQQ','DIA','GOLD','SILVER','BTC'];
function loadSel(k,def){try{var v=JSON.parse(localStorage.getItem(k));if(v&&v.length){v=v.filter(poolById);if(v.length)return v.slice(0,6);}}catch(e){}return def.filter(poolById).slice(0,6);}
var SEL=[loadSel('beta_expl1',DEF1),loadSel('beta_expl2',DEF2)];
function saveSel(){try{localStorage.setItem('beta_expl1',JSON.stringify(SEL[0]));localStorage.setItem('beta_expl2',JSON.stringify(SEL[1]));}catch(e){}}
function renderExplorer(){[1,2].forEach(function(row){var ids=SEL[row-1];var el=document.getElementById(row===1?'assets-live':'assets-quote');el.innerHTML=ids.map(function(id){var x=poolById(id);return x?asetChip(x,row):'';}).join('');var used={};SEL[0].concat(SEL[1]).forEach(function(i){used[i]=1;});var opts=['<option value="">+ add</option>'];POOL.forEach(function(p){if(!used[p.id])opts.push('<option value="'+p.id+'">'+p.id+(p.name?' · '+p.name:'')+'</option>');});var s=document.getElementById('add-'+row);if(s){s.innerHTML=opts.join('');s.disabled=ids.length>=6;}});document.querySelectorAll('#assets-live .aset, #assets-quote .aset').forEach(function(e){e.onclick=function(){window.pick(e.dataset.id);};});syncSel();}
window.explAdd=function(row,id){if(!id)return;if(SEL[row-1].length>=6)return;if(SEL[0].indexOf(id)>=0||SEL[1].indexOf(id)>=0)return;SEL[row-1].push(id);saveSel();renderExplorer();};
window.explRemove=function(row,id){SEL[row-1]=SEL[row-1].filter(function(x){return x!==id;});saveSel();renderExplorer();};'''
rep(old_render, new_render, 'render-block')

rep('''document.querySelectorAll('.aset').forEach(e=>e.onclick=()=>window.pick(e.dataset.id));''',
    'renderExplorer();', 'bind-line')

rep('<div class="exprow"><div class="rowlab"><b>STOCKS</b><span>&amp; semis</span></div><div class="aset6" id="assets-live"></div></div>',
    '<div class="exprow"><div class="rowlab"><b>STOCKS</b><span>&amp; semis</span></div><div class="aset6" id="assets-live"></div><div class="rowadd"><select id="add-1" onchange="explAdd(1,this.value)"></select></div></div>', 'html-row1')
rep('<div class="exprow"><div class="rowlab"><b>MARKETS</b><span>index, gold, crypto</span></div><div class="aset6" id="assets-quote"></div></div>',
    '<div class="exprow"><div class="rowlab"><b>MARKETS</b><span>index, gold, crypto</span></div><div class="aset6" id="assets-quote"></div><div class="rowadd"><select id="add-2" onchange="explAdd(2,this.value)"></select></div></div>', 'html-row2')

rep("const CLASSMAP={NVDA:'growth_tech',INTC:'growth_tech',AVGO:'growth_tech',SMH:'growth_tech',QQQ:'index',SPY:'index',MSFT:'quality',GOLD:'gold',BTC:'crypto'};",
    "const CLASSMAP={NVDA:'growth_tech',INTC:'growth_tech',AVGO:'growth_tech',SMH:'growth_tech',QQQ:'index',SPY:'index',MSFT:'quality',GOLD:'gold',BTC:'crypto',AAPL:'quality',AMZN:'growth_tech',META:'growth_tech',GOOGL:'growth_tech',TSLA:'growth_tech',NFLX:'growth_tech',DIS:'quality',BRKB:'quality',DIA:'index',SILVER:'gold',OIL:'gold'};", 'classmap')

assert all(ord(c) < 128 for c in t), 'non-ascii introduced'
open('dashboard_template_beta.html', 'w').write(t)
d = json.load(open('dashboard_data_beta.json')); d['build_meta']['build_version'] = '2.6.0'
json.dump(d, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('explorer v2 applied; version 2.6.0')
