# 🚀 Test Optimization Guide

## 📊 Performance Improvements

### Before Optimization

- **Sequential execution:** 6 minutes for full test suite
- **No parallel processing**
- **All tests run in order**
- **Sleep delays and polling loops**

### After Optimization

- **Parallel execution:** 3:10 minutes (47% faster)
- **8 workers** (auto-detected CPU cores)
- **Smart test categorization**
- **Optimized sleep times and reduced polling**

## 🔧 Implementation Details

### 1. Parallel Execution Setup

```bash
# Install pytest-xdist for parallel testing
pip install pytest-xdist

# Configure pytest.ini for automatic parallel execution
addopts = 
    -n auto          # Auto-detect CPU cores
    --maxfail=5      # Stop after 5 failures
    --color=yes      # Colored output
```

### 2. Test Categorization

```python
# Mark tests for optimal execution
@pytest.mark.fast      # < 1s tests
@pytest.mark.slow      # > 5s tests  
@pytest.mark.unit      # Isolated unit tests
@pytest.mark.api       # API endpoint tests
@pytest.mark.integration  # End-to-end tests
```

### 3. Optimized Test Scripts

```bash
# Main optimized runner
python scripts/testing/run_tests_optimized.py

# Fast tests only (development)
python scripts/testing/run_tests_optimized.py --fast-only

# Specific categories
python scripts/testing/run_tests_optimized.py --category "risk"
```

## 🎯 Best Practices

### For Developers

1. **Always use parallel execution:**

   ```bash
   python -m pytest backend/tests/  # Uses -n auto by default
   ```

2. **Use fast tests for development:**

   ```bash
   python scripts/testing/run_tests_optimized.py --fast-only
   ```

3. **Categorize new tests:**

   ```python
   @pytest.mark.fast
   def test_quick_function():
       # Fast test implementation
       pass
   
   @pytest.mark.slow  
   def test_complex_integration():
       # Slow test implementation
       pass
   ```

### For CI/CD

1. **Use optimized runner:**

   ```bash
   python scripts/testing/run_tests_optimized.py
   ```

2. **Configure appropriate workers:**

   ```bash
   # For CI with limited resources
   python scripts/testing/run_tests_optimized.py --workers 2
   ```

## 🔍 Troubleshooting

### Common Issues

#### 1. Parallel Execution Not Working

```bash
# Check if pytest-xdist is installed
pip show pytest-xdist

# Verify plugin is loaded
python -m pytest --trace-config | grep xdist
```

#### 2. Tests Running Slowly

```bash
# Check if using optimized script
python scripts/testing/run_tests_optimized.py --fast-only

# Verify no plugin autoload disabled
echo $PYTEST_DISABLE_PLUGIN_AUTOLOAD  # Should be empty
```

#### 3. Test Failures in Parallel

```bash
# Run with single worker for debugging
python scripts/testing/run_tests_optimized.py --workers 1
```

## 📈 Performance Monitoring

### Test Duration Tracking

```bash
# Show slowest tests
python -m pytest backend/tests/ --durations=10

# Show tests taking > 0.5s
python -m pytest backend/tests/ --durations-min=0.5
```

### Worker Utilization

```bash
# Monitor worker performance
python -m pytest backend/tests/ -n auto -v
```

## 🚨 Important Notes

### 1. Test Isolation

- Ensure tests don't share state
- Use proper fixtures and cleanup
- Avoid global variables in tests

### 2. Resource Management

- Monitor memory usage with parallel execution
- Adjust worker count based on system resources
- Consider using fewer workers for slow tests

### 3. Integration Tests

- Integration tests still require running server
- Run separately: `pytest backend/tests/integration/`
- Mark with `@pytest.mark.integration`

## 🔄 Migration Guide

### From Old Test Scripts

```bash
# Old way (slow)
python scripts/testing/run_tests_fast.py

# New way (fast)
python scripts/testing/run_tests_optimized.py --fast-only
```

### From Sequential Execution

```bash
# Old way (slow)
python -m pytest backend/tests/

# New way (fast) - automatically parallel
python -m pytest backend/tests/  # Now uses -n auto by default
```

## 📋 Checklist for New Tests

- [ ] Add appropriate markers (`@pytest.mark.fast`, `@pytest.mark.slow`, etc.)
- [ ] Ensure test isolation (no shared state)
- [ ] Optimize sleep times and polling loops
- [ ] Test with parallel execution
- [ ] Document any special requirements

## 🎉 Success Metrics

- **47% faster test execution** (6min → 3:10min)
- **8 parallel workers** utilizing all CPU cores
- **Smart categorization** for optimal execution order
- **Automatic parallel execution** by default

## 🚦 Frontend Testning (Vitest)

- Frontend-tester körs med Vitest:

  ```bash
  npm run test
  npx vitest list
  ```

- Förväntat resultat: **10/10 testfiler ska passera** (1 test kan vara "skipped" – detta är normalt).
- Alla tester måste passera innan PR/merge.
