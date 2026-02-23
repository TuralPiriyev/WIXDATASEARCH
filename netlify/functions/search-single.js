const { createWixRowFromModel } = require('./_shared');

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const model = String(body.model_number || '').trim();
    if (!model) {
      return { statusCode: 400, body: JSON.stringify({ error: 'model_number is required' }) };
    }
    const result = createWixRowFromModel(model);
    return {
      statusCode: 200,
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ success: true, model_number: model, result })
    };
  } catch (e) {
    return {
      statusCode: 500,
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ error: String(e) })
    };
  }
};
