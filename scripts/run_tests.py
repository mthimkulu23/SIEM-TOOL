# scripts/run_tests.py

import unittest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Discover and run tests
def run_all_tests():
    """
    Discovers and runs all tests in the 'backend' and 'frontend' directories.
    (Frontend tests would require a JS test runner like Jest/Mocha,
    this focuses on Python backend tests for now.)
    """
    # Discover tests in the backend directory
    backend_tests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    print(f"Discovering tests in: {backend_tests_dir}")

    # You might want to create a 'tests' folder inside 'backend' and discover from there
    # For now, we'll assume tests are within the backend sub-folders or directly in backend/
    loader = unittest.TestLoader()
    suite = loader.discover(backend_tests_dir, pattern="test_*.py")

    if not suite.countTestCases():
        print("No Python backend tests found. Please create test files (e.g., 'test_parser.py').")
        return

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\nAll backend tests passed!")
    else:
        print("\nSome backend tests failed.")

    # Add commands to run frontend tests if you set up a JS test runner (e.g., npm test)
    # print("\nTo run frontend tests (if configured):")
    # print("  cd frontend && npm test")


if __name__ == "__main__":
    run_all_tests()

