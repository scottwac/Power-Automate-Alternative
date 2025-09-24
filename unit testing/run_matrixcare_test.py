#!/usr/bin/env python3
"""
Run the MatrixCare scheduling test.

This script runs the unit test that simulates the correct time
and verifies the MatrixCare Looker Dashboard automation works.
"""

import os
import sys
import subprocess

def main():
    """Run the MatrixCare test."""
    print("MatrixCare Looker Dashboard Automation Test")
    print("=" * 50)
    
    # Get the directory of this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the test directory
    os.chdir(test_dir)
    
    # Run the specific test
    try:
        print("Running MatrixCare schedule test...")
        result = subprocess.run([
            sys.executable, 
            '-m', 'pytest', 
            'test_matrixcare_schedule.py', 
            '-v', 
            '--tb=short'
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            
    except FileNotFoundError:
        # If pytest is not available, try running with unittest
        print("Pytest not found, running with unittest...")
        result = subprocess.run([
            sys.executable, 
            'test_matrixcare_schedule.py'
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")

if __name__ == '__main__':
    main()
