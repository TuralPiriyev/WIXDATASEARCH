const { WIX_COLUMNS, escapeCsv } = require('./_shared');

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const results = Array.isArray(body.results) ? body.results : [];
    if (!results.length) {
      return { statusCode: 400, body: JSON.stringify({ error: 'No data to generate CSV' }) };
    }

    const lines = [];
    lines.push(WIX_COLUMNS.join(','));
    for (const row of results) {
      const values = WIX_COLUMNS.map((c) => escapeCsv((row || {})[c] || ''));
      lines.push(values.join(','));
    }

    return {
      statusCode: 200,
      headers: {
        'content-type': 'text/csv; charset=utf-8',
        'content-disposition': 'attachment; filename=wix_watches.csv'
      },
      body: lines.join('\r\n')
    };
  } catch (e) {
    return {
      statusCode: 500,
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ error: String(e) })
    };
  }
};
