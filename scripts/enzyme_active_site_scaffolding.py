#!/usr/bin/env python3
"""
Script: enzyme_active_site_scaffolding.py
Description: Design proteins around enzyme active sites using RFdiffusion2

Original Use Case: examples/use_case_1_enzyme_active_site_scaffolding.py
Dependencies Removed: Inlined path setup and container checks

Usage:
    python scripts/enzyme_active_site_scaffolding.py --input <pdb_file> --output <output_dir>

Example:
    python scripts/enzyme_active_site_scaffolding.py --input examples/data/M0584_1ldm.pdb --output results/enzyme_scaffolds
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import subprocess
import time
import shutil
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json

# Local utilities
import sys
sys.path.insert(0, str(Path(__file__).parent))
from lib.utils import setup_repo_paths, check_required_files, format_duration, print_section_header, validate_numeric_param
from lib.io import ensure_path, copy_to_output, list_files

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "ligands": "NAD,OXM",
    "contigs": "46,A106-106,59,A166-166,2,A169-169,23,A193-193,46",
    "contig_atoms": "{'A106':'NE,CD,CZ','A166':'OD1,CG','A169':'NH2,CZ','A193':'NE2,CD2,CE1'}",
    "num_designs": 5,
    "use_apptainer": True,
    "inference_steps": 50,
    "noise_scale": 1.0
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def check_rfdiffusion2_setup(paths: Dict[str, Path]) -> List[str]:
    """Check if RFdiffusion2 is properly set up."""
    repo_root = paths["repo_root"]
    required_files = {
        "Apptainer container": repo_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif",
        "Pipeline script": repo_root / "rf_diffusion" / "benchmark" / "pipeline.py",
        "Run inference script": repo_root / "scripts" / "run_inference.py"
    }

    missing = check_required_files(required_files)

    # Check if apptainer/singularity is available
    try:
        subprocess.run(["apptainer", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["singularity", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("Container runtime: apptainer or singularity not found in PATH")

    return missing

def build_rfdiffusion2_command(
    input_pdb: Path,
    output_dir: Path,
    config: Dict[str, Any],
    repo_root: Path
) -> List[str]:
    """Build the RFdiffusion2 command for enzyme scaffolding."""

    if config["use_apptainer"]:
        # Use Apptainer container
        container_path = repo_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif"
        cmd = [
            "apptainer", "exec", "--nv",
            str(container_path),
            "python", "/app/scripts/run_inference.py"
        ]
    else:
        # Use local installation
        inference_script = repo_root / "scripts" / "run_inference.py"
        cmd = ["python", str(inference_script)]

    # Add scaffolding-specific arguments
    cmd.extend([
        "inference.input_pdb=" + str(input_pdb),
        "inference.output_prefix=" + str(output_dir / "scaffold"),
        "inference.num_designs=" + str(config["num_designs"]),

        # Enzyme scaffolding specific
        "diffuser.scaffolding=True",
        f"contigmap.contigs=[{config['contigs']}]",
        f"contigmap.inpaint_seq={config['contig_atoms']}",

        # Ligand specification
        f"inference.ligands={config['ligands']}",

        # Diffusion parameters
        f"diffuser.T={config['inference_steps']}",
        f"diffuser.noise_scale_ca={config['noise_scale']}"
    ])

    return cmd

def run_subprocess_with_output(cmd: List[str], cwd: Path = None) -> Dict[str, Any]:
    """Run subprocess and capture output with real-time display."""
    print(f"🔄 Running command: {' '.join(cmd[:3])}...")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": duration,
            "command": cmd
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Process timed out after 1 hour",
            "duration": 3600,
            "command": cmd
        }

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_enzyme_scaffolding(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for enzyme active site scaffolding.

    Args:
        input_file: Path to input PDB file with enzyme structure
        output_file: Path to save output directory
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: List of generated scaffold PDB files
            - output_file: Path to output directory
            - metadata: Execution metadata

    Example:
        >>> result = run_enzyme_scaffolding("enzyme.pdb", output_file="scaffolds/")
        >>> print(result['result'])  # List of scaffold PDB files
    """
    # Setup
    paths = setup_repo_paths(__file__)
    input_file = ensure_path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    if not input_file.exists():
        raise FileNotFoundError(f"Input PDB file not found: {input_file}")

    # Validate parameters
    config["num_designs"] = validate_numeric_param(config["num_designs"], "num_designs", 1, 100)
    config["inference_steps"] = validate_numeric_param(config["inference_steps"], "inference_steps", 10, 1000)

    print_section_header("Enzyme Active Site Scaffolding")
    print(f"🧬 Input PDB: {input_file}")
    print(f"🧪 Ligands: {config['ligands']}")
    print(f"🔢 Number of designs: {config['num_designs']}")
    print(f"🔗 Contigs: {config['contigs']}")

    # Check RFdiffusion2 setup
    missing = check_rfdiffusion2_setup(paths)
    if missing:
        error_msg = "❌ Missing RFdiffusion2 requirements:\n" + "\n".join(f"  - {item}" for item in missing)
        error_msg += "\n\n💡 Run setup first:\n"
        error_msg += f"  cd {paths['repo_root']}\n"
        error_msg += "  python setup.py"
        raise RuntimeError(error_msg)

    # Setup output
    if output_file:
        output_path = ensure_path(output_file)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = paths["results"] / f"enzyme_scaffolds_{int(time.time())}"
        output_path.mkdir(parents=True, exist_ok=True)

    # Build and run command
    cmd = build_rfdiffusion2_command(input_file, output_path, config, paths["repo_root"])

    print(f"\n🚀 Starting RFdiffusion2 scaffolding...")
    print(f"📂 Output directory: {output_path}")

    # Run RFdiffusion2
    result = run_subprocess_with_output(cmd, cwd=paths["repo_root"])

    print(f"\n⏱️  Total time: {format_duration(result['duration'])}")

    if not result["success"]:
        error_msg = f"❌ RFdiffusion2 failed with return code {result['returncode']}\n"
        error_msg += f"STDERR: {result['stderr']}\n"
        error_msg += f"STDOUT: {result['stdout']}"
        raise RuntimeError(error_msg)

    print("✅ RFdiffusion2 completed successfully!")

    # Collect output files
    pdb_files = list_files(output_path, "*.pdb")
    trb_files = list_files(output_path, "*.trb")  # Trajectory files

    print(f"📁 Generated files:")
    print(f"  - PDB structures: {len(pdb_files)}")
    print(f"  - Trajectory files: {len(trb_files)}")

    # Analyze outputs (basic file info)
    output_analysis = []
    for pdb_file in pdb_files:
        file_info = {
            "file": str(pdb_file),
            "name": pdb_file.name,
            "size_kb": pdb_file.stat().st_size / 1024,
            "type": "structure"
        }
        output_analysis.append(file_info)
        print(f"  📄 {pdb_file.name}: {file_info['size_kb']:.1f} KB")

    return {
        "result": [str(f) for f in pdb_files],
        "output_file": str(output_path),
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "duration_seconds": result['duration'],
            "num_structures": len(pdb_files),
            "num_trajectories": len(trb_files),
            "output_analysis": output_analysis,
            "command_executed": result['command'][:3],  # First 3 parts for security
            "stdout_preview": result['stdout'][-500:] if result['stdout'] else ""  # Last 500 chars
        }
    }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input', '-i', required=True, help='Input PDB file with enzyme structure')
    parser.add_argument('--output', '-o', help='Output directory for scaffolds')
    parser.add_argument('--config', '-c', help='Config file (JSON)')

    # Override config options
    parser.add_argument('--ligands', help='Comma-separated ligand names (default: NAD,OXM)')
    parser.add_argument('--num-designs', type=int, help='Number of designs to generate (default: 5)')
    parser.add_argument('--contigs', help='Contig specification')
    parser.add_argument('--contig-atoms', help='Atomic specification for active site')
    parser.add_argument('--steps', type=int, help='Number of inference steps (default: 50)')
    parser.add_argument('--no-container', action='store_true', help='Use local installation instead of container')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Prepare arguments
    kwargs = {}
    if args.ligands:
        kwargs['ligands'] = args.ligands
    if args.num_designs:
        kwargs['num_designs'] = args.num_designs
    if args.contigs:
        kwargs['contigs'] = args.contigs
    if args.contig_atoms:
        kwargs['contig_atoms'] = args.contig_atoms
    if args.steps:
        kwargs['inference_steps'] = args.steps
    if args.no_container:
        kwargs['use_apptainer'] = False

    # Run scaffolding
    result = run_enzyme_scaffolding(
        input_file=args.input,
        output_file=args.output,
        config=config,
        **kwargs
    )

    print(f"\n✅ Success: {result['output_file']}")
    print(f"📊 Generated {len(result['result'])} scaffold structure(s)")

    return result

if __name__ == '__main__':
    main()