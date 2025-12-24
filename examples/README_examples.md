# RFdiffusion2 MCP Examples

This directory contains standalone Python scripts demonstrating the main use cases for RFdiffusion2 through MCP (Model Context Protocol) tools.

## Use Cases

### 1. Enzyme Active Site Scaffolding
**Script:** `use_case_1_enzyme_active_site_scaffolding.py`

Design proteins around specific enzyme active sites with atomic-level precision.

```bash
# Basic usage
python use_case_1_enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --output enzyme_scaffolds/

# Quick test
python use_case_1_enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --num-designs 1 \
  --output test_enzyme/
```

**Features:**
- Atomic motif scaffolding
- Ligand-aware design (NAD, OXM, etc.)
- Unindexed positioning for flexible placement
- Full pipeline including MPNN sequence design and Chai1 folding

### 2. Small Molecule Binder Design
**Script:** `use_case_2_small_molecule_binder.py`

Design proteins that bind to small molecules with RASA conditioning.

```bash
# Design binder for small molecule
python use_case_2_small_molecule_binder.py \
  --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb \
  --ligand PH2 \
  --output binder_designs/

# Customize protein length and burial
python use_case_2_small_molecule_binder.py \
  --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb \
  --ligand PH2 \
  --length 200 \
  --rasa 0.3 \
  --num-designs 10
```

**Features:**
- RASA (Relative Accessible Surface Area) conditioning
- Customizable protein length
- Burial control (0.0 = fully buried, 1.0 = exposed)
- Multiple designs for diversity

### 3. Chai1 Structure Prediction
**Script:** `use_case_3_chai1_structure_prediction.py`

Predict protein structures from sequences using Chai1 (included with RFdiffusion2).

```bash
# Predict from FASTA file
python use_case_3_chai1_structure_prediction.py \
  --input examples/data/example_sequences.fasta

# Single sequence prediction
python use_case_3_chai1_structure_prediction.py \
  --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ..."

# Example sequences for testing
python use_case_3_chai1_structure_prediction.py --example

# High quality prediction
python use_case_3_chai1_structure_prediction.py \
  --input examples/data/example_sequences.fasta \
  --recycles 5 \
  --timesteps 500
```

**Features:**
- Multi-sequence FASTA support
- Proteins, nucleic acids, and ligands
- Confidence scoring (pLDDT, pAE, etc.)
- Adjustable quality/speed tradeoffs

## Demo Data

### PDB Structures

| File | Description | Use Case |
|------|-------------|----------|
| `M0584_1ldm.pdb` | Enzyme with NAD/OXM ligands | Enzyme scaffolding |
| `trimmed_ec2_M0151_NO_ORI_zero_com0.pdb` | Small molecule complex | Binder design |
| `M0024_1nzy.pdb`, `M0058_1cju.pdb`, etc. | Additional enzyme examples | Enzyme scaffolding |

### Sequence Data

| File | Description | Use Case |
|------|-------------|----------|
| `example_sequences.fasta` | Mixed proteins and ligands | Structure prediction |

## Requirements

### System Requirements
- Linux system (WSL2 on Windows)
- CUDA-capable GPU (strongly recommended)
- 16+ GB RAM
- 50+ GB disk space for models

### Software Requirements
- Apptainer/Singularity (for containerized execution)
- Conda/Mamba package manager
- Python 3.11+

### Environment Setup
All scripts assume the conda environment is activated:

```bash
# Activate the main environment
mamba activate ./env
```

## Performance Notes

### GPU Memory Requirements
- **Enzyme scaffolding:** 8-16 GB GPU memory
- **Binder design:** 4-8 GB GPU memory
- **Chai1 prediction:** 6-12 GB GPU memory (depends on sequence length)

### Runtime Estimates
- **Enzyme scaffolding:** 10-30 minutes per design (GPU)
- **Binder design:** 5-15 minutes per design (GPU)
- **Chai1 prediction:** 1-10 minutes per 100 residues (GPU)

CPU execution is 10-100x slower and not recommended for production use.

## Output Files

### Structure Files
- **`.pdb`** - Protein Data Bank format structures
- **`.cif`** - Crystallographic Information File (Chai1 output)

### Metadata Files
- **`.trb`** - RFdiffusion2 trajectory and metadata (pickle format)
- **`scores.model_idx_*.npz`** - Chai1 confidence scores (NumPy format)

## Troubleshooting

### Common Issues

1. **"Container not found"**
   ```bash
   cd repo/RFdiffusion2
   python setup.py  # Downloads containers and models
   ```

2. **"CUDA out of memory"**
   - Reduce `--num-designs`
   - Use smaller protein lengths
   - Lower Chai1 `--recycles` and `--timesteps`

3. **"Import errors"**
   ```bash
   mamba activate ./env
   pip install --force-reinstall fastmcp
   ```

4. **Very slow execution**
   - Ensure GPU is available and being used
   - Check CUDA installation
   - Consider using fewer timesteps/recycles for testing

### Getting Help

For issues specific to:
- **RFdiffusion2:** Check the original repository documentation
- **Apptainer:** Verify container installation and GPU access
- **MCP integration:** Check the MCP server logs and environment

## Example Workflows

### Quick Test Workflow
```bash
# 1. Check environment
python use_case_3_chai1_structure_prediction.py --check-only

# 2. Test structure prediction (fastest)
python use_case_3_chai1_structure_prediction.py --example

# 3. Test binder design (medium)
python use_case_2_small_molecule_binder.py \
  --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb \
  --ligand PH2 --num-designs 1

# 4. Test enzyme scaffolding (slowest)
python use_case_1_enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --num-designs 1 --check-only
```

### Production Workflow
```bash
# 1. Design multiple enzyme scaffolds
python use_case_1_enzyme_active_site_scaffolding.py \
  --input my_enzyme.pdb \
  --num-designs 20 \
  --output production_scaffolds/

# 2. Design diverse binders
python use_case_2_small_molecule_binder.py \
  --input my_complex.pdb \
  --ligand MY_LIG \
  --num-designs 50 \
  --output production_binders/

# 3. Predict structures for validation
python use_case_3_chai1_structure_prediction.py \
  --input designed_sequences.fasta \
  --recycles 5 \
  --output validation_structures/
```