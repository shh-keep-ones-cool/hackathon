// node analysis/test_stage5.js  (run from the repo root; reads data/*.csv, not the built HTML)
const fs=require('fs'),path=require('path'),Core=require('./dashboard_core.js');
const R=path.resolve(__dirname,'..'),rd=n=>fs.readFileSync(path.join(R,'data',n+'.csv'),'utf8');
const CSV={};['pci_provinces','outcomes_34_rebuilt','bridge_groups','pci_subindex_meta','pci_groups_34_panel','model_results','pci_bpi_2025','bootstrap_results'].forEach(n=>CSV[n]=rd(n));
const META={files:[]},D=Core.build(CSV,{features:[]},META);let fails=0,runs=0;
const ok=(c,m)=>{runs++;if(!c){fails++;console.log('FAIL',m);}};
const near=(a,b,t,m)=>ok(Math.abs(a-b)<=t,`${m}: ${a} vs ${b}`);
const base={pid:'bac-ninh',k:3,peer:'quartile',ev:'both',sg:'auto',frac:100,excl:false,adjust:false,map:'auto'};
// 1. peer averages never include the selected province; HCMC/HN are never peers when excluded
for(const pid of D.ids)for(const peer of['quartile','nearest8','region','all'])for(const excl of[false,true]){
  const A=Core.analyse(D,{...base,pid,peer,excl});
  ok(!A.peers.includes(pid),`peer set contains ${pid} (${peer})`);
  if(excl)ok(!A.peers.some(i=>Core.TOP2.includes(i)),`excluded province among peers (${pid},${peer})`);
  ok(A.peers.length>=2,`fewer than 2 peers ${pid} ${peer} ${excl}`);
  const r=A.rows[0],med=Core.median(A.peers.map(i=>D.zg[i][r.g.id]));near(r.peerMedian,med,1e-12,'peer median');}
// 2. HCMC/HN switch reproduces the Stage 2 specification values
const MR=Core.parseCSV(CSV.model_results);
for(const k of[1,2,3])for(const [excl,smp,n] of[[false,'all',null],[true,'excl_HCMC_HN',null]]){
  const A=Core.analyse(D,{...base,k,excl});ok(A.n25===(excl?32:34),`n25 ${excl}`);
  A.rows.forEach(r=>{const g=r.g.id,f=st=>MR.find(m=>m.block==='panel_fe'&&m.outcome==='ln_firms_new_per1000_t+'+k&&m.controls==='weighted'&&m['sample']===smp&&m.row===g&&m.stat===st);
    near(r.pc.coef,f('coef').value,1e-12,`panel coef ${g} k${k} ${smp}`);near(r.pc.lo,f('ci_low').value,1e-12,'panel lo');near(r.pc.hi,f('ci_high').value,1e-12,'panel hi');ok(r.pc.n===f('coef').n,`panel n ${g} ${k} ${smp}: ${r.pc.n}`);});
  ok(A.nPanel===(excl?224:238)||k>0,'nPanel');}
// 2025 OLS: standardised coef x SD(y)/SD(x) = raw Stage 2 coefficient; G1 = pci_s1, G2 = pci_s2 (single sub-index groups). Expected values: uploaded Stage 2 table (all) and independent HC3 recomputation (excl).
const sdv=a=>{const m=a.reduce((s,x)=>s+x,0)/a.length;return Math.sqrt(a.reduce((q,x)=>q+(x-m)**2,0)/(a.length-1));};
const EXP={all:{G1:[0.16750608457150798,0.093723497109534],G2:[0.3461786145833831,0.2256486543881105]},excl:{G1:[0.1564902089,0.0910014277],G2:[0.0668328372,0.1329398419]}};
for(const excl of[false,true]){const A=Core.analyse(D,{...base,excl}),S=A.sample;
  ['G1','G2'].forEach((g,gi)=>{const col='pci_s'+(gi+1),x=S.map(i=>D.P.find(r=>r.province_id===i)[col]),yv=S.map(i=>D.y25[i]),r=A.rows[gi],e=EXP[excl?'excl':'all'][g];
    const f=sdv(yv)/sdv(x),coef=r.c2.coef*f,se=(r.c2.hi-r.c2.lo)/(2*1.959963984540054)*f;   // (HC3 SE is scale-equivariant)
    near(coef,e[0],1e-6,`2025 coef ${g} excl=${excl}`);near(se,e[1],1e-6,`2025 HC3 se ${g} excl=${excl}`);ok(r.c2.n===S.length,'c2.n');});}
// 3. scenario arithmetic
for(const excl of[false,true])for(const k of[1,2,3])for(const adjust of[false,true]){
  const A=Core.analyse(D,{...base,pid:'ha-noi',k,excl,adjust}),gi=A.featured,r=A.rows[gi];
  for(const frac of[0,50,100]){const S=Core.scenario(D,A,gi,frac);near(S.shift,r.shortfall*frac/100,1e-12,'shift');
    ok(S.a&&S.p,'bootstrap rows missing '+[excl,k,adjust]);
    if(S.a){near(S.a.lo,S.shift*D.bt[['boot_2025','firms_new_per1000',adjust?'lnGRDPpc+coastal':'none',excl?'excl_HCMC_HN':'all',r.g.id,'ci_low'].join('|')],1e-12,'a.lo');ok(S.a.lo<=S.a.mid+1e-12&&S.a.mid<=S.a.hi+1e-12||frac===0,'2025 point inside interval');}
    if(S.p)ok(S.p.lo<=S.p.hi&&(frac>0||(S.p.lo===0&&S.p.hi===0)),'panel interval order/zero');}
  const h=Core.scenarioHTML(A,Core.scenario(D,A,gi,100));ok(/association, not a forecast/.test(h)||!(r.shortfall>0),'wording');ok(!/will |would raise|forecast:/i.test(h.replace(/not a forecast/,'')),'forecast wording');}
// 4. evidence modes change the label rule
{const a=Core.analyse(D,{...base,ev:'y25'}),p=Core.analyse(D,{...base,ev:'panel'}),b=Core.analyse(D,base);
  a.rows.forEach((r,i)=>{ok(r.stable===r.ex02,'y25 rule');ok(p.rows[i].stable===p.rows[i].ex0,'panel rule');ok(b.rows[i].stable===(b.rows[i].signOK&&b.rows[i].ex0),'both rule');});}
// 5. n line
{const A=Core.analyse(D,{...base,excl:true,pid:'ha-noi'}),t=Core.nLine(A);ok(/n = 32 provinces/.test(t)&&/outside the estimation sample/.test(t)&&/peers n = /.test(t),'nLine: '+t);}
console.log(`${runs} checks, ${fails} failed`);process.exit(fails?1:0);
