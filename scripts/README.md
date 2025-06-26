# 🛠️ Scripts & Tools Documentation

This directory contains development, deployment, and testing scripts for the **Crypto Trading Bot Dashboard Nexus** project.

---

## 📁 **Directory Structure**

```
scripts/
├── deployment/         # 🚀 Server startup and deployment
├── development/        # 🛠️ Development utilities and code quality
├── testing/           # 🧪 Test automation and verification
└── README.md          # 📖 This documentation
```

---

## 🚀 **[deployment/](./deployment/)** - Server Management

Scripts for starting, stopping, and managing application servers.

### 📋 **Available Scripts**

| Script | Platform | Description | Usage |
|--------|----------|-------------|-------|
| **[start-dev.sh](./deployment/start-dev.sh)** | Linux/macOS | Quick development startup | `./scripts/deployment/start-dev.sh` |
| **[start-servers.sh](./deployment/start-servers.sh)** | Linux/macOS | Flexible server management | `./scripts/deployment/start-servers.sh [backend\|frontend]` |
| **[start-servers.ps1](./deployment/start-servers.ps1)** | Windows PowerShell | Windows server management | `.\scripts\deployment\start-servers.ps1 [backend\|frontend]` |

### 🔥 **Quick Start Examples**

```bash
# Start both servers quickly
./scripts/deployment/start-dev.sh

# Start only backend
./scripts/deployment/start-servers.sh backend

# Start only frontend  
./scripts/deployment/start-servers.sh frontend

# Windows PowerShell
.\scripts\deployment\start-servers.ps1 backend
```

### ⚙️ **Script Features**

- **Health Checks**: Verify server startup and port availability
- **Error Handling**: Graceful failure with helpful error messages
- **Flexible Options**: Start individual services or both together
- **Cross-Platform**: Linux, macOS, and Windows support
- **Environment Setup**: Automatic virtual environment activation

---

## 🛠️ **[development/](./development/)** - Development Tools

Utilities for code quality, formatting, and development workflow.

### 📋 **Available Tools**

| Tool | Description | Purpose | Usage |
|------|-------------|---------|-------|
| **[format_code.sh](./development/format_code.sh)** | Code formatting pipeline | Code quality | `./scripts/development/format_code.sh` |
| **[fix_line_length.py](./development/fix_line_length.py)** | Automatic line length fixer | Code formatting | `python scripts/development/fix_line_length.py` |

### 🎨 **Code Formatting Pipeline**

**[format_code.sh](./development/format_code.sh)** - Comprehensive code quality pipeline:

```bash
# Run complete formatting pipeline
./scripts/development/format_code.sh
```

**Pipeline Steps:**
1. **isort** - Import organization
2. **black** - Code formatting  
3. **flake8** - Linting and quality checks

**Features:**
- ✅ Excludes `venv/` directories automatically
- ✅ Progress reporting with colored output
- ✅ Error handling with helpful tips
- ✅ Summary report of all changes

### 🔧 **Line Length Fixer**

**[fix_line_length.py](./development/fix_line_length.py)** - Automatic E501 error resolution:

```bash
# Fix line length issues automatically
cd backend
python ../scripts/development/fix_line_length.py
```

**Features:**
- ✅ Automatically applies Black formatting
- ✅ Handles E501 line-too-long errors
- ✅ Preserves code functionality
- ✅ Shows before/after diff

---

## 🧪 **[testing/](./testing/)** - Test Automation & Verification

Tools for testing, verification, and quality assurance.

### 📋 **Available Tools**

| Tool | Description | Focus Area | Usage |
|------|-------------|------------|-------|
| **[fix_orderbook_integration.sh](./testing/fix_orderbook_integration.sh)** | OrderBook integration fixes | API Integration | `./scripts/testing/fix_orderbook_integration.sh` |
| **[performance-test.sh](./testing/performance-test.sh)** | Performance testing suite | Performance | `./scripts/testing/performance-test.sh` |
| **[run_backend_integration_test.sh](./testing/run_backend_integration_test.sh)** | Backend integration tests | API Testing | `./scripts/testing/run_backend_integration_test.sh` |
| **[run_websocket_verification.sh](./testing/run_websocket_verification.sh)** | WebSocket verification | Real-time Testing | `./scripts/testing/run_websocket_verification.sh` |
| **[test_backend_websocket_integration.py](./testing/test_backend_websocket_integration.py)** | WebSocket integration test | WebSocket Testing | `python scripts/testing/test_backend_websocket_integration.py` |
| **[test_bitfinex_connection.py](./testing/test_bitfinex_connection.py)** | Bitfinex API connection test | Exchange Testing | `python scripts/testing/test_bitfinex_connection.py` |
| **[websocket_verification_tool.py](./testing/websocket_verification_tool.py)** | WebSocket verification utility | Real-time Verification | `python scripts/testing/websocket_verification_tool.py` |

### 🔍 **Testing Categories**

#### 📡 **WebSocket Testing**
```bash
# Verify WebSocket connections
./scripts/testing/run_websocket_verification.sh

# Test WebSocket integration
python scripts/testing/test_backend_websocket_integration.py

# WebSocket verification tool
python scripts/testing/websocket_verification_tool.py
```

#### 📈 **Exchange Integration Testing**
```bash
# Test Bitfinex connection
python scripts/testing/test_bitfinex_connection.py

# Fix OrderBook integration issues
./scripts/testing/fix_orderbook_integration.sh
```

#### 🔄 **Backend Integration Testing**
```bash
# Run complete backend integration tests
./scripts/testing/run_backend_integration_test.sh

# Performance testing
./scripts/testing/performance-test.sh
```

---

## 🎯 **Usage Workflows**

### 🚀 **Development Workflow**

```bash
# 1. Start development environment
./scripts/deployment/start-dev.sh

# 2. Format code before commits
./scripts/development/format_code.sh

# 3. Run integration tests
./scripts/testing/run_backend_integration_test.sh

# 4. Verify WebSocket functionality
./scripts/testing/run_websocket_verification.sh
```

### 🧪 **CI Preparation Workflow**

```bash
# 1. Format and lint all code
./scripts/development/format_code.sh

# 2. Fix line length issues
cd backend && python ../scripts/development/fix_line_length.py

# 3. Run comprehensive tests
pytest backend/tests/ -v

# 4. Verify integrations
./scripts/testing/run_backend_integration_test.sh
```

### 🔧 **Troubleshooting Workflow**

```bash
# 1. Test exchange connections
python scripts/testing/test_bitfinex_connection.py

# 2. Verify WebSocket functionality
python scripts/testing/websocket_verification_tool.py

# 3. Fix integration issues
./scripts/testing/fix_orderbook_integration.sh

# 4. Performance analysis
./scripts/testing/performance-test.sh
```

---

## 🏗️ **Script Development Guidelines**

### ✅ **Best Practices**

1. **Error Handling**: All scripts should handle errors gracefully
2. **Documentation**: Include clear usage instructions and examples
3. **Cross-Platform**: Consider Windows compatibility where possible
4. **Progress Feedback**: Provide clear output about what's happening
5. **Exit Codes**: Use proper exit codes (0 = success, 1+ = error)

### 📋 **Script Template**

```bash
#!/bin/bash
# Script Name: example_script.sh
# Description: Brief description of what this script does
# Usage: ./scripts/category/example_script.sh [options]

set -e  # Exit on error

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting example script..."

# Main script logic here

echo "✅ Script completed successfully"
```

### 🔧 **Adding New Scripts**

1. **Choose correct directory** (`deployment/`, `development/`, or `testing/`)
2. **Follow naming conventions** (descriptive, lowercase with hyphens)
3. **Include proper shebang** (`#!/bin/bash` for shell scripts)
4. **Add documentation** (description, usage, examples)
5. **Make executable** (`chmod +x script_name.sh`)
6. **Update this README** with script description and usage

---

## 🤝 **Contributing**

When adding new scripts or modifying existing ones:

1. **Test thoroughly** on multiple platforms where applicable
2. **Document changes** in this README
3. **Follow existing patterns** for consistency
4. **Include error handling** and helpful output messages
5. **Update main project documentation** if scripts affect user workflows

---

## 📚 **Related Documentation**

- **[../docs/guides/QUICK_DEPLOYMENT_GUIDE.md](../docs/guides/QUICK_DEPLOYMENT_GUIDE.md)** - Deployment procedures
- **[../docs/guides/DEBUG_GUIDE.md](../docs/guides/DEBUG_GUIDE.md)** - Troubleshooting guide
- **[../docs/solutions/SERVER_START_SOLUTION.md](../docs/solutions/SERVER_START_SOLUTION.md)** - Server startup solutions
- **[../README.md](../README.md)** - Main project documentation

---

**🔄 Last Updated:** Created during CI preparation and file organization (December 2024)  
**📊 Total Scripts:** 10+ tools organized across 3 categories 