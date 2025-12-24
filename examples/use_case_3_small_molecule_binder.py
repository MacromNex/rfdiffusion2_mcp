#!/usr/bin/env python3
"""
Use Case 3: Small Molecule Binder Design

This script demonstrates designing protein binders for small molecules using
RASA (Relative Accessible Surface Area) conditioning for buried binding sites.

Usage:
    python use_case_3_small_molecule_binder.py [--input INPUT_PDB] [--ligand LIGAND] [--output OUTPUT_PREFIX]

Example:
    python use_case_3_small_molecule_binder.py --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb --ligand "PH2" --output binder_design
"""

import argparse
import sys
import os
from pathlib import Path

def setup_environment():
    """Setup the environment for RFDiffusion2."""
    repo_root = Path(__file__).parent.parent / "repo" / "RFdiffusion2"
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("PYTHONPATH", str(repo_root))
    return repo_root

def main():
    parser = argparse.ArgumentParser(description="Small molecule binder design")
    parser.add_argument("--input", "-i", default="examples/data/1yzr_no_covalent_ORI_cm1.pdb",
                       help="Input PDB file with small molecule")
    parser.add_argument("--ligand", "-l", default="PH2",
                       help="Ligand specification")
    parser.add_argument("--output", "-o", default="examples/outputs/binder_design",
                       help="Output prefix for generated designs")
    parser.add_argument("--num_designs", "-n", type=int, default=5,
                       help="Number of designs to generate")
    parser.add_argument("--length", default="150",
                       help="Protein length specification")
    parser.add_argument("--rasa", type=float, default=0.0,
                       help="Relative accessible surface area (0.0 = buried)")

    args = parser.parse_args()

    # Setup environment
    repo_root = setup_environment()

    try:
        from hydra import compose, initialize
        from hydra.core.hydra_config import HydraConfig
        import run_inference

        print(f"🎯 Running small molecule binder design...")
        print(f"   Input: {args.input}")
        print(f"   Ligand: {args.ligand}")
        print(f"   Output: {args.output}")
        print(f"   Target length: {args.length}")
        print(f"   RASA conditioning: {args.rasa} (0.0 = buried, 1.0 = exposed)")

        # Create output directory
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Hydra configuration
        config_path = repo_root / "rf_diffusion" / "config" / "inference"
        with initialize(version_base=None, config_path=str(config_path)):

            # Configuration for small molecule binder design with RASA conditioning
            overrides = [
                f"inference.input_pdb={args.input}",
                f"inference.ligand={args.ligand}",
                f"inference.output_prefix={args.output}",
                f"inference.num_designs={args.num_designs}",
                f"contigmap.contigs=['{args.length}']",
                f"contigmap.length={args.length}-{args.length}",
                "inference.design_startnum=0",
                # Enable RASA conditioning for buried binding sites
                "inference.conditions.relative_sasa_v2.active=True",
                f"inference.conditions.relative_sasa_v2.rasa={args.rasa}",
                "diffuser.T=25",  # More timesteps for binder design
                "inference.write_trajectory=False",
                "inference.cautious=False",
            ]

            conf = compose(config_name="base.yaml", overrides=overrides, return_hydra_config=True)
            HydraConfig.instance().set_config(conf)
            conf = compose(config_name="base.yaml", overrides=overrides)

            # Run inference
            print("🚀 Starting binder design...")
            print("💡 This will generate proteins that bind to the specified small molecule")
            run_inference.main(conf)

            print(f"✅ Binder design completed!")
            print(f"   Output files: {args.output}_*.pdb")

            # List generated files
            output_files = list(Path(output_dir).glob(f"{Path(args.output).name}_*.pdb"))
            if output_files:
                print(f"   Generated {len(output_files)} binder design(s):")
                for f in output_files:
                    print(f"     - {f}")
                print("\n💡 Analysis tips:")
                print("   - Check binding interface quality with PyMOL")
                print("   - Verify buried surface area around the ligand")
                print("   - Consider running sequence optimization with LigandMPNN")
            else:
                print("   ⚠️  No output files found - check for errors above")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the conda environment is activated and dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during binder design: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()