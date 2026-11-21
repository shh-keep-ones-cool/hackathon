// Dashboard core: pure functions (no DOM). Inlined into dashboard.html by analysis/06_build_dashboard.py and run in node by 07_test_dashboard.py.
// LIVE (computed in the browser from the embedded CSVs): 2025 group scores, peer sets, gaps, income-predicted score, 2025 OLS (HC3), priority score, labels, key numbers.
// FROM analysis/ (Python, read from CSV): merged 63->34 panel scores, panel fixed-effects coefficients, ridge LOO R2, bootstrap intervals for the scenario (06a_bootstrap.py).
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.Core=factory();})(this,function(){
'use strict';
const MINUS='\u2212', TOP2=['ha-noi','tp-ho-chi-minh'], COST={low:1,medium:2,high:3};
const TREND_BASE=[2015,2016,2017], TREND_END=[2022,2023,2024];   // design choice (3-year averages inside the old framework); stated in the footer
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const sd=a=>{const m=mean(a);return Math.sqrt(a.reduce((q,x)=>q+(x-m)**2,0)/(a.length-1));};       // ddof = 1
const zs=a=>{const m=mean(a),s=sd(a);return a.map(x=>(x-m)/s);};
const median=a=>{const s=[...a].sort((x,y)=>x-y),n=s.length;return n%2?s[(n-1)/2]:(s[n/2-1]+s[n/2])/2;};
const quant=(a,p)=>{const s=[...a].sort((x,y)=>x-y),h=(s.length-1)*p,l=Math.floor(h);return l+1<s.length?s[l]+(h-l)*(s[l+1]-s[l]):s[l];};  // linear interpolation (pandas default)
function parseCSV(text){ // minimal RFC4180 reader; empty -> NaN; numeric strings -> numbers
  text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],c='',q=false;
  for(let i=0;i<text.length;i++){const ch=text[i];
    if(q){if(ch=='"'){if(text[i+1]=='"'){c+='"';i++;}else q=false;}else c+=ch;}
    else if(ch=='"')q=true;else if(ch==','){row.push(c);c='';}
    else if(ch=='\n'||ch=='\r'){if(ch=='\r'&&text[i+1]=='\n')i++;row.push(c);c='';if(row.length>1||row[0]!=='')rows.push(row);row=[];}
    else c+=ch;}
  if(c!==''||row.length){row.push(c);rows.push(row);}
  const h=rows[0];return rows.slice(1).map(r=>{const o={};h.forEach((k,i)=>{const v=r[i]===undefined?'':r[i];o[k]=v===''?NaN:(v.trim()!==''&&isFinite(+v)?+v:v);});return o;});}
function inv(M){const n=M.length,A=M.map((r,i)=>[...r,...Array.from({length:n},(_,j)=>+(i==j))]);
  for(let i=0;i<n;i++){let p=i;for(let r=i+1;r<n;r++)if(Math.abs(A[r][i])>Math.abs(A[p][i]))p=r;[A[i],A[p]]=[A[p],A[i]];const d=A[i][i];for(let j=0;j<2*n;j++)A[i][j]/=d;
    for(let r=0;r<n;r++)if(r!=i){const f=A[r][i];for(let j=0;j<2*n;j++)A[r][j]-=f*A[i][j];}}return A.map(r=>r.slice(n));}
function olsHC3(X,y){ // same maths as analysis/ols_hc3.js and 03_models.py
  const n=X.length,k=X[0].length,Xt=X[0].map((_,j)=>X.map(r=>r[j]));
  const XtXi=inv(Xt.map(a=>Xt.map(b=>a.reduce((s,v,i)=>s+v*b[i],0))));
  const b=XtXi.map(r=>r.reduce((s,v,j)=>s+v*Xt[j].reduce((q,x,i)=>q+x*y[i],0),0));
  const e=y.map((v,i)=>v-X[i].reduce((s,x,j)=>s+x*b[j],0)),h=X.map(r=>r.reduce((s,x,i)=>s+x*XtXi[i].reduce((q,v,j)=>q+v*r[j],0),0));
  const meat=Array.from({length:k},()=>Array(k).fill(0));
  X.forEach((r,i)=>{const w=(e[i]/(1-h[i]))**2;for(let a=0;a<k;a++)for(let c=0;c<k;c++)meat[a][c]+=w*r[a]*r[c];});
  const mm=(A,B)=>A.map(r=>B[0].map((_,j)=>r.reduce((s,v,i)=>s+v*B[i][j],0))),V=mm(mm(XtXi,meat),XtXi);
  return {b,se:V.map((r,i)=>Math.sqrt(r[i]))};}
const pretty=k=>{const t=k.replace(/^\d+_/,'').replace(/_/g,' ');return t.charAt(0).toUpperCase()+t.slice(1);};
const fnum=(x,d=2)=>(x<0?MINUS:'')+Math.abs(x).toFixed(d), fsgn=(x,d=2)=>(x<0?MINUS:'+')+Math.abs(x).toFixed(d);
const pct=b=>100*(Math.exp(b)-1), fpct=b=>{const v=pct(b);return (v<0?MINUS:'+')+Math.abs(v).toFixed(1)+'%';};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function build(csv,geo,meta){
  const P=parseCSV(csv.pci_provinces),O=parseCSV(csv.outcomes_34_rebuilt),BR=parseCSV(csv.bridge_groups),SM=parseCSV(csv.pci_subindex_meta),PAN=parseCSV(csv.pci_groups_34_panel),MR=parseCSV(csv.model_results),BPI=parseCSV(csv.pci_bpi_2025);
  const ids=P.map(r=>r.province_id),name={},region={};BPI.forEach(r=>name[r.province_id]=r.province_name);P.forEach(r=>region[r.province_id]=r.region);
  const groups=BR.map(r=>({id:r.group_id,key:r.bridge_group,label:pretty(r.bridge_group),cols:r.new_cols.split('+')}));
  // group score 2025: z-score each mapped sub-index across the 34, average, re-standardise across the 34 (units = SD of the 34-province distribution)
  const cols=[...new Set(groups.flatMap(g=>g.cols))],subz={};cols.forEach(c=>subz[c]=zs(P.map(r=>r[c])));
  const zg={};ids.forEach(i=>zg[i]={});
  groups.forEach(g=>{const raw=P.map((r,i)=>mean(g.cols.map(c=>subz[c][i]))),z=zs(raw);ids.forEach((id,i)=>zg[id][g.id]=z[i]);});
  const o24={};O.filter(r=>r.year===2024).forEach(r=>o24[r.province_id]=r);
  const lninc={},y25={},coastal={};P.forEach(r=>{lninc[r.province_id]=Math.log(o24[r.province_id].grdp/o24[r.province_id].pop);y25[r.province_id]=r.firms_new/r.pop;coastal[r.province_id]=r.coastal;});
  const li=ids.map(i=>lninc[i]),e=[0.25,0.5,0.75].map(p=>quant(li,p)),qOf={};ids.forEach(i=>qOf[i]=lninc[i]<=e[0]?1:lninc[i]<=e[1]?2:lninc[i]<=e[2]?3:4);
  groups.forEach(g=>{const cs=g.cols.map(c=>SM.find(r=>r.code===c.toUpperCase()));g.horizon=mean(cs.map(r=>r.horizon_years));g.cost=mean(cs.map(r=>COST[r.cost_level]));g.subs=cs.map(r=>r.name_en);});
  const pan={};PAN.forEach(r=>{(pan[r.province_id]=pan[r.province_id]||{})[r.year]=r;});
  const BT={};(csv.bootstrap_results?parseCSV(csv.bootstrap_results):[]).forEach(r=>{BT[[r.block,r.outcome,r.controls,r['sample'],r.row,r.stat].join('|')]=r.value;});
  const mr={};MR.filter(r=>r.block==='panel_fe'||r.block==='panel_label'||r.block==='loo').forEach(r=>{mr[[r.block,r.outcome,r.controls,r['sample'],r.row,r.stat].join('|')]=r;});
  return {bt:BT,P,ids,name,region,groups,zg,lninc,y25,coastal,qOf,qEdges:e,pan,mr,geo,meta,csvRows:{MR,PAN}};}

function analyse(D,s){
  const sample=D.ids.filter(i=>!(s.excl&&TOP2.includes(i))),cand=sample.filter(i=>i!==s.pid);
  let peers,peerText,peerNote='';
  if(s.peer==='nearest8'){peers=[...cand].sort((a,b)=>Math.abs(D.lninc[a]-D.lninc[s.pid])-Math.abs(D.lninc[b]-D.lninc[s.pid])||(a<b?-1:1)).slice(0,8);peerText='the 8 provinces nearest in GRDP per capita';}
  else if(s.peer==='all'){peers=cand;peerText='all other provinces';}
  else if(s.peer==='region'){peers=cand.filter(i=>D.region[i]===D.region[s.pid]);peerText='provinces in the same region ('+D.region[s.pid]+')';}
  else{peers=cand.filter(i=>D.qOf[i]===D.qOf[s.pid]);peerText='provinces in the same GRDP-per-capita quartile';}
  if(peers.length<2){peerNote=`Only ${peers.length} province${peers.length===1?'':'s'} matched this peer set, so all other provinces are used instead.`;peers=cand;peerText='all other provinces (fallback)';}
  else if(peers.length<5)peerNote=`Only ${peers.length} peers: the median of so few provinces is unstable.`;
  const ev=s.ev||'both',panSample=s.excl?'excl_HCMC_HN':'all',outc='ln_firms_new_per1000_t+'+s.k,yz=zs(sample.map(i=>D.y25[i])),Z95=1.959963984540054;
  const rows=D.groups.map(g=>{
    const sc=D.zg[s.pid][g.id],pm=median(peers.map(i=>D.zg[i][g.id])),gap=sc-pm;
    const rank=1+D.ids.filter(i=>D.zg[i][g.id]>sc).length;
    const x=sample.map(i=>D.zg[i][g.id]),xz=zs(x),ln=sample.map(i=>D.lninc[i]);                      // income fit and 2025 association are live OLS on the chosen sample
    const mx=mean(x),ml=mean(ln),sl=ln.reduce((q,v,j)=>q+(v-ml)*(x[j]-mx),0)/ln.reduce((q,v)=>q+(v-ml)**2,0),pred=mx+sl*(D.lninc[s.pid]-ml);
    const C=s.adjust?[zs(sample.map(i=>D.lninc[i])),zs(sample.map(i=>D.coastal[i]))]:[],f=olsHC3(xz.map((v,j)=>[1,v,...C.map(c=>c[j])]),yz);
    const pf=st=>{const r=D.mr[['panel_fe',outc,'weighted',panSample,g.id,st].join('|')];return r?r.value:NaN;},pn=D.mr[['panel_fe',outc,'weighted',panSample,g.id,'coef'].join('|')];
    const pc={coef:pf('coef'),lo:pf('ci_low'),hi:pf('ci_high'),n:pn?pn.n:NaN},c2={coef:f.b[1],lo:f.b[1]-Z95*f.se[1],hi:f.b[1]+Z95*f.se[1],n:sample.length};
    const signOK=Math.sign(c2.coef)===Math.sign(pc.coef),ex0=pc.lo>0||pc.hi<0,ex02=c2.lo>0||c2.hi<0,
      stable=ev==='y25'?ex02:ev==='panel'?ex0:signOK&&ex0,pos=ev==='y25'?c2.coef>0:pc.coef>0;   // evidence: 2025 only | panel only | both (same sign and panel interval excludes 0)
    const label=stable&&pos?'strong priority candidate':stable?'stable negative association':'low reliability';
    const shortfall=Math.max(0,-gap),score=shortfall/g.cost,tier=stable&&pos?1:0;
    const dev=peers.map(i=>D.zg[i][g.id]-pm);
    const avg=(i,yrs)=>mean(yrs.map(y=>D.pan[i][y][g.id+'_w_z34'])),chg=i=>avg(i,TREND_END)-avg(i,TREND_BASE),tr=chg(s.pid),trPeers=median(peers.map(chg));
    return {g,score:sc,peerMedian:pm,gap,rank,pred,predGap:sc-pred,predDev:pred-pm,dev,c2,pc,signOK,ex0,ex02,stable,label,shortfall,priority:score,tier,trend:tr,trendPeers:trPeers};});
  const order=rows.map((_,i)=>i).sort((a,b)=>rows[b].tier-rows[a].tier||rows[b].priority-rows[a].priority||rows[a].gap-rows[b].gap);
  const elig=order.filter(i=>rows[i].shortfall>0),top=elig.length?elig[0]:null,featured=top!==null?top:[...order].sort((a,b)=>rows[a].gap-rows[b].gap)[0];
  const A={s,ev,peerNote,pid:s.pid,name:D.name[s.pid],sample,peers,peerText,rows,order,top,featured,k:s.k,panSample,nPanel:rows[0].pc.n,n25:sample.length};
  const t=top!==null?rows[top]:null,pn=A.nPanel,nTxt=`n = ${A.n25} provinces in 2025; ${pn} province-years in the panel`;
  if(!t)A.headline=`${A.name} is at or above the median of ${peers.length} similar provinces on all ${rows.length} bridge groups, so no group stands out as a shortfall (${nTxt}).`;
  else if(t.tier===1)A.headline=`${A.name}: ${t.g.label.toLowerCase()} is the largest shortfall against similar provinces (${t.shortfall.toFixed(1)} SD below the median of ${peers.length} peers) and the only kind of gap whose score has been positively associated with new-firm formation ${ev==='both'?'in 2025 and in the panel':ev==='y25'?'in 2025 (interval excludes 0)':'in the panel (interval excludes 0)'}. A candidate to review, not evidence that investing in it would raise new-firm numbers (${nTxt}).`;
  else A.headline=`${A.name}\u2019s largest shortfall against similar provinces is ${t.g.label.toLowerCase()} (${t.shortfall.toFixed(1)} SD below the median of ${peers.length} peers), but no group shows a reliable link ${ev==='both'?`in both 2025 and the panel at the ${s.k}-year horizon`:ev==='y25'?'in the 2025 data':`in the panel at the ${s.k}-year horizon`}: low reliability, so these data do not support ranking reform priorities for this province (${nTxt}).`;
  const F=rows[featured];
  A.key={level:{group:F.g.label,score:F.score,rank:F.rank,n:34},benchmark:{gap:F.gap,predGap:F.predGap,peers:peers.length},trend:{change:F.trend,peers:F.trendPeers,base:TREND_BASE,end:TREND_END}};
  const lo=D.mr[['loo','firms_new_per1000','none','all','ridge','loo_r2'].join('|')];A.looR2=lo?{v:lo.value,n:lo.n}:null;
  return A;}


// ---------- scenario (association, not forecast): bootstrap intervals are precomputed in analysis/06a_bootstrap.py; the arithmetic below is live ----------
function scenario(D,A,gi,frac){
  const r=A.rows[gi],g=r.g,shift=r.shortfall*frac/100,ctl=A.s.adjust?'lnGRDPpc+coastal':'none',smp=A.panSample,B=(b,o,c,st)=>D.bt[[b,o,c,smp,g.id,st].join('|')];
  const o25=['boot_2025','firms_new_per1000',ctl],op=['boot_panel','ln_firms_new_per1000_t+'+A.k,'weighted'],get=o=>({coef:B(...o,'coef'),lo:B(...o,'ci_low'),hi:B(...o,'ci_high'),B:B(...o,'boot_B')});
  const a=get(o25),p=get(op),ok=x=>isFinite(x.coef)&&isFinite(x.lo)&&isFinite(x.hi),y0=D.y25[A.pid];
  return {r,g,shift,frac,y0,a:ok(a)?{...a,lo:a.lo*shift,hi:a.hi*shift,mid:a.coef*shift,n:A.n25,ctl}:null,p:ok(p)?{...p,lo:p.lo*shift,hi:p.hi*shift,mid:p.coef*shift,n:A.nPanel}:null};}
function scenarioHTML(A,S){
  const g=S.g.label.toLowerCase(),nm=esc(A.name),ev=A.ev;
  if(!(S.r.shortfall>0))return `<p>${nm} is already at or above the peer median on ${esc(g)} (${fsgn(S.r.gap)} SD), so there is no gap to close. Choose another group.</p>`;
  const tgt=S.frac===100?'the peer median':`${S.frac}% of the way to the peer median`,span=(lo,hi)=>lo<=0&&hi>=0?'includes 0 (the data are also consistent with no difference)':'excludes 0';
  let h=`<p><b>${esc(S.g.label)}:</b> ${nm} scores ${fnum(S.r.score)} SD, the peer median is ${fnum(S.r.peerMedian)} SD. Moving to ${tgt} is <b>+${S.shift.toFixed(2)} SD</b>.</p><ul>`;
  const rel=S.r.label==='strong priority candidate'?'':` Label for this group: <i>${esc(S.r.label)}</i>; read this range as weak evidence.`;
  if(ev!=='panel')h+=S.a?`<li><b>2025 cross-section</b> (n = ${S.a.n} provinces${S.a.ctl!=='none'?', adjusted for GRDP per capita and coast':''}): provinces scoring that much higher had <b>${fsgn(S.a.lo)} to ${fsgn(S.a.hi)} new firms per 1000 residents</b> (95% bootstrap interval; ${fpctRaw(100*S.a.lo/S.y0)} to ${fpctRaw(100*S.a.hi/S.y0)} of ${nm}\u2019s 2024 level of ${S.y0.toFixed(2)}). The interval ${span(S.a.lo,S.a.hi)}.</li>`:'<li>2025 interval not available for this selection.</li>';
  if(ev!=='y25')h+=S.p?`<li><b>Panel, ${A.k} year${A.k>1?'s':''} later</b> (n = ${S.p.n} province-years): <b>${fpct(S.p.lo)} to ${fpct(S.p.hi)} in new firms per 1000 residents</b> (95% bootstrap interval, province and year fixed effects). The interval ${span(S.p.lo,S.p.hi)}.</li>`:'<li>Panel interval not available for this selection.</li>';
  return h+`</ul><p class="note">This describes differences associated with scores across provinces in past data. It is an association, not a forecast of what would happen if ${nm} raised its score. It assumes a straight-line relationship and treats the peer median as fixed. The panel slope comes from the legacy PCI (2010\u20132024), the gap from PCI 2.0 (2025): read the panel range as indicative.${rel}</p>`;}
const fpctRaw=v=>(v<0?MINUS:'+')+Math.abs(v).toFixed(0)+'%';
function nLine(A){
  const s=A.s,out=A.sample.length<34,inSample=A.sample.includes(A.pid);
  return `<b>Current selection:</b> 2025 association n = ${A.n25} provinces${out?' (HCMC and H\u00E0 N\u1ED9i left out)':''}; panel n = ${A.nPanel} province-years (${A.n25} provinces) at t+${A.k}; peers n = ${A.peers.length} (${esc(A.name)} itself excluded).${inSample?'':` ${esc(A.name)} is outside the estimation sample and is shown for comparison only.`}${A.peerNote?' '+esc(A.peerNote):''}`;}

// ---------- renderers (return strings) ----------
const COL={blue:'#0072B2',orange:'#E69F00',verm:'#D55E00',grey:'#6b7280',ink:'#1f2937'};
function chipHTML(label){return label==='strong priority candidate'?'<span class="chip c-strong"><span aria-hidden="true">\u2605</span> strong priority candidate</span>':label==='stable negative association'?'<span class="chip c-neg"><span aria-hidden="true">\u25BC</span> stable, negative sign: review</span>':'<span class="chip c-low"><span aria-hidden="true">\u25CB</span> low reliability</span>';}
function keyHTML(A){const k=A.key,u='SD of the 34-province distribution';
  const dir=x=>Math.abs(x)<0.05?'level with':x<0?'below':'above';
  return `<div class="kn"><div class="kl">Level <span class="badge live">live</span></div><div class="kv">${fnum(k.level.score)} SD</div><div class="kd">${esc(k.level.group)}: rank ${k.level.rank} of ${k.level.n} provinces in 2025 (1 = highest score)</div></div>
<div class="kn"><div class="kl">Benchmark <span class="badge live">live</span></div><div class="kv">${fnum(k.benchmark.gap)} SD</div><div class="kd">${dir(k.benchmark.gap)} the median of ${k.benchmark.peers} peers; ${fnum(Math.abs(k.benchmark.predGap))} SD ${dir(k.benchmark.predGap)} the score its GRDP per capita predicts</div></div>
<div class="kn"><div class="kl">Trend <span class="badge py">analysis/</span></div><div class="kv">${fsgn(k.trend.change)} SD</div><div class="kd">change in relative position, 3-year averages ${k.trend.base[0]}\u2013${k.trend.base[2]} to ${k.trend.end[0]}\u2013${k.trend.end[2]} (old framework, merged series); peers\u2019 median ${fsgn(k.trend.peers)}. Not compared with 2025.</div></div>`;}
function chartSVG(A,W){
  const rows=A.order.map(i=>A.rows[i]),padL=14,padR=14,rowH=66,top0=8,axisH=46,H=top0+rows.length*rowH+axisH;
  let mx=0;rows.forEach(r=>{[r.gap,r.predDev,...r.dev].forEach(v=>mx=Math.max(mx,Math.abs(v)));});const m=Math.max(1,Math.ceil(mx*2)/2),X=v=>padL+(v+m)/(2*m)*(W-padL-padR);
  let s=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="ct cd"><title id="ct">Gap to peer median by bridge group for ${esc(A.name)}</title><desc id="cd">Each row shows the province\u2019s 2025 score minus the median of its peers, in standard deviations, with the score predicted by its GRDP per capita and the spread of the peers.</desc>`;
  for(let v=-Math.floor(m);v<=Math.floor(m);v++)if(v!==0)s+=`<line x1="${X(v)}" x2="${X(v)}" y1="${top0}" y2="${H-axisH}" stroke="#e5e7eb"/>`;
  s+=`<line x1="${X(0)}" x2="${X(0)}" y1="${top0}" y2="${H-axisH}" stroke="${COL.ink}" stroke-width="1.5" stroke-dasharray="5 3"/>`;
  rows.forEach((r,i)=>{const y0=top0+i*rowH,cy=y0+44,dir=Math.abs(r.gap)<0.05?'level with':r.gap<0?'below':'above';
    s+=`<text x="${padL}" y="${y0+15}" font-size="13.5" font-weight="700" fill="${COL.ink}">${i+1}. ${esc(r.g.label)}</text><text x="${W-padR}" y="${y0+15}" text-anchor="end" font-size="12.5" fill="${COL.ink}">${fnum(Math.abs(r.gap))} SD ${dir} peers</text>`;
    s+=`<line x1="${padL}" x2="${W-padR}" y1="${cy}" y2="${cy}" stroke="#d1d5db"/>`;
    r.dev.forEach((v,j)=>{s+=`<circle cx="${X(v)}" cy="${cy+((j*37)%5-2)*3.2}" r="3.6" fill="#fff" stroke="${COL.grey}" stroke-width="1.3"><title>peer, ${fsgn(v)} SD vs peer median</title></circle>`;});
    const dx=X(r.predDev);s+=`<path d="M${dx} ${cy-9}L${dx+9} ${cy}L${dx} ${cy+9}L${dx-9} ${cy}Z" fill="${COL.orange}" stroke="${COL.ink}" stroke-width="1.4"><title>score predicted by GRDP per capita: ${fsgn(r.predDev)} SD vs peer median</title></path>`;
    s+=`<circle cx="${X(r.gap)}" cy="${cy}" r="8.5" fill="${COL.blue}" stroke="#fff" stroke-width="2.2"/><circle cx="${X(r.gap)}" cy="${cy}" r="9.6" fill="none" stroke="${COL.ink}" stroke-width="1.2"><title>${esc(A.name)}: ${fsgn(r.gap)} SD vs peer median</title></circle>`;});
  const ay=H-axisH+14;for(let v=-Math.floor(m);v<=Math.floor(m);v++)s+=`<text x="${X(v)}" y="${ay}" text-anchor="middle" font-size="12" fill="${COL.grey}">${v===0?'0':fsgn(v,0)}</text>`;
  s+=`<text x="${padL}" y="${H-6}" font-size="12" fill="${COL.ink}">\u2190 below peers</text><text x="${W-padR}" y="${H-6}" text-anchor="end" font-size="12" fill="${COL.ink}">above peers \u2192</text></svg>`;return s;}
function tableHTML(A){
  const k=A.k;let h=`<table class="pt"><thead><tr><th>#</th><th>Bridge group</th><th>Gap vs peer median (SD) <span class="badge live">live</span></th><th>2025 association: std. coef [95% CI] <span class="badge live">live</span></th><th>Panel association, t+${k}: % new firms per 1000 per +1 SD [95% CI] <span class="badge py">analysis/</span></th><th>Stability label</th><th>Horizon (years)*</th><th>Cost score*</th><th>Priority score</th></tr></thead><tbody>`;
  A.order.forEach((i,j)=>{const r=A.rows[i],c=r.c2,p=r.pc;
    h+=`<tr${i===A.top?' class="topr"':''}><td>${j+1}</td><th scope="row">${esc(r.g.label)}<div class="sub">${esc(r.g.subs.join(' + '))}</div></th><td class="num">${fsgn(r.gap)}</td><td class="num${A.ev==='panel'?' dim':''}">${fsgn(c.coef)} [${fnum(c.lo)}, ${fnum(c.hi)}]<div class="sub">n = ${c.n}</div></td><td class="num${A.ev==='y25'?' dim':''}">${fpct(p.coef)} [${fpct(p.lo)}, ${fpct(p.hi)}]<div class="sub">n = ${p.n}, signs ${r.signOK?'agree':'differ'}, interval ${r.ex0?'excludes':'includes'} 0</div></td><td>${chipHTML(r.label)}</td><td class="num">${r.g.horizon.toFixed(1)}</td><td class="num">${r.g.cost.toFixed(1)}</td><td class="num">${r.shortfall>0?r.priority.toFixed(2):'0 (no shortfall)'}</td></tr>`;});
  return h+'</tbody></table>';}
function lerp(a,b,t){return a+(b-a)*t;}
const RAMP=['#ffffcc','#a1dab4','#41b6c4','#2c7fb8','#253494'];
function rampColor(t){t=Math.max(0,Math.min(1,t));const x=t*(RAMP.length-1),i=Math.min(RAMP.length-2,Math.floor(x)),f=x-i,h=c=>[1,3,5].map(k=>parseInt(c.slice(k,k+2),16)),a=h(RAMP[i]),b=h(RAMP[i+1]);return '#'+a.map((v,k)=>Math.round(lerp(v,b[k],f)).toString(16).padStart(2,'0')).join('');}
function projGeo(geo){ // equirectangular scaled by cos(mid latitude); returns {paths:{id:d}, w, h, centroid:{id:[x,y]}}
  let xs=[],ys=[];geo.features.forEach(f=>f.geometry.coordinates.forEach(p=>p.forEach(r=>r.forEach(([x,y])=>{xs.push(x);ys.push(y);}))));
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),k=Math.cos((y0+y1)/2*Math.PI/180),S=100,w=(x1-x0)*k*S,h=(y1-y0)*S;
  const px=([x,y])=>[((x-x0)*k*S).toFixed(1),((y1-y)*S).toFixed(1)],paths={},cen={};
  geo.features.forEach(f=>{const id=f.properties.province_id;let d='',best=-1;f.geometry.coordinates.forEach(p=>p.forEach((r,ri)=>{d+='M'+r.map(px).map(q=>q.join(' ')).join('L')+'Z';if(ri===0){const a=Math.abs(r.reduce((s,q,i)=>{const n=r[(i+1)%r.length];return s+q[0]*n[1]-n[0]*q[1];},0));if(a>best){best=a;const xsr=r.map(q=>q[0]),ysr=r.map(q=>q[1]);cen[id]=px([(Math.min(...xsr)+Math.max(...xsr))/2,(Math.min(...ysr)+Math.max(...ysr))/2]);}}}));paths[id]=d;});
  return {paths,w,h,cen};}
function mapSVG(A,D,gi,pxW){const G=projGeo(D.geo),z=D.ids.map(i=>D.zg[i][D.groups[gi].id]),lo=Math.min(...z),hi=Math.max(...z),fs=(13*G.w/pxW).toFixed(1),sw=(G.w/pxW);
  let s=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${G.w.toFixed(0)} ${G.h.toFixed(0)}" width="100%" role="img" aria-labelledby="mt"><title id="mt">Map of 2025 ${esc(D.groups[gi].label)} score by province; ${esc(A.name)} outlined</title>`;
  D.ids.forEach(id=>{const v=D.zg[id][D.groups[gi].id],sel=id===A.pid,peer=A.peers.includes(id);
    s+=`<path class="prov" data-id="${id}" d="${G.paths[id]}" fill="${rampColor((v-lo)/(hi-lo))}" stroke="${sel?'#000':peer?'#000':'#fff'}" stroke-width="${(sel?3:peer?1.4:0.7)*sw}"${peer&&!sel?` stroke-dasharray="${3*sw} ${2*sw}"`:''} tabindex="0" aria-label="${esc(D.name[id])}: ${fnum(v)} SD"><title>${esc(D.name[id])}: ${fnum(v)} SD${sel?' (selected)':peer?' (peer)':''}</title></path>`;});
  const c=G.cen[A.pid],right=c[0]<G.w*0.55;s+=`<text x="${(+c[0]+(right?14:-14)*sw).toFixed(1)}" y="${(+c[1]).toFixed(1)}" font-size="${fs}" font-weight="700" text-anchor="${right?'start':'end'}" paint-order="stroke" stroke="#fff" stroke-width="${(4*sw).toFixed(1)}" fill="#000">${esc(A.name)}</text></svg>`;
  return {svg:s,lo,hi};}
return {scenario,scenarioHTML,nLine,parseCSV,build,analyse,chartSVG,tableHTML,keyHTML,mapSVG,chipHTML,rampColor,RAMP,esc,fnum,fsgn,fpct,median,zs,TOP2,TREND_BASE,TREND_END};
});
