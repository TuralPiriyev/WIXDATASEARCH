import csv
import json
import sys
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import WIX_COLUMNS, generate_handle_id  # noqa: E402


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        results = body.get("results", [])

        if not isinstance(results, list) or not results:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json; charset=utf-8"},
                "body": json.dumps({"error": "No data to generate CSV"})
            }

        normalized_results = []
        used_handles = set()

        for idx, row in enumerate(results, start=1):
            safe_row = dict(row) if isinstance(row, dict) else {}

            handle_id = str(safe_row.get("handleId", "")).strip()
            if not handle_id:
                fallback_source = str(safe_row.get("name") or safe_row.get("sku") or f"product-{idx}")
                handle_id = generate_handle_id(fallback_source)
            if not handle_id:
                handle_id = f"product-{idx}"

            base = handle_id
            suffix = 1
            while handle_id in used_handles:
                suffix += 1
                handle_id = f"{base}-{suffix}"
            used_handles.add(handle_id)

            field_type = str(safe_row.get("fieldType", "")).strip()
            if field_type not in ["Product", "Variant"]:
                field_type = "Product"

            safe_row["handleId"] = handle_id
            safe_row["fieldType"] = field_type

            for col in WIX_COLUMNS:
                val = safe_row.get(col, "")
                safe_row[col] = "" if val is None else str(val)

            normalized_results.append(safe_row)

        output = StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=WIX_COLUMNS,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\r\n"
        )
        writer.writeheader()
        for row in normalized_results:
            writer.writerow({col: row.get(col, "") for col in WIX_COLUMNS})

        csv_content = output.getvalue()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": "attachment; filename=wix_watches.csv"
            },
            "body": csv_content
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps({"error": f"CSV generation failed: {str(e)}"})
        }
