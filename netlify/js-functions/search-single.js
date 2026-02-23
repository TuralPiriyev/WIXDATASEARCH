const { createWixRowFromModel } = require('./_shared');

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const model = String(body.model_number || '').trim();
    if (!model) {
      return { statusCode: 400, body: JSON.stringify({ error: 'model_number is required' }) };
    }
    const result = await createWixRowFromModel(model);
    return {
      statusCode: 200,
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ success: true, model_number: model, result })
    };
  } catch (e) {
    const msg = String(e && e.message ? e.message : e);
    const invalidModel = /MODEL_CODE_NOT_IDENTIFIED|SERIES_CODE_NOT_IDENTIFIED|MODEL_INPUT_EMPTY/.test(msg);
    return {
      statusCode: invalidModel ? 422 : 500,
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ error: msg })
    };
  }
};
