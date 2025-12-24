# RFDiffusion2 MCP Examples

This directory contains standalone Python scripts demonstrating the main use cases for RFDiffusion2 protein design.

## Quick Start

1. **Activate the conda environment:**
   ```bash
   conda activate ./env
   ```

2. **Run a basic example:**
   ```bash
   python examples/use_case_1_basic_inference.py --input examples/data/1qys.pdb --num_designs 3
   ```

## Use Cases

### 1. Basic Protein Design (`use_case_1_basic_inference.py`)
**Purpose:** Simple protein design with minimal configuration
**Input:** Any PDB file
**Output:** Redesigned protein structures

```bash
python examples/use_case_1_basic_inference.py \
  --input examples/data/1qys.pdb \
  --output examples/outputs/basic_design \
  --num_designs 3
```

### 2. Enzyme Design (`use_case_2_enzyme_design.py`)
**Purpose:** Design enzymes with atomic motifs and small molecules
**Input:** PDB file with enzyme structure and ligands
**Output:** Enzyme scaffolds with optimized active sites

```bash
python examples/use_case_2_enzyme_design.py \
  --input examples/data/M0584_1ldm.pdb \
  --ligand "NAD,OXM" \
  --output examples/outputs/enzyme_design \
  --num_designs 3
```

### 3. Small Molecule Binder (`use_case_3_small_molecule_binder.py`)
**Purpose:** Design protein binders for small molecules with buried binding sites
**Input:** PDB file with small molecule
**Output:** Protein binders with optimized interfaces

```bash
python examples/use_case_3_small_molecule_binder.py \
  --input examples/data/1yzr_no_covalent_ORI_cm1.pdb \
  --ligand "PH2" \
  --output examples/outputs/binder_design \
  --num_designs 5
```

### 4. Partial Ligand Diffusion (`use_case_4_partial_ligand_diffusion.py`)
**Purpose:** Fix some ligand atoms while allowing others to move during design
**Input:** PDB file with multi-atom ligands
**Output:** Designs with optimized ligand conformations

```bash
python examples/use_case_4_partial_ligand_diffusion.py \
  --input examples/data/M0584_1ldm.pdb \
  --ligand "NAD,OXM" \
  --output examples/outputs/partial_design \
  --num_designs 3
```

### 5. Unconditional Generation (`use_case_5_unconditional_generation.py`)
**Purpose:** Generate novel protein structures without constraints
**Input:** None (length specification only)
**Output:** Novel protein folds

```bash
python examples/use_case_5_unconditional_generation.py \
  --length 100 \
  --output examples/outputs/unconditional_design \
  --num_designs 5
```

## Demo Data Files

| File | Size | Description | Use Case |
|------|------|-------------|----------|
| `1qys.pdb` | 86 KB | Basic protein structure for testing | Basic inference |
| `M0584_1ldm.pdb` | 7 KB | Enzyme with NAD/OXM ligands | Enzyme design |
| `M0024_1nzy.pdb` | 9 KB | Enzyme for motif scaffolding | Enzyme design |
| `1yzr_no_covalent_ORI_cm1.pdb` | 57 KB | Small molecule complex | Binder design |
| `ra_5an7_no_cov.pdb` | 540 KB | Retroaldolase enzyme | Enzyme design |
| `partial_T_example_mini.pdb` | 18 KB | Partial diffusion example | Partial diffusion |
| `two_chain.pdb` | 24 KB | Multi-chain protein | PPI design |

## Configuration Files

| File | Description |
|------|-------------|
| `base.yaml` | Default inference configuration with all parameters |
| `aa.yaml` | All-atom inference settings |
| `aa_tip_atoms_positioned.yaml` | Positioned atomic motif design |
| `aa_tip_atoms_position_agnostic.yaml` | Position-agnostic motif design |
| `unconditional.yaml` | Unconditional generation settings |

## Common Parameters

- `--input`: Input PDB file path
- `--output`: Output file prefix
- `--num_designs`: Number of designs to generate (default: 3-5)
- `--ligand`: Ligand specification (e.g., "NAD,OXM")
- `--length`: Target protein length
- `--contigs`: Motif region specification

## Output Files

Each script generates:
- `{output_prefix}_N.pdb`: Design N (backbone structure)
- `{output_prefix}_N-atomized-bb-True.pdb`: Design N with atomized sidechains
- Optional: trajectory and analysis files

## Tips for Analysis

1. **Visualization:** Use PyMOL to visualize designs
2. **Quality Check:** Verify secondary structure and compactness
3. **Validation:** Run AlphaFold/Chai-1 predictions on generated sequences
4. **Optimization:** Use LigandMPNN for sequence optimization
5. **Scoring:** Check binding interfaces and motif recapitulation

## Troubleshooting

- **Import errors:** Ensure conda environment is activated
- **CUDA errors:** Check GPU availability and CUDA version compatibility
- **Memory errors:** Reduce `num_designs` or use smaller input structures
- **Config errors:** Verify input file paths and parameter formats

## Performance Notes

- Basic inference: ~1-5 minutes per design
- Enzyme design: ~5-15 minutes per design
- Complex designs: ~10-30 minutes per design
- Performance depends on protein size, complexity, and GPU specs