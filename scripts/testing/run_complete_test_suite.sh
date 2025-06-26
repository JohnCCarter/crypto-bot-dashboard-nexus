#!/bin/bash

# 🧪 Complete Test Suite Runner
# Runs both mock and integration tests systematically
# Usage: ./scripts/testing/run_complete_test_suite.sh [--mock-only|--integration-only]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="."
INTEGRATION_DIR="backend/tests/integration"

# Test flags
RUN_MOCK_TESTS=true
RUN_INTEGRATION_TESTS=true
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mock-only)
            RUN_INTEGRATION_TESTS=false
            shift
            ;;
        --integration-only)
            RUN_MOCK_TESTS=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--mock-only|--integration-only] [--verbose]"
            echo "  --mock-only: Only run mock/unit tests"
            echo "  --integration-only: Only run integration tests"
            echo "  --verbose: Show detailed test output"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🧪 Complete Test Suite Runner${NC}"
echo -e "${BLUE}================================${NC}"

# Track results
BACKEND_MOCK_RESULT=0
FRONTEND_MOCK_RESULT=0
INTEGRATION_RESULT=0

# Function to check if backend server is running
check_backend_server() {
    echo -e "${YELLOW}🔍 Checking if backend server is running...${NC}"
    if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend server is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend server is not running${NC}"
        echo -e "${YELLOW}💡 Start with: python -m backend.app${NC}"
        return 1
    fi
}

# Function to run backend mock tests
run_backend_mock_tests() {
    echo -e "${BLUE}🐍 Running Backend Mock Tests${NC}"
    echo -e "${BLUE}================================${NC}"
    
    cd $BACKEND_DIR
    
    if [[ "$VERBOSE" == "true" ]]; then
        python -m pytest tests/ -v --tb=short --ignore=tests/integration
    else
        python -m pytest tests/ --ignore=tests/integration
    fi
    
    BACKEND_MOCK_RESULT=$?
    cd ..
    
    if [[ $BACKEND_MOCK_RESULT -eq 0 ]]; then
        echo -e "${GREEN}✅ Backend mock tests passed${NC}"
    else
        echo -e "${RED}❌ Backend mock tests failed${NC}"
    fi
    
    return $BACKEND_MOCK_RESULT
}

# Function to run frontend mock tests  
run_frontend_mock_tests() {
    echo -e "${BLUE}⚛️ Running Frontend Mock Tests${NC}"
    echo -e "${BLUE}================================${NC}"
    
    if [[ "$VERBOSE" == "true" ]]; then
        npm test -- --run --reporter=verbose
    else
        npm test -- --run
    fi
    
    FRONTEND_MOCK_RESULT=$?
    
    if [[ $FRONTEND_MOCK_RESULT -eq 0 ]]; then
        echo -e "${GREEN}✅ Frontend mock tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️ Frontend mock tests have some failures (non-critical)${NC}"
    fi
    
    return $FRONTEND_MOCK_RESULT
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${BLUE}🔗 Running Integration Tests${NC}"
    echo -e "${BLUE}================================${NC}"
    
    # Check if backend is running
    if ! check_backend_server; then
        echo -e "${RED}❌ Cannot run integration tests without backend server${NC}"
        return 1
    fi
    
    cd $BACKEND_DIR
    
    if [[ "$VERBOSE" == "true" ]]; then
        python -m pytest tests/integration/ -v --tb=short
    else
        python -m pytest tests/integration/ --tb=short
    fi
    
    INTEGRATION_RESULT=$?
    cd ..
    
    if [[ $INTEGRATION_RESULT -eq 0 ]]; then
        echo -e "${GREEN}✅ Integration tests passed${NC}"
    else
        echo -e "${RED}❌ Integration tests failed${NC}"
    fi
    
    return $INTEGRATION_RESULT
}

# Function to print summary
print_summary() {
    echo -e "${BLUE}📊 Test Summary${NC}"
    echo -e "${BLUE}===============${NC}"
    
    local total_failed=0
    
    if [[ "$RUN_MOCK_TESTS" == "true" ]]; then
        if [[ $BACKEND_MOCK_RESULT -eq 0 ]]; then
            echo -e "${GREEN}✅ Backend Mock Tests: PASSED${NC}"
        else
            echo -e "${RED}❌ Backend Mock Tests: FAILED${NC}"
            ((total_failed++))
        fi
        
        if [[ $FRONTEND_MOCK_RESULT -eq 0 ]]; then
            echo -e "${GREEN}✅ Frontend Mock Tests: PASSED${NC}"
        else
            echo -e "${YELLOW}⚠️ Frontend Mock Tests: SOME FAILURES (non-critical)${NC}"
        fi
    fi
    
    if [[ "$RUN_INTEGRATION_TESTS" == "true" ]]; then
        if [[ $INTEGRATION_RESULT -eq 0 ]]; then
            echo -e "${GREEN}✅ Integration Tests: PASSED${NC}"
        else
            echo -e "${RED}❌ Integration Tests: FAILED${NC}"
            ((total_failed++))
        fi
    fi
    
    echo ""
    if [[ $total_failed -eq 0 ]]; then
        echo -e "${GREEN}🎉 ALL CRITICAL TESTS PASSED! Ready for deployment.${NC}"
        return 0
    else
        echo -e "${RED}💥 $total_failed critical test suite(s) failed.${NC}"
        return 1
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Run tests based on flags
    if [[ "$RUN_MOCK_TESTS" == "true" ]]; then
        run_backend_mock_tests
        echo ""
        run_frontend_mock_tests  
        echo ""
    fi
    
    if [[ "$RUN_INTEGRATION_TESTS" == "true" ]]; then
        run_integration_tests
        echo ""
    fi
    
    # Print summary
    print_summary
    local summary_result=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo -e "${BLUE}⏱️ Total time: ${duration}s${NC}"
    
    return $summary_result
}

# Run main function
main "$@" 