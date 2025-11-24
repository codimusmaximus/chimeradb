#!/bin/bash
set -e

echo "========================================="
echo "🔥 ChimeraDB Setup"
echo "========================================="

# Detect platform
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected: $OS $ARCH"

# Check for uv, install if needed
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment with uv
echo ""
echo "[1/6] Creating virtual environment with uv..."
if [ ! -d ".venv" ]; then
    uv venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo ""
echo "[2/6] Installing Python dependencies..."
uv pip install -r requirements.txt
echo "✓ Dependencies installed"

# Install package in editable mode
echo ""
echo "[3/6] Installing chimeradb package..."
uv pip install -e .
echo "✓ Package installed in editable mode"

# Create extensions directory
echo ""
echo "[4/6] Setting up extensions directory..."
mkdir -p extensions
echo "✓ Extensions directory created"

# Download sqlite-graph extension
echo ""
echo "[5/6] Downloading sqlite-graph extension..."

if [ "$OS" = "Darwin" ]; then
    # macOS
    if [ "$ARCH" = "arm64" ]; then
        GRAPH_EXT="chimeradb/extensions/libgraph.dylib"
    else
        GRAPH_EXT="chimeradb/extensions/libgraph.dylib"
    fi

    if [ ! -f "$GRAPH_EXT" ]; then
        # Build from source since pre-built may not be available
        echo "  Building sqlite-graph from source..."
        if [ ! -d "../sqlite-graph" ]; then
            echo "  Error: sqlite-graph source not found at ../sqlite-graph"
            echo "  Please clone: git clone https://github.com/agentflare-ai/sqlite-graph.git ../sqlite-graph"
            exit 1
        fi

        cd ../sqlite-graph
        make clean && make
        cd -
        cp ../sqlite-graph/build/libgraph.dylib chimeradb/extensions/
        echo "  ✓ Built and copied libgraph.dylib"
    else
        echo "  ✓ libgraph.dylib already exists"
    fi

elif [ "$OS" = "Linux" ]; then
    # Linux
    GRAPH_EXT="chimeradb/extensions/libgraph.so"

    if [ ! -f "$GRAPH_EXT" ]; then
        echo "  Building sqlite-graph from source..."
        if [ ! -d "../sqlite-graph" ]; then
            echo "  Error: sqlite-graph source not found"
            exit 1
        fi

        cd ../sqlite-graph
        make clean && make
        cd -
        cp ../sqlite-graph/build/libgraph.so chimeradb/extensions/
        echo "  ✓ Built and copied libgraph.so"
    else
        echo "  ✓ libgraph.so already exists"
    fi
else
    echo "  Warning: Unsupported OS. Please install extensions manually."
fi

# Download sqlite-vector extension
echo ""
echo "[6/6] Downloading sqlite-vector extension..."

if [ "$OS" = "Darwin" ]; then
    # macOS
    if [ "$ARCH" = "arm64" ]; then
        VECTOR_URL="https://github.com/sqliteai/sqlite-vector/releases/download/v0.9.52/vector-macos-arm64.dylib"
        VECTOR_EXT="chimeradb/extensions/vector.dylib"
    else
        VECTOR_URL="https://github.com/sqliteai/sqlite-vector/releases/download/v0.9.52/vector-macos-x86_64.dylib"
        VECTOR_EXT="chimeradb/extensions/vector.dylib"
    fi

    if [ ! -f "$VECTOR_EXT" ] || [ $(stat -f%z "$VECTOR_EXT" 2>/dev/null || echo 0) -lt 1000 ]; then
        echo "  Downloading from $VECTOR_URL..."
        curl -L "$VECTOR_URL" -o "$VECTOR_EXT"

        # Verify download
        if [ $(stat -f%z "$VECTOR_EXT") -lt 1000 ]; then
            echo "  Download failed. Trying Python package method..."
            pip install sqliteai-vector -q
            VECTOR_PATH=$(python3 -c "import os; import sqlite_vector; print(os.path.join(os.path.dirname(sqlite_vector.__file__), 'binaries', 'vector.dylib'))" 2>/dev/null || echo "")
            if [ -f "$VECTOR_PATH" ]; then
                cp "$VECTOR_PATH" "$VECTOR_EXT"
                echo "  ✓ Copied from Python package"
            else
                echo "  Error: Could not download vector extension"
                exit 1
            fi
        else
            echo "  ✓ Downloaded vector.dylib"
        fi
    else
        echo "  ✓ vector.dylib already exists"
    fi

elif [ "$OS" = "Linux" ]; then
    # Linux
    VECTOR_URL="https://github.com/sqliteai/sqlite-vector/releases/download/v0.9.52/vector-linux-x86_64.so"
    VECTOR_EXT="chimeradb/extensions/vector.so"

    if [ ! -f "$VECTOR_EXT" ] || [ $(stat -c%s "$VECTOR_EXT" 2>/dev/null || echo 0) -lt 1000 ]; then
        echo "  Downloading from $VECTOR_URL..."
        curl -L "$VECTOR_URL" -o "$VECTOR_EXT"

        if [ $(stat -c%s "$VECTOR_EXT") -lt 1000 ]; then
            echo "  Download failed. Trying Python package method..."
            pip install sqliteai-vector -q
            VECTOR_PATH=$(python3 -c "import os; import sqlite_vector; print(os.path.join(os.path.dirname(sqlite_vector.__file__), 'binaries', 'vector.so'))" 2>/dev/null || echo "")
            if [ -f "$VECTOR_PATH" ]; then
                cp "$VECTOR_PATH" "$VECTOR_EXT"
                echo "  ✓ Copied from Python package"
            else
                echo "  Error: Could not download vector extension"
                exit 1
            fi
        else
            echo "  ✓ Downloaded vector.so"
        fi
    else
        echo "  ✓ vector.so already exists"
    fi
fi

# Test the setup
echo ""
echo "========================================="
echo "Testing installation..."
echo "========================================="

python3 << 'PYTEST'
import sqlite3
import os
import sys

try:
    conn = sqlite3.connect(":memory:")
    conn.enable_load_extension(True)

    # Determine extension paths
    if sys.platform == "darwin":
        graph_ext = "chimeradb/extensions/libgraph.dylib"
        vector_ext = "chimeradb/extensions/vector.dylib"
    else:
        graph_ext = "chimeradb/extensions/libgraph.so"
        vector_ext = "chimeradb/extensions/vector.so"

    # Test graph extension
    if os.path.exists(graph_ext):
        conn.load_extension(graph_ext.replace('.dylib', '').replace('.so', ''))
        print("✓ Graph extension loaded")
    else:
        print(f"✗ Graph extension not found: {graph_ext}")
        sys.exit(1)

    # Test vector extension
    if os.path.exists(vector_ext):
        conn.load_extension(vector_ext.replace('.dylib', '').replace('.so', ''))
        version = conn.execute("SELECT vector_version()").fetchone()[0]
        print(f"✓ Vector extension loaded (v{version})")
    else:
        print(f"✗ Vector extension not found: {vector_ext}")
        sys.exit(1)

    # Test basic functionality
    conn.execute("CREATE VIRTUAL TABLE graph USING graph()")
    print("✓ Graph table created")

    conn.close()
    print("\n✅ Installation successful!")

except Exception as e:
    print(f"\n✗ Installation test failed: {e}")
    sys.exit(1)
PYTEST

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "To get started:"
echo "  source .venv/bin/activate"
echo "  python3 examples/01_getting_started.py"
echo ""
