#!/usr/bin/env python3
"""
Test runner for PARA + Daily Task Management System
Runs both unit tests and integration tests
"""

import unittest
import sys
import os

def run_tests():
    """Run all tests and report results"""
    print("🧪 Running PARA + Daily Task Management System Tests")
    print("=" * 60)
    
    # Discover and run unit tests
    print("\n📋 Running Unit Tests...")
    unit_loader = unittest.TestLoader()
    unit_suite = unit_loader.discover('.', pattern='test_tasks.py')
    unit_runner = unittest.TextTestRunner(verbosity=2)
    unit_result = unit_runner.run(unit_suite)
    
    # Discover and run integration tests
    print("\n🔗 Running Integration Tests...")
    integration_loader = unittest.TestLoader()
    integration_suite = integration_loader.discover('.', pattern='test_integration.py')
    integration_runner = unittest.TextTestRunner(verbosity=2)
    integration_result = integration_runner.run(integration_suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    unit_tests_run = unit_result.testsRun
    unit_tests_failed = len(unit_result.failures) + len(unit_result.errors)
    unit_tests_passed = unit_tests_run - unit_tests_failed
    
    integration_tests_run = integration_result.testsRun
    integration_tests_failed = len(integration_result.failures) + len(integration_result.errors)
    integration_tests_passed = integration_tests_run - integration_tests_failed
    
    total_tests_run = unit_tests_run + integration_tests_run
    total_tests_failed = unit_tests_failed + integration_tests_failed
    total_tests_passed = total_tests_run - total_tests_failed
    
    print(f"Unit Tests:      {unit_tests_passed}/{unit_tests_run} passed")
    print(f"Integration Tests: {integration_tests_passed}/{integration_tests_run} passed")
    print(f"Total:           {total_tests_passed}/{total_tests_run} passed")
    
    if total_tests_failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total_tests_failed} test(s) failed")
        
        if unit_result.failures:
            print("\nUnit Test Failures:")
            for test, traceback in unit_result.failures:
                print(f"  - {test}")
        
        if unit_result.errors:
            print("\nUnit Test Errors:")
            for test, traceback in unit_result.errors:
                print(f"  - {test}")
        
        if integration_result.failures:
            print("\nIntegration Test Failures:")
            for test, traceback in integration_result.failures:
                print(f"  - {test}")
        
        if integration_result.errors:
            print("\nIntegration Test Errors:")
            for test, traceback in integration_result.errors:
                print(f"  - {test}")
        
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
