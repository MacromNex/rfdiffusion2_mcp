#!/usr/bin/env python3
"""
Use Case 3: Chai1 Protein Structure Prediction

This script demonstrates how to use Chai1 (included with RFdiffusion2) for
protein structure prediction from amino acid sequences. Chai1 can predict
structures for proteins, nucleic acids, ligands, and their complexes.

This is based on the Chai1 example from lib/chai/examples/predict_structure.py
but adapted for standalone use with the RFdiffusion2 environment.

Requirements:
- RFdiffusion2 repository with Chai1 dependencies
- CUDA-capable GPU (recommended)
- Input sequences in FASTA format

Usage:
    python use_case_3_chai1_structure_prediction.py --input examples/data/sequences.fasta
    python use_case_3_chai1_structure_prediction.py --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQNAAPLAASALAKKMEEAGKTGFRLRPITIVIEGPSVEYWG..."
"""

import argparse
import os
import sys
import time
from pathlib import Path
import tempfile

# Try to import required packages
try:
    import numpy as np
    import torch
    from chai_lab.chai1 import run_inference
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're using the conda environment with Chai1 installed")
    print("   Activate environment: mamba activate ./env")
    sys.exit(1)

def setup_paths():
    """Setup required paths for Chai1"""
    script_dir = Path(__file__).parent.absolute()
    rfd2_root = script_dir.parent / "repo" / "RFdiffusion2"

    # Add paths for Chai1
    chai_path = rfd2_root / "lib" / "chai"
    if chai_path.exists():
        sys.path.insert(0, str(chai_path))

    return rfd2_root, chai_path

def check_cuda_availability():
    """Check CUDA availability and GPU memory"""
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

def create_example_fasta():
    """Create an example multi-sequence FASTA file for testing"""
    example_content = """
>protein|example-long-protein|150-residues
AGSHSMRYFSTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASPRGEPRAPWVEQEGPEYWDRETQKYKRQAQTDRVSLRNLRGYYNQSEAGSHTLQWMFGCDLGPDGRLLRGYDQSAYDGKDYIALNEDLRSWTAADTAAQITQRKWEAAREAEQRRAYLEGTCVEWLRRYLENGKETLQRAEHPKTHVTHHPVSDHEATLRCWALGFYPAEITLTWQWDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPEPLTLRWEP

>protein|example-short-protein|96-residues
AIQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFTPTEKDEYACRVNHVTLSQPKIVKWDRDM

>protein|example-peptide|4-residues
GAAL

>ligand|example-fatty-acid|SMILES
CCCCCCCCCCCCCC(=O)O
""".strip()

    return example_content

def parse_fasta_content(content: str):
    """Parse FASTA content and return sequences with metadata"""
    sequences = []
    current_header = None
    current_seq = ""

    for line in content.strip().split('\n'):
        if line.startswith('>'):
            if current_header and current_seq:
                sequences.append({
                    'header': current_header,
                    'sequence': current_seq.strip(),
                    'type': parse_sequence_type(current_header),
                    'length': len(current_seq.strip())
                })
            current_header = line[1:]  # Remove '>'
            current_seq = ""
        else:
            current_seq += line.strip()

    # Add the last sequence
    if current_header and current_seq:
        sequences.append({
            'header': current_header,
            'sequence': current_seq.strip(),
            'type': parse_sequence_type(current_header),
            'length': len(current_seq.strip())
        })

    return sequences

def parse_sequence_type(header: str):
    """Parse sequence type from FASTA header"""
    header_lower = header.lower()
    if header_lower.startswith('protein|'):
        return 'protein'
    elif header_lower.startswith('ligand|'):
        return 'ligand'
    elif header_lower.startswith('rna|'):
        return 'rna'
    elif header_lower.startswith('dna|'):
        return 'dna'
    else:
        # Heuristic: if it contains only standard amino acids, assume protein
        seq_part = header.split('|')[-1] if '|' in header else header
        if all(c in 'ACDEFGHIKLMNPQRSTVWY' for c in seq_part.replace(' ', '').upper()):
            return 'protein'
        return 'unknown'

def run_chai1_prediction(
    fasta_content: str = None,
    fasta_file: str = None,
    output_dir: str = "chai1_predictions",
    num_recycles: int = 3,
    num_timesteps: int = 200,
    seed: int = 42,
    device: str = "cuda:0"
):
    """
    Run Chai1 structure prediction

    Args:
        fasta_content: FASTA content as string
        fasta_file: Path to FASTA file
        output_dir: Output directory for predictions
        num_recycles: Number of trunk recycles (more = better quality, slower)
        num_timesteps: Number of diffusion timesteps (more = better quality, slower)
        seed: Random seed for reproducibility
        device: Device to run on ('cuda:0', 'cpu')

    Returns:
        List of output CIF file paths
    """

    if fasta_content is None and fasta_file is None:
        raise ValueError("Either fasta_content or fasta_file must be provided")

    # Read FASTA content
    if fasta_file:
        with open(fasta_file, 'r') as f:
            fasta_content = f.read()

    # Parse sequences
    sequences = parse_fasta_content(fasta_content)

    print(f"🧬 Parsed {len(sequences)} sequences:")
    for seq in sequences:
        print(f"  - {seq['type']}: {seq['header'][:50]}{'...' if len(seq['header']) > 50 else ''} ({seq['length']} residues)")

    # Create temporary FASTA file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp_fasta:
        tmp_fasta.write(fasta_content)
        temp_fasta_path = Path(tmp_fasta.name)

    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        print(f"\n🚀 Starting Chai1 structure prediction...")
        print(f"📂 Output directory: {output_path}")
        print(f"🔄 Recycles: {num_recycles}")
        print(f"⏱️  Timesteps: {num_timesteps}")
        print(f"🎲 Seed: {seed}")
        print(f"💻 Device: {device}")

        start_time = time.time()

        # Run Chai1 inference
        output_cif_paths = run_inference(
            fasta_file=temp_fasta_path,
            output_dir=output_path,
            num_trunk_recycles=num_recycles,
            num_diffn_timesteps=num_timesteps,
            seed=seed,
            device=torch.device(device),
            use_esm_embeddings=True,
        )

        end_time = time.time()
        duration = (end_time - start_time) / 60  # minutes

        print(f"\n✅ Chai1 prediction completed successfully!")
        print(f"⏱️  Total time: {duration:.2f} minutes")
        print(f"📁 Output files: {len(output_cif_paths)}")

        # Analyze outputs
        for i, cif_path in enumerate(output_cif_paths):
            print(f"\n📊 Model {i+1}: {cif_path.name}")

            # Load scores if available
            scores_file = output_path / f"scores.model_idx_{i}.npz"
            if scores_file.exists():
                scores = np.load(scores_file)
                print(f"  Confidence scores:")
                for key in ['pae', 'pde', 'plddt', 'resolved']:
                    if key in scores:
                        values = scores[key]
                        if hasattr(values, 'mean'):
                            print(f"    {key.upper()}: mean={values.mean():.3f}, std={values.std():.3f}")

        return output_cif_paths

    finally:
        # Clean up temporary file
        if temp_fasta_path.exists():
            temp_fasta_path.unlink()

def main():
    parser = argparse.ArgumentParser(
        description="Predict protein structures using Chai1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Predict from FASTA file
  python %(prog)s --input my_sequences.fasta

  # Predict single protein sequence
  python %(prog)s --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ..."

  # Create and run example sequences
  python %(prog)s --example

  # Fast prediction (lower quality)
  python %(prog)s --input seqs.fasta --recycles 1 --timesteps 50

  # High quality prediction (slower)
  python %(prog)s --input seqs.fasta --recycles 5 --timesteps 500

FASTA Format:
  Chai1 supports proteins, nucleic acids, and ligands in FASTA format:

  >protein|name|description
  MKLLISGLVFGLVLALILSHQQAYEMAQ...

  >ligand|name|description-or-SMILES
  CCCCCCCCCCCCCC(=O)O

  >rna|name|description
  AUGGCUAACUCA...

Notes:
  - GPU strongly recommended (10-100x faster than CPU)
  - Memory requirements scale with sequence length
  - Typical prediction times: 1-10 minutes per 100 residues on GPU
  - Output includes CIF structure files and confidence scores
        """)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input", "-i",
        help="Input FASTA file with sequences to predict"
    )

    group.add_argument(
        "--sequence", "-s",
        help="Single amino acid sequence to predict"
    )

    group.add_argument(
        "--example",
        action="store_true",
        help="Run with example sequences (good for testing)"
    )

    parser.add_argument(
        "--output", "-o",
        default="chai1_predictions",
        help="Output directory (default: chai1_predictions)"
    )

    parser.add_argument(
        "--recycles", "-r",
        type=int,
        default=3,
        help="Number of trunk recycles (1-10, default: 3, more=better+slower)"
    )

    parser.add_argument(
        "--timesteps", "-t",
        type=int,
        default=200,
        help="Number of diffusion timesteps (50-1000, default: 200, more=better+slower)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU usage (very slow, not recommended)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check requirements and CUDA availability"
    )

    args = parser.parse_args()

    # Setup paths
    rfd2_root, chai_path = setup_paths()

    # Check CUDA
    has_cuda, device = check_cuda_availability()
    if args.cpu:
        device = "cpu"
        print("🐌 Forcing CPU usage (this will be very slow)")

    if args.check_only:
        print(f"✅ Chai1 setup looks good!")
        print(f"📁 RFdiffusion2 root: {rfd2_root}")
        print(f"📁 Chai path: {chai_path}")
        print(f"💻 Device: {device}")
        sys.exit(0)

    # Validate arguments
    if args.recycles < 1 or args.recycles > 10:
        print(f"❌ Number of recycles must be 1-10, got: {args.recycles}")
        sys.exit(1)

    if args.timesteps < 50 or args.timesteps > 1000:
        print(f"❌ Number of timesteps must be 50-1000, got: {args.timesteps}")
        sys.exit(1)

    # Prepare input
    fasta_content = None
    fasta_file = None

    if args.input:
        if not os.path.exists(args.input):
            print(f"❌ Input FASTA file not found: {args.input}")
            sys.exit(1)
        fasta_file = args.input

    elif args.sequence:
        fasta_content = f">protein|user_sequence|{len(args.sequence)}_residues\n{args.sequence}"

    elif args.example:
        fasta_content = create_example_fasta()
        print("🧪 Using example sequences for testing")

    # Run prediction
    try:
        output_cifs = run_chai1_prediction(
            fasta_content=fasta_content,
            fasta_file=fasta_file,
            output_dir=args.output,
            num_recycles=args.recycles,
            num_timesteps=args.timesteps,
            seed=args.seed,
            device=device
        )

        print(f"\n🎉 Chai1 structure prediction completed!")
        print(f"📁 Results saved to: {args.output}")
        print(f"🧬 Generated {len(output_cifs)} structure model(s)")

        print(f"\n📋 Output files:")
        for cif_path in output_cifs:
            print(f"  - {cif_path}")

        print(f"\n💡 Next steps:")
        print(f"  - View structures in PyMOL, ChimeraX, or other molecular viewer")
        print(f"  - Check confidence scores in scores.model_idx_*.npz files")
        print(f"  - Lower pLDDT regions may be less reliable")

    except Exception as e:
        print(f"❌ Chai1 prediction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()