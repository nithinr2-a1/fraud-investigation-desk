/* ============================= STATE ============================= */
let claims = [];
let selectedId = null;
let sortKey = 'score';
let sortDir = -1;
let histChartInst = null;
let typeChartInst = null;

const CLAIM_TYPES = ['Auto','Property','Liability','Health','Workers Comp'];

/* ============================= TRAINED MODEL ============================= */
/* Exported from scikit-learn LogisticRegression trained on a 6,000-claim
   synthetic dataset. See companion ML Methodology Report for the full
   training pipeline and evaluation. */
const MODEL = {
  feature_order: ["claim_to_limit_ratio","claim_to_premium_ratio","policy_age_days","prior_claims","report_delay_days","police_report","is_round_amount","early_policy_30","early_policy_90","late_report","type_Auto","type_Health","type_Liability","type_Property","type_Workers Comp"],
  scaler_mean: [0.2787927571559962,9.857199690701043,419.13177777777776,0.452,3.5091111111111113,0.7675555555555555,0.25155555555555553,0.07244444444444445,0.12577777777777777,0.020666666666666667,0.354,0.18355555555555556,0.14244444444444446,0.20955555555555555,0.11044444444444444],
  scaler_scale: [0.1704510819855114,7.8988699349333364,428.78722432662147,0.6687686861356141,3.5076622935271433,0.4223908435221555,0.43390708455231675,0.25922238891264826,0.33159874606979706,0.14226579193732963,0.47820915925983687,0.38712131635993247,0.34950540008898007,0.40699143073455246,0.31344292803603413],
  coefficients: [1.0201878632954662,0.07565273469231579,0.07111621676189311,0.5112989090334488,-0.025669582629706585,-0.4612323395235569,0.37991711151856433,0.7354830760026901,0.5102423180153103,0.15355092189493946,0.01970515158734774,0.03744449264088346,0.03913103209942612,-0.06663351291433744,-0.03342229985793218],
  intercept: -0.7214746897034323,
  metrics: { accuracy: 0.788, precision: 0.37528604118993136, recall: 0.784688995215311, f1: 0.5077399380804953, roc_auc: 0.8614663904321046 }
};

const FEATURE_LABELS = {
  claim_to_limit_ratio: 'Claim-to-policy-limit ratio',
  claim_to_premium_ratio: 'Claim-to-premium ratio',
  policy_age_days: 'Policy age at time of claim',
  prior_claims: 'Prior claims by claimant',
  report_delay_days: 'Delay before incident was reported',
  police_report: 'Police report filed',
  is_round_amount: 'Round-number claim amount',
  early_policy_30: 'Filed within 30 days of policy start',
  early_policy_90: 'Filed within 31\u201390 days of policy start',
  late_report: 'Reported 14+ days late',
  type_Auto: 'Claim type: Auto',
  type_Health: 'Claim type: Health',
  type_Liability: 'Claim type: Liability',
  type_Property: 'Claim type: Property',
  'type_Workers Comp': 'Claim type: Workers Comp'
};

function buildRawFeatures(c){
  const ctl = (c.amount != null && c.limit) ? c.amount / c.limit : null;
  const ctp = (c.amount != null && c.premium) ? c.amount / c.premium : null;
  const isRound = (c.amount != null && c.amount > 0) ? (c.amount % 500 === 0 ? 1 : 0) : null;
  const early30 = (c.policyAgeDays != null) ? (c.policyAgeDays <= 30 ? 1 : 0) : null;
  const early90 = (c.policyAgeDays != null) ? (c.policyAgeDays > 30 && c.policyAgeDays <= 90 ? 1 : 0) : null;
  const lateReport = (c.reportDelayDays != null) ? (c.reportDelayDays >= 14 ? 1 : 0) : null;
  const police = (c.policeReport === null || c.policeReport === undefined) ? null : (c.policeReport ? 1 : 0);
  const typeOneHot = {Auto:0, Health:0, Liability:0, Property:0, 'Workers Comp':0};
  if (c.type && Object.prototype.hasOwnProperty.call(typeOneHot, c.type)) typeOneHot[c.type] = 1;

  return {
    claim_to_limit_ratio: ctl,
    claim_to_premium_ratio: ctp,
    policy_age_days: c.policyAgeDays ?? null,
    prior_claims: c.priorClaims ?? null,
    report_delay_days: c.reportDelayDays ?? null,
    police_report: police,
    is_round_amount: isRound,
    early_policy_30: early30,
    early_policy_90: early90,
    late_report: lateReport,
    type_Auto: typeOneHot.Auto,
    type_Health: typeOneHot.Health,
    type_Liability: typeOneHot.Liability,
    type_Property: typeOneHot.Property,
    'type_Workers Comp': typeOneHot['Workers Comp']
  };
}

/* ============================= SCORING ============================= */
function scoreClaim(c){
  const raw = buildRawFeatures(c);
  let z = MODEL.intercept;
  const contributions = [];

  MODEL.feature_order.forEach((feat, i) => {
    let val = raw[feat];
    const mean = MODEL.scaler_mean[i];
    const scale = MODEL.scaler_scale[i] || 1;
    const wasObserved = (val !== null && val !== undefined);
    if (!wasObserved) val = mean; // impute at training mean -> zero contribution
    const standardized = (val - mean) / scale;
    const contribution = MODEL.coefficients[i] * standardized;
    z += contribution;
    if (wasObserved && Math.abs(contribution) > 0.005){
      contributions.push([FEATURE_LABELS[feat] || feat, contribution]);
    }
  });

  const probability = 1 / (1 + Math.exp(-z));
  const score = Math.min(100, Math.max(0, Math.round(probability * 100)));

  let verdict = 'low';
  if (score >= 65) verdict = 'high';
  else if (score >= 35) verdict = 'med';

  contributions.sort((a,b) => Math.abs(b[1]) - Math.abs(a[1]));
  const reasons = contributions.slice(0, 6);

  return { score, verdict, reasons, probability };
}

/* ============================= SAMPLE DATA ============================= */
function rand(min,max){ return Math.random()*(max-min)+min; }
function randInt(min,max){ return Math.floor(rand(min,max+1)); }
function pick(arr){ return arr[randInt(0,arr.length-1)]; }
function roundTo(n, step){ return Math.round(n/step)*step; }

function generateSample(n=140){
  const out = [];
  const fraudShare = 0.16;
  for (let i=0;i<n;i++){
    const isSeededFraud = Math.random() < fraudShare;
    const type = pick(CLAIM_TYPES);
    const limit = roundTo(rand(8000, 60000), 500);
    const premium = roundTo(limit * rand(0.015,0.05), 25);

    let amount, policyAgeDays, priorClaims, reportDelayDays, policeReport;

    if (isSeededFraud){
      amount = roundTo(limit * rand(0.65, 0.99), 500);
      policyAgeDays = randInt(2, 80);
      priorClaims = randInt(1,5);
      reportDelayDays = randInt(10, 45);
      policeReport = Math.random() < 0.25;
    } else {
      amount = roundTo(limit * rand(0.03, 0.5), Math.random()<0.3?500:137);
      policyAgeDays = randInt(60, 2200);
      priorClaims = Math.random()<0.7 ? 0 : randInt(1,2);
      reportDelayDays = randInt(0, 10);
      policeReport = Math.random() < 0.85;
    }

    out.push({
      id: 'CLM-' + (10000 + i),
      type,
      amount, limit, premium,
      policyAgeDays, priorClaims, reportDelayDays,
      policeReport
    });
  }
  return out;
}

/* ============================= CSV MAPPING ============================= */
function findCol(headers, candidates){
  const lower = headers.map(h => h.toLowerCase().trim());
  for (const cand of candidates){
    const idx = lower.findIndex(h => h.includes(cand));
    if (idx !== -1) return headers[idx];
  }
  return null;
}
function toNum(v){
  if (v === undefined || v === null || v === '') return null;
  const n = parseFloat(String(v).replace(/[$,]/g,''));
  return isNaN(n) ? null : n;
}
function toBool(v){
  if (v === undefined || v === null || v === '') return null;
  const s = String(v).trim().toLowerCase();
  if (['yes','y','true','1'].includes(s)) return true;
  if (['no','n','false','0'].includes(s)) return false;
  return null;
}

function mapCsvRows(rows, headers){
  const colId = findCol(headers, ['claim_id','claimid','id']);
  const colType = findCol(headers, ['claim_type','type']);
  const colAmount = findCol(headers, ['claim_amount','amount','amt']);
  const colLimit = findCol(headers, ['policy_limit','limit']);
  const colPremium = findCol(headers, ['premium']);
  const colAge = findCol(headers, ['policy_age','days_since_policy','tenure']);
  const colPrior = findCol(headers, ['prior_claims','previous_claims','claim_history']);
  const colDelay = findCol(headers, ['report_delay','days_to_report','delay']);
  const colPolice = findCol(headers, ['police_report','police']);

  return rows.map((r, i) => ({
    id: colId ? String(r[colId]) : ('ROW-' + (i+1)),
    type: colType ? String(r[colType]) : 'Unspecified',
    amount: colAmount ? toNum(r[colAmount]) : null,
    limit: colLimit ? toNum(r[colLimit]) : null,
    premium: colPremium ? toNum(r[colPremium]) : null,
    policyAgeDays: colAge ? toNum(r[colAge]) : null,
    priorClaims: colPrior ? toNum(r[colPrior]) : null,
    reportDelayDays: colDelay ? toNum(r[colDelay]) : null,
    policeReport: colPolice ? toBool(r[colPolice]) : null,
    _mappedFields: { colId, colType, colAmount, colLimit, colPremium, colAge, colPrior, colDelay, colPolice }
  }));
}

/* ============================= RENDER ============================= */
const fmtMoney = n => n == null ? '—' : '$' + Math.round(n).toLocaleString();

function computeAll(){
  claims.forEach(c => {
    const r = scoreClaim(c);
    c.score = r.score; c.verdict = r.verdict; c.reasons = r.reasons;
  });
}

function renderStats(){
  const total = claims.length;
  const flagged = claims.filter(c => c.verdict === 'high').length;
  const exposure = claims.filter(c => c.verdict === 'high').reduce((s,c) => s + (c.amount||0), 0);
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statFlagged').textContent = flagged;
  document.getElementById('statExposure').textContent = fmtMoney(exposure);
  document.getElementById('statRate').textContent = total ? Math.round(flagged/total*100) + '%' : '—';
  document.getElementById('docketNote').textContent = total ? `${total} claims · sorted by ${sortKey}` : 'click a row to review';
}

function renderTable(){
  const body = document.getElementById('tableBody');
  if (!claims.length){
    body.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);font-style:italic;padding:30px;">No docket loaded — load the sample or upload a CSV.</td></tr>';
    return;
  }
  const sorted = [...claims].sort((a,b) => {
    let av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'string') return sortDir * av.localeCompare(bv);
    return sortDir * ((av ?? -Infinity) - (bv ?? -Infinity));
  });
  body.innerHTML = sorted.map(c => `
    <tr data-id="${c.id}" class="${c.id===selectedId?'selected':''}">
      <td>${c.id}</td>
      <td>${c.type}</td>
      <td>${fmtMoney(c.amount)}</td>
      <td>${c.score}</td>
      <td><span class="tag ${c.verdict}">${c.verdict==='high'?'Flagged':c.verdict==='med'?'Review':'Cleared'}</span></td>
    </tr>
  `).join('');
  body.querySelectorAll('tr').forEach(tr => {
    tr.addEventListener('click', () => { selectedId = tr.dataset.id; renderTable(); renderDetail(); });
  });
}

function renderDetail(){
  const card = document.getElementById('detailCard');
  const c = claims.find(x => x.id === selectedId);
  if (!c){
    card.innerHTML = '<div class="detail-empty">Select a claim from the docket to view its risk breakdown.</div>';
    return;
  }
  const verdictLabel = c.verdict === 'high' ? 'Flagged — Refer to SIU' : c.verdict === 'med' ? 'Flagged — Manual Review' : 'Cleared';
  const barColor = c.verdict === 'high' ? 'var(--stamp-red)' : c.verdict === 'med' ? 'var(--stamp-amber)' : 'var(--stamp-green)';

  const reasonsHtml = c.reasons.length
    ? c.reasons.map(([label,val]) => `<li><span>${label}</span><span class="pts ${val>=0?'up':'down'}">${val>=0?'+':''}${val.toFixed(2)}</span></li>`).join('')
    : '<li class="none">No notable contributing factors.</li>';

  card.innerHTML = `
    <div class="detail-id">${c.id}</div>
    <div class="detail-amount">${fmtMoney(c.amount)}</div>
    <div class="stamp ${c.verdict}">${verdictLabel}</div>
    <div class="score-row">
      <div class="score-num">${c.score}</div>
      <div class="score-bar-track"><div class="score-bar-fill" style="width:${c.score}%;background:${barColor};"></div></div>
    </div>
    <div class="k" style="margin-bottom:6px;">Top contributing factors (log-odds impact)</div>
    <ul class="reason-list">${reasonsHtml}</ul>
    <div class="meta-grid">
      <div><span class="k">Type</span><span class="v">${c.type}</span></div>
      <div><span class="k">Policy limit</span><span class="v">${fmtMoney(c.limit)}</span></div>
      <div><span class="k">Premium</span><span class="v">${fmtMoney(c.premium)}</span></div>
      <div><span class="k">Policy age (days)</span><span class="v">${c.policyAgeDays ?? '—'}</span></div>
      <div><span class="k">Prior claims</span><span class="v">${c.priorClaims ?? '—'}</span></div>
      <div><span class="k">Report delay (days)</span><span class="v">${c.reportDelayDays ?? '—'}</span></div>
      <div><span class="k">Police report</span><span class="v">${c.policeReport===null?'—':(c.policeReport?'Yes':'No')}</span></div>
    </div>
  `;
}

function renderCharts(){
  const histCtx = document.getElementById('histChart').getContext('2d');
  const typeCtx = document.getElementById('typeChart').getContext('2d');

  const buckets = [0,0,0,0,0]; // 0-19,20-39,40-59,60-79,80-100
  claims.forEach(c => {
    const idx = Math.min(Math.floor(c.score/20),4);
    buckets[idx]++;
  });

  const typeMap = {};
  claims.forEach(c => {
    if (!typeMap[c.type]) typeMap[c.type] = {total:0, flagged:0};
    typeMap[c.type].total++;
    if (c.verdict === 'high') typeMap[c.type].flagged++;
  });
  const typeLabels = Object.keys(typeMap);
  const typeRates = typeLabels.map(t => typeMap[t].total ? Math.round(typeMap[t].flagged/typeMap[t].total*100) : 0);

  if (histChartInst) histChartInst.destroy();
  if (typeChartInst) typeChartInst.destroy();

  const inkColor = '#1B2A41';
  const gridColor = 'rgba(91,70,54,0.15)';

  histChartInst = new Chart(histCtx, {
    type: 'bar',
    data: {
      labels: ['0–19','20–39','40–59','60–79','80–100'],
      datasets: [{
        data: buckets,
        backgroundColor: ['#3F6B4F','#3F6B4F','#B5821E','#A1311F','#A1311F'],
        borderRadius: 2
      }]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{
        x:{grid:{display:false}, ticks:{color:inkColor, font:{family:'IBM Plex Mono',size:10}}},
        y:{grid:{color:gridColor}, ticks:{color:inkColor, font:{family:'IBM Plex Mono',size:10}}, beginAtZero:true}
      }
    }
  });

  typeChartInst = new Chart(typeCtx, {
    type: 'bar',
    data: {
      labels: typeLabels,
      datasets: [{
        data: typeRates,
        backgroundColor: '#1B2A41',
        borderRadius: 2
      }]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      indexAxis: 'y',
      plugins:{legend:{display:false}},
      scales:{
        x:{grid:{color:gridColor}, ticks:{color:inkColor, font:{family:'IBM Plex Mono',size:10}, callback:v=>v+'%'}, beginAtZero:true, max:100},
        y:{grid:{display:false}, ticks:{color:inkColor, font:{family:'IBM Plex Mono',size:10}}}
      }
    }
  });
}

function renderAll(){
  computeAll();
  renderStats();
  renderTable();
  renderDetail();
  renderCharts();
}

/* ============================= EVENTS ============================= */
document.getElementById('loadSampleBtn').addEventListener('click', () => {
  claims = generateSample(140);
  selectedId = null;
  document.getElementById('fileName').textContent = 'sample-docket-140-claims.csv';
  renderAll();
});

document.getElementById('uploadBtn').addEventListener('click', () => {
  document.getElementById('fileInput').click();
});

document.getElementById('fileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  document.getElementById('fileName').textContent = file.name;
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      const headers = results.meta.fields || [];
      claims = mapCsvRows(results.data, headers);
      selectedId = null;
      renderAll();
    },
    error: (err) => {
      alert('Could not parse that CSV: ' + err.message);
    }
  });
});

document.getElementById('templateBtn').addEventListener('click', () => {
  const headers = ['claim_id','claim_type','claim_amount','policy_limit','premium','policy_age_days','prior_claims','report_delay_days','police_report'];
  const rows = [
    ['CLM-10001','Auto','7200','9000','950','22','1','18','no'],
    ['CLM-10002','Property','3100','40000','1200','620','0','2','yes']
  ];
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'claims_template.csv';
  a.click();
});

document.querySelectorAll('thead th').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.key;
    if (sortKey === key) sortDir *= -1; else { sortKey = key; sortDir = -1; }
    renderTable();
    renderStats();
  });
});

document.getElementById('testBtn').addEventListener('click', () => {
  const c = {
    amount: toNum(document.getElementById('tAmount').value),
    limit: toNum(document.getElementById('tLimit').value),
    premium: toNum(document.getElementById('tPremium').value),
    policyAgeDays: toNum(document.getElementById('tPolicyAge').value),
    priorClaims: toNum(document.getElementById('tPrior').value),
    reportDelayDays: toNum(document.getElementById('tDelay').value),
    type: document.getElementById('tType').value,
    policeReport: document.getElementById('tPolice').value === 'yes'
  };
  const r = scoreClaim(c);
  const verdictLabel = r.verdict === 'high' ? 'Flagged — Refer to SIU' : r.verdict === 'med' ? 'Flagged — Manual Review' : 'Cleared';
  const barColor = r.verdict === 'high' ? 'var(--stamp-red)' : r.verdict === 'med' ? 'var(--stamp-amber)' : 'var(--stamp-green)';
  const reasonsHtml = r.reasons.length
    ? r.reasons.map(([label,val]) => `<li><span>${label}</span><span class="pts ${val>=0?'up':'down'}">${val>=0?'+':''}${val.toFixed(2)}</span></li>`).join('')
    : '<li class="none">No notable contributing factors.</li>';
  document.getElementById('testResult').innerHTML = `
    <div style="margin-top:18px;padding-top:18px;border-top:1px solid var(--rule-soft);">
      <div class="stamp ${r.verdict}">${verdictLabel}</div>
      <div class="score-row">
        <div class="score-num">${r.score}</div>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${r.score}%;background:${barColor};"></div></div>
      </div>
      <div class="k" style="margin-bottom:6px;">Model probability: ${(r.probability*100).toFixed(1)}% &nbsp;·&nbsp; Top contributing factors (log-odds impact)</div>
      <ul class="reason-list">${reasonsHtml}</ul>
    </div>
  `;
});

/* ============================= INIT ============================= */
document.getElementById('mAcc').textContent = Math.round(MODEL.metrics.accuracy*100) + '%';
document.getElementById('mPrec').textContent = Math.round(MODEL.metrics.precision*100) + '%';
document.getElementById('mRec').textContent = Math.round(MODEL.metrics.recall*100) + '%';
document.getElementById('mAuc').textContent = MODEL.metrics.roc_auc.toFixed(3);

claims = generateSample(140);
document.getElementById('fileName').textContent = 'sample-docket-140-claims.csv';
renderAll();