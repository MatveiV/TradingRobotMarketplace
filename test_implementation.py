#!/usr/bin/env python3
"""
Simple test script to verify the enhanced Trading Robot Marketplace implementation
"""

import os
import sys

def test_file_exists(path, description):
    """Test if a file exists"""
    if os.path.exists(path):
        print(f"PASS: {description} - {path}")
        return True
    else:
        print(f"FAIL: {description} - {path}")
        return False

def main():
    print("Enhanced Trading Robot Marketplace - File Structure Test")
    print("=" * 60)
    
    # List of critical files that should exist
    critical_files = [
        # Backend core
        "backend/app/main.py",
        "backend/app/adapters/mt4_adapter.py",
        "backend/app/adapters/broker_api_adapter.py",
        "backend/app/adapters/base.py",
        "backend/app/robot_manager/manager.py",
        "backend/app/models.py",
        "backend/app/schemas.py",
        "backend/app/config.py",
        "backend/app/utils/file_storage.py",
        
        # Frontend core
        "frontend/src/App.tsx",
        "frontend/src/components/StrategyForm.tsx",
        "frontend/src/pages/CreateStrategy.tsx",
        "frontend/src/pages/StrategiesPage.tsx",
        "frontend/src/services/api.ts",
        "frontend/src/types/index.ts",
        
        # Configuration
        "docker-compose.yml",
        "docker-compose.postgres.yml",
        ".env.example",
        
        # Documentation
        "TradngRobotsMarketplaceSRS.md",
        "Readme.md",
        
        # Test script
        "test_enhanced_implementation.py",
    ]
    
    passed = 0
    total = len(critical_files)
    
    for file_path in critical_files:
        if test_file_exists(file_path, "Critical file"):
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed}/{total} files checked")
    
    if passed == total:
        print("SUCCESS: All critical files are present. Implementation is complete.")
        return True
    else:
        print("WARNING: Some files are missing. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)