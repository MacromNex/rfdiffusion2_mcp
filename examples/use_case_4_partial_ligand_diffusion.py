#!/usr/bin/env python3
"""
Use Case 4: Partial Ligand Diffusion

This script demonstrates partial ligand diffusion where some atoms of the ligand
are kept fixed while others are allowed to diffuse during design.

Usage:
    python use_case_4_partial_ligand_diffusion.py [--input INPUT_PDB] [--ligand LIGAND] [--output OUTPUT_PREFIX]

Example:
    python use_case_4_partial_ligand_diffusion.py --input examples/data/M0584_1ldm.pdb --ligand "NAD,OXM" --output partial_design
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
    parser = argparse.ArgumentParser(description="Partial ligand diffusion design")
    parser.add_argument("--input", "-i", default="examples/data/M0584_1ldm.pdb",
                       help="Input PDB file with ligands")
    parser.add_argument("--ligand", "-l", default="NAD,OXM",
                       help="Ligand specification")
    parser.add_argument("--output", "-o", default="examples/outputs/partial_design",
                       help="Output prefix for generated designs")
    parser.add_argument("--num_designs", "-n", type=int, default=3,
                       help="Number of designs to generate")
    parser.add_argument("--contigs", default="46,A106-106,59,A166-166,2,A169-169,23,A193-193,46",
                       help="Contig specification")

    args = parser.parse_args()

    # Setup environment
    repo_root = setup_environment()

    try:
        from hydra import compose, initialize
        from hydra.core.hydra_config import HydraConfig
        import run_inference

        print(f"🧪 Running partial ligand diffusion design...")
        print(f"   Input: {args.input}")
        print(f"   Ligands: {args.ligand}")
        print(f"   Output: {args.output}")

        # Create output directory
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Hydra configuration
        config_path = repo_root / "rf_diffusion" / "config" / "inference"
        with initialize(version_base=None, config_path=str(config_path)):

            # Configuration for partial ligand diffusion
            overrides = [
                f"inference.input_pdb={args.input}",
                f"inference.ligand='{args.ligand}'",
                f"inference.output_prefix={args.output}",
                f"inference.num_designs={args.num_designs}",
                f"contigmap.contigs=['{args.contigs}']",
                "inference.contig_as_guidepost=True",
                "inference.design_startnum=0",
                # Partial ligand specification - fix some atoms, diffuse others
                "++inference.partially_fixed_ligand=\"{NAD:[O7N,C7N,C3N,N7N,C2N,C4N,N1N,C5N,C1D],OXM:[O3,C2,C1,O2,N1]}\"",
                "contigmap.contig_atoms=\"{'A106':'NE,CD,CZ','A166':'OD1,CG','A169':'NH2,CZ','A193':'NE2,CD2,CE1'}\"",
                "diffuser.T=30",  # More timesteps for complex design
                "inference.write_trajectory=False",
                "inference.cautious=False",
                # Enable sidechain partial diffusion safety
                "inference.safety.sidechain_partial_diffusion=True",
            ]

            conf = compose(config_name="aa_tip_atoms_position_agnostic.yaml", overrides=overrides, return_hydra_config=True)
            HydraConfig.instance().set_config(conf)
            conf = compose(config_name="aa_tip_atoms_position_agnostic.yaml", overrides=overrides)

            # Run inference
            print("🚀 Starting partial ligand diffusion...")
            print("💡 Some ligand atoms are fixed while others can move during design")
            run_inference.main(conf)

            print(f"✅ Partial ligand diffusion completed!")
            print(f"   Output files: {args.output}_*.pdb")

            # List generated files
            output_files = list(Path(output_dir).glob(f"{Path(args.output).name}_*.pdb"))
            if output_files:
                print(f"   Generated {len(output_files)} design(s) with partial ligand diffusion:")
                for f in output_files:
                    print(f"     - {f}")
                print("\n💡 Analysis notes:")
                print("   - Fixed atoms maintain their original positions")
                print("   - Flexible atoms adapt to optimize protein-ligand interactions")
                print("   - This approach is useful for fragment-based drug design")
            else:
                print("   ⚠️  No output files found - check for errors above")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the conda environment is activated and dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during partial ligand diffusion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()