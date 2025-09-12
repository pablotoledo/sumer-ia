#!/usr/bin/env python3
"""
Troubleshooting script for large file uploads in Streamlit WhisperX app.
This script helps diagnose and fix common issues with uploading large audio files.
"""

import os
import sys
import subprocess
import time
import requests


def check_streamlit_version():
    """Check Streamlit version for known issues."""
    try:
        result = subprocess.run([sys.executable, '-c', 'import streamlit; print(streamlit.__version__)'], 
                              capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"📊 Streamlit version: {version}")
        
        # Known problematic versions
        problematic = ['1.30.0', '1.31.0', '1.32.0']
        if version in problematic:
            print(f"⚠️  Warning: Version {version} has known upload issues")
            print("💡 Consider downgrading to 1.29.0: uv add streamlit==1.29.0")
        else:
            print("✅ Version looks good")
            
    except Exception as e:
        print(f"❌ Could not check Streamlit version: {e}")


def check_port_availability():
    """Check if ports are available."""
    ports_to_check = [8501, 8502, 8503]
    
    for port in ports_to_check:
        try:
            response = requests.get(f'http://localhost:{port}', timeout=2)
            print(f"🟡 Port {port}: In use (status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"✅ Port {port}: Available")
        except requests.exceptions.Timeout:
            print(f"🔴 Port {port}: Timeout (possibly hung)")
        except Exception as e:
            print(f"🟡 Port {port}: {e}")


def kill_streamlit_processes():
    """Kill existing Streamlit processes."""
    print("\n🔄 Cleaning up existing Streamlit processes...")
    
    try:
        # Kill by process name
        subprocess.run(['pkill', '-f', 'streamlit'], stderr=subprocess.DEVNULL)
        
        # Kill by port (backup)
        for port in [8501, 8502, 8503]:
            try:
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    pid = result.stdout.strip()
                    subprocess.run(['kill', '-9', pid])
                    print(f"✅ Killed process on port {port}")
            except:
                pass
                
        time.sleep(2)
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"⚠️  Could not clean processes: {e}")


def test_upload_endpoint():
    """Test if upload endpoint is responsive."""
    ports = [8502, 8501]
    
    for port in ports:
        try:
            response = requests.get(f'http://localhost:{port}/_stcore/upload', timeout=5)
            print(f"📡 Upload endpoint on {port}: {response.status_code}")
            return port
        except:
            continue
    
    print("❌ No responsive upload endpoints found")
    return None


def start_optimized_streamlit():
    """Start Streamlit with optimized settings for large files."""
    print("\n🚀 Starting optimized Streamlit for large files...")
    
    os.chdir('src')
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', '8502',
        '--server.maxUploadSize', '1024',  # 1GB
        '--server.maxMessageSize', '1024',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--server.fileWatcherType', 'none',
        '--browser.gatherUsageStats', 'false',
        '--logger.level', 'info',
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print("⏱️  Starting server... (this may take a moment)")
    
    try:
        process = subprocess.Popen(cmd)
        time.sleep(5)  # Wait for startup
        
        # Test if server started
        try:
            response = requests.get('http://localhost:8502', timeout=10)
            print("✅ Server started successfully!")
            print("🌐 Access at: http://localhost:8502")
            print("\n📋 Tips for 360MB files:")
            print("  - Upload may take 5-15 minutes")
            print("  - Don't refresh during upload")
            print("  - Try again if you get Network Error")
            print("  - Browser may appear frozen - this is normal")
            
        except:
            print("⚠️  Server started but may still be loading...")
            print("🌐 Try accessing: http://localhost:8502")
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")


def main():
    """Main troubleshooting routine."""
    print("🔍 WhisperX Large File Upload Troubleshooter")
    print("=" * 50)
    
    print("\n1️⃣ Checking Streamlit version...")
    check_streamlit_version()
    
    print("\n2️⃣ Checking port availability...")
    check_port_availability()
    
    print("\n3️⃣ Cleaning up processes...")
    kill_streamlit_processes()
    
    print("\n4️⃣ Testing upload endpoints...")
    active_port = test_upload_endpoint()
    
    if not active_port:
        print("\n5️⃣ Starting fresh server...")
        start_optimized_streamlit()
    else:
        print(f"\n✅ Server already running on port {active_port}")
        print("🌐 Access at: http://localhost:{active_port}")


if __name__ == "__main__":
    main()