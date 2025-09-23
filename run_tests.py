"""
Test runner script with additional test utilities.
"""

import unittest
import sys
import os
from io import StringIO

def run_specific_test(test_class=None, test_method=None):
    """Run specific test class or method."""
    if test_class and test_method:
        suite = unittest.TestLoader().loadTestsFromName(f'{test_class}.{test_method}', module=__import__('test_email_processor'))
    elif test_class:
        suite = unittest.TestLoader().loadTestsFromName(test_class, module=__import__('test_email_processor'))
    else:
        suite = unittest.TestLoader().loadTestsFromModule(__import__('test_email_processor'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_coverage_test():
    """Run tests with coverage report if coverage is available."""
    try:
        import coverage
        
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        suite = unittest.TestLoader().loadTestsFromModule(__import__('test_email_processor'))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        cov.stop()
        cov.save()
        
        print("\n" + "="*50)
        print("COVERAGE REPORT")
        print("="*50)
        cov.report()
        
        return result.wasSuccessful()
        
    except ImportError:
        print("Coverage module not installed. Running tests without coverage.")
        return run_specific_test()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--coverage':
            success = run_coverage_test()
        elif sys.argv[1] == '--help':
            print("Usage:")
            print("  python run_tests.py                    # Run all tests")
            print("  python run_tests.py --coverage         # Run with coverage")
            print("  python run_tests.py TestClassName      # Run specific test class")
            print("  python run_tests.py TestClass.method   # Run specific test method")
            sys.exit(0)
        else:
            # Parse test class/method
            test_arg = sys.argv[1]
            if '.' in test_arg:
                test_class, test_method = test_arg.split('.', 1)
                success = run_specific_test(test_class, test_method)
            else:
                success = run_specific_test(test_arg)
    else:
        success = run_specific_test()
    
    sys.exit(0 if success else 1)
