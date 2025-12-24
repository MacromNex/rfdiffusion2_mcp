#!/usr/bin/env python3
"""
Use Case 1: Basic Protein Design Inference

This script demonstrates basic protein design using RFDiffusion2.
It uses the default configuration with minimal parameters for a quick test.

Usage:
    python use_case_1_basic_inference.py [--input INPUT_PDB] [--output OUTPUT_PREFIX] [--num_designs N]

Example:
    python use_case_1_basic_inference.py --input examples/data/1qys.pdb --output basic_design --num_designs 5
"""

import argparse
import sys
import os
from pathlib import Path

def setup_environment():
    """Setup the environment for RFDiffusion2."""
    # Add the RFDiffusion2 repo to Python path
    repo_root = Path(__file__).parent.parent / "repo" / "RFdiffusion2"
    sys.path.insert(0, str(repo_root))

    # Set required environment variables
    os.environ.setdefault("PYTHONPATH", str(repo_root))

    return repo_root

def main():
    parser = argparse.ArgumentParser(description="Basic RFDiffusion2 protein design")
    parser.add_argument("--input", "-i", default="examples/data/1qys.pdb",
                       help="Input PDB file")
    parser.add_argument("--output", "-o", default="examples/outputs/basic_design",
                       help="Output prefix for generated designs")
    parser.add_argument("--num_designs", "-n", type=int, default=3,
                       help="Number of designs to generate")
    parser.add_argument("--config", default="base",
                       help="Configuration name (without .yaml)")

    args = parser.parse_args()

    # Setup environment
    repo_root = setup_environment()

    try:
        # Import RFDiffusion2 modules after setting up environment
        from hydra import compose, initialize
        from hydra.core.hydra_config import HydraConfig
        import run_inference

        print(f"🔬 Running basic protein design inference...")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        print(f"   Number of designs: {args.num_designs}")

        # Create output directory
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Hydra configuration
        config_path = repo_root / "rf_diffusion" / "config" / "inference"
        with initialize(version_base=None, config_path=str(config_path)):

            # Compose configuration with overrides
            overrides = [
                f"inference.input_pdb={args.input}",
                f"inference.output_prefix={args.output}",
                f"inference.num_designs={args.num_designs}",
                "inference.design_startnum=0",
                "diffuser.T=10",  # Reduced timesteps for faster execution
                "inference.write_trajectory=False",  # Skip trajectory for speed
                "inference.cautious=False",  # Speed up inference
            ]

            conf = compose(config_name=f"{args.config}.yaml", overrides=overrides, return_hydra_config=True)
            HydraConfig.instance().set_config(conf)
            conf = compose(config_name=f"{args.config}.yaml", overrides=overrides)

            # Run inference
            print("🚀 Starting inference...")
            run_inference.main(conf)

            print(f"✅ Basic inference completed!")
            print(f"   Output files: {args.output}_*.pdb")

            # List generated files
            output_files = list(Path(output_dir).glob(f"{Path(args.output).name}_*.pdb"))
            if output_files:
                print(f"   Generated {len(output_files)} design(s):")
                for f in output_files:
                    print(f"     - {f}")
            else:
                print("   ⚠️  No output files found - check for errors above")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the conda environment is activated and dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()