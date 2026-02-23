# Watch Data Scraper & Wix Porter

A web-based tool to search for watch models, extract product details and images, and generate WIX-compatible CSV files for store import.

## Features

✅ **Easy-to-use Web Interface** - Clean, modern UI built with Tailwind CSS
✅ **Multi-source Search** - Searches Chrono24 and Google for watch data
✅ **Automatic Data Extraction** - Extracts product name, description, and image URLs
✅ **WIX CSV Generation** - Outputs data in exact WIX Stores import format
✅ **Progress Tracking** - Real-time progress indicator during searches
✅ **Batch Processing** - Handle multiple model numbers at once

## Tech Stack

- **Backend**: Python Flask
- **Web Scraping**: BeautifulSoup4, Requests
- **Data Processing**: Pandas
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **CSV Handling**: Python csv module

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step-by-Step Setup

1. **Navigate to the project directory:**
   ```bash
   cd c:\Users\Admin\Desktop\WIXSEARCHSYSTEM
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   
   **On Windows (PowerShell):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   **On Windows (Command Prompt):**
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Ensure your virtual environment is activated** (you should see `(venv)` in your terminal)

2. **Start the Flask server:**
   ```bash
   python app.py
   ```

3. **Open your web browser:**
   ```
   http://localhost:5000
   ```

4. **Use the application:**
   - Paste watch model numbers in the text area (one per line)
   - Click "Search & Extract Data"
   - Wait for the search to complete
   - Review the extracted data in the table
   - Click "Download WIX CSV" to get the file

## WIX CSV Format

The output CSV file includes these columns required by WIX:

| Column | Purpose | Default Value |
|--------|---------|---|
| `handle` | Product URL slug | Derived from product name |
| `name` | Product name | Extracted from search |
| `description` | Product description | Model number + source |
| `price` | Product price | Empty (you fill in) |
| `sku` | Stock keeping unit | Original model number |
| `visible` | Is product visible | true |
| `ribbon` | Ribbon/badge text | Empty |
| `inventory` | Stock quantity | 10 |
| `weight` | Product weight | Empty |
| `productImageUrl` | Image URL | Extracted from search |

## How It Works

1. **Input**: User pastes watch model numbers
2. **Search**: System searches multiple sources:
   - Chrono24 (specialized watch marketplace)
   - Google Images & Search
3. **Extract**: Extracts:
   - Product name
   - Technical specifications
   - Primary image URL
4. **Transform**: Converts to WIX format:
   - Generates URL-friendly handles
   - Maps fields to WIX columns
   - Applies default values
5. **Output**: Downloads CSV file ready for import

## API Endpoints

### POST `/api/search`
Searches for watch data based on model numbers.

**Request:**
```json
{
  "model_numbers": ["SKX007", "SNZH55J1"]
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "handle": "seiko-skx007",
      "name": "Seiko SKX007",
      "description": "Model: SKX007 - Search Result",
      "price": "",
      "sku": "SKX007",
      "visible": "true",
      "ribbon": "",
      "inventory": "10",
      "weight": "",
      "productImageUrl": "https://..."
    }
  ]
}
```

### POST `/api/generate-csv`
Generates and returns CSV file for download.

**Request:**
```json
{
  "results": [...]
}
```

**Response:** CSV file (text/csv)

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Search Not Finding Results
- The tool will still create entries with model numbers as fallback
- You can manually fill in product details after import to WIX
- Make sure you have an active internet connection
- Some websites may block automated requests (check logs)

### Virtual Environment Not Activating
On Windows PowerShell, you may need to change execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Errors
Ensure all dependencies are installed:
```bash
pip install --upgrade -r requirements.txt
```

## File Structure

```
WIXSEARCHSYSTEM/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Frontend HTML interface
```

## Usage Examples

### Example 1: Single Watch Model
```
Input: SKX007
Output: Handle: seiko-skx007, Name: Seiko SKX007, SKU: SKX007
```

### Example 2: Multiple Watch Models
```
Input:
SKX007
SNZH55J1
FAA00016L

Output: CSV with 3 products, ready for WIX import
```

## Features & Customization

### Modifying Search Sources
Edit the `search_watch_data()` function in `app.py` to add or change data sources.

### Adjusting Default Values
Modify these constants in `app.py`:
- `inventory`: Change default stock (currently 10)
- `visible`: Change default visibility (currently true)

### Rate Limiting
To add delays between requests (avoid being blocked):
```python
import time
time.sleep(2)  # 2-second delay between requests
```

## Performance Notes

- Average search time: 2-3 seconds per model
- Batch processing is sequential (can be optimized with threading)
- Image extraction works best with Chrono24 source
- Google searches are fallback only

## Future Enhancements

- [ ] Add SerpApi integration for more reliable Google searches
- [ ] Implement threading for parallel searches
- [ ] Cache search results to avoid duplicate requests
- [ ] Add more watch-specific sources
- [ ] Support for Excel (.xlsx) output
- [ ] Batch scheduling for large imports
- [ ] Database storage for historical searches

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Flask and BeautifulSoup documentation
3. Check internet connection and proxy settings
4. Verify all dependencies are installed correctly

---

**Created**: February 2026
**Version**: 1.0
