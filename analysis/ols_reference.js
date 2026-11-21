// Simple OLS (intercept + one predictor), for independent JS/Python parity checking.
const fs = require('fs');
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
const n = rows.length;
if (n < 3) throw new Error('Need at least 3 complete cases');
const xs = rows.map(r => Number(r.x));
const ys = rows.map(r => Number(r.y));
const mx = xs.reduce((a,b)=>a+b,0)/n;
const my = ys.reduce((a,b)=>a+b,0)/n;
let sxx=0,sxy=0,syy=0;
for (let i=0;i<n;i++) { const dx=xs[i]-mx, dy=ys[i]-my; sxx+=dx*dx; sxy+=dx*dy; syy+=dy*dy; }
if (sxx===0) throw new Error('Predictor has zero variance');
const slope=sxy/sxx, intercept=my-slope*mx;
const r2=syy===0 ? null : (sxy*sxy)/(sxx*syy);
process.stdout.write(JSON.stringify({n,intercept,slope,r2}));
