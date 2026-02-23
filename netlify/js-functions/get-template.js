const { WIX_COLUMNS, createWixRowFromModel, escapeCsv } = require('./_shared');

exports.handler = async () => {
  const sample = await createWixRowFromModel('EXAMPLE001');
  const lines = [WIX_COLUMNS.join(','), WIX_COLUMNS.map((c) => escapeCsv(sample[c] || '')).join(',')];
  return {
    statusCode: 200,
    headers: {
      'content-type': 'text/csv; charset=utf-8',
      'content-disposition': 'attachment; filename=wix_template.csv'
    },
    body: lines.join('\r\n')
  };
};
