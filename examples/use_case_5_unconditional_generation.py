#!/usr/bin/env python3
"""
Use Case 5: Unconditional Protein Generation

This script demonstrates unconditional protein generation where the model
generates completely new protein structures without specific constraints.

Usage:
    python use_case_5_unconditional_generation.py [--length LENGTH] [--output OUTPUT_PREFIX]

Example:
    python use_case_5_unconditional_generation.py --length 100 --output unconditional_design
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
    parser = argparse.ArgumentParser(description="Unconditional protein generation")
    parser.add_argument("--length", "-l", type=int, default=100,
                       help="Target protein length")
    parser.add_argument("--output", "-o", default="examples/outputs/unconditional_design",
                       help="Output prefix for generated designs")
    parser.add_argument("--num_designs", "-n", type=int, default=5,
                       help="Number of designs to generate")
    parser.add_argument("--min_length", type=int, default=None,
                       help="Minimum length (for length range)")

    args = parser.parse_args()

    # Setup environment
    repo_root = setup_environment()

    # Set length range
    if args.min_length:
        length_spec = f"{args.min_length}-{args.length}"
    else:
        length_spec = f"{args.length}-{args.length}"

    try:
        from hydra import compose, initialize
        from hydra.core.hydra_config import HydraConfig
        import run_inference

        print(f"🎲 Running unconditional protein generation...")
        print(f"   Target length: {length_spec}")
        print(f"   Number of designs: {args.num_designs}")
        print(f"   Output: {args.output}")

        # Create output directory
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Hydra configuration
        config_path = repo_root / "rf_diffusion" / "config" / "inference"
        with initialize(version_base=None, config_path=str(config_path)):

            # Configuration for unconditional generation
            overrides = [
                f"inference.output_prefix={args.output}",
                f"inference.num_designs={args.num_designs}",
                f"contigmap.contigs=['{args.length}']",
                f"contigmap.length={length_spec}",
                "inference.design_startnum=0",
                # Remove input constraints for unconditional generation
                "inference.input_pdb=null",
                "inference.ligand=null",
                # Generation parameters
                "diffuser.T=50",  # More timesteps for better quality
                "inference.write_trajectory=False",
                "inference.cautious=False",
                # Optional: Add some conditioning for better results
                "inference.conditions.radius_of_gyration.mean=15",
                "inference.conditions.radius_of_gyration.std=5",
            ]

            conf = compose(config_name="unconditional.yaml", overrides=overrides, return_hydra_config=True)
            HydraConfig.instance().set_config(conf)
            conf = compose(config_name="unconditional.yaml", overrides=overrides)

            # Run inference
            print("🚀 Starting unconditional generation...")
            print("💡 Generating novel protein structures without constraints")
            run_inference.main(conf)

            print(f"✅ Unconditional generation completed!")
            print(f"   Output files: {args.output}_*.pdb")

            # List generated files
            output_files = list(Path(output_dir).glob(f"{Path(args.output).name}_*.pdb"))
            if output_files:
                print(f"   Generated {len(output_files)} novel protein design(s):")
                for f in output_files:
                    print(f"     - {f}")
                print("\n💡 Analysis suggestions:")
                print("   - Check secondary structure content")
                print("   - Verify compactness (radius of gyration)")
                print("   - Run structure prediction validation with AlphaFold/Chai-1")
                print("   - Consider sequence optimization for improved stability")
            else:
                print("   ⚠️  No output files found - check for errors above")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the conda environment is activated and dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during unconditional generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()