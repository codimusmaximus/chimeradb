#!/bin/bash
set -e

echo "========================================="
echo "SQLite Knowledge Graph Setup"
echo "========================================="

# Detect platform
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected: $OS $ARCH"

# Create virtual environment
echo ""
echo "[1/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo ""
echo "[2/5] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Create extensions directory
echo ""
echo "[3/5] Setting up extensions directory..."
mkdir -p extensions
echo "✓ Extensions directory created"

# Download sqlite-graph extension
echo ""
echo "[4/5] Downloading sqlite-graph extension..."

if [ "$OS" = "Darwin" ]; then
    # macOS
    if [ "$ARCH" = "arm64" ]; then
        GRAPH_EXT="extensions/libgraph.dylib"
    else
        GRAPH_EXT="extensions/libgraph.dylib"
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
        cp ../sqlite-graph/build/libgraph.dylib extensions/
        echo "  ✓ Built and copied libgraph.dylib"
    else
        echo "  ✓ libgraph.dylib already exists"
    fi

elif [ "$OS" = "Linux" ]; then
    # Linux
    GRAPH_EXT="extensions/libgraph.so"

    if [ ! -f "$GRAPH_EXT" ]; then
        echo "  Building sqlite-graph from source..."
        if [ ! -d "../sqlite-graph" ]; then
            echo "  Error: sqlite-graph source not found"
            exit 1
        fi

        cd ../sqlite-graph
        make clean && make
        cd -
        cp ../sqlite-graph/build/libgraph.so extensions/
        echo "  ✓ Built and copied libgraph.so"
    else
        echo "  ✓ libgraph.so already exists"
    fi
else
    echo "  Warning: Unsupported OS. Please install extensions manually."
fi

# Download sqlite-vector extension
echo ""
echo "[5/5] Downloading sqlite-vector extension..."

if [ "$OS" = "Darwin" ]; then
    # macOS
    if [ "$ARCH" = "arm64" ]; then
        VECTOR_URL="https://github.com/sqliteai/sqlite-vector/releases/download/v0.9.52/vector-macos-arm64.dylib"
        VECTOR_EXT="extensions/vector.dylib"
    else
        VECTOR_URL="https://github.com/sqliteai/sqlite-vector/releases/download/v0.9.52/vector-macos-x86_64.dylib"
        VECTOR_EXT="extensions/vector.dylib"
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
    VECTOR_EXT="extensions/vector.so"

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
        graph_ext = "extensions/libgraph.dylib"
        vector_ext = "extensions/vector.dylib"
    else:
        graph_ext = "extensions/libgraph.so"
        vector_ext = "extensions/vector.so"

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
echo "  source venv/bin/activate"
echo "  python examples/01_quickstart.py"
echo ""
