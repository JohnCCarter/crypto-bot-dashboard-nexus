#!/bin/bash
# 🔧 Development Environment Setup Script
# Följer cursor-rules-general-standards.mdc och Zero-Fault Troubleshooting

set -e  # Exit on any error

echo "🔧 Setting up Development Environment..."
echo "════════════════════════════════════════"

# 1. Kontrollera att vi är i rätt katalog
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# 2. Hantera Python environment (venv or system)
echo "🐍 Setting up Python environment..."
# Test if venv module is actually functional
if python3 -c "import venv; import tempfile; import os; d=tempfile.mkdtemp(); venv.create(d); os.rmdir(d)" 2>/dev/null; then
    # venv is available and functional
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"  
    fi
    PYTHON_SETUP="source venv/bin/activate"
    PIP_CMD="pip"
else
    # venv not available, use system python with --user
    echo "⚠️  python3-venv not functional, using system Python with --user"
    PYTHON_SETUP=""
    PIP_CMD="pip3 install --user --break-system-packages"
fi

# 3. Installera backend dependencies
echo "📦 Installing backend dependencies..."
if [ -n "$PYTHON_SETUP" ]; then
    eval $PYTHON_SETUP
    pip install --upgrade pip
    pip install -r backend/requirements.txt
else
    $PIP_CMD --upgrade pip
    $PIP_CMD -r backend/requirements.txt
fi
echo "✅ Backend dependencies installed"

# 4. Installera frontend dependencies
echo "📱 Installing frontend dependencies..."
npm ci
echo "✅ Frontend dependencies installed"

# 5. Kontrollera att alla __init__.py finns (enligt general standards)
echo "🔍 Verifying Python package structure..."
find backend -type d -name "*" | grep -v "__pycache__" | while read dir; do
    if [[ "$dir" != "backend" ]] && [[ ! -f "$dir/__init__.py" ]]; then
        echo "⚠️  Missing __init__.py in $dir"
    fi
done

# 6. Testa imports
echo "🧪 Testing backend imports..."
if [ -n "$PYTHON_SETUP" ]; then
    eval $PYTHON_SETUP
fi
PYTHONPATH=/workspace python3 -c "
import sys
sys.path.insert(0, '/workspace')
try:
    import backend.app
    print('✅ Backend imports working')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "✅ Development environment setup complete!"
echo "🚀 Run './scripts/start-dev.sh' to start servers"