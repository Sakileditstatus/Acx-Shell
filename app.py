import os
import sys
import subprocess
import tempfile
import shutil
import traceback
import logging
import hashlib
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

# Configure logging to show errors in terminal
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import CORS - make it optional for environments where it's not installed
try:
    from flask_cors import CORS  # type: ignore
    cors_available = True
except ImportError:
    cors_available = False
    CORS = None  # type: ignore
    print("Warning: flask-cors not installed. CORS support disabled.")

app = Flask(__name__)
if cors_available and CORS:
    CORS(app)  # Enable CORS for all routes
app.config['MAX_CONTENT_LENGTH'] = 150 * 1024 * 1024  # 150MB max file size (Render free tier optimized)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for file downloads

# Path to dpt.jar
DPT_JAR_PATH = os.path.join(os.path.dirname(__file__), 'executable', 'dpt.jar')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/protect', methods=['POST'])
def protect_apk():
    try:
        logger.info("=" * 60)
        logger.info("Acx Shell - APK Protection Request Received")
        logger.info("=" * 60)
        
        # Check if file is present
        if 'apk_file' not in request.files:
            error_msg = 'No APK file provided'
            logger.error(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        file = request.files['apk_file']
        if file.filename == '':
            error_msg = 'No file selected'
            logger.error(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        if not file.filename.lower().endswith(('.apk', '.aab')):
            error_msg = 'Invalid file type. Only APK and AAB files are supported'
            logger.error(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        # Validate file size before processing (150MB limit for Render free tier)
        # Read file content length from request
        file.seek(0, os.SEEK_END)
        file_size_bytes = file.tell()
        file.seek(0)  # Reset to beginning
        max_size = 150 * 1024 * 1024  # 150MB limit for free tier
        
        if file_size_bytes > max_size:
            error_msg = f'File size ({file_size_bytes / (1024*1024):.2f} MB) exceeds maximum allowed size (150 MB) for free tier. Please use a smaller APK file.'
            logger.error(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        logger.info(f"File size validated: {file_size_bytes / (1024*1024):.2f} MB (within 150MB free tier limit)")
        
        # Calculate file hash to prevent duplicate protection
        file.seek(0)
        file_content = file.read()
        file.seek(0)  # Reset for later use
        file_hash = hashlib.md5(file_content).hexdigest()
        logger.info(f"File hash (MD5): {file_hash}")
        
        # Check if file was already protected (check if filename starts with "protected_")
        original_filename = file.filename
        if original_filename.startswith('protected_'):
            error_msg = 'This file appears to be already protected. Please upload the original APK file, not the protected version.'
            logger.warning(f"Duplicate protection attempt detected: {original_filename}")
            return jsonify({'error': error_msg}), 400
        
        # Create temporary directory for processing (Windows compatible)
        # Use /tmp on Render for better performance, fallback to system temp
        if os.path.exists('/tmp'):
            temp_base = '/tmp'
        else:
            temp_base = tempfile.gettempdir()
        temp_dir = tempfile.mkdtemp(prefix='apk_protect_', dir=temp_base)
        input_file_path = os.path.join(temp_dir, secure_filename(file.filename))
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save uploaded file
        logger.info(f"Saving uploaded file to: {input_file_path}")
        file.save(input_file_path)
        saved_size = os.path.getsize(input_file_path)
        logger.info(f"File saved. Size: {saved_size / (1024*1024):.2f} MB")
        
        # Check if Java is available (Windows compatible)
        java_path = os.environ.get('JAVA_HOME', '')
        if java_path:
            # Windows uses 'bin\java.exe', Linux/Mac uses 'bin/java'
            java_exe = 'java.exe' if os.name == 'nt' else 'java'
            java_cmd = os.path.join(java_path, 'bin', java_exe)
            if not os.path.exists(java_cmd):
                java_cmd = 'java.exe' if os.name == 'nt' else 'java'
        else:
            java_cmd = 'java.exe' if os.name == 'nt' else 'java'
        
        logger.info(f"Using Java command: {java_cmd}")
        
        # Verify Java is installed
        try:
            logger.info("Verifying Java installation...")
            java_check = subprocess.run(
                [java_cmd, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.info(f"Java check output: {java_check.stderr[:100] if java_check.stderr else 'OK'}")
        except subprocess.TimeoutExpired:
            error_msg = 'Java verification timed out'
            logger.error(f"ERROR: {error_msg}")
            return jsonify({
                'error': 'Java JDK 21 is not installed or not found in PATH',
                'details': 'Please ensure Java JDK 21 is installed and JAVA_HOME is set correctly.'
            }), 500
        except FileNotFoundError:
            error_msg = 'Java command not found'
            logger.error(f"ERROR: {error_msg}")
            logger.error(f"Java command path: {java_cmd}")
            logger.error(f"JAVA_HOME: {java_path if java_path else 'Not set'}")
            return jsonify({
                'error': 'Java JDK 21 is not installed or not found in PATH',
                'details': 'Please ensure Java JDK 21 is installed and JAVA_HOME is set correctly.'
            }), 500
        except Exception as e:
            error_msg = f'Error checking Java: {str(e)}'
            logger.error(f"ERROR: {error_msg}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Java JDK 21 is not installed or not found in PATH',
                'details': f'Error: {str(e)}'
            }), 500
        
        # Build command
        cmd = [java_cmd, '-jar', DPT_JAR_PATH, '-f', input_file_path, '-o', output_dir]
        
        # Add options based on form data
        options_used = []
        if request.form.get('debug') == 'true':
            cmd.append('--debug')
            options_used.append('debug')
        
        if request.form.get('disable_acf') == 'true':
            cmd.append('--disable-acf')
            options_used.append('disable-acf')
        
        if request.form.get('dump_code') == 'true':
            cmd.append('--dump-code')
            options_used.append('dump-code')
        
        if request.form.get('keep_classes') == 'true':
            cmd.append('-K')  # Short form: -K,--keep-classes
            options_used.append('keep-classes')
        
        if request.form.get('noisy_log') == 'true':
            cmd.append('--noisy-log')
            options_used.append('noisy-log')
        
        if request.form.get('smaller') == 'true':
            cmd.append('-S')  # Short form: -S,--smaller
            options_used.append('smaller')
        
        # APK will always be signed (no-sign option removed)
        logger.info("APK will be signed by dpt.jar (default behavior)")
        
        # Exclude ABIs
        exclude_abis = request.form.get('exclude_abis', '').strip()
        if exclude_abis:
            cmd.extend(['-e', exclude_abis])
            options_used.append(f'exclude-abis: {exclude_abis}')
        
        # Protect config
        if request.form.get('use_protect_config') == 'true':
            config_file = os.path.join(os.path.dirname(__file__), 'executable', 'dpt-protect-config-template.json')
            if os.path.exists(config_file):
                cmd.extend(['-c', config_file])
                options_used.append('protect-config')
        
        logger.info(f"Options selected: {', '.join(options_used) if options_used else 'None'}")
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Get current working directory to restore later
        original_cwd = os.getcwd()
        
        # Change to temp directory to prevent creating folders in project root
        # This prevents dump-code from creating package name folders in project directory
        os.chdir(temp_dir)
        
        # Run the command
        try:
            logger.info("Starting APK protection process...")
            logger.info(f"Working directory: {temp_dir}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout (Render free tier optimized)
                cwd=temp_dir  # Run from temp directory
            )
            
            logger.info(f"Command completed with return code: {result.returncode}")
            
            if result.returncode != 0:
                error_details = result.stderr or result.stdout
                logger.error("=" * 60)
                logger.error("PROTECTION FAILED")
                logger.error("=" * 60)
                logger.error(f"Return code: {result.returncode}")
                logger.error(f"STDERR:\n{result.stderr}")
                logger.error(f"STDOUT:\n{result.stdout}")
                logger.error("=" * 60)
                return jsonify({
                    'error': 'Protection failed',
                    'details': error_details
                }), 500
            
            # Find the output file
            logger.info("Searching for output file...")
            output_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(('.apk', '.aab')):
                        output_files.append(os.path.join(root, f))
            
            if not output_files:
                logger.error("=" * 60)
                logger.error("NO OUTPUT FILE GENERATED")
                logger.error("=" * 60)
                logger.error(f"Output directory: {output_dir}")
                logger.error(f"STDOUT:\n{result.stdout}")
                logger.error(f"STDERR:\n{result.stderr}")
                logger.error("=" * 60)
                return jsonify({
                    'error': 'No output file generated',
                    'details': result.stdout or result.stderr or 'No output file found in output directory'
                }), 500
            
            output_file = output_files[0]
            logger.info(f"Found output file: {output_file}")
            
            # Verify APK signature (always verify since signing is always enabled)
            try:
                logger.info("Verifying APK signature...")
                # Check if APK is signed using apksigner (Android SDK tool)
                # If apksigner is not available, we'll try jarsigner
                apksigner_cmd = None
                jarsigner_cmd = None
                
                # Try to find apksigner (Android SDK)
                android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
                if android_home:
                    apksigner_path = os.path.join(android_home, 'build-tools')
                    if os.path.exists(apksigner_path):
                        # Find latest build-tools version
                        build_tools = [d for d in os.listdir(apksigner_path) if os.path.isdir(os.path.join(apksigner_path, d))]
                        if build_tools:
                            latest_version = sorted(build_tools, reverse=True)[0]
                            apksigner_cmd = os.path.join(apksigner_path, latest_version, 'apksigner.bat' if os.name == 'nt' else 'apksigner')
                            if not os.path.exists(apksigner_cmd):
                                apksigner_cmd = None
                
                # Check if jarsigner is available (comes with JDK)
                java_path = os.environ.get('JAVA_HOME', '')
                if java_path:
                    jarsigner_exe = 'jarsigner.exe' if os.name == 'nt' else 'jarsigner'
                    jarsigner_cmd = os.path.join(java_path, 'bin', jarsigner_exe)
                    if not os.path.exists(jarsigner_cmd):
                        jarsigner_cmd = 'jarsigner.exe' if os.name == 'nt' else 'jarsigner'
                else:
                    jarsigner_cmd = 'jarsigner.exe' if os.name == 'nt' else 'jarsigner'
                
                # Try to verify signature
                signature_valid = False
                if apksigner_cmd and os.path.exists(apksigner_cmd):
                    try:
                        verify_result = subprocess.run(
                            [apksigner_cmd, 'verify', '--print-certs', output_file],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if verify_result.returncode == 0:
                            signature_valid = True
                            logger.info("APK signature verified using apksigner")
                        else:
                            logger.warning(f"APK signature verification failed: {verify_result.stderr}")
                    except Exception as e:
                        logger.warning(f"Could not verify with apksigner: {e}")
                
                if not signature_valid and jarsigner_cmd:
                    try:
                        verify_result = subprocess.run(
                            [jarsigner_cmd, '-verify', '-verbose', '-certs', output_file],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if verify_result.returncode == 0 and 'jar verified' in verify_result.stdout.lower():
                            signature_valid = True
                            logger.info("APK signature verified using jarsigner")
                        else:
                            logger.warning("APK signature verification failed or APK is not signed")
                    except Exception as e:
                        logger.warning(f"Could not verify with jarsigner: {e}")
                
                if not signature_valid:
                    logger.warning("=" * 60)
                    logger.warning("APK SIGNATURE WARNING")
                    logger.warning("=" * 60)
                    logger.warning("The protected APK may not be properly signed.")
                    logger.warning("This can cause 'package appears to be invalid' error on Android.")
                    logger.warning("dpt.jar should sign the APK by default, but verification failed.")
                    logger.warning("=" * 60)
                else:
                    logger.info("APK is properly signed and ready for installation")
                    
            except Exception as e:
                logger.warning(f"Could not verify APK signature: {e}")
                logger.warning("Continuing anyway - APK should be signed by dpt.jar")
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            # Clean up any folders created in project root by dump-code
            # These folders are created with package names like com.spiderautobet
            project_root = os.path.dirname(os.path.abspath(__file__))
            logger.info("Cleaning up any folders created in project root...")
            
            try:
                for item in os.listdir(project_root):
                    item_path = os.path.join(project_root, item)
                    # Check if it's a directory that looks like a package name (contains dots)
                    if os.path.isdir(item_path) and '.' in item and item != 'venv' and not item.startswith('.'):
                        # Check if it contains .json files (dump-code output)
                        has_json = False
                        try:
                            for root, dirs, files in os.walk(item_path):
                                if any(f.endswith('.json') for f in files):
                                    has_json = True
                                    break
                        except:
                            pass
                        
                        if has_json:
                            logger.info(f"Removing dump-code folder: {item_path}")
                            try:
                                shutil.rmtree(item_path, ignore_errors=True)
                                logger.info(f"Successfully removed: {item}")
                            except Exception as e:
                                logger.warning(f"Could not remove {item_path}: {e}")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
            
            # Return the first output file
            output_file = output_files[0]
            output_size = os.path.getsize(output_file)
            logger.info(f"Output file size: {output_size / (1024*1024):.2f} MB")
            
            # Generate a unique filename
            output_filename = f"protected_{secure_filename(file.filename)}"
            
            # Read file into memory before cleanup - with error handling
            try:
                logger.info(f"Reading output file: {output_file}")
                with open(output_file, 'rb') as f:
                    file_data = f.read()
                
                if not file_data or len(file_data) == 0:
                    logger.error("Output file is empty!")
                    return jsonify({
                        'error': 'Protected file is empty',
                        'details': 'The protection process completed but generated an empty file. Please try again.'
                    }), 500
                
                logger.info(f"File read successfully. Size: {len(file_data) / (1024*1024):.2f} MB")
            except IOError as e:
                logger.error(f"Error reading output file: {e}")
                return jsonify({
                    'error': 'Failed to read protected file',
                    'details': f'Could not read the output file: {str(e)}'
                }), 500
            except Exception as e:
                logger.error(f"Unexpected error reading file: {e}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': 'Unexpected error reading file',
                    'details': str(e)
                }), 500
            
            # Cleanup temporary directory and any project root folders (after reading file)
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                # Also clean up any package name folders created in project root by dump-code
                project_root = os.path.dirname(os.path.abspath(__file__))
                if os.path.exists(project_root):
                    for item in os.listdir(project_root):
                        item_path = os.path.join(project_root, item)
                        if os.path.isdir(item_path) and '.' in item and item != 'venv' and not item.startswith('.'):
                            # Check if it contains .json files (dump-code output)
                            try:
                                has_json = False
                                for root, dirs, files in os.walk(item_path):
                                    if any(f.endswith('.json') for f in files):
                                        has_json = True
                                        break
                                if has_json:
                                    logger.info(f"Cleaning up dump-code folder: {item}")
                                    shutil.rmtree(item_path, ignore_errors=True)
                            except Exception as cleanup_error:
                                logger.warning(f"Error cleaning up {item_path}: {cleanup_error}")
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
            
            logger.info("=" * 60)
            logger.info("PROTECTION SUCCESSFUL!")
            logger.info(f"Output file: {output_filename}")
            logger.info(f"File size: {len(file_data) / (1024*1024):.2f} MB")
            logger.info("=" * 60)
            
            # Create response from memory with proper headers for large files - crash prevention
            from io import BytesIO
            from flask import Response
            
            try:
                file_size = len(file_data)
                file_size_mb = file_size / (1024 * 1024)
                
                logger.info(f"Preparing file response. Size: {file_size_mb:.2f} MB ({file_size} bytes)")
                
                # For very large files, ensure we're using BytesIO correctly
                file_stream = BytesIO(file_data)
                file_stream.seek(0)  # Reset to beginning
                
                # Verify file stream is valid
                if file_stream.tell() != 0:
                    file_stream.seek(0)
                
                response = Response(
                    file_stream,
                    mimetype='application/vnd.android.package-archive',
                    headers={
                        'Content-Disposition': f'attachment; filename="{output_filename}"',
                        'Content-Length': str(file_size),
                        'Content-Type': 'application/vnd.android.package-archive',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0',
                        'Accept-Ranges': 'bytes',
                        'Connection': 'keep-alive'
                    },
                    direct_passthrough=False  # Ensure Flask handles the streaming
                )
                
                logger.info(f"File response created. Headers set. Starting transfer...")
                return response
                
            except Exception as response_error:
                logger.error(f"Error creating response: {response_error}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': 'Failed to create file response',
                    'details': f'Error: {str(response_error)}'
                }), 500
            
        except subprocess.TimeoutExpired:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except:
                pass
            
            # Cleanup on timeout
            logger.error("=" * 60)
            logger.error("PROCESS TIMEOUT")
            logger.error("=" * 60)
            logger.error("The APK protection process timed out after 5 minutes (free tier limit).")
            logger.error("The APK might be too large or complex.")
            logger.error("=" * 60)
            
            # Clean up temp directory and any project root folders
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                # Clean up any package name folders in project root
                project_root = os.path.dirname(os.path.abspath(__file__))
                for item in os.listdir(project_root):
                    item_path = os.path.join(project_root, item)
                    if os.path.isdir(item_path) and '.' in item and item != 'venv' and not item.startswith('.'):
                        try:
                            shutil.rmtree(item_path, ignore_errors=True)
                        except:
                            pass
            except:
                pass
            return jsonify({'error': 'Process timed out. Free tier limit: 5 minutes processing time. Please try a smaller APK (max 150MB) or wait and retry.'}), 500
        except Exception as e:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except:
                pass
            
            # Cleanup on error
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "Unknown error"
            error_traceback = traceback.format_exc()
            
            # Log all error information together to prevent missing messages
            error_log = f"""
{'=' * 60}
ERROR RUNNING PROTECTION
{'=' * 60}
Error type: {error_type}
Error message: {error_msg}
Full traceback:
{error_traceback}
{'=' * 60}
"""
            logger.error(error_log)
            
            # Clean up temp directory and any project root folders
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                # Clean up any package name folders in project root
                project_root = os.path.dirname(os.path.abspath(__file__))
                for item in os.listdir(project_root):
                    item_path = os.path.join(project_root, item)
                    if os.path.isdir(item_path) and '.' in item and item != 'venv' and not item.startswith('.'):
                        try:
                            shutil.rmtree(item_path, ignore_errors=True)
                        except:
                            pass
            except:
                pass
            return jsonify({'error': f'Error running protection: {str(e)}'}), 500
    
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else "Unknown error"
        error_traceback = traceback.format_exc()
        
        # Log all error information together to prevent missing messages
        error_log = f"""
{'=' * 60}
SERVER ERROR
{'=' * 60}
Error type: {error_type}
Error message: {error_msg}
Full traceback:
{error_traceback}
{'=' * 60}
"""
        logger.error(error_log)
        return jsonify({'error': f'Server error: {error_msg}'}), 500

@app.route('/health', methods=['GET'])
def health():
    # Check Java availability (Windows compatible)
    java_available = False
    java_version = 'Not found'
    try:
        java_path = os.environ.get('JAVA_HOME', '')
        if java_path:
            java_exe = 'java.exe' if os.name == 'nt' else 'java'
            java_cmd = os.path.join(java_path, 'bin', java_exe)
            if not os.path.exists(java_cmd):
                java_cmd = 'java.exe' if os.name == 'nt' else 'java'
        else:
            java_cmd = 'java.exe' if os.name == 'nt' else 'java'
        
        result = subprocess.run(
            [java_cmd, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        java_available = True
        java_version = result.stderr.split('\n')[0] if result.stderr else 'Unknown'
    except:
        pass
    
    return jsonify({
        'status': 'ok',
        'dpt_jar_exists': os.path.exists(DPT_JAR_PATH),
        'java_available': java_available,
        'java_version': java_version
    })

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")
    if request.method == 'POST' and request.path == '/protect':
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Content-Length: {request.content_length} bytes")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} {response.status}")
    # Add headers for large file downloads
    if response.status_code == 200:
        content_length = response.headers.get('Content-Length')
        if content_length:
            file_size_mb = int(content_length) / (1024 * 1024)
            logger.info(f"Response file size: {file_size_mb:.2f} MB")
        content_type = response.headers.get('Content-Type', '')
        if content_type:
            logger.info(f"Response Content-Type: {content_type}")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info("=" * 60)
    logger.info("Acx Shell Server Starting")
    logger.info("=" * 60)
    logger.info(f"Server running on: http://0.0.0.0:{port}")
    logger.info(f"Local access: http://localhost:{port}")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
