# 🧪 Test Scripts

## 🚀 Optimized Test Runner

### Quick Start
```bash
# Run all tests in optimized order (fast first, then slow)
python scripts/testing/run_tests_optimized.py

# Run only fast tests (recommended for development)
python scripts/testing/run_tests_optimized.py --fast-only

# Run only slow tests
python scripts/testing/run_tests_optimized.py --slow-only
```

### Advanced Usage
```bash
# Run specific test categories
python scripts/testing/run_tests_optimized.py --category "risk"
python scripts/testing/run_tests_optimized.py --category "positions"

# Run tests with specific markers
python scripts/testing/run_tests_optimized.py --markers "fast or api"
python scripts/testing/run_tests_optimized.py --markers "unit and not slow"

# Control number of parallel workers
python scripts/testing/run_tests_optimized.py --workers 4
python scripts/testing/run_tests_optimized.py --workers 2
```

## 📊 Performance

### Before Optimization
- **Sequential execution:** 6 minutes
- **No parallel processing**
- **All tests run in order**

### After Optimization
- **Parallel execution:** 3:10 minutes (47% faster)
- **8 workers** (auto-detected)
- **Smart categorization** (fast/slow)
- **Load balancing** across CPU cores

## 🔧 Configuration

### Environment Variables
The optimized runner sets these for better performance:
- `FASTAPI_DISABLE_WEBSOCKETS=true`
- `FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER=true`
- `FASTAPI_DEV_MODE=true`

### Test Categories
- **Fast:** `< 1s per test`
- **Slow:** `> 5s per test`
- **Integration:** Requires running server
- **Unit:** Isolated tests with mocks
- **API:** FastAPI endpoint tests

## 📋 Available Scripts

| Script | Purpose | Performance |
|--------|---------|-------------|
| `run_tests_optimized.py` | **Main optimized runner** | ⚡ 47% faster |
| `run_fast_tests.py` | Fast tests only | ⚡ Very fast |
| `run_tests_fast.py` | Legacy fast runner | 🐌 Slower |
| `run_integration_tests.py` | Integration tests | 🐌 Requires server |

## 🎯 Best Practices

### For Development
```bash
# Quick feedback loop
python scripts/testing/run_tests_optimized.py --fast-only
```

### For CI/CD
```bash
# Full test suite
python scripts/testing/run_tests_optimized.py
```

### For Debugging
```bash
# Single worker for easier debugging
python scripts/testing/run_tests_optimized.py --workers 1
```

## ⚠️ Troubleshooting

### If tests are slow
1. Check if you're running the optimized script
2. Verify pytest-xdist is installed: `pip show pytest-xdist`
3. Ensure no `PYTEST_DISABLE_PLUGIN_AUTOLOAD` is set

### If parallel execution fails
1. Try with fewer workers: `--workers 2`
2. Check for test isolation issues
3. Run with single worker for debugging: `--workers 1` 