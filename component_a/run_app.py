#!/usr/bin/env python3
"""
WhisperX Streamlit App Runner with 1GB Upload Limit

This script ensures the Streamlit app starts with the correct configuration
for 1GB file uploads.
"""

import os
import sys
import subprocess


def main():
    """Run the Streamlit app with proper configuration."""
    # Change to src directory
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    os.chdir(src_dir)
    
    # Streamlit command with 1GB upload limit and large file optimizations
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.headless', 'false',  # Allow browser opening
        '--server.port', '8502',  # Use different port to avoid conflicts
        '--server.maxUploadSize', '1024',  # 1GB in MB
        '--server.maxMessageSize', '1024',  # Also increase message size
        '--server.enableCORS', 'false',  # Disable CORS for large uploads
        '--server.enableXsrfProtection', 'false',  # Disable XSRF protection
        '--server.fileWatcherType', 'none',  # Disable file watcher for performance
        '--browser.gatherUsageStats', 'false',  # Reduce overhead
    ]
    
    print("🚀 Starting WhisperX Streamlit App with 1GB upload limit...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Command: {' '.join(cmd)}")
    print("🌐 App will be available at: http://localhost:8502")
    print("=" * 60)
    
    try:
        # Run the command
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()