# 🧪 Testing & Debugging Guide

## Running Tests

### 1. Verify Installation
```bash
python -m pip list | find "Flask"
python -m pip list | find "requests"
python -m pip list | find "pandas"
```

### 2. Test Health Endpoint
Open your browser or use curl:
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-21T10:30:45.123456"
}
```

### 3. Test Search Endpoint (Manual)
Use a tool like Postman or curl:

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "model_numbers": ["SKX007", "SNZH55J1"]
  }'
```

### 4. Test with Sample Data
```
1. Open http://localhost:5000 in browser
2. Paste content from sample_models.txt
3. Click "Search & Extract Data"
4. Wait for completion
5. Click "Download WIX CSV"
```

---

## Common Test Cases

### Test 1: Single Model
**Input**: SKX007
**Expected**: Finds Seiko SKX007, extracts name and image

### Test 2: Multiple Models
**Input**: 
```
SKX007
SNZH55J1
FAA00016L
```
**Expected**: Processes all 3, returns results table

### Test 3: Invalid Model
**Input**: XYZABC123XYZ
**Expected**: Creates record with model number as fallback

### Test 4: Empty Input
**Input**: (nothing)
**Expected**: Shows error message

### Test 5: Special Characters
**Input**: SKX-007-J
**Expected**: Handles special characters in handle generation

---

## Debugging Tips

### Enable Debug Logs
The app already logs to console. Look for these prefixes:
- `INFO` - Normal operations
- `WARNING` - Issues but continuing
- `ERROR` - Problems occurred
- `DEBUG` - Detailed information

### View Browser Console Logs
1. Press `F12` in browser
2. Go to "Console" tab
3. Look for errors/warnings
4. Check "Network" tab for API calls

### Check Server Logs
Terminal where Flask is running shows:
```
INFO:app:Searching for model: SKX007
INFO:app:Chrono24 found: Seiko SKX007
```

### Common Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| "Chrono24 search failed" | Website blocked/timeout | Normal, uses fallback |
| "Google search failed" | Search issue | Normal, uses model number |
| "Error rendering index" | Template missing | Check templates/ folder |
| "Port already in use" | Port 5000 taken | Change port in app.py |
| "Module not found" | Dependency missing | Run pip install -r requirements.txt |

---

## Performance Testing

### Measure Search Speed
```python
import time
start = time.time()
# do search
end = time.time()
print(f"Time: {end - start:.2f} seconds")
```

### Expected Performance
- Single model: 2-3 seconds
- 5 models: 10-15 seconds
- 10 models: 20-30 seconds
- 50 models: 100-150 seconds

### Optimize Performance
If searches are slow:
1. Check internet connection
2. Try different search model (Chrono24 vs Google)
3. Increase timeout in app.py if needed
4. Consider adding threading (advanced)

---

## Network Debugging

### Check if Chrono24 is Accessible
```bash
curl -I https://www.chrono24.com
```
Should return: `HTTP/1.1 200 OK`

### Check if Google is Accessible
```bash
curl -I https://www.google.com/search?q=SKX007
```
Should return: `HTTP/1.1 200 OK`

### Check if Local Server is Running
```bash
curl http://localhost:5000/
```
Should return HTML content

---

## CSV Validation

### Check Generated CSV
1. Download the CSV
2. Open in Excel or Google Sheets
3. Verify:
   - All 10 columns present
   - No empty headers
   - Values in correct columns
   - Special characters handled
   - Image URLs valid

### CSV Column Validation
```
✓ handle      - lowercase, hyphens only, no spaces
✓ name        - Product name extracted
✓ description - Contains model + source info
✓ price       - Empty (fill in manually)
✓ sku         - Original model number
✓ visible     - "true"
✓ ribbon      - Empty (optional)
✓ inventory   - "10"
✓ weight      - Empty (optional)
✓ productImageUrl - URL or empty
```

---

## Error Recovery

### Issue: App Crashes on Startup
**Debug Steps:**
1. Check Python version: `python --version` (need 3.8+)
2. Check virtual env activated
3. Check dependencies: `pip install -r requirements.txt`
4. Check port not in use: `netstat -ano | findstr :5000` (Windows)

### Issue: Search Returns No Results
**Debug Steps:**
1. Check internet connection
2. Test website manually (Chrono24, Google)
3. Try different model number
4. Check logs for errors
5. Increase REQUEST_TIMEOUT in app.py

### Issue: CSV Won't Download
**Debug Steps:**
1. Check browser console (F12)
2. Check flask logs
3. Try different browser
4. Clear browser cache
5. Try smaller batch (fewer models)

### Issue: HTML Not Loading
**Debug Steps:**
1. Verify `templates/index.html` exists
2. Check file permissions
3. Try refreshing browser (Ctrl+F5)
4. Check Flask error logs

---

## Advanced Debugging

### Enable Verbose Logging
Edit app.py:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Profile Code Execution
```python
import cProfile
cProfile.run('search_watch_data("SKX007")')
```

### Memory Usage
```python
import tracemalloc
tracemalloc.start()
# ... run code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")
```

---

## Unit Test Examples

### Test Search Function
```python
def test_search():
    result = search_watch_data("SKX007")
    assert result is not None
    assert 'name' in result
    assert 'description' in result
    assert 'image_url' in result

test_search()
print("✓ Search function works")
```

### Test Handle Generation
```python
def test_handle():
    assert generate_handle("Seiko SKX007") == "seiko-skx007"
    assert generate_handle("CITIZEN ECO-DRIVE") == "citizen-eco-drive"
    assert generate_handle("TAG Heuer!!!") == "tag-heuer"

test_handle()
print("✓ Handle generation works")
```

### Test CSV Generation
```python
def test_csv():
    test_data = [{
        'handle': 'test-watch',
        'name': 'Test Watch',
        'sku': 'TEST001',
        # ... other fields
    }]
    # Try generating CSV
    # Check if file created correctly

test_csv()
print("✓ CSV generation works")
```

---

## Browser DevTools Checks

### Network Tab
1. Check API calls to `/api/search`
2. Verify response status (200)
3. Check response time
4. Verify JSON response format

### Console Tab
1. Check for JavaScript errors
2. Look for CORS errors
3. Check for network warnings

### Storage Tab
1. Check localStorage (if using caching)
2. Verify no sensitive data stored

---

## WIX Integration Testing

### Before Importing
1. ✓ Download CSV locally
2. ✓ Open in Excel - verify formatting
3. ✓ Check for duplicate SKUs
4. ✓ Verify image URLs work
5. ✓ Check all required fields populated

### After Importing
1. ✓ Login to WIX dashboard
2. ✓ Go to Products
3. ✓ Filter by import date
4. ✓ Click each product
5. ✓ Verify data displays correctly
6. ✓ Check images load
7. ✓ Verify descriptions are readable
8. ✓ Test purchase flow

---

## Reporting Issues

If you encounter issues, provide:
1. Error message (copy from console)
2. Steps to reproduce
3. Model number tested
4. Python version: `python --version`
5. OS: Windows/Mac/Linux
6. Browser type
7. Flask console output
8. Browser console output (F12)

---

## Performance Optimization Tips

### For Faster Searches
1. Use wired internet (not WiFi)
2. Close other applications
3. Reduce number of models per batch
4. Increase timeout if on slow connection

### For Faster CSV Download
1. Ensure good internet
2. Disable browser extensions
3. Use wired connection
4. Clear browser cache

### For Better Stability
1. Update Python to latest 3.x version
2. Update Flask and dependencies
3. Use recommended browser (Chrome/Firefox)
4. Restart computer if running long
5. Don't paste 100+ models at once

---

## Useful Debug Commands

### Python Shell Tests
```python
python
>>> from app import search_watch_data, generate_handle
>>> search_watch_data("SKX007")
>>> generate_handle("Seiko SKX007")
>>> exit()
```

### Check Dependencies
```bash
pip list
pip show Flask
pip show requests
```

### Test API Directly
```bash
# GET health
curl http://localhost:5000/api/health

# POST search (requires curl with JSON)
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"model_numbers": ["SKX007"]}'
```

---

**Need Help?**
1. Check README.md for full documentation
2. Check QUICK_START.md for setup
3. Review logs in console
4. Check browser DevTools (F12)
5. Try test with sample data first

**Last Updated**: February 2026
