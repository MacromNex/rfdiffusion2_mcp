"""Shared utilities for MCP server."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# Setup paths
MCP_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"

# Add scripts to Python path for imports
sys.path.insert(0, str(SCRIPTS_DIR))


def validate_dependencies() -> Dict[str, bool]:
    """Check which dependencies are available."""
    dependencies = {
        "chai_lab": False,
        "apptainer": False,
        "rfdf_repo": False
    }

    # Check chai_lab
    try:
        import chai_lab
        dependencies["chai_lab"] = True
    except ImportError:
        pass

    # Check apptainer/singularity
    import shutil
    if shutil.which("apptainer") or shutil.which("singularity"):
        dependencies["apptainer"] = True

    # Check RFdiffusion2 repo
    rfdf_path = MCP_ROOT / "repo" / "RFdiffusion2"
    if rfdf_path.exists():
        container_path = rfdf_path / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif"
        if container_path.exists():
            dependencies["rfdf_repo"] = True

    return dependencies


def check_script_requirements(script_name: str) -> Dict[str, Any]:
    """Check if requirements are met for a specific script."""
    deps = validate_dependencies()

    requirements = {
        "chai1_structure_prediction": ["chai_lab"],
        "enzyme_active_site_scaffolding": ["apptainer", "rfdf_repo"],
        "small_molecule_binder": ["apptainer", "rfdf_repo"]
    }

    script_deps = requirements.get(script_name, [])
    missing = [dep for dep in script_deps if not deps[dep]]

    return {
        "available": len(missing) == 0,
        "missing_dependencies": missing,
        "all_dependencies": deps
    }


def get_script_path(script_name: str) -> Path:
    """Get the full path to a script."""
    if not script_name.endswith('.py'):
        script_name += '.py'
    return SCRIPTS_DIR / script_name


def handle_script_error(error: Exception, script_name: str) -> Dict[str, Any]:
    """Handle and format script execution errors."""
    error_msg = str(error)

    # Common error patterns and user-friendly messages
    if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
        return {
            "status": "error",
            "error_type": "dependency_missing",
            "error": f"Missing required dependencies for {script_name}. {error_msg}",
            "suggestion": "Check that all required packages are installed in the environment."
        }
    elif "FileNotFoundError" in error_msg:
        return {
            "status": "error",
            "error_type": "file_not_found",
            "error": f"Required file not found: {error_msg}",
            "suggestion": "Check that input files exist and paths are correct."
        }
    elif "Permission" in error_msg:
        return {
            "status": "error",
            "error_type": "permission_error",
            "error": f"Permission error: {error_msg}",
            "suggestion": "Check file permissions and write access to output directories."
        }
    else:
        return {
            "status": "error",
            "error_type": "execution_error",
            "error": f"Script execution failed: {error_msg}",
            "suggestion": "Check the log output for more details."
        }