#!/usr/bin/env python3
"""
Use Case 2: Enzyme Design from Atomic Motif

This script demonstrates enzyme design by scaffolding a protein around atomic motifs
and small molecules. It uses the position-agnostic motif placement for flexible design.

Usage:
    python use_case_2_enzyme_design.py [--input INPUT_PDB] [--ligand LIGAND] [--output OUTPUT_PREFIX]

Example:
    python use_case_2_enzyme_design.py --input examples/data/M0584_1ldm.pdb --ligand "NAD,OXM" --output enzyme_design
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
    parser = argparse.ArgumentParser(description="Enzyme design from atomic motif")
    parser.add_argument("--input", "-i", default="examples/data/M0584_1ldm.pdb",
                       help="Input PDB file with enzyme structure")
    parser.add_argument("--ligand", "-l", default="NAD,OXM",
                       help="Ligand specification (comma-separated)")
    parser.add_argument("--output", "-o", default="examples/outputs/enzyme_design",
                       help="Output prefix for generated designs")
    parser.add_argument("--num_designs", "-n", type=int, default=3,
                       help="Number of designs to generate")
    parser.add_argument("--contigs", default="46,A106-106,59,A166-166,2,A169-169,23,A193-193,46",
                       help="Contig specification for motif regions")

    args = parser.parse_args()

    # Setup environment
    repo_root = setup_environment()

    try:
        from hydra import compose, initialize
        from hydra.core.hydra_config import HydraConfig
        import run_inference

        print(f"🧬 Running enzyme design inference...")
        print(f"   Input: {args.input}")
        print(f"   Ligands: {args.ligand}")
        print(f"   Output: {args.output}")
        print(f"   Contigs: {args.contigs}")

        # Create output directory
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Hydra configuration
        config_path = repo_root / "rf_diffusion" / "config" / "inference"
        with initialize(version_base=None, config_path=str(config_path)):

            # Configuration for enzyme design with position-agnostic motif placement
            overrides = [
                f"inference.input_pdb={args.input}",
                f"inference.ligand='{args.ligand}'",
                f"inference.output_prefix={args.output}",
                f"inference.num_designs={args.num_designs}",
                f"contigmap.contigs=['{args.contigs}']",
                "inference.contig_as_guidepost=True",  # Position-agnostic motif placement
                "inference.design_startnum=0",
                "diffuser.T=20",  # More timesteps for complex design
                "inference.write_trajectory=False",
                "inference.cautious=False",
                # Atomic motif specification (example for common enzyme residues)
                "contigmap.contig_atoms=\"{'A106':'NE,CD,CZ','A166':'OD1,CG','A169':'NH2,CZ','A193':'NE2,CD2,CE1'}'\"",
            ]

            conf = compose(config_name="aa_tip_atoms_position_agnostic.yaml", overrides=overrides, return_hydra_config=True)
            HydraConfig.instance().set_config(conf)
            conf = compose(config_name="aa_tip_atoms_position_agnostic.yaml", overrides=overrides)

            # Run inference
            print("🚀 Starting enzyme design...")
            run_inference.main(conf)

            print(f"✅ Enzyme design completed!")
            print(f"   Output files: {args.output}_*.pdb")

            # List generated files
            output_files = list(Path(output_dir).glob(f"{Path(args.output).name}_*.pdb"))
            if output_files:
                print(f"   Generated {len(output_files)} enzyme design(s):")
                for f in output_files:
                    print(f"     - {f}")
                print("\n💡 Tip: The designs include:")
                print("   - Green: Atomized protein motif atoms")
                print("   - Blue: Backbone protein motif atoms")
                print("   - Yellow: Backbone protein motif atoms")
                print("   - Purple: Small molecule carbons")
            else:
                print("   ⚠️  No output files found - check for errors above")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the conda environment is activated and dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during enzyme design: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()