# RFdiffusion2 MCP Scripts

Clean, self-contained scripts extracted from RFdiffusion2 use cases for MCP tool wrapping.

## Design Principles

1. **Minimal Dependencies**: Only essential packages imported
2. **Self-Contained**: Functions inlined where possible
3. **Configurable**: Parameters in config files, not hardcoded
4. **MCP-Ready**: Each script has a main function ready for MCP wrapping
5. **Robust Error Handling**: Clear error messages and dependency checking

## Scripts Overview

| Script | Description | Repo Dependent | Config | Test Status |
|--------|-------------|----------------|--------|-------------|
| `chai1_structure_prediction.py` | Predict protein structures from sequences | Partial (chai_lab) | ✅ | ✅ Tested |
| `enzyme_active_site_scaffolding.py` | Design proteins around enzyme active sites | Yes (RFdiffusion2) | ✅ | ✅ Tested |
| `small_molecule_binder.py` | Design protein binders for small molecules | Yes (RFdiffusion2) | ✅ | ✅ Tested |

## Dependencies Summary

### Essential Dependencies (Required for all scripts)
- `pathlib`: Path handling
- `json`: Configuration parsing
- `argparse`: Command line interfaces

### Scientific Dependencies
- `numpy`: Required by Chai1 script only
- `torch`: Required by Chai1 script only
- `chai_lab`: Required by Chai1 script only

### RFdiffusion2 Dependencies
- `apptainer`/`singularity`: Container runtime for RFdiffusion2 scripts
- Full RFdiffusion2 installation: Required for enzyme and binder design scripts

## Usage Examples

### 1. Chai1 Structure Prediction

```bash
# Activate environment
mamba activate ./env  # or: conda activate ./env

# Predict from single sequence
python scripts/chai1_structure_prediction.py --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ" --output results/pred1

# Predict from FASTA file
python scripts/chai1_structure_prediction.py --input examples/data/sequences.fasta --output results/pred2

# Run with example sequences
python scripts/chai1_structure_prediction.py --example --output results/pred3

# Use custom config
python scripts/chai1_structure_prediction.py --example --config configs/chai1_structure_prediction_config.json

# Fast prediction (lower quality)
python scripts/chai1_structure_prediction.py --example --recycles 1 --timesteps 50

# High quality prediction (slower)
python scripts/chai1_structure_prediction.py --example --recycles 5 --timesteps 500
```

### 2. Enzyme Active Site Scaffolding

```bash
# Standard scaffolding (requires RFdiffusion2 setup)
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --output results/enzyme_scaffolds \
  --num-designs 5

# Custom ligands and contigs
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/enzyme.pdb \
  --ligands "ATP,MG" \
  --contigs "20,A50-50,30" \
  --num-designs 3

# Use config file
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/enzyme.pdb \
  --config configs/enzyme_active_site_scaffolding_config.json

# Fast test run
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/enzyme.pdb \
  --num-designs 2 \
  --steps 20
```

### 3. Small Molecule Binder Design

```bash
# Design binder for specific ligand
python scripts/small_molecule_binder.py \
  --input examples/data/protein_ligand.pdb \
  --ligand PH2 \
  --output results/binder_designs

# List available ligand codes
python scripts/small_molecule_binder.py --list-ligands

# Custom binder parameters
python scripts/small_molecule_binder.py \
  --input examples/data/protein.pdb \
  --ligand ATP \
  --min-length 30 \
  --max-length 100 \
  --radius 6.0 \
  --num-designs 3

# Use config file
python scripts/small_molecule_binder.py \
  --input examples/data/protein.pdb \
  --ligand NAD \
  --config configs/small_molecule_binder_config.json
```

## Configuration Files

All scripts support JSON configuration files in the `configs/` directory:

- `configs/chai1_structure_prediction_config.json`: Chai1 parameters
- `configs/enzyme_active_site_scaffolding_config.json`: Enzyme scaffolding settings
- `configs/small_molecule_binder_config.json`: Binder design parameters
- `configs/default_config.json`: Default settings for all scripts

### Example Config Usage

```bash
# Use specific config
python scripts/chai1_structure_prediction.py --input file.fasta --config configs/chai1_structure_prediction_config.json

# Override config parameters
python scripts/chai1_structure_prediction.py --input file.fasta --config configs/chai1_structure_prediction_config.json --recycles 1
```

## Shared Library

Common functions are in `scripts/lib/`:

- `lib/io.py`: File loading/saving utilities
- `lib/utils.py`: General utilities for path setup, validation, formatting

## For MCP Wrapping (Next Step)

Each script exports a main function that can be wrapped as an MCP tool:

```python
# Example MCP wrapper
from scripts.chai1_structure_prediction import run_chai1_prediction

@mcp.tool()
def predict_protein_structure(sequence: str, output_dir: str = None) -> dict:
    """Predict protein structure from amino acid sequence using Chai1."""
    return run_chai1_prediction(sequence=sequence, output_file=output_dir)
```

## Environment Setup

The scripts require different levels of setup:

### Minimal Setup (Chai1 only)
```bash
pip install chai-lab numpy torch
```

### Full Setup (All scripts)
```bash
# Install RFdiffusion2 environment
mamba env create -f repo/RFdiffusion2/envs/cuda124_env.yml -p ./env_rfd2

# Install Chai1
mamba run -p ./env_rfd2 pip install -e repo/RFdiffusion2/lib/chai

# Download models and containers
cd repo/RFdiffusion2
mamba run -p ../../env_rfd2 python setup.py

# Install container runtime
sudo apt-get install -y apptainer
```

## Error Handling

All scripts include comprehensive error handling:

- **Dependency Checks**: Verify required files and packages exist
- **Parameter Validation**: Check ranges and formats for all parameters
- **Clear Error Messages**: Human-readable error descriptions with solutions
- **Graceful Failures**: Clean up temporary files on errors

## Debugging

### Common Issues

1. **"chai_lab not found"**: Install Chai1 dependencies
   ```bash
   pip install chai-lab
   ```

2. **"Missing RFdiffusion2 requirements"**: Run setup script
   ```bash
   cd repo/RFdiffusion2 && python setup.py
   ```

3. **"apptainer not found"**: Install container runtime
   ```bash
   sudo apt-get install apptainer
   ```

4. **CUDA errors**: Use `--cpu` flag or check GPU availability
   ```bash
   python scripts/chai1_structure_prediction.py --example --cpu
   ```

### Testing Script Functionality

Test each script's help and dependency checking:

```bash
# Test help output
python scripts/chai1_structure_prediction.py --help
python scripts/enzyme_active_site_scaffolding.py --help
python scripts/small_molecule_binder.py --help

# Test dependency checking (will show missing dependencies)
python scripts/enzyme_active_site_scaffolding.py --input examples/data/M0584_1ldm.pdb --output test

# Test config loading
python scripts/chai1_structure_prediction.py --example --config configs/chai1_structure_prediction_config.json
```

## File Structure

```
scripts/
├── lib/                              # Shared utilities
│   ├── __init__.py                   # Library initialization
│   ├── io.py                        # File I/O functions (8 functions)
│   └── utils.py                      # General utilities (12 functions)
├── chai1_structure_prediction.py     # Structure prediction script
├── enzyme_active_site_scaffolding.py # Enzyme scaffolding script
├── small_molecule_binder.py          # Binder design script
└── README.md                         # This file

configs/
├── chai1_structure_prediction_config.json
├── enzyme_active_site_scaffolding_config.json
├── small_molecule_binder_config.json
└── default_config.json
```

## Next Steps

These scripts are ready for MCP tool wrapping in Step 6. Each script:
- ✅ Has a main function that returns structured data
- ✅ Accepts input/output file parameters
- ✅ Supports configuration via JSON files
- ✅ Provides comprehensive error handling
- ✅ Is tested and functional