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

function normalizeModelKey(model) {
  return String(model || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function inferBrand(model) {
  const m = String(model || '').toUpperCase().trim();
  if (/^(SKX|SNZH|SRP|SRPE|SNK|SSA|SSK|SNXS|SPB)/.test(m)) return 'SEIKO';
  if (/^(RA-|RA\d|F[A-Z]{2}\d|AC\d)/.test(m)) return 'ORIENT';
  if (/^(BN\d|NJ\d|NY\d)/.test(m)) return 'CITIZEN';
  if (/^(F-\d|AE-\d|GA-\d|GA-B\d|GAB\d|G-\d|DW-\d|A\d{3})/.test(m)) return 'CASIO';
  if (/^(T\d|PRX|LE\s?LOCLE|SEASTAR)/.test(m)) return 'TISSOT';
  return '';
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
  const brand = inferBrand(model);
  return {
    name: `${BRAND_COLLECTIONS[brand] || brand || 'Watch'} ${model}`.trim(),
    brand: brand || 'Bütün Məhsullar',
    description: `Watch Model: ${model}`,
    price: '',
    image_url: 'https://dummyimage.com/1200x1200/e9ecef/212529.jpg?text=No+Image',
    siferblat_rengi: 'SR - Qara',
    bilerzik: 'Bilərzik - Polad',
    cinsi: 'Cinsi - Kişi',
    olcu: 'Ölçü - 41 x 41 mm',
    mexanizm: brand === 'CASIO' ? 'Kvarts' : 'Mexanika',
    kemer_rengi: 'KR - Boz',
    korpus: 'Polad'
  };
}

function createWixRowFromModel(model) {
  const spec = findSpec(model);
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
