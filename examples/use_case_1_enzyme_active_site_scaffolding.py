#!/usr/bin/env python3
"""
Use Case 1: Enzyme Active Site Scaffolding with RFdiffusion2

This script demonstrates how to use RFdiffusion2 to design proteins around
specific enzyme active sites with atomic-level precision. This is one of the
main capabilities of RFdiffusion2.

The script implements the "active_site_unindexed_atomic" demo from open_source_demo.json
which scaffolds an enzyme active site using unindexed atomic positioning.

Requirements:
- RFdiffusion2 repository setup with model weights
- Apptainer/Singularity for containerized execution
- Input PDB structure with enzyme active site
- Ligand specification (NAD, OXM in this example)

Usage:
    python use_case_1_enzyme_active_site_scaffolding.py --input examples/data/M0584_1ldm.pdb --output designs/
    python use_case_1_enzyme_active_site_scaffolding.py --help
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
        rfd2_root / "rf_diffusion" / "benchmark" / "pipeline.py"
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

def run_enzyme_scaffolding(
    input_pdb: str,
    output_dir: str,
    ligands: str = "NAD,OXM",
    contigs: str = "46,A106-106,59,A166-166,2,A169-169,23,A193-193,46",
    contig_atoms: str = "{'A106':'NE,CD,CZ','A166':'OD1,CG','A169':'NH2,CZ','A193':'NE2,CD2,CE1'}",
    num_designs: int = 5,
    use_apptainer: bool = True
):
    """
    Run enzyme active site scaffolding using RFdiffusion2

    Args:
        input_pdb: Path to input PDB file with enzyme structure
        output_dir: Output directory for generated designs
        ligands: Comma-separated ligand names (e.g., "NAD,OXM")
        contigs: Contig specification for scaffold design
        contig_atoms: Atomic specification for active site atoms
        num_designs: Number of designs to generate
        use_apptainer: Whether to use Apptainer container (recommended)

    Returns:
        Path to output directory containing designs
    """

    rfd2_root = setup_paths()

    if not check_requirements(rfd2_root):
        raise RuntimeError("Requirements check failed. Please setup RFdiffusion2 first.")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Construct the RFdiffusion2 command
    if use_apptainer:
        sif_path = rfd2_root / "rf_diffusion" / "exec" / "bakerlab_rf_diffusion_aa.sif"
        base_cmd = f"apptainer exec --nv {sif_path}"
    else:
        base_cmd = "python"

    # Pipeline script path
    pipeline_script = rfd2_root / "rf_diffusion" / "benchmark" / "pipeline.py"

    # Hydra override arguments for enzyme scaffolding
    hydra_overrides = [
        "--config-name=open_source_demo",
        "sweep.benchmarks=active_site_unindexed_atomic",
        f"inference.input_pdb={input_pdb}",
        f"inference.ligand={ligands}",
        f"contigmap.contigs=[{contigs}]",
        "inference.contig_as_guidepost=True",
        f'contigmap.contig_atoms="{contig_atoms}"',
        f"inference.num_designs={num_designs}",
        f"outdir={output_dir}",
        "in_proc=True",  # Run locally instead of SLURM
        "stop_step=end"  # Run full pipeline including MPNN and Chai1
    ]

    # Full command
    cmd = [base_cmd, str(pipeline_script)] + hydra_overrides
    cmd_str = " ".join(cmd)

    print(f"🚀 Starting enzyme active site scaffolding...")
    print(f"📂 Input PDB: {input_pdb}")
    print(f"🧬 Ligands: {ligands}")
    print(f"📊 Number of designs: {num_designs}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⚡ Command: {cmd_str}")
    print()

    # Run the command
    start_time = time.time()
    try:
        result = subprocess.run(cmd_str, shell=True, check=True,
                              capture_output=True, text=True)

        end_time = time.time()
        duration = (end_time - start_time) / 60  # minutes

        print(f"✅ Enzyme scaffolding completed successfully!")
        print(f"⏱️  Total time: {duration:.2f} minutes")
        print(f"📁 Results saved to: {output_dir}")

        # List generated files
        output_path = Path(output_dir)
        pdb_files = list(output_path.glob("*.pdb"))
        trb_files = list(output_path.glob("*.trb"))

        print(f"\n📋 Generated files:")
        print(f"  - PDB structures: {len(pdb_files)}")
        print(f"  - TRB metadata: {len(trb_files)}")

        if pdb_files:
            print(f"\n🧬 Example structures:")
            for i, pdb_file in enumerate(pdb_files[:3]):
                print(f"  - {pdb_file.name}")
                if i >= 2 and len(pdb_files) > 3:
                    print(f"  - ... and {len(pdb_files)-3} more")
                    break

        return str(output_path)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running enzyme scaffolding:")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Generate enzyme active site scaffolds using RFdiffusion2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with demo data
  python %(prog)s --input examples/data/M0584_1ldm.pdb --output results/enzyme_scaffolds/

  # Custom ligands and scaffold size
  python %(prog)s --input my_enzyme.pdb --ligands "ATP,MG" --num-designs 10

  # Quick test (no containerization)
  python %(prog)s --input examples/data/M0584_1ldm.pdb --output test/ --no-apptainer --num-designs 1

Notes:
  - This process can take 30+ minutes for full pipeline with multiple designs
  - GPU is highly recommended for reasonable performance
  - Output includes both PDB structures and TRB metadata files
  - Use --num-designs 1 for quick testing
        """)

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input PDB file containing enzyme structure with active site"
    )

    parser.add_argument(
        "--output", "-o",
        default="enzyme_scaffolds/",
        help="Output directory for generated scaffold designs (default: enzyme_scaffolds/)"
    )

    parser.add_argument(
        "--ligands",
        default="NAD,OXM",
        help="Comma-separated ligand names to include (default: NAD,OXM)"
    )

    parser.add_argument(
        "--contigs",
        default="46,A106-106,59,A166-166,2,A169-169,23,A193-193,46",
        help="Contig specification for scaffold design"
    )

    parser.add_argument(
        "--contig-atoms",
        default="{'A106':'NE,CD,CZ','A166':'OD1,CG','A169':'NH2,CZ','A193':'NE2,CD2,CE1'}",
        help="Atomic specification for active site atoms"
    )

    parser.add_argument(
        "--num-designs", "-n",
        type=int,
        default=5,
        help="Number of scaffold designs to generate (default: 5)"
    )

    parser.add_argument(
        "--no-apptainer",
        action="store_true",
        help="Don't use Apptainer container (requires local RFdiffusion2 installation)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check requirements without running scaffolding"
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

    # Run scaffolding
    try:
        output_path = run_enzyme_scaffolding(
            input_pdb=args.input,
            output_dir=args.output,
            ligands=args.ligands,
            contigs=args.contigs,
            contig_atoms=args.contig_atoms,
            num_designs=args.num_designs,
            use_apptainer=not args.no_apptainer
        )

        print(f"\n🎉 Enzyme active site scaffolding completed!")
        print(f"📁 Results: {output_path}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()