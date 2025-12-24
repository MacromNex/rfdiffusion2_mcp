#!/usr/bin/env python3
"""
Use Case 2: Small Molecule Binder Design with RFdiffusion2

This script demonstrates how to design proteins that bind to small molecules
using RFdiffusion2 with RASA (Relative Accessible Surface Area) conditioning.

This implements the "small_molecule_binder_rasa_buried" demo which designs
proteins that bury small molecules with specific surface accessibility patterns.

Requirements:
- RFdiffusion2 repository setup with model weights
- Apptainer/Singularity for containerized execution
- Input PDB structure with small molecule
- Target molecule specification

Usage:
    python use_case_2_small_molecule_binder.py --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb --ligand PH2
    python use_case_2_small_molecule_binder.py --help
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

def setup_paths():
    """Setup required paths for RFdiffusion2"""
    script_dir = Path(__file__).parent.absolute()
    rfd2_root = script_dir.parent / "repo" / "RFdiffusion2"

    # Add RFdiffusion2 to PYTHONPATH
    rf_path = str(rfd2_root)
    current_path = os.environ.get('PYTHONPATH', '')
    if rf_path not in current_path:
        os.environ['PYTHONPATH'] = f"{rf_path}:{current_path}" if current_path else rf_path

    return rfd2_root

def check_requirements(rfd2_root):
    """Check if required files and containers exist"""
    required_files = [
        rfd2_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif",
        rfd2_root / "rf_diffusion" / "run_inference.py"
    ]

    missing = []
    for file_path in required_files:
        if not file_path.exists():
            missing.append(str(file_path))

    if missing:
        print("❌ Missing required files:")
        for f in missing:
            print(f"  - {f}")
        print("\n💡 Run the setup.py script first:")
        print(f"  cd {rfd2_root}")
        print("  python setup.py")
        return False

    return True

def run_binder_design(
    input_pdb: str,
    ligand: str,
    output_prefix: str = "binder",
    protein_length: int = 150,
    rasa_threshold: float = 0.0,
    num_designs: int = 5,
    use_apptainer: bool = True
):
    """
    Design a small molecule binder using RFdiffusion2

    Args:
        input_pdb: Path to input PDB file with small molecule
        ligand: Ligand name/identifier in the PDB
        output_prefix: Prefix for output files
        protein_length: Length of protein to design
        rasa_threshold: RASA threshold for buried surface (0.0 = fully buried)
        num_designs: Number of designs to generate
        use_apptainer: Whether to use Apptainer container

    Returns:
        List of paths to generated PDB files
    """

    rfd2_root = setup_paths()

    if not check_requirements(rfd2_root):
        raise RuntimeError("Requirements check failed. Please setup RFdiffusion2 first.")

    # Create output directory
    output_dir = Path(output_prefix).parent
    os.makedirs(output_dir, exist_ok=True)

    # Construct the RFdiffusion2 command
    if use_apptainer:
        sif_path = rfd2_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif"
        base_cmd = f"apptainer exec --nv {sif_path}"
    else:
        base_cmd = "python"

    # Inference script path
    inference_script = rfd2_root / "rf_diffusion" / "run_inference.py"

    # Hydra override arguments for small molecule binder design
    hydra_overrides = [
        f"inference.input_pdb={input_pdb}",
        f"inference.ligand={ligand}",
        f"inference.output_prefix={output_prefix}",
        f"inference.num_designs={num_designs}",
        f"contigmap.contigs=[{protein_length}]",
        f"contigmap.length={protein_length}-{protein_length}",
        "inference.conditions.relative_sasa_v2.active=True",
        f"inference.conditions.relative_sasa_v2.rasa={rasa_threshold}",
    ]

    # Full command
    cmd = [base_cmd, str(inference_script)] + hydra_overrides
    cmd_str = " ".join(cmd)

    print(f"🚀 Starting small molecule binder design...")
    print(f"📂 Input PDB: {input_pdb}")
    print(f"🧬 Target ligand: {ligand}")
    print(f"📏 Protein length: {protein_length}")
    print(f"🎯 RASA threshold: {rasa_threshold} (lower = more buried)")
    print(f"📊 Number of designs: {num_designs}")
    print(f"📁 Output prefix: {output_prefix}")
    print(f"⚡ Command: {cmd_str}")
    print()

    # Run the command
    start_time = time.time()
    try:
        result = subprocess.run(cmd_str, shell=True, check=True,
                              capture_output=True, text=True)

        end_time = time.time()
        duration = (end_time - start_time) / 60  # minutes

        print(f"✅ Small molecule binder design completed successfully!")
        print(f"⏱️  Total time: {duration:.2f} minutes")

        # Find generated files
        output_pattern = f"{output_prefix}_*.pdb"
        pdb_files = list(Path(output_dir).glob(os.path.basename(output_pattern)))
        trb_files = list(Path(output_dir).glob(os.path.basename(output_pattern.replace('.pdb', '.trb'))))

        print(f"\n📋 Generated files:")
        print(f"  - PDB structures: {len(pdb_files)}")
        print(f"  - TRB metadata: {len(trb_files)}")

        if pdb_files:
            print(f"\n🧬 Generated binder structures:")
            for pdb_file in pdb_files:
                print(f"  - {pdb_file}")

        return [str(f) for f in pdb_files]

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running binder design:")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        raise

def analyze_binder_properties(pdb_file: str, ligand: str):
    """
    Analyze basic properties of the designed binder

    Args:
        pdb_file: Path to designed binder PDB file
        ligand: Ligand name to analyze
    """

    try:
        with open(pdb_file, 'r') as f:
            lines = f.readlines()

        protein_atoms = []
        ligand_atoms = []

        for line in lines:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                residue_name = line[17:20].strip()
                if residue_name == ligand:
                    ligand_atoms.append(line)
                else:
                    protein_atoms.append(line)

        print(f"\n📊 Analysis of {os.path.basename(pdb_file)}:")
        print(f"  - Protein atoms: {len(protein_atoms)}")
        print(f"  - Ligand atoms ({ligand}): {len(ligand_atoms)}")

        if ligand_atoms:
            print(f"  - Ligand successfully included in design ✅")
        else:
            print(f"  - Warning: No ligand atoms found ⚠️")

    except Exception as e:
        print(f"  - Analysis failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Design small molecule binders using RFdiffusion2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic binder design
  python %(prog)s --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb --ligand PH2

  # Custom protein length and multiple designs
  python %(prog)s --input my_complex.pdb --ligand ATP --length 200 --num-designs 10

  # Partially buried ligand (RASA > 0)
  python %(prog)s --input my_complex.pdb --ligand HEM --rasa 0.3 --output my_binders

Notes:
  - RASA threshold controls burial: 0.0 = fully buried, 1.0 = fully exposed
  - Shorter proteins (100-200 residues) typically work better for binder design
  - The input PDB should contain the target small molecule
  - GPU recommended for reasonable performance (10-30 minutes per design)
        """)

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input PDB file containing small molecule to bind"
    )

    parser.add_argument(
        "--ligand", "-l",
        required=True,
        help="Ligand name/identifier in the PDB file"
    )

    parser.add_argument(
        "--output", "-o",
        default="binder_designs/binder",
        help="Output prefix for generated files (default: binder_designs/binder)"
    )

    parser.add_argument(
        "--length",
        type=int,
        default=150,
        help="Length of protein to design (default: 150)"
    )

    parser.add_argument(
        "--rasa",
        type=float,
        default=0.0,
        help="RASA threshold for ligand burial (0.0=buried, 1.0=exposed, default: 0.0)"
    )

    parser.add_argument(
        "--num-designs", "-n",
        type=int,
        default=5,
        help="Number of binder designs to generate (default: 5)"
    )

    parser.add_argument(
        "--no-apptainer",
        action="store_true",
        help="Don't use Apptainer container (requires local installation)"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze generated binder structures"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check requirements without running design"
    )

    args = parser.parse_args()

    # Setup paths
    rfd2_root = setup_paths()

    # Check requirements
    if not check_requirements(rfd2_root):
        sys.exit(1)

    if args.check_only:
        print("✅ All requirements satisfied!")
        sys.exit(0)

    # Validate input
    if not os.path.exists(args.input):
        print(f"❌ Input PDB file not found: {args.input}")
        sys.exit(1)

    # Validate RASA threshold
    if not 0.0 <= args.rasa <= 1.0:
        print(f"❌ RASA threshold must be between 0.0 and 1.0, got: {args.rasa}")
        sys.exit(1)

    # Run binder design
    try:
        pdb_files = run_binder_design(
            input_pdb=args.input,
            ligand=args.ligand,
            output_prefix=args.output,
            protein_length=args.length,
            rasa_threshold=args.rasa,
            num_designs=args.num_designs,
            use_apptainer=not args.no_apptainer
        )

        print(f"\n🎉 Small molecule binder design completed!")
        print(f"📁 Generated {len(pdb_files)} binder designs")

        # Analyze designs if requested
        if args.analyze and pdb_files:
            print(f"\n🔬 Analyzing designed binders...")
            for pdb_file in pdb_files:
                analyze_binder_properties(pdb_file, args.ligand)

    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()