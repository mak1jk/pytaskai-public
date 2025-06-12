"""
PyTaskAI Comprehensive Test Runner
Runs all test suites and provides detailed reporting
"""

import asyncio
import sys
import time
import traceback
from typing import Dict, List, Tuple, Any
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from test_basic import test_imports, test_aiservice_creation
from test_mcp_tools import run_mcp_tools_tests
from test_integration_workflows import run_sync_integration_tests
from test_jira_integration import run_jira_integration_tests
from test_performance import run_sync_performance_tests
from test_end_to_end_workflows import run_sync_end_to_end_tests


class TestRunner:
    """Comprehensive test runner for PyTaskAI"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        self.end_time = None
    
    def run_test_suite(self, name: str, test_func, description: str = "") -> bool:
        """Run a test suite and record results"""
        print(f"\n{'='*60}")
        print(f"🧪 Running {name}")
        if description:
            print(f"   {description}")
        print(f"{'='*60}")
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            success = test_func()
            if success:
                print(f"✅ {name} - PASSED")
            else:
                print(f"❌ {name} - FAILED")
                
        except Exception as e:
            success = False
            error_message = str(e)
            print(f"❌ {name} - ERROR: {error_message}")
            print(f"Traceback: {traceback.format_exc()}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Record results
        self.results[name] = {
            "success": success,
            "duration": duration,
            "error": error_message,
            "description": description
        }
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        self.total_tests += 1
        
        print(f"⏱️  Completed in {duration:.2f} seconds")
        return success
    
    def run_all_tests(self, skip_performance: bool = False) -> bool:
        """Run all test suites"""
        print("🚀 PyTaskAI Comprehensive Test Suite")
        print("="*60)
        
        self.start_time = time.time()
        
        # Test suite definitions
        test_suites = [
            {
                "name": "Basic Tests",
                "func": self._run_basic_tests,
                "description": "Core imports and basic functionality"
            },
            {
                "name": "MCP Tools Tests", 
                "func": run_mcp_tools_tests,
                "description": "Bug reporting, analytics, and task management tools"
            },
            {
                "name": "Integration Tests",
                "func": run_sync_integration_tests,
                "description": "Bug tracking workflows and task management integration"
            },
            {
                "name": "Jira Integration Tests",
                "func": run_jira_integration_tests,
                "description": "Jira mapping, configuration, and sync functionality"
            },
            {
                "name": "End-to-End Tests",
                "func": run_sync_end_to_end_tests,
                "description": "Complete user workflows and real-world scenarios"
            }
        ]
        
        # Conditionally add performance tests
        if not skip_performance:
            test_suites.append({
                "name": "Performance Tests",
                "func": run_sync_performance_tests,
                "description": "Large dataset handling and concurrent operations"
            })
        
        # Run all test suites
        for suite in test_suites:
            self.run_test_suite(
                suite["name"],
                suite["func"],
                suite["description"]
            )
        
        self.end_time = time.time()
        
        # Generate final report
        self._generate_final_report()
        
        return self.failed_tests == 0
    
    def _run_basic_tests(self) -> bool:
        """Run basic functionality tests"""
        try:
            test_imports()
            test_aiservice_creation()
            print("✅ All basic tests passed")
            return True
        except Exception as e:
            print(f"❌ Basic tests failed: {e}")
            return False
    
    def _generate_final_report(self):
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time
        
        print(f"\n{'='*60}")
        print("📊 FINAL TEST REPORT")
        print(f"{'='*60}")
        
        print(f"Total Tests Run: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📈 Success Rate: {(self.passed_tests/max(self.total_tests, 1)*100):.1f}%")
        
        print(f"\n{'='*40}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*40}")
        
        for name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f"{result['duration']:.2f}s"
            
            print(f"{status:<8} {name:<25} ({duration})")
            if result["description"]:
                print(f"         {result['description']}")
            if result["error"]:
                print(f"         Error: {result['error']}")
        
        if self.failed_tests > 0:
            print(f"\n⚠️  {self.failed_tests} test suite(s) failed!")
            print("Please review the detailed output above for specific issues.")
        else:
            print(f"\n🎉 All {self.total_tests} test suites passed successfully!")
        
        print(f"\n{'='*60}")
    
    def run_specific_test(self, test_name: str) -> bool:
        """Run a specific test suite"""
        test_mapping = {
            "basic": self._run_basic_tests,
            "mcp": run_mcp_tools_tests,
            "integration": run_sync_integration_tests,
            "jira": run_jira_integration_tests,
            "performance": run_sync_performance_tests,
            "e2e": run_sync_end_to_end_tests,
            "end-to-end": run_sync_end_to_end_tests
        }
        
        if test_name.lower() not in test_mapping:
            print(f"❌ Unknown test suite: {test_name}")
            print(f"Available tests: {', '.join(test_mapping.keys())}")
            return False
        
        self.start_time = time.time()
        success = self.run_test_suite(
            test_name.title() + " Tests",
            test_mapping[test_name.lower()],
            f"Running {test_name} test suite only"
        )
        self.end_time = time.time()
        
        self._generate_final_report()
        return success


def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PyTaskAI Comprehensive Test Runner")
    parser.add_argument(
        "--test", 
        type=str, 
        help="Run specific test suite (basic, mcp, integration, jira, performance, e2e)"
    )
    parser.add_argument(
        "--skip-performance", 
        action="store_true",
        help="Skip performance tests (for faster execution)"
    )
    parser.add_argument(
        "--quick",
        action="store_true", 
        help="Run only basic and MCP tools tests"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.test:
        # Run specific test
        success = runner.run_specific_test(args.test)
    elif args.quick:
        # Quick test mode
        print("🏃 Running quick test suite (basic + MCP tools only)")
        runner.start_time = time.time()
        
        basic_success = runner.run_test_suite(
            "Basic Tests",
            runner._run_basic_tests,
            "Core imports and basic functionality"
        )
        
        mcp_success = runner.run_test_suite(
            "MCP Tools Tests",
            run_mcp_tools_tests,
            "Bug reporting, analytics, and task management tools"
        )
        
        runner.end_time = time.time()
        runner._generate_final_report()
        success = basic_success and mcp_success
    else:
        # Run all tests
        success = runner.run_all_tests(skip_performance=args.skip_performance)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()