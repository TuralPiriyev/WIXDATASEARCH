# 🚀 QUICK START GUIDE

## 5-Minute Setup

### For Windows Users

**Option 1: Automatic Setup (Easiest)**
1. Open File Explorer and navigate to the project folder
2. Double-click `run.bat`
3. The script will:
   - Create virtual environment
   - Install all dependencies
   - Start the Flask server
   - Open browser to http://localhost:5000

**Option 2: Manual Setup**
1. Open PowerShell in this folder
2. Run these commands:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```
3. Open browser to http://localhost:5000

### For macOS/Linux Users

1. Open Terminal in this folder
2. Make run script executable:
   ```bash
   chmod +x run.sh
   ```
3. Run it:
   ```bash
   ./run.sh
   ```
4. Open browser to http://localhost:5000

---

## Using the Application

### Step 1: Enter Watch Model Numbers
- Click in the text area
- Paste or type watch model numbers
- One model per line
- Example:
  ```
  SKX007
  SNZH55J1
  FAA00016L
  ```

### Step 2: Click Search
- Click the "Search & Extract Data" button
- Wait for the progress bar to complete
- The system searches and extracts data for each model

### Step 3: Review Results
- Table shows extracted data for all models
- Check product names, handles, and image URLs
- Click "View Image" links to verify images

### Step 4: Download CSV
- Click "Download WIX CSV" button
- File `wix_watches.csv` is saved to your Downloads folder

### Step 5: Import to WIX
1. Login to your WIX Store
2. Go to Products → Import Products
3. Upload the downloaded CSV file
4. Review and confirm import
5. Edit any missing information (prices, descriptions, etc.)

---

## Sample Data

The file `sample_models.txt` contains 8 popular watch models you can use for testing:
- SKX007 (Seiko Diver)
- SNZH55J1 (Seiko 5 Sports)
- FAA00016L (Citizen Eco-Drive)
- SRP777K1 (Seiko Prospex)
- SPB187J1 (Seiko Prospex)
- SNZF23J1 (Seiko 5)
- SRPE69K1 (Seiko Prospex)
- FAA02004B (Citizen Eco-Drive)

Copy-paste these to test the application!

---

## Troubleshooting

### "Python not found"
- Install Python 3.8+ from https://www.python.org
- During installation, check "Add Python to PATH"
- Restart your computer
- Try again

### Port 5000 already in use
- Edit last line of `app.py`:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
  ```
- Then restart the server

### No search results
- Check your internet connection
- Website may be blocking requests (normal behavior)
- System will still create records with model numbers
- You can manually add details in WIX after import

### Virtual environment won't activate (PowerShell)
Run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## WIX CSV Format Explained

Generated CSV contains these columns:

| Column | What It Is | Your Action |
|--------|-----------|------------|
| handle | URL slug (auto-generated) | Leave as-is |
| name | Product name (auto-filled) | Review & edit if needed |
| description | Product description (auto-filled) | Add more details |
| price | Product price (empty) | **YOU MUST FILL THIS** |
| sku | Model number (auto-filled) | Usually correct |
| visible | Is it visible in store? | true (visible) or false (hidden) |
| ribbon | Sale badge/ribbon | Leave empty or add "Sale", "New", etc. |
| inventory | Stock quantity (default: 10) | Update your actual inventory |
| weight | Product weight | Leave empty or add shipping weight |
| productImageUrl | Image URL (auto-filled) | Verify images work |

---

## Advanced Features

### Editing Search Sources
Edit `app.py` to add more websites:
- Look for `search_chrono24()` and `search_google()`
- Add new functions for additional sources
- Update `search_watch_data()` to call them

### Custom Default Values
Edit these in `app.py`:
```python
'inventory': '10'      # Change to your default
'visible': 'true'      # Change visibility
```

### Adding Rate Limiting
To avoid being blocked by websites:
```python
import time
time.sleep(2)  # Add 2-second delay between requests
```

---

## Support Files

- `README.md` - Full documentation
- `requirements.txt` - Python dependencies
- `config.ini` - Configuration options
- `sample_models.txt` - Test data
- `run.bat` - Windows startup script
- `run.sh` - macOS/Linux startup script

---

## Next Steps

After generating your CSV:

1. **Review the data** in Excel or Google Sheets
2. **Fill in missing information** (prices, detailed descriptions)
3. **Update inventory counts** to match your stock
4. **Add high-quality images** if extracted images don't work
5. **Import to WIX** using the Products import tool
6. **Publish** your products to the store

---

**Happy selling! 🎉**

For detailed help, see `README.md` for complete documentation.
