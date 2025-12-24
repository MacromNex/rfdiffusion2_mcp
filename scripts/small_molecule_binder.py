#!/usr/bin/env python3
"""
Script: small_molecule_binder.py
Description: Design protein binders for small molecules using RFdiffusion2

Original Use Case: examples/use_case_2_small_molecule_binder.py
Dependencies Removed: Simplified container handling and path management

Usage:
    python scripts/small_molecule_binder.py --input <pdb_file> --ligand <ligand_name> --output <output_dir>

Example:
    python scripts/small_molecule_binder.py --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb --ligand PH2 --output results/binder_design
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import subprocess
import time
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json

# Local utilities
import sys
sys.path.insert(0, str(Path(__file__).parent))
from lib.utils import setup_repo_paths, check_required_files, format_duration, print_section_header, validate_numeric_param
from lib.io import ensure_path, list_files

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "num_designs": 5,
    "hotspot_residues": "auto",  # Will be determined from input structure
    "binding_site_radius": 8.0,  # Angstroms around ligand
    "use_apptainer": True,
    "inference_steps": 50,
    "noise_scale": 1.0,
    "min_length": 50,
    "max_length": 150
}

# Common ligands and their three-letter codes
COMMON_LIGANDS = {
    "PH2": "Phthalic acid",
    "NAD": "Nicotinamide adenine dinucleotide",
    "ATP": "Adenosine triphosphate",
    "GTP": "Guanosine triphosphate",
    "FAD": "Flavin adenine dinucleotide",
    "FMN": "Flavin mononucleotide",
    "HEM": "Heme",
    "ZN": "Zinc ion",
    "MG": "Magnesium ion",
    "CA": "Calcium ion",
    "FE": "Iron ion"
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def check_rfdiffusion2_setup(paths: Dict[str, Path]) -> List[str]:
    """Check if RFdiffusion2 is properly set up for binder design."""
    repo_root = paths["repo_root"]
    required_files = {
        "Apptainer container": repo_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif",
        "Run inference script": repo_root / "scripts" / "run_inference.py"
    }

    missing = check_required_files(required_files)

    # Check container runtime
    try:
        subprocess.run(["apptainer", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["singularity", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("Container runtime: apptainer or singularity not found in PATH")

    return missing

def analyze_pdb_for_ligands(pdb_file: Path) -> Dict[str, Any]:
    """Simple PDB analysis to find ligands and potential binding sites."""
    ligands_found = []
    chain_info = {}

    try:
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith('HETATM'):
                    # Extract ligand info
                    residue_name = line[17:20].strip()
                    chain_id = line[21].strip()
                    residue_num = line[22:26].strip()

                    if residue_name not in ['HOH', 'WAT'] and len(residue_name) >= 2:  # Skip water
                        ligand_key = f"{chain_id}:{residue_name}:{residue_num}"
                        if ligand_key not in ligands_found:
                            ligands_found.append(ligand_key)

                elif line.startswith('ATOM'):
                    # Count protein chains
                    chain_id = line[21].strip()
                    if chain_id not in chain_info:
                        chain_info[chain_id] = 0
                    chain_info[chain_id] += 1

    except Exception as e:
        print(f"⚠️  Could not analyze PDB file: {e}")

    return {
        "ligands_found": ligands_found,
        "chain_info": chain_info,
        "total_ligands": len(ligands_found),
        "protein_chains": len(chain_info)
    }

def build_binder_design_command(
    input_pdb: Path,
    ligand: str,
    output_dir: Path,
    config: Dict[str, Any],
    repo_root: Path
) -> List[str]:
    """Build the RFdiffusion2 command for binder design."""

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

    # Add binder design specific arguments
    cmd.extend([
        "inference.input_pdb=" + str(input_pdb),
        "inference.output_prefix=" + str(output_dir / "binder"),
        "inference.num_designs=" + str(config["num_designs"]),

        # Binder design mode
        "diffuser.binder_design=True",
        f"inference.ligand={ligand}",

        # Hotspot and binding site
        f"inference.hotspot_res={config['hotspot_residues']}",
        f"inference.binding_radius={config['binding_site_radius']}",

        # Length constraints
        f"contigmap.length=[{config['min_length']}-{config['max_length']}]",

        # Diffusion parameters
        f"diffuser.T={config['inference_steps']}",
        f"diffuser.noise_scale_ca={config['noise_scale']}"
    ])

    return cmd

def run_subprocess_with_output(cmd: List[str], cwd: Path = None) -> Dict[str, Any]:
    """Run subprocess and capture output."""
    print(f"🔄 Running: {' '.join(cmd[:3])}...")

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
def run_small_molecule_binder(
    input_file: Union[str, Path],
    ligand: str,
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for small molecule binder design.

    Args:
        input_file: Path to input PDB file with target protein and ligand
        ligand: Three-letter code for target ligand
        output_file: Path to save output directory
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: List of generated binder PDB files
            - output_file: Path to output directory
            - metadata: Execution metadata

    Example:
        >>> result = run_small_molecule_binder("protein.pdb", "ATP", output_file="binders/")
        >>> print(result['result'])  # List of binder PDB files
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

    print_section_header("Small Molecule Binder Design")
    print(f"🧬 Input PDB: {input_file}")
    print(f"🧪 Target ligand: {ligand}")

    # Show ligand info if known
    if ligand.upper() in COMMON_LIGANDS:
        print(f"  📋 {COMMON_LIGANDS[ligand.upper()]}")

    print(f"🔢 Number of designs: {config['num_designs']}")
    print(f"📏 Length range: {config['min_length']}-{config['max_length']} residues")

    # Analyze input PDB
    print(f"\n🔍 Analyzing input structure...")
    pdb_analysis = analyze_pdb_for_ligands(input_file)
    print(f"  Found {pdb_analysis['total_ligands']} ligand(s): {', '.join(pdb_analysis['ligands_found'])}")
    print(f"  Protein chains: {pdb_analysis['protein_chains']}")

    # Check if target ligand is present
    target_found = any(ligand.upper() in lig for lig in pdb_analysis['ligands_found'])
    if not target_found:
        print(f"⚠️  Target ligand '{ligand}' not found in structure")
        print(f"  Available ligands: {', '.join(pdb_analysis['ligands_found'])}")

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
        output_path = paths["results"] / f"binder_designs_{int(time.time())}"
        output_path.mkdir(parents=True, exist_ok=True)

    # Build and run command
    cmd = build_binder_design_command(input_file, ligand, output_path, config, paths["repo_root"])

    print(f"\n🚀 Starting binder design...")
    print(f"📂 Output directory: {output_path}")

    # Run RFdiffusion2
    result = run_subprocess_with_output(cmd, cwd=paths["repo_root"])

    print(f"\n⏱️  Total time: {format_duration(result['duration'])}")

    if not result["success"]:
        error_msg = f"❌ RFdiffusion2 failed with return code {result['returncode']}\n"
        error_msg += f"STDERR: {result['stderr']}\n"
        error_msg += f"STDOUT: {result['stdout']}"
        raise RuntimeError(error_msg)

    print("✅ Binder design completed successfully!")

    # Collect output files
    pdb_files = list_files(output_path, "*.pdb")
    trb_files = list_files(output_path, "*.trb")  # Trajectory files

    print(f"📁 Generated files:")
    print(f"  - Binder structures: {len(pdb_files)}")
    print(f"  - Trajectory files: {len(trb_files)}")

    # Analyze outputs
    output_analysis = []
    for pdb_file in pdb_files:
        file_info = {
            "file": str(pdb_file),
            "name": pdb_file.name,
            "size_kb": pdb_file.stat().st_size / 1024,
            "type": "binder"
        }
        output_analysis.append(file_info)
        print(f"  📄 {pdb_file.name}: {file_info['size_kb']:.1f} KB")

    return {
        "result": [str(f) for f in pdb_files],
        "output_file": str(output_path),
        "metadata": {
            "input_file": str(input_file),
            "target_ligand": ligand,
            "config": config,
            "duration_seconds": result['duration'],
            "num_binders": len(pdb_files),
            "num_trajectories": len(trb_files),
            "pdb_analysis": pdb_analysis,
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
    parser.add_argument('--input', '-i', help='Input PDB file with target protein and ligand')
    parser.add_argument('--ligand', '-l', help='Three-letter code for target ligand')
    parser.add_argument('--output', '-o', help='Output directory for binder designs')
    parser.add_argument('--config', '-c', help='Config file (JSON)')

    # Override config options
    parser.add_argument('--num-designs', type=int, help='Number of designs to generate (default: 5)')
    parser.add_argument('--min-length', type=int, help='Minimum binder length (default: 50)')
    parser.add_argument('--max-length', type=int, help='Maximum binder length (default: 150)')
    parser.add_argument('--radius', type=float, help='Binding site radius in Angstroms (default: 8.0)')
    parser.add_argument('--steps', type=int, help='Number of inference steps (default: 50)')
    parser.add_argument('--no-container', action='store_true', help='Use local installation instead of container')

    # List available ligands
    parser.add_argument('--list-ligands', action='store_true', help='List common ligand codes and exit')

    args = parser.parse_args()

    if args.list_ligands:
        print("Common ligand three-letter codes:")
        for code, name in COMMON_LIGANDS.items():
            print(f"  {code}: {name}")
        return

    # Check required arguments when not listing ligands
    if not args.input:
        parser.error("--input/-i is required")
    if not args.ligand:
        parser.error("--ligand/-l is required")

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Prepare arguments
    kwargs = {}
    if args.num_designs:
        kwargs['num_designs'] = args.num_designs
    if args.min_length:
        kwargs['min_length'] = args.min_length
    if args.max_length:
        kwargs['max_length'] = args.max_length
    if args.radius:
        kwargs['binding_site_radius'] = args.radius
    if args.steps:
        kwargs['inference_steps'] = args.steps
    if args.no_container:
        kwargs['use_apptainer'] = False

    # Run binder design
    result = run_small_molecule_binder(
        input_file=args.input,
        ligand=args.ligand,
        output_file=args.output,
        config=config,
        **kwargs
    )

    print(f"\n✅ Success: {result['output_file']}")
    print(f"📊 Generated {len(result['result'])} binder design(s)")

    return result

if __name__ == '__main__':
    main()