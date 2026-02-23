const fs = require('fs');
const path = require('path');

const WIX_COLUMNS = [
  'handleId', 'fieldType', 'name', 'description', 'productImageUrl',
  'collection', 'sku', 'ribbon', 'price', 'surcharge',
  'visible', 'discountMode', 'discountValue', 'inventory', 'weight',
  'cost', 'productOptionName1', 'productOptionType1', 'productOptionDescription1',
  'productOptionName2', 'productOptionType2', 'productOptionDescription2',
  'productOptionName3', 'productOptionType3', 'productOptionDescription3',
  'productOptionName4', 'productOptionType4', 'productOptionDescription4',
  'productOptionName5', 'productOptionType5', 'productOptionDescription5',
  'productOptionName6', 'productOptionType6', 'productOptionDescription6',
  'productVariantName1', 'productVariantOptionValue1_1', 'productVariantOptionValue1_2',
  'productVariantOptionValue1_3', 'productVariantOptionValue1_4', 'productVariantOptionValue1_5',
  'productVariantOptionValue1_6', 'productVariantPrice1', 'productVariantInventory1',
  'productVariantVisible1', 'productVariantSku1', 'productVariantWeight1',
  'productVariantCost1', 'productVariantWholesalePrice1', 'productVariantMetaData1', 'brand'
];

const BRAND_COLLECTIONS = {
  CASIO: 'CASIO', CITIZEN: 'CITIZEN', EDIFICE: 'EDIFICE', INGERSOLL: 'INGERSOLL',
  ORIENT: 'ORIENT', SEIKO: 'SEİKO', 'SEİKO': 'SEİKO', HAMILTON: 'HAMILTON', LONGINES: 'LONGINES',
  OMEGA: 'OMEGA', ROLEX: 'ROLEX', TISSOT: 'TISSOT', TUDOR: 'TUDOR', TIMEX: 'TIMEX', BULOVA: 'BULOVA'
};

const CLASSIFIER_ALLOWED_VALUES = {
  sr_dial_color: ['Ağ', 'Boz', 'Firuzə', 'Gəhvəyi', 'Göy', 'Krem', 'Mavi', 'Qara', 'Qırmızı', 'Sarı', 'Yaşıl'],
  bracelet_type: ['Dəri', 'Kauçuk', 'Polad'],
  gender: ['Kişi', 'Qadın'],
  movement: ['Kvarts', 'Mexanika'],
  bracelet_color: ['Ağ', 'Boz', 'Boz/Sarı', 'Gəhvəyi', 'Göy', 'Krem', 'Qara', 'Sarı'],
  case_material: ['Polad', 'Plastik']
};

function rootPath(...parts) {
  return path.resolve(__dirname, '..', '..', ...parts);
}

function loadCatalog() {
  try {
    const p = rootPath('model_specs_catalog.json');
    const raw = fs.readFileSync(p, 'utf8');
    const data = JSON.parse(raw);
    return data && typeof data === 'object' ? data : {};
  } catch (_) {
    return {};
  }
}

function normalizeBrand(brand) {
  const v = String(brand || '').toUpperCase().replace(/İ/g, 'I').trim();
  const known = Object.keys(BRAND_COLLECTIONS);
  for (const k of known) {
    if (v.includes(k.replace(/İ/g, 'I'))) return k;
  }
  return '';
}

function normalizeModelKey(model) {
  return String(model || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function inferBrand(model) {
  const m = String(model || '').toUpperCase().trim();
  if (/^(SKX|SNZH|SRP|SRPE|SNK|SSA|SSK|SNXS|SPB)/.test(m)) return 'SEIKO';
  if (/^(RA-|RA\d|F[A-Z]{2}\d|AC\d)/.test(m)) return 'ORIENT';
  if (/^(BN\d|NJ\d|NY\d)/.test(m)) return 'CITIZEN';
  if (/^(F-\d|AE-\d|GA-\d|GMA-|GA-B\d|GAB\d|G-\d|DW-\d|A\d{3})/.test(m)) return 'CASIO';
  if (/^(T\d|PRX|LE\s?LOCLE|SEASTAR)/.test(m)) return 'TISSOT';
  if (/^(L3\.|L2\.|L4\.|LONGINES)/.test(m)) return 'LONGINES';
  if (/^(M0|M8|H32|H40|H7)/.test(m)) return 'HAMILTON';
  if (/^(210\.|220\.|OMEGA)/.test(m)) return 'OMEGA';
  if (/^(M12|M34|M95)/.test(m)) return 'INGERSOLL';
  return '';
}

function estimateSizeLabel(model, brand) {
  const m = String(model || '').toUpperCase().trim();
  const b = normalizeBrand(brand) || inferBrand(m) || normalizeBrand(m);
  const patterns = [
    [/^(GA-B\d|GAB\d|GA-\d|G-\d|DW-\d)/, '45'],
    [/^(F-91W|AE-1200)/, '36'],
    [/^(SPB)/, '40.5'],
    [/^(SRPD|SRPE|SRPG|SNZH|SKX)/, '42'],
    [/^(SNXS)/, '37'],
    [/^(NY\d|BN\d)/, '42'],
    [/^(RA-AA|RA-AC|RAAA|RAAC)/, '42'],
    [/^(T137)/, '40'],
    [/^(T127)/, '40'],
    [/^(L3\.|L2\.|L4\.)/, '39'],
    [/^(M0|M8|H3|H4)/, '40']
  ];
  for (const [rx, s] of patterns) {
    if (rx.test(m)) return `Ölçü - ${s} x ${s} mm`;
  }
  const defaults = {
    CASIO: '42',
    SEIKO: '41',
    'SEİKO': '41',
    CITIZEN: '42',
    ORIENT: '42',
    TISSOT: '40',
    ROLEX: '41',
    OMEGA: '42',
    LONGINES: '39',
    TUDOR: '41',
    HAMILTON: '40',
    TIMEX: '40'
  };
  const size = defaults[String(b).toUpperCase()] || '41';
  return `Ölçü - ${size} x ${size} mm`;
}

function normalizeOlcuLabel(value, model, brand) {
  const v = String(value || '').trim();
  if (!v) return estimateSizeLabel(model, brand);
  const pair = v.match(/(\d{2}(?:[\.,]\d{1,2})?)\s*[x×]\s*(\d{2}(?:[\.,]\d{1,2})?)\s*mm/i);
  if (pair) {
    const a = String(pair[1]).replace(',', '.');
    const b = String(pair[2]).replace(',', '.');
    return `Ölçü - ${Number(a) % 1 === 0 ? parseInt(a, 10) : Number(a)} x ${Number(b) % 1 === 0 ? parseInt(b, 10) : Number(b)} mm`;
  }
  const single = v.match(/(\d{2}(?:[\.,]\d{1,2})?)\s*mm/i);
  if (single) {
    const a = String(single[1]).replace(',', '.');
    const av = Number(a) % 1 === 0 ? parseInt(a, 10) : Number(a);
    return `Ölçü - ${av} x ${av} mm`;
  }
  return estimateSizeLabel(model, brand);
}

function detectDialColorFromModel(model) {
  const m = String(model || '').toUpperCase();
  if (/-1[A-Z0-9]*$/.test(m)) return 'Qara';
  if (/-2[A-Z0-9]*$/.test(m)) return 'Mavi';
  if (/-3[A-Z0-9]*$/.test(m)) return 'Yaşıl';
  if (/-4[A-Z0-9]*$/.test(m)) return 'Qırmızı';
  if (/-7[A-Z0-9]*$/.test(m)) return 'Boz';
  if (/(BL|BLUE|NAVY)/.test(m)) return 'Mavi';
  if (/(BK|BLACK)/.test(m)) return 'Qara';
  if (/(GR|GREEN)/.test(m)) return 'Yaşıl';
  if (/(WH|WHITE)/.test(m)) return 'Ağ';
  return '';
}

function heuristicClassifier(model, brandHint = '') {
  const m = String(model || '').toUpperCase().trim();
  const brand = normalizeBrand(brandHint) || inferBrand(m) || normalizeBrand(m);

  const out = {
    sr_dial_color: detectDialColorFromModel(m) || 'Qara',
    bracelet_type: 'Polad',
    gender: 'Kişi',
    movement: 'Kvarts',
    bracelet_color: 'Boz',
    case_material: 'Polad'
  };

  if (['SEIKO', 'SEİKO', 'ORIENT', 'TISSOT', 'ROLEX', 'OMEGA', 'LONGINES', 'TUDOR', 'HAMILTON'].includes(brand)) {
    out.movement = 'Mexanika';
  }

  if (brand === 'CITIZEN') {
    out.movement = /^(NY\d|NJ\d|NB\d)/.test(m) ? 'Mexanika' : 'Kvarts';
  }

  if (/^(GA-|GMA-|GAB|GA-B|G-|DW-|AE-|F-|A\d{3}|LTP|SHEEN|BABY-G|BGD)/.test(m) || brand === 'CASIO') {
    out.bracelet_type = 'Kauçuk';
    out.bracelet_color = 'Qara';
    out.case_material = 'Plastik';
    out.movement = 'Kvarts';
  }

  if (/^(RA-AC0|FAC|BAMBINO|SARB|PRESAGE|T137|PRX)/.test(m)) {
    out.bracelet_type = 'Dəri';
    out.bracelet_color = out.sr_dial_color === 'Qara' ? 'Qara' : 'Gəhvəyi';
  }

  if (/\b(30|31|32|33|34)\b/.test(m) || /^(LTP|SHEEN|LA670|BA-)/.test(m)) {
    out.gender = 'Qadın';
  }

  if (out.bracelet_type === 'Polad') out.bracelet_color = 'Boz';
  if (out.bracelet_type === 'Kauçuk' && out.bracelet_color === 'Boz') out.bracelet_color = 'Qara';

  return out;
}

function normalizeAllowed(value, allowed, fallback) {
  const raw = String(value || '').trim();
  if (!raw) return fallback;
  for (const c of allowed) {
    if (raw === c) return c;
  }
  for (const c of allowed) {
    if (raw.toLowerCase() === c.toLowerCase()) return c;
  }
  return fallback;
}

function buildClassifierPrompt(model, brandHint = '') {
  return (
    'You are an expert WATCH CATALOG CLASSIFIER. Return STRICT JSON only. No explanation.\n\n'
    + `MODEL_NUMBER: ${model}\n`
    + `BRAND_HINT: ${brandHint}\n\n`
    + 'Allowed values only:\n'
    + `sr_dial_color: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.sr_dial_color)}\n`
    + `bracelet_type: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.bracelet_type)}\n`
    + `gender: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.gender)}\n`
    + `movement: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.movement)}\n`
    + `bracelet_color: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.bracelet_color)}\n`
    + `case_material: ${JSON.stringify(CLASSIFIER_ALLOWED_VALUES.case_material)}\n\n`
    + 'Output JSON keys exactly: sr_dial_color, bracelet_type, gender, movement, bracelet_color, case_material'
  );
}

function tryParseJsonObject(text) {
  const t = String(text || '').trim();
  if (!t) return null;
  try {
    const j = JSON.parse(t);
    return j && typeof j === 'object' ? j : null;
  } catch (_) {}
  const m = t.match(/\{[\s\S]*\}/);
  if (!m) return null;
  try {
    const j = JSON.parse(m[0]);
    return j && typeof j === 'object' ? j : null;
  } catch (_) {
    return null;
  }
}

async function classifyWithAI(model, brandHint = '') {
  const apiKey = String(process.env.WIXWATCHSEARCH || process.env.GEMINI_API_KEY || '').trim();
  const defaults = heuristicClassifier(model, brandHint);
  if (!apiKey) return defaults;

  const prompt = buildClassifierPrompt(model, brandHint);

  try {
    let raw = '';
    if (apiKey.startsWith('sk-or-')) {
      const modelName = String(process.env.GEMINI_MODEL || 'google/gemini-2.5-pro').trim();
      const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelName,
          temperature: 0,
          response_format: { type: 'json_object' },
          messages: [{ role: 'user', content: prompt }]
        })
      });
      if (!resp.ok) return defaults;
      const body = await resp.json();
      raw = String((((body || {}).choices || [])[0] || {}).message?.content || '');
    } else {
      const modelName = String(process.env.GEMINI_MODEL || 'gemini-1.5-pro').trim();
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(modelName)}:generateContent?key=${encodeURIComponent(apiKey)}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0, responseMimeType: 'application/json' }
        })
      });
      if (!resp.ok) return defaults;
      const body = await resp.json();
      raw = String((((body || {}).candidates || [])[0] || {}).content?.parts?.[0]?.text || '');
    }

    const parsed = tryParseJsonObject(raw);
    if (!parsed) return defaults;

    return {
      sr_dial_color: normalizeAllowed(parsed.sr_dial_color, CLASSIFIER_ALLOWED_VALUES.sr_dial_color, defaults.sr_dial_color),
      bracelet_type: normalizeAllowed(parsed.bracelet_type, CLASSIFIER_ALLOWED_VALUES.bracelet_type, defaults.bracelet_type),
      gender: normalizeAllowed(parsed.gender, CLASSIFIER_ALLOWED_VALUES.gender, defaults.gender),
      movement: normalizeAllowed(parsed.movement, CLASSIFIER_ALLOWED_VALUES.movement, defaults.movement),
      bracelet_color: normalizeAllowed(parsed.bracelet_color, CLASSIFIER_ALLOWED_VALUES.bracelet_color, defaults.bracelet_color),
      case_material: normalizeAllowed(parsed.case_material, CLASSIFIER_ALLOWED_VALUES.case_material, defaults.case_material)
    };
  } catch (_) {
    return defaults;
  }
}

function generateHandleId(name) {
  const h = String(name || '').toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-').replace(/-+/g, '-');
  return h || 'product';
}

function buildCollection(spec) {
  const out = ['Bütün Məhsullar'];
  const brand = String(spec.brand || '').toUpperCase();
  if (BRAND_COLLECTIONS[brand]) out.push(BRAND_COLLECTIONS[brand]);
  ['siferblat_rengi', 'bilerzik', 'cinsi', 'olcu', 'mexanizm', 'kemer_rengi', 'korpus'].forEach((k) => {
    const v = String(spec[k] || '').trim();
    if (v) out.push(v);
  });
  return [...new Set(out)].join(';');
}

function findSpec(model) {
  const catalog = loadCatalog();
  const key = normalizeModelKey(model);
  if (catalog[key]) return catalog[key];
  for (const k of Object.keys(catalog)) {
    if (normalizeModelKey(k) === key) return catalog[k];
  }

  // partial match fallback (e.g. catalog has GA-B2100, input GA-B2100-1A1)
  for (const k of Object.keys(catalog)) {
    const ck = normalizeModelKey(k);
    if (key.startsWith(ck) || ck.startsWith(key)) return catalog[k];
  }

  const brand = inferBrand(model);
  return {
    name: `${BRAND_COLLECTIONS[brand] || brand || 'Watch'} ${model}`.trim(),
    brand: brand || 'Bütün Məhsullar',
    description: `Watch Model: ${model}`,
    price: '',
    image_url: 'https://dummyimage.com/1200x1200/e9ecef/212529.jpg?text=No+Image',
    siferblat_rengi: '',
    bilerzik: '',
    cinsi: '',
    olcu: '',
    mexanizm: '',
    kemer_rengi: '',
    korpus: ''
  };
}

function applyClassifierOnSpec(spec, classified, model) {
  const out = { ...(spec || {}) };
  if (!String(out.brand || '').trim()) {
    out.brand = inferBrand(model) || 'Bütün Məhsullar';
  }
  const size = normalizeOlcuLabel(out.olcu, model, out.brand || inferBrand(model));
  out.siferblat_rengi = out.siferblat_rengi || `SR - ${classified.sr_dial_color}`;
  out.bilerzik = out.bilerzik || `Bilərzik - ${classified.bracelet_type}`;
  out.cinsi = out.cinsi || `Cinsi - ${classified.gender}`;
  out.olcu = size;
  out.mexanizm = out.mexanizm || classified.movement;
  out.kemer_rengi = out.kemer_rengi || `KR - ${classified.bracelet_color}`;
  out.korpus = out.korpus || classified.case_material;
  return out;
}

async function createWixRowFromModel(model) {
  const baseSpec = findSpec(model);
  const brandHint = baseSpec.brand || inferBrand(model);
  const classified = await classifyWithAI(model, brandHint);
  const spec = applyClassifierOnSpec(baseSpec, classified, model);

  const row = {};
  WIX_COLUMNS.forEach((c) => { row[c] = ''; });
  row.handleId = generateHandleId(model);
  row.fieldType = 'Product';
  row.name = String(spec.name || model).slice(0, 255);
  row.description = `<p>${String(spec.description || `Watch Model: ${model}`)}</p>`;
  row.productImageUrl = String(spec.image_url || 'https://dummyimage.com/1200x1200/e9ecef/212529.jpg?text=No+Image');
  row.collection = buildCollection(spec);
  row.sku = model;
  row.price = String(spec.price || '');
  row.visible = 'true';
  row.inventory = '10';
  const b = String(spec.brand || '').toUpperCase();
  row.brand = BRAND_COLLECTIONS[b] || 'Bütün Məhsullar';
  return row;
}

function escapeCsv(value) {
  const s = String(value ?? '');
  if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

module.exports = {
  WIX_COLUMNS,
  createWixRowFromModel,
  escapeCsv
};
