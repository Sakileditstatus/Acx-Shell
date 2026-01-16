# Acx Shell

A Flask-based web application for protecting Android APK/AAB files using DPT (Dex Protection Tool).

## Features

- 🛡️ Protect APK/AAB files with advanced encryption
- ⚙️ Multiple protection options
- 📱 Modern, responsive web interface
- 🚀 Easy deployment on Render (free tier)

## Protection Options

- **Debug Mode**: Make package debuggable
- **Disable ACF**: Disable app component factory
- **Dump Code**: Dump code items to JSON files
- **Keep Classes**: Keep some classes for faster startup
- **Noisy Log**: Enable verbose logging
- **Smaller Size**: Trade performance for smaller app size
- **Exclude ABIs**: Exclude specific architectures (arm, arm64, x86, x86_64)
- **Rules File**: Use custom ProGuard rules (custom-rules.rules)
- **Protect Config**: Use custom protection configuration
- **Auto Signing**: APK is always signed (required for installation)

## Setup

### 🚀 Quick Start (All Platforms - Recommended)

**Just run one command:**

- **Windows**: Double-click `run.bat` or run `python main.py`
- **Linux/Mac**: Run `bash run.sh` or `python3 main.py`

The `main.py` script will automatically:
- ✓ Check Python installation
- ✓ Check Java JDK 21
- ✓ Create virtual environment
- ✓ Install all dependencies
- ✓ Verify all files
- ✓ Start the application


### Linux/Mac Local Development

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure Java JDK 21 is installed (required for dpt.jar)
4. Run the application:
   ```bash
   python app.py
   ```
5. Open http://localhost:5000 in your browser

### Deploy on Render (Recommended - Free Tier Available)

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` which includes:
   - Java JDK 21 installation
   - Python dependencies installation
   - Proper environment variables

**Alternative: Using Docker**
- Render can also use the provided `Dockerfile` which includes Java JDK 21
- Select "Docker" as the environment type

### Deploy on Google Cloud Run (Serverless-like)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT/apk-protection
gcloud run deploy apk-protection \
  --image gcr.io/YOUR_PROJECT/apk-protection \
  --platform managed \
  --memory 4Gi \
  --timeout 900 \
  --allow-unauthenticated
```

### Other Deployment Options

See [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md) for:
- AWS App Runner
- Railway
- Fly.io
- And more options

**Note:** This app is NOT suitable for traditional serverless (Lambda/Functions) due to:
- Long execution times (up to 10 minutes)
- Large file processing (500MB)
- Java subprocess requirements

Use container-based platforms (Cloud Run, App Runner) or traditional hosting (Render, Railway).

## Requirements

- Python 3.11+
- Java JDK 21 (for running dpt.jar)
- Flask 3.0.0
- flask-cors 4.0.0
- dpt.jar (included in `executable/` folder)

## File Structure

```
.
├── main.py                         # Auto setup and run script
├── app.py                          # Flask application
├── requirements.txt                # Python dependencies
├── run.bat                         # Windows quick launcher
├── run.sh                          # Linux/Mac quick launcher
├── render.yaml                     # Render deployment config (free tier optimized)
├── RENDER_FREE_TIER_SETUP.md       # Complete Render setup guide
├── Dockerfile                      # Docker deployment config
├── templates/
│   └── index.html                  # Frontend interface
├── executable/
│   ├── dpt.jar                     # Protection tool
│   ├── dpt-exclude-classes-template.rules
│   └── dpt-protect-config-template.json
└── README.md
```

## Usage

1. Upload your APK or AAB file
2. Select desired protection options
3. Click "Protect APK"
4. Wait for processing (may take a few minutes)
5. Download the protected file

## Notes

- Maximum file size: 150MB (optimized for Render free tier)
- Processing time: Up to 5 minutes (free tier limit)
- Processing time depends on APK size and complexity
- The protected APK will be automatically downloaded when ready
- Free tier service may sleep after 15 minutes of inactivity

## License

This project uses DPT (Dex Protection Tool) for APK protection.
