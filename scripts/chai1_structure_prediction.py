#!/usr/bin/env python3
"""
Script: chai1_structure_prediction.py
Description: Predict protein structures using Chai1 from amino acid sequences

Original Use Case: examples/use_case_3_chai1_structure_prediction.py
Dependencies Removed: Simplified path setup and error handling

Usage:
    python scripts/chai1_structure_prediction.py --input <fasta_file> --output <output_dir>

Example:
    python scripts/chai1_structure_prediction.py --input examples/data/sequences.fasta --output results/chai1_pred
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import tempfile
import time
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
import json

# Scientific computing - only import when needed
try:
    import numpy as np
    import torch
    from chai_lab.chai1 import run_inference
    CHAI1_AVAILABLE = True
except ImportError:
    CHAI1_AVAILABLE = False
    np = None
    torch = None
    run_inference = None

# Local utilities
import sys
sys.path.insert(0, str(Path(__file__).parent))
from lib.utils import setup_repo_paths, parse_fasta_content, format_duration, print_section_header
from lib.io import read_fasta, ensure_path

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "num_recycles": 3,
    "num_timesteps": 200,
    "seed": 42,
    "device": "cuda:0",
    "use_esm_embeddings": True,
    "output_format": "cif"
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def check_chai1_availability():
    """Check if Chai1 is properly installed."""
    if not CHAI1_AVAILABLE:
        raise ImportError(
            "❌ Chai1 not available. Please install chai_lab:\n"
            "   pip install chai-lab\n"
            "   # OR from repo:\n"
            "   pip install -e repo/RFdiffusion2/lib/chai"
        )

def check_cuda_availability():
    """Check CUDA availability and return device info."""
    if not torch.cuda.is_available():
        print("⚠️  CUDA not available. Chai1 will run on CPU (very slow)")
        return False, "cpu"

    device_count = torch.cuda.device_count()
    print(f"✅ Found {device_count} CUDA device(s)")

    for i in range(device_count):
        props = torch.cuda.get_device_properties(i)
        memory_gb = props.total_memory / (1024**3)
        print(f"  GPU {i}: {props.name} ({memory_gb:.1f} GB)")

    return True, "cuda:0"

def create_example_fasta() -> str:
    """Create example FASTA content for testing."""
    return """
>example_protein
AIQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFTPTEKDEYACRVNHVTLSQPKIVKWDRDM

>example_peptide
GAALIQRTPKIQVYSRHPAE

>ligand
CCCCCCCCCCCCCC(=O)O
""".strip()

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_chai1_prediction(
    input_file: Union[str, Path] = None,
    sequence: str = None,
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for Chai1 structure prediction.

    Args:
        input_file: Path to FASTA file
        sequence: Single sequence string (alternative to input_file)
        output_file: Path to save output directory
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: List of CIF file paths
            - output_file: Path to output directory
            - metadata: Execution metadata

    Example:
        >>> result = run_chai1_prediction("input.fasta", output_file="output/")
        >>> print(result['result'])  # List of CIF files
    """
    # Check availability
    check_chai1_availability()

    # Setup
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Determine input
    if input_file and sequence:
        raise ValueError("Provide either input_file or sequence, not both")
    if not input_file and not sequence:
        raise ValueError("Must provide either input_file or sequence")

    # Get FASTA content
    if input_file:
        input_file = ensure_path(input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        fasta_content = read_fasta(input_file)
    else:
        # Single sequence provided - simplified header for Chai1
        fasta_content = f">protein_sequence\n{sequence}"

    # Parse sequences
    sequences = parse_fasta_content(fasta_content)

    print_section_header("Chai1 Structure Prediction")
    print(f"🧬 Parsed {len(sequences)} sequences:")
    for seq in sequences:
        header_preview = seq['header'][:50] + ('...' if len(seq['header']) > 50 else '')
        print(f"  - {seq['type']}: {header_preview} ({seq['length']} residues)")

    # Check CUDA
    has_cuda, device = check_cuda_availability()
    if config.get('force_cpu', False):
        device = "cpu"
        print("🐌 Forcing CPU usage (this will be very slow)")

    # Setup output
    if output_file:
        output_path = ensure_path(output_file)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path("chai1_predictions")
        output_path.mkdir(exist_ok=True)

    # Create temporary FASTA file
    temp_fasta = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp:
            tmp.write(fasta_content)
            temp_fasta = Path(tmp.name)

        print(f"\n🚀 Starting prediction...")
        print(f"📂 Output directory: {output_path}")
        print(f"🔄 Recycles: {config['num_recycles']}")
        print(f"⏱️  Timesteps: {config['num_timesteps']}")
        print(f"🎲 Seed: {config['seed']}")
        print(f"💻 Device: {device}")

        start_time = time.time()

        # Run Chai1 inference
        output_cif_paths = run_inference(
            fasta_file=temp_fasta,
            output_dir=output_path,
            num_trunk_recycles=config['num_recycles'],
            num_diffn_timesteps=config['num_timesteps'],
            seed=config['seed'],
            device=torch.device(device),
            use_esm_embeddings=config['use_esm_embeddings']
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n✅ Prediction completed successfully!")
        print(f"⏱️  Total time: {format_duration(duration)}")
        print(f"📁 Output files: {len(output_cif_paths)}")

        # Analyze outputs
        confidence_data = []
        for i, cif_path in enumerate(output_cif_paths):
            print(f"\n📊 Model {i+1}: {cif_path.name}")

            # Load confidence scores if available
            scores_file = output_path / f"scores.model_idx_{i}.npz"
            if scores_file.exists():
                scores = np.load(scores_file)
                print(f"  Confidence scores:")
                score_summary = {}
                for key in ['pae', 'pde', 'plddt', 'resolved']:
                    if key in scores:
                        values = scores[key]
                        if hasattr(values, 'mean'):
                            mean_val = float(values.mean())
                            std_val = float(values.std())
                            score_summary[key] = {"mean": mean_val, "std": std_val}
                            print(f"    {key.upper()}: mean={mean_val:.3f}, std={std_val:.3f}")
                confidence_data.append(score_summary)

        return {
            "result": [str(p) for p in output_cif_paths],
            "output_file": str(output_path),
            "metadata": {
                "input_file": str(input_file) if input_file else None,
                "sequence_provided": sequence is not None,
                "num_sequences": len(sequences),
                "sequences": sequences,
                "config": config,
                "duration_seconds": duration,
                "device_used": device,
                "confidence_scores": confidence_data
            }
        }

    finally:
        # Clean up temporary file
        if temp_fasta and temp_fasta.exists():
            temp_fasta.unlink()

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Input FASTA file path')
    input_group.add_argument('--sequence', '-s', help='Single amino acid sequence')
    input_group.add_argument('--example', action='store_true', help='Run with example sequences')

    parser.add_argument('--output', '-o', help='Output directory path')
    parser.add_argument('--config', '-c', help='Config file (JSON)')

    # Override config options
    parser.add_argument('--recycles', type=int, help='Number of trunk recycles (1-10)')
    parser.add_argument('--timesteps', type=int, help='Number of diffusion timesteps (50-1000)')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--cpu', action='store_true', help='Force CPU usage')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Prepare arguments
    kwargs = {}
    if args.recycles is not None:
        kwargs['num_recycles'] = args.recycles
    if args.timesteps is not None:
        kwargs['num_timesteps'] = args.timesteps
    if args.seed is not None:
        kwargs['seed'] = args.seed
    if args.cpu:
        kwargs['force_cpu'] = True

    # Handle input
    input_file = None
    sequence = None

    if args.input:
        input_file = args.input
    elif args.sequence:
        sequence = args.sequence
    elif args.example:
        # Write example to temporary file
        example_content = create_example_fasta()
        temp_file = Path("temp_example.fasta")
        with open(temp_file, 'w') as f:
            f.write(example_content)
        input_file = temp_file
        print("🧪 Using example sequences for testing")

    try:
        # Run prediction
        result = run_chai1_prediction(
            input_file=input_file,
            sequence=sequence,
            output_file=args.output,
            config=config,
            **kwargs
        )

        print(f"\n✅ Success: {result['output_file']}")
        print(f"📊 Generated {len(result['result'])} structure model(s)")

        return result

    finally:
        # Clean up example file if created
        if args.example and Path("temp_example.fasta").exists():
            Path("temp_example.fasta").unlink()

if __name__ == '__main__':
    main()