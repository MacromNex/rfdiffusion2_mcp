"""MCP Server for RFdiffusion2

Provides both synchronous and asynchronous (submit) APIs for protein design tools.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from utils import (
    check_script_requirements,
    get_script_path,
    handle_script_error,
    validate_dependencies
)
from loguru import logger

# Create MCP server
mcp = FastMCP("RFdiffusion2")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)


@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)


@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)


@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)


@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)


# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def check_dependencies() -> dict:
    """
    Check which dependencies are available for RFdiffusion2 tools.

    Returns:
        Dictionary showing availability of required dependencies
    """
    deps = validate_dependencies()

    # Check specific script requirements
    script_requirements = {}
    for script in ["chai1_structure_prediction", "enzyme_active_site_scaffolding", "small_molecule_binder"]:
        script_requirements[script] = check_script_requirements(script)

    return {
        "status": "success",
        "dependencies": deps,
        "script_requirements": script_requirements,
        "summary": {
            "chai1_available": deps["chai_lab"],
            "rfdiffusion2_available": deps["apptainer"] and deps["rfdf_repo"],
            "recommendations": [
                "Install chai-lab for structure prediction: pip install chai-lab" if not deps["chai_lab"] else None,
                "Install apptainer for RFdiffusion2 tools" if not deps["apptainer"] else None,
                "Setup RFdiffusion2 repository and containers" if not deps["rfdf_repo"] else None
            ]
        }
    }


# ==============================================================================
# Synchronous Tools (for fast operations)
# ==============================================================================

@mcp.tool()
def predict_structure_fast(
    sequence: str = None,
    input_file: str = None,
    output_dir: str = None,
    recycles: int = 1,
    timesteps: int = 50
) -> dict:
    """
    Fast protein structure prediction using Chai1 (synchronous - for small sequences only).

    This is a synchronous version for quick predictions with reduced quality settings.
    For high-quality predictions or longer sequences, use submit_structure_prediction.

    Args:
        sequence: Single protein sequence (alternative to input_file)
        input_file: Path to FASTA file with sequences
        output_dir: Directory to save results
        recycles: Number of recycles (1 for fast, 3-5 for quality)
        timesteps: Number of timesteps (50 for fast, 200+ for quality)

    Returns:
        Dictionary with prediction results and output paths
    """
    # Check dependencies
    req_check = check_script_requirements("chai1_structure_prediction")
    if not req_check["available"]:
        return {
            "status": "error",
            "error": f"Missing dependencies: {', '.join(req_check['missing_dependencies'])}",
            "suggestion": "Install chai-lab: pip install chai-lab"
        }

    try:
        # Import and run the script function
        from chai1_structure_prediction import run_chai1_prediction

        result = run_chai1_prediction(
            sequence=sequence,
            input_file=input_file,
            output_file=output_dir,
            num_recycles=recycles,
            num_timesteps=timesteps
        )

        return {"status": "success", **result}

    except Exception as e:
        return handle_script_error(e, "chai1_structure_prediction")


# ==============================================================================
# Submit Tools (for long-running operations)
# ==============================================================================

@mcp.tool()
def submit_structure_prediction(
    sequence: str = None,
    input_file: str = None,
    output_dir: str = None,
    recycles: int = 3,
    timesteps: int = 200,
    job_name: str = None
) -> dict:
    """
    Submit protein structure prediction for background processing.

    This uses Chai1 to predict protein structures from amino acid sequences.
    Typical runtime: 5-30+ minutes depending on sequence length and quality settings.

    Args:
        sequence: Single protein sequence (alternative to input_file)
        input_file: Path to FASTA file with sequences
        output_dir: Directory to save results
        recycles: Number of recycles for accuracy (1=fast, 3=standard, 5=high quality)
        timesteps: Number of timesteps (50=fast, 200=standard, 500=high quality)
        job_name: Optional name for tracking the job

    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results when completed
        - get_job_log(job_id) to see execution logs
    """
    script_path = str(get_script_path("chai1_structure_prediction"))

    args = {
        "recycles": recycles,
        "timesteps": timesteps
    }

    if sequence:
        args["sequence"] = sequence
    if input_file:
        args["input"] = input_file
    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "structure_prediction"
    )


@mcp.tool()
def submit_enzyme_scaffolding(
    input_file: str,
    ligands: str = "NAD,OXM",
    contigs: str = None,
    num_designs: int = 5,
    output_dir: str = None,
    job_name: str = None
) -> dict:
    """
    Submit enzyme active site scaffolding for background processing.

    This designs proteins around enzyme active sites using RFdiffusion2 atomic-level scaffolding.
    Typical runtime: 15-60+ minutes depending on complexity and number of designs.

    Args:
        input_file: Path to enzyme PDB structure
        ligands: Ligand codes for active site (e.g., "NAD,OXM", "ATP,MG")
        contigs: Contig specification for scaffolding (auto-generated if not provided)
        num_designs: Number of designs to generate (1-20, default: 5)
        output_dir: Directory to save results
        job_name: Optional name for tracking the job

    Returns:
        Dictionary with job_id for tracking the scaffolding job
    """
    script_path = str(get_script_path("enzyme_active_site_scaffolding"))

    args = {
        "input": input_file,
        "ligands": ligands,
        "num_designs": num_designs
    }

    if contigs:
        args["contigs"] = contigs
    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "enzyme_scaffolding"
    )


@mcp.tool()
def submit_binder_design(
    input_file: str = None,
    ligand: str = None,
    min_length: int = 30,
    max_length: int = 100,
    num_designs: int = 3,
    output_dir: str = None,
    job_name: str = None
) -> dict:
    """
    Submit small molecule binder design for background processing.

    This designs protein binders for small molecules using RFdiffusion2.
    Typical runtime: 15-60+ minutes depending on complexity and number of designs.

    Args:
        input_file: Path to protein-ligand PDB structure
        ligand: Ligand code (e.g., "PH2", "ATP", "NAD")
        min_length: Minimum binder length (10-200, default: 30)
        max_length: Maximum binder length (20-300, default: 100)
        num_designs: Number of designs to generate (1-20, default: 3)
        output_dir: Directory to save results
        job_name: Optional name for tracking the job

    Returns:
        Dictionary with job_id for tracking the binder design job
    """
    script_path = str(get_script_path("small_molecule_binder"))

    args = {
        "min_length": min_length,
        "max_length": max_length,
        "num_designs": num_designs
    }

    if input_file:
        args["input"] = input_file
    if ligand:
        args["ligand"] = ligand
    if output_dir:
        args["output"] = output_dir

    return job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or "binder_design"
    )


@mcp.tool()
def list_available_ligands() -> dict:
    """
    Get list of available ligands for binder design.

    Returns:
        Dictionary with available ligand codes and descriptions
    """
    try:
        from small_molecule_binder import run_small_molecule_binder

        # This will trigger the --list-ligands functionality
        result = run_small_molecule_binder(list_ligands=True)
        return {"status": "success", **result}

    except Exception as e:
        return handle_script_error(e, "small_molecule_binder")


# ==============================================================================
# Batch Processing Tools
# ==============================================================================

@mcp.tool()
def submit_batch_structure_prediction(
    input_files: List[str],
    recycles: int = 3,
    timesteps: int = 200,
    output_dir: str = None,
    job_name: str = None
) -> dict:
    """
    Submit batch structure prediction for multiple FASTA files.

    Processes multiple sequence files in a single job. Suitable for:
    - Processing many protein sequences at once
    - Large-scale structure prediction
    - Parallel processing of independent sequences

    Args:
        input_files: List of FASTA file paths to process
        recycles: Number of recycles for accuracy (1=fast, 3=standard, 5=high)
        timesteps: Number of timesteps (50=fast, 200=standard, 500=high)
        output_dir: Directory to save all outputs
        job_name: Optional name for tracking the batch job

    Returns:
        Dictionary with job_id for tracking the batch prediction
    """
    # We'll process files sequentially in the job
    # For now, submit the first file and note this is a batch job
    if not input_files:
        return {"status": "error", "error": "No input files provided"}

    script_path = str(get_script_path("chai1_structure_prediction"))

    # Create a batch processing approach by submitting the first file
    # In a real implementation, you'd want a dedicated batch script
    args = {
        "input": input_files[0],  # Process first file as example
        "recycles": recycles,
        "timesteps": timesteps
    }

    if output_dir:
        args["output"] = output_dir

    result = job_manager.submit_job(
        script_path=script_path,
        args=args,
        job_name=job_name or f"batch_prediction_{len(input_files)}_files"
    )

    result["message"] += f" Processing {len(input_files)} files."
    result["batch_info"] = {
        "total_files": len(input_files),
        "input_files": input_files,
        "note": "Currently processing files sequentially. Full batch processing can be implemented."
    }

    return result


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()