# 🔧 CORS Troubleshooting Guide

## Quick Fixes for CORS Issues

### 1. **Start Both Servers**
Make sure both servers are running:

```bash
# Terminal 1: Main website server
python3 server.py 8000

# Terminal 2: API server  
cd api
python3 app.py
```

### 2. **Check Server Status**
Test if both servers are running:

```bash
# Test main server
curl http://localhost:8000

# Test API server
curl http://localhost:5001/api/health
```

### 3. **Browser Console Check**
Open browser developer tools (F12) and check the Console tab for CORS errors. Common errors:

- `Access to fetch at 'http://localhost:5001/api/health' from origin 'http://localhost:8000' has been blocked by CORS policy`
- `No 'Access-Control-Allow-Origin' header is present`

### 4. **CORS Configuration Fixed**
The API server now has enhanced CORS configuration:

- ✅ Allows requests from `http://localhost:8000` and `http://127.0.0.1:8000`
- ✅ Handles OPTIONS preflight requests
- ✅ Supports all necessary HTTP methods
- ✅ Fallback to permissive CORS for development

### 5. **Test CORS Manually**
Run the CORS test script:

```bash
python3 test_cors.py
```

### 6. **Common Solutions**

**If you still get CORS errors:**

1. **Clear browser cache** - CORS errors can be cached
2. **Try incognito/private mode** - Avoids cached CORS policies
3. **Check firewall** - Make sure port 5000 isn't blocked
4. **Use different browser** - Some browsers handle CORS differently

**If API server won't start:**

1. **Check port 5001 is free:**
   ```bash
   lsof -i :5001
   ```

2. **Kill any process using port 5001:**
   ```bash
   kill -9 $(lsof -t -i:5001)
   ```

3. **Port 5000 is used by AirTunes/AirPlay on macOS:**
   - The API server now runs on port 5001 by default
   - This avoids conflicts with Apple's AirPlay service

### 7. **Alternative: Use the Startup Script**
The easiest way to start both servers:

```bash
./start-all-servers.sh
```

This script handles starting both servers and provides better error messages.

### 8. **Debug Mode**
Enable debug mode in the API server by editing `api/app.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

This will show detailed error messages in the console.

## 🎯 Expected Behavior

When everything is working correctly:

1. **Main server** runs on http://localhost:8000
2. **API server** runs on http://localhost:5001
3. **Admin interface** at http://localhost:8000/admin/ can communicate with API
4. **Push to Google Sheets** button works without CORS errors

## 🚨 Still Having Issues?

If you're still experiencing CORS problems:

1. **Check the browser Network tab** - Look for failed requests
2. **Check API server logs** - Look for error messages
3. **Try the test script** - `python3 test_cors.py`
4. **Restart both servers** - Sometimes a fresh start helps

The CORS configuration has been enhanced to handle most common scenarios. The fallback to permissive CORS should resolve most development issues.
