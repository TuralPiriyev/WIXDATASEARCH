import csv
import sys
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import WIX_COLUMNS, create_wix_row  # noqa: E402


def handler(event, context):
    try:
        example_row = create_wix_row(
            {
                "name": "Example Watch",
                "description": "This is an example watch product",
                "image_url": "https://example.com/watch.jpg",
                "brand": "Seiko",
                "specs": ["Quartz Movement", "Stainless Steel", "100m Water Resistant"]
            },
            "EXAMPLE001"
        )

        output = StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=WIX_COLUMNS,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\r\n"
        )
        writer.writeheader()
        writer.writerow({col: str(example_row.get(col, "") or "") for col in WIX_COLUMNS})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": "attachment; filename=wix_template.csv"
            },
            "body": output.getvalue()
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": '{"error": "' + str(e).replace('"', "'") + '"}'
        }
