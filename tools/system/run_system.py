#!/usr/bin/env python3
"""
Abodient System Runner
======================

This script provides a simple way to start the entire Abodient tenant 
management system with proper environment loading and error handling.

Usage:
    python run_system.py              # Start both frontend and backend
    python run_system.py --backend    # Start backend only  
    python run_system.py --frontend   # Start frontend only
    python run_system.py --test       # Test agent functionality
    python run_system.py --debug      # Run debugging analysis
"""

import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path

def load_env():
    """Load environment variables from backend/.env"""
    env_path = Path("backend/.env")
    if env_path.exists():
        print("🔧 Loading environment variables...")
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Environment loaded")
    else:
        print("❌ Warning: backend/.env not found")
        print("   Please ensure environment variables are configured")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    required_packages = ['fastapi', 'uvicorn', 'langchain', 'openai', 'pinecone']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r backend/api/requirements.txt")
        return False
    
    # Check Node.js for frontend
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js/npm not found. Frontend won't work.")
        print("   Install Node.js from https://nodejs.org/")
        return False
    
    print("✅ All dependencies found")
    return True

def test_agents():
    """Test agent functionality"""
    print("🧪 Testing agent functionality...")
    load_env()
    
    try:
        # Add backend to path for imports
        sys.path.append('backend/api')
        
        from agents.main_agent import handle_message
        from database import get_db
        
        # Test with a simple query
        test_query = "My heating is broken and it's very cold"
        test_session = "test-session"
        
        print(f"📝 Test Query: {test_query}")
        
        # Get database session
        db = next(get_db())
        
        # Test the main agent
        result = handle_message(db, test_session, test_query)
        
        print("✅ Agent test completed successfully!")
        print(f"📄 Response: {result.get('chat_output', 'No output')[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

def run_debug_analysis():
    """Run debugging analysis"""
    print("🔍 Running system debugging analysis...")
    load_env()
    
    try:
        result = subprocess.run(['python', 'debug_orchestration.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return True
    except Exception as e:
        print(f"❌ Debug analysis failed: {e}")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    load_env()
    
    os.chdir("backend/api")
    
    # Start FastAPI with uvicorn
    cmd = [
        'uvicorn', 'api_server:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ]
    
    return subprocess.Popen(cmd)

def start_frontend():
    """Start the React frontend"""
    print("🎨 Starting frontend server...")
    
    os.chdir("frontend")
    
    # Install dependencies if node_modules doesn't exist
    if not Path("node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(['npm', 'install'], check=True)
    
    # Start development server
    cmd = ['npm', 'run', 'dev']
    return subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description='Abodient System Runner')
    parser.add_argument('--backend', action='store_true', help='Start backend only')
    parser.add_argument('--frontend', action='store_true', help='Start frontend only')
    parser.add_argument('--test', action='store_true', help='Test agent functionality')
    parser.add_argument('--debug', action='store_true', help='Run debugging analysis')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency check')
    
    args = parser.parse_args()
    
    print("🏠 Abodient Tenant Management System")
    print("=" * 50)
    
    # Handle specific commands
    if args.test:
        success = test_agents()
        sys.exit(0 if success else 1)
    
    if args.debug:
        success = run_debug_analysis()
        sys.exit(0 if success else 1)
    
    # Check dependencies
    if not args.skip_deps:
        if not check_dependencies():
            print("❌ Dependency check failed. Use --skip-deps to continue anyway.")
            sys.exit(1)
    
    processes = []
    
    try:
        # Store original directory
        original_dir = os.getcwd()
        
        # Start services based on arguments
        if args.backend or (not args.frontend and not args.backend):
            backend_process = start_backend()
            processes.append(('Backend', backend_process))
            os.chdir(original_dir)  # Reset directory
            time.sleep(2)  # Give backend time to start
        
        if args.frontend or (not args.frontend and not args.backend):
            frontend_process = start_frontend()
            processes.append(('Frontend', frontend_process))
            os.chdir(original_dir)  # Reset directory
        
        if processes:
            print("\n✅ System started successfully!")
            print("Backend API: http://localhost:8000")
            print("Frontend UI: http://localhost:5173")
            print("\nPress Ctrl+C to stop all services")
            
            # Wait for interrupt
            signal.signal(signal.SIGINT, lambda s, f: None)
            
            while True:
                # Check if processes are still running
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {name} process stopped unexpectedly")
                        break
                time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 Stopping services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 