# 🧪 MindAware Test Suite

## Quick Start

### Run All Tests
```bash
cd /Users/zain/Desktop/MindAware
python run_tests.py
```

### Run Individual Test
```bash
python tests/test_policy.py          # Policy engine
python tests/test_tools.py           # Drone tools
python tests/test_integration.py     # Integration
python tests/test_simulators.py      # Simulators
python tests/test_api.py             # API (requires backend)
```

---

## Test Files

| File | Tests | Description | Duration |
|------|-------|-------------|----------|
| `test_policy.py` | 5 | Binary decision logic | ~0.1s |
| `test_tools.py` | 6 | Drone control actions | ~0.1s |
| `test_integration.py` | 5 | End-to-end flows | ~0.2s |
| `test_simulators.py` | 6 | EEG & Drone sims | ~0.5s |
| `test_api.py` | 7 | API endpoints | ~2s |
| **TOTAL** | **29** | **Full coverage** | **~3s** |

---

## Test Results

```
✅ ALL 29 TESTS PASSING
```

See `../TESTING_SUMMARY.md` for detailed results.

---

## Documentation

- **`../TESTING_GUIDE.md`** - Comprehensive testing guide
- **`../TEST_QUICK_REFERENCE.md`** - Quick command reference
- **`../TESTING_SUMMARY.md`** - Test results and coverage
- **`../TEST_FILES_OVERVIEW.md`** - File descriptions

---

**Built for reliable cognitive monitoring**


