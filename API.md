# Acx Shell API Documentation

## Overview

Acx Shell is a Flask-based web application for protecting Android APK/AAB files using DPT (Dex Protection Tool). This document describes all available API endpoints.

## Base URL

- **Local Development**: `http://localhost:5000`
- **Production**: `https://your-render-app.onrender.com`

## Endpoints

### 1. Get Home Page

**Endpoint**: `GET /`

**Description**: Returns the main web interface (HTML page) for uploading and protecting APK files.

**Request**:
```http
GET / HTTP/1.1
```

**Response**:
- **Status Code**: `200 OK`
- **Content-Type**: `text/html`
- **Body**: HTML page with the Acx Shell interface

**Example**:
```bash
curl http://localhost:5000/
```

---

### 2. Protect APK

**Endpoint**: `POST /protect`

**Description**: Protects an Android APK or AAB file using DPT (Dex Protection Tool) with various protection options.

**Request**:
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

**Form Data Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `apk_file` | File | Yes | The APK or AAB file to protect (max 150MB) |
| `debug` | String | No | Set to `"true"` to make package debuggable |
| `disable_acf` | String | No | Set to `"true"` to disable app component factory |
| `dump_code` | String | No | Set to `"true"` to dump code items to JSON files |
| `keep_classes` | String | No | Set to `"true"` to keep some classes for faster startup |
| `noisy_log` | String | No | Set to `"true"` to enable verbose logging |
| `smaller` | String | No | Set to `"true"` to trade performance for smaller size |
| `exclude_abis` | String | No | Comma-separated ABIs to exclude (e.g., `"x86,x86_64"`) |
| `use_protect_config` | String | No | Set to `"true"` to use custom protect config file |

**Supported ABIs for `exclude_abis`**:
- `arm` (armeabi-v7a)
- `arm64` (arm64-v8a)
- `x86`
- `x86_64`

**Success Response**:
- **Status Code**: `200 OK`
- **Content-Type**: `application/vnd.android.package-archive`
- **Headers**:
  - `Content-Disposition`: `attachment; filename="protected_<original_filename>"`
  - `Content-Length`: File size in bytes
- **Body**: Protected APK/AAB file (binary)

**Error Responses**:

| Status Code | Description |
|-------------|-------------|
| `400 Bad Request` | Invalid file type, file too large (>150MB), or file already protected |
| `500 Internal Server Error` | Protection failed, Java not found, or server error |

**Error Response Format**:
```json
{
  "error": "Error message",
  "details": "Detailed error information"
}
```

**Example Request**:
```bash
curl -X POST http://localhost:5000/protect \
  -F "apk_file=@app.apk" \
  -F "debug=true" \
  -F "keep_classes=true" \
  -F "smaller=true" \
  -F "exclude_abis=x86,x86_64" \
  --output protected_app.apk
```

**Example with cURL**:
```bash
curl -X POST http://localhost:5000/protect \
  -F "apk_file=@myapp.apk" \
  -F "debug=true" \
  -F "keep_classes=true" \
  -o protected_myapp.apk
```

**Example with Python**:
```python
import requests

url = "http://localhost:5000/protect"
files = {'apk_file': open('app.apk', 'rb')}
data = {
    'debug': 'true',
    'keep_classes': 'true',
    'smaller': 'true',
    'exclude_abis': 'x86,x86_64'
}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    with open('protected_app.apk', 'wb') as f:
        f.write(response.content)
    print("APK protected successfully!")
else:
    print(f"Error: {response.json()}")
```

**Example with JavaScript (Fetch API)**:
```javascript
const formData = new FormData();
formData.append('apk_file', fileInput.files[0]);
formData.append('debug', 'true');
formData.append('keep_classes', 'true');

fetch('/protect', {
    method: 'POST',
    body: formData
})
.then(response => {
    if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
    }
    return response.blob();
})
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'protected_app.apk';
    a.click();
})
.catch(error => {
    console.error('Error:', error);
});
```

**Notes**:
- Maximum file size: **150MB** (free tier limit)
- Processing timeout: **5 minutes** (free tier limit)
- APK is **always signed** by default (no-sign option removed)
- Custom rules file option has been removed
- The protected file will be named `protected_<original_filename>`

---

### 3. Health Check

**Endpoint**: `GET /health`

**Description**: Returns the health status of the API server, including Java availability and DPT JAR file status.

**Request**:
```http
GET /health HTTP/1.1
```

**Response**:
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`

**Response Body**:
```json
{
  "status": "ok",
  "dpt_jar_exists": true,
  "java_available": true,
  "java_version": "openjdk version \"21.0.1\" 2023-10-17"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | Always `"ok"` if endpoint is reachable |
| `dpt_jar_exists` | Boolean | Whether the DPT JAR file exists |
| `java_available` | Boolean | Whether Java JDK is available |
| `java_version` | String | Java version string or `"Not found"` |

**Example**:
```bash
curl http://localhost:5000/health
```

**Example Response**:
```json
{
  "status": "ok",
  "dpt_jar_exists": true,
  "java_available": true,
  "java_version": "openjdk version \"21.0.1\" 2023-10-17\nOpenJDK Runtime Environment (build 21.0.1+12-29)\nOpenJDK 64-Bit Server VM (build 21.0.1+12-29, mixed mode, sharing)"
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters or file validation failed
- **500 Internal Server Error**: Server error, protection failed, or Java not available

Error responses include a JSON object with error details:

```json
{
  "error": "Brief error message",
  "details": "Detailed error information or stack trace"
}
```

## Rate Limiting

Currently, there are no rate limits implemented. However, for free tier deployments:

- **File Size Limit**: 150MB per request
- **Processing Timeout**: 5 minutes per request
- **Concurrent Requests**: Limited by server resources

## Security Considerations

1. **File Validation**: Only APK and AAB files are accepted
2. **File Size Limits**: Maximum 150MB per file (free tier)
3. **Duplicate Protection**: Files starting with `protected_` are rejected
4. **Temporary Files**: All temporary files are cleaned up after processing
5. **CORS**: Enabled for cross-origin requests (if flask-cors is installed)

## DPT Command Options Reference

The following options are available for APK protection (mapped to form parameters):

| Form Parameter | DPT Option | Description |
|----------------|-----------|-------------|
| `debug` | `--debug` | Make package debuggable |
| `disable_acf` | `--disable-acf` | Disable app component factory |
| `dump_code` | `--dump-code` | Dump code items to JSON files |
| `keep_classes` | `-K` | Keep some classes for faster startup |
| `noisy_log` | `--noisy-log` | Enable verbose logging |
| `smaller` | `-S` | Trade performance for smaller size |
| `exclude_abis` | `-e` | Exclude specific ABIs (comma-separated) |
| `use_protect_config` | `-c` | Use custom protect config file |

**Note**: The `--no-sign` option has been removed. APKs are always signed by default.

## Examples

### Protect APK with Debug Mode
```bash
curl -X POST http://localhost:5000/protect \
  -F "apk_file=@app.apk" \
  -F "debug=true" \
  -o protected_app.apk
```

### Protect APK with Multiple Options
```bash
curl -X POST http://localhost:5000/protect \
  -F "apk_file=@app.apk" \
  -F "debug=true" \
  -F "keep_classes=true" \
  -F "smaller=true" \
  -F "exclude_abis=arm,x86" \
  -o protected_app.apk
```

### Check Server Health
```bash
curl http://localhost:5000/health
```

## Support

For issues, questions, or contributions, please contact:
- **Telegram**: [https://t.me/+qvphv9Q8d1hhMzNl](https://t.me/+qvphv9Q8d1hhMzNl)

## License

Copyright © 2026 Acx Shell. All rights reserved.
