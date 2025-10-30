#!/bin/bash
"""
Install MCP requirements for the enhanced orchestrator
"""

echo "🔧 Installing MCP Requirements for Enhanced Orchestrator..."
echo "=" * 60

# Check if we're in the right environment
if [[ "$CONDA_DEFAULT_ENV" != "tech_summit" ]]; then
    echo "⚠️  Please activate the tech_summit conda environment first:"
    echo "conda activate tech_summit"
    exit 1
fi

# Install MCP Python SDK
echo "📦 Installing MCP Python SDK..."
pip install mcp>=1.17.1

# Install async tools
echo "📦 Installing async utilities..."
pip install asyncio-tools aiofiles

# Verify installation
echo "✅ Verifying MCP installation..."
python -c "
try:
    import mcp
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    print('✅ MCP SDK installed successfully')
    print(f'   Version: {mcp.__version__ if hasattr(mcp, \"__version__\") else \"Unknown\"}')
except ImportError as e:
    print(f'❌ MCP installation failed: {e}')
    exit(1)
"

# Install other dependencies if not already present
echo "📦 Installing additional dependencies..."
pip install boto3>=1.40.0 pydantic>=2.11.0

echo ""
echo "🎉 MCP Requirements Installation Complete!"
echo "=" * 60
echo "Next steps:"
echo "1. Deploy the MCP orchestrator: python deploy_mcp_orchestrator.py"
echo "2. Test MCP connectivity: python test_mcp_agents.py"  
echo "3. Run enhanced Streamlit: streamlit run streamlit_mcp_orchestrator.py"
