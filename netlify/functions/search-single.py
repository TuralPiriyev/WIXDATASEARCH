import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import search_watch_data, create_wix_row, extract_brand  # noqa: E402


def _json_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8"
        },
        "body": json.dumps(payload, ensure_ascii=False)
    }


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        model_number = str(body.get("model_number", "") or "").strip()

        if not model_number:
            return _json_response(400, {"error": "model_number is required"})

        try:
            watch_data = search_watch_data(model_number)
            wix_row = create_wix_row(watch_data, model_number)
            return _json_response(200, {
                "success": True,
                "result": wix_row,
                "model_number": model_number,
            })
        except Exception as model_error:
            fallback_row = create_wix_row(
                {
                    "name": model_number,
                    "description": f"Watch Model: {model_number}",
                    "image_url": "",
                    "brand": extract_brand(model_number),
                    "specs": []
                },
                model_number,
            )
            return _json_response(200, {
                "success": False,
                "result": fallback_row,
                "model_number": model_number,
                "error": str(model_error),
            })
    except Exception as e:
        return _json_response(500, {"error": str(e)})
