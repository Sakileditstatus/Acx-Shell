#!/usr/bin/env python3
"""
Acx Shell - Auto Setup and Run Script
Automatically downloads dependencies, sets up environment, and runs the application
"""

import os
import sys
import subprocess
import platform
import urllib.request
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.RESET):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def print_header(text):
    """Print header"""
    print_colored("\n" + "="*60, Colors.CYAN)
    print_colored(f"  {text}", Colors.BOLD + Colors.CYAN)
    print_colored("="*60 + "\n", Colors.CYAN)

def print_step(step_num, text):
    """Print step"""
    print_colored(f"[{step_num}] {text}", Colors.BLUE)

def print_success(text):
    """Print success message"""
    print_colored(f"✓ {text}", Colors.GREEN)

def print_error(text):
    """Print error message"""
    print_colored(f"✗ {text}", Colors.RED)

def print_warning(text):
    """Print warning message"""
    print_colored(f"⚠ {text}", Colors.YELLOW)

def check_command(cmd):
    """Check if command exists"""
    try:
        result = subprocess.run(
            [cmd, '--version'] if cmd != 'java' else [cmd, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_python():
    """Check Python installation"""
    print_step(1, "Checking Python installation...")
    if sys.version_info < (3, 11):
        print_error(f"Python 3.11+ required. Found: {sys.version}")
        print_warning("Please install Python 3.11+ from https://www.python.org/downloads/")
        return False
    print_success(f"Python {sys.version.split()[0]} found")
    return True

def check_java():
    """Check Java JDK 21 installation"""
    print_step(2, "Checking Java JDK 21 installation...")
    
    # Check JAVA_HOME
    java_home = os.environ.get('JAVA_HOME', '')
    java_cmd = None
    
    if java_home:
        java_exe = 'java.exe' if platform.system() == 'Windows' else 'java'
        java_cmd = os.path.join(java_home, 'bin', java_exe)
        if not os.path.exists(java_cmd):
            java_cmd = None
    
    # Check if java is in PATH
    if not java_cmd or not os.path.exists(java_cmd):
        if check_command('java'):
            java_cmd = 'java'
        else:
            print_error("Java JDK 21 not found!")
            print_warning("Please install Java JDK 21:")
            if platform.system() == 'Windows':
                print("  Windows: https://adoptium.net/temurin/releases/?version=21")
            else:
                print("  Linux/Mac: Use package manager or download from Adoptium")
            return False, None
    
    # Check Java version
    try:
        result = subprocess.run(
            [java_cmd, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_output = result.stderr or result.stdout
        if '21' in version_output or 'openjdk version "21' in version_output:
            print_success("Java JDK 21 found")
            return True, java_cmd
        else:
            print_warning(f"Java found but version might not be 21: {version_output.split()[0] if version_output else 'Unknown'}")
            print_warning("Continuing anyway...")
            return True, java_cmd
    except Exception as e:
        print_error(f"Error checking Java: {e}")
        return False, None

def setup_virtual_environment():
    """Setup Python virtual environment"""
    print_step(3, "Setting up virtual environment...")
    
    venv_path = Path('venv')
    
    if venv_path.exists():
        print_success("Virtual environment already exists")
    else:
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError:
            print_error("Failed to create virtual environment")
            return False
    
    return True

def get_pip_command():
    """Get pip command for virtual environment"""
    if platform.system() == 'Windows':
        return str(Path('venv') / 'Scripts' / 'pip.exe')
    else:
        return str(Path('venv') / 'bin' / 'pip')

def get_python_command():
    """Get python command for virtual environment"""
    if platform.system() == 'Windows':
        return str(Path('venv') / 'Scripts' / 'python.exe')
    else:
        return str(Path('venv') / 'bin' / 'python')

def install_dependencies():
    """Install Python dependencies"""
    print_step(4, "Installing Python dependencies...")
    
    pip_cmd = get_pip_command()
    
    # Upgrade pip first
    try:
        print("Upgrading pip...")
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True, capture_output=True)
    except:
        pass
    
    # Install requirements
    if not Path('requirements.txt').exists():
        print_error("requirements.txt not found!")
        return False
    
    try:
        print("Installing packages from requirements.txt...")
        result = subprocess.run(
            [pip_cmd, 'install', '-r', 'requirements.txt'],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e.stderr}")
        return False

def check_dpt_jar():
    """Check if dpt.jar exists"""
    print_step(5, "Checking dpt.jar...")
    
    dpt_jar = Path('executable') / 'dpt.jar'
    if dpt_jar.exists():
        print_success("dpt.jar found")
        return True
    else:
        print_error("dpt.jar not found in executable/ folder!")
        print_warning("Please ensure dpt.jar is in the executable/ directory")
        return False

def check_templates():
    """Check if templates exist"""
    print_step(6, "Checking templates...")
    
    template_file = Path('templates') / 'index.html'
    if template_file.exists():
        print_success("Templates found")
        return True
    else:
        print_error("templates/index.html not found!")
        return False

def run_application():
    """Run the Flask application"""
    print_header("Starting Acx Shell")
    
    python_cmd = get_python_command()
    app_file = Path('app.py')
    
    if not app_file.exists():
        print_error("app.py not found!")
        return False
    
    print_success("All checks passed!")
    print_colored("\n" + "="*60, Colors.CYAN)
    print_colored("  Server starting...", Colors.BOLD + Colors.GREEN)
    print_colored("  Open your browser at: http://localhost:5000", Colors.CYAN)
    print_colored("  Press Ctrl+C to stop the server", Colors.YELLOW)
    print_colored("="*60 + "\n", Colors.CYAN)
    
    try:
        # Set environment variables
        env = os.environ.copy()
        port = env.get('PORT', '5000')
        env['PORT'] = port
        
        # Run the application
        subprocess.run([python_cmd, str(app_file)], env=env)
    except KeyboardInterrupt:
        print_colored("\n\nServer stopped by user", Colors.YELLOW)
        return True
    except Exception as e:
        print_error(f"Error running application: {e}")
        return False

def main():
    """Main function"""
    print_header("Acx Shell - Auto Setup")
    
    # Check Python
    if not check_python():
        sys.exit(1)
    
    # Check Java
    java_ok, java_cmd = check_java()
    if not java_ok:
        print_warning("\nYou can still continue, but APK protection won't work without Java.")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print_warning("Some dependencies failed to install. Continuing anyway...")
    
    # Check dpt.jar
    if not check_dpt_jar():
        print_warning("dpt.jar not found. APK protection will not work.")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Check templates
    if not check_templates():
        print_error("Templates missing. Cannot start application.")
        sys.exit(1)
    
    # Run application
    print_header("Setup Complete!")
    run_application()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nSetup interrupted by user", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)
