#!/usr/bin/env python3
"""
Complete System Verification Script
Tests all components of the AI Study Companion platform
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")

def check_backend_health(base_url: str = "http://localhost:8000") -> bool:
    """Check if backend is running"""
    if not HAS_REQUESTS:
        print_warning("requests module not installed - skipping backend health check")
        print_info("Install with: pip install requests")
        return False
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend is running at {base_url}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Backend is not accessible: {e}")
        print_info("Start backend with: python -m uvicorn src.api.main:app --reload")
        return False

def check_api_docs(base_url: str = "http://localhost:8000") -> bool:
    """Check if API docs are accessible"""
    if not HAS_REQUESTS:
        return False
    
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print_success("API documentation is accessible")
            return True
        else:
            print_warning(f"API docs returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_warning(f"API docs not accessible: {e}")
        return False

def check_frontend_files() -> Tuple[bool, List[str]]:
    """Check if frontend files exist"""
    frontend_dir = Path("examples/frontend-starter")
    required_files = [
        "package.json",
        "src/App.jsx",
        "src/pages/Login.jsx",
        "src/pages/Dashboard.jsx",
        "src/pages/Practice.jsx",
        "src/pages/QA.jsx",
        "src/pages/Progress.jsx",
        "src/pages/Goals.jsx",
        "src/pages/Settings.jsx",
        "src/pages/Messaging.jsx",
        "src/pages/Gamification.jsx",
        "src/services/apiClient.js",
        "src/contexts/AuthContext.jsx",
    ]
    
    missing = []
    for file in required_files:
        file_path = frontend_dir / file
        if not file_path.exists():
            missing.append(str(file))
    
    if missing:
        print_error(f"Missing frontend files: {len(missing)}")
        for file in missing:
            print_error(f"  - {file}")
        return False, missing
    else:
        print_success(f"All {len(required_files)} required frontend files exist")
        return True, []

def check_backend_files() -> Tuple[bool, List[str]]:
    """Check if backend files exist"""
    required_files = [
        "src/api/main.py",
        "src/api/handlers/summaries.py",
        "src/api/handlers/practice.py",
        "src/api/handlers/qa.py",
        "src/api/handlers/progress.py",
        "src/api/handlers/nudges.py",
        "src/api/handlers/overrides.py",
        "src/api/handlers/messaging.py",
        "src/api/handlers/gamification.py",
        "src/api/handlers/dashboards.py",
        "src/api/handlers/advanced_analytics.py",
        "src/api/handlers/integrations.py",
        "src/api/handlers/enhancements.py",
        "requirements.txt",
        "run_server.py",
    ]
    
    missing = []
    for file in required_files:
        file_path = Path(file)
        if not file_path.exists():
            missing.append(str(file))
    
    if missing:
        print_error(f"Missing backend files: {len(missing)}")
        for file in missing:
            print_error(f"  - {file}")
        return False, missing
    else:
        print_success(f"All {len(required_files)} required backend files exist")
        return True, []

def check_documentation() -> Tuple[bool, List[str]]:
    """Check if documentation exists"""
    required_docs = [
        "README.md",
        "QUICK_START.md",
        "DEPLOYMENT_CHECKLIST.md",
        "COMPLETE_PROJECT_STATUS.md",
        "FINAL_SUMMARY.md",
        "_docs/active/MVP_PRD.md",
        "_docs/active/POST_MVP_PRD.md",
        "examples/frontend-starter/README.md",
    ]
    
    missing = []
    for doc in required_docs:
        doc_path = Path(doc)
        if not doc_path.exists():
            missing.append(str(doc))
    
    if missing:
        print_warning(f"Missing documentation: {len(missing)}")
        for doc in missing:
            print_warning(f"  - {doc}")
        return False, missing
    else:
        print_success(f"All {len(required_docs)} required documentation files exist")
        return True, []

def check_tests() -> bool:
    """Check if tests can run"""
    try:
        import pytest
        print_success("pytest is installed")
        
        # Check if test files exist
        test_dir = Path("tests")
        if test_dir.exists():
            test_files = list(test_dir.glob("test_*.py"))
            if test_files:
                print_success(f"Found {len(test_files)} test files")
                return True
            else:
                print_warning("No test files found in tests/")
                return False
        else:
            print_warning("tests/ directory not found")
            return False
    except ImportError:
        print_warning("pytest is not installed")
        return False

def check_docker() -> bool:
    """Check if Docker files exist"""
    docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
    all_exist = all(Path(f).exists() for f in docker_files)
    
    if all_exist:
        print_success("All Docker files exist")
        return True
    else:
        missing = [f for f in docker_files if not Path(f).exists()]
        print_warning(f"Missing Docker files: {', '.join(missing)}")
        return False

def main():
    print_header("AI Study Companion - Complete System Verification")
    
    results = {
        "backend_running": False,
        "api_docs": False,
        "backend_files": False,
        "frontend_files": False,
        "documentation": False,
        "tests": False,
        "docker": False,
    }
    
    # Check backend
    print_header("Backend Status")
    results["backend_running"] = check_backend_health()
    results["api_docs"] = check_api_docs()
    
    # Check files
    print_header("File Structure")
    backend_ok, _ = check_backend_files()
    results["backend_files"] = backend_ok
    
    frontend_ok, _ = check_frontend_files()
    results["frontend_files"] = frontend_ok
    
    docs_ok, _ = check_documentation()
    results["documentation"] = docs_ok
    
    # Check tests
    print_header("Testing")
    results["tests"] = check_tests()
    
    # Check Docker
    print_header("Docker")
    results["docker"] = check_docker()
    
    # Summary
    print_header("Verification Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.RESET}\n")
    
    for check, status in results.items():
        if status:
            print_success(f"{check.replace('_', ' ').title()}")
        else:
            print_error(f"{check.replace('_', ' ').title()}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] All checks passed! System is ready.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARN] Some checks failed. Review the output above.{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

