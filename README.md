# RFdiffusion2 MCP

> Protein design and structure prediction tools using RFdiffusion2 and Chai1, available as MCP tools for Claude Code and other MCP clients.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

This MCP server provides tools for protein design and structure prediction using cutting-edge AI models. It combines RFdiffusion2 for protein design with Chai1 for structure prediction, offering both quick synchronous operations and robust asynchronous job management for long-running tasks.

### Features
- **Protein Structure Prediction**: Fast and high-quality structure prediction from sequences using Chai1
- **Enzyme Active Site Scaffolding**: Design proteins around specific enzyme active sites using RFdiffusion2
- **Small Molecule Binder Design**: Create protein binders for small molecules with surface conditioning
- **Asynchronous Job Management**: Submit, monitor, and retrieve results from long-running tasks
- **Batch Processing**: Handle multiple sequences or designs in a single job
- **Smart Dependency Management**: Graceful handling of missing dependencies with helpful suggestions

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   ├── server.py           # MCP server (12 tools)
│   ├── utils.py            # Dependency checking utilities
│   └── jobs/               # Job management system
├── scripts/
│   ├── chai1_structure_prediction.py      # Structure prediction
│   ├── enzyme_active_site_scaffolding.py  # Enzyme scaffolding
│   ├── small_molecule_binder.py           # Binder design
│   └── lib/                # Shared utilities
├── examples/
│   └── data/               # Demo data (12 sample files)
├── configs/                # Configuration files
├── jobs/                   # Job execution directory
└── repo/                   # Original RFdiffusion2 repository
```

---

## Installation

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.11+
- NVIDIA GPU (optional but recommended for performance)

### Step 1: Create Environment

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/rfdiffusion2_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.11 -y
# or: conda create -p ./env python=3.11 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env
```

### Step 2: Install Dependencies

```bash
# Install MCP dependencies (already done)
pip install fastmcp==2.14.1 loguru==0.7.3 numpy pandas tqdm

# Install optional dependencies for full functionality
pip install chai-lab  # For structure prediction tools
```

### Step 3: Verify Installation

```bash
# Test MCP server
python -c "from src.server import mcp; print(f'Found {len(mcp.list_tools())} tools')"
# Expected output: Found 12 tools

# Check dependencies
python -c "from src.utils import validate_dependencies; print(validate_dependencies())"
```

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Dependencies | Example |
|--------|-------------|--------------|---------|
| `scripts/chai1_structure_prediction.py` | Predict protein structures from sequences | chai_lab | See below |
| `scripts/enzyme_active_site_scaffolding.py` | Design proteins around enzyme active sites | RFdiffusion2 + apptainer | See below |
| `scripts/small_molecule_binder.py` | Design protein binders for small molecules | RFdiffusion2 + apptainer | See below |

### Script Examples

#### Structure Prediction (Chai1)

```bash
# Activate environment
mamba activate ./env

# From single sequence
python scripts/chai1_structure_prediction.py \
  --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ" \
  --output results/prediction1

# From FASTA file
python scripts/chai1_structure_prediction.py \
  --input examples/data/example_sequences.fasta \
  --output results/prediction2

# With example sequences (built-in)
python scripts/chai1_structure_prediction.py \
  --example \
  --output results/prediction3

# Fast prediction (lower quality, faster)
python scripts/chai1_structure_prediction.py \
  --example \
  --recycles 1 \
  --timesteps 50

# High quality prediction (slower)
python scripts/chai1_structure_prediction.py \
  --example \
  --recycles 5 \
  --timesteps 500 \
  --config configs/chai1_structure_prediction_config.json
```

**Parameters:**
- `--input, -i`: FASTA file path (optional if using --sequence or --example)
- `--sequence, -s`: Single amino acid sequence (optional)
- `--example`: Use built-in example sequences (optional)
- `--output, -o`: Output directory (default: results/)
- `--recycles, -r`: Number of recycles (1=fast, 3=standard, 5=high quality)
- `--timesteps, -t`: Diffusion timesteps (50=fast, 200=standard, 500=high)
- `--config, -c`: JSON config file (optional)

#### Enzyme Active Site Scaffolding

```bash
# Requires RFdiffusion2 setup + apptainer
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --ligands "NAD,OXM" \
  --num-designs 5 \
  --output results/enzyme_scaffolds
```

**Parameters:**
- `--input, -i`: Enzyme PDB structure (required)
- `--ligands`: Comma-separated ligand codes (default: "NAD,OXM")
- `--contigs`: Contig specification (auto-generated if not provided)
- `--num-designs, -n`: Number of designs to generate (1-20, default: 5)
- `--output, -o`: Output directory (default: results/)

#### Small Molecule Binder Design

```bash
# List available ligands
python scripts/small_molecule_binder.py --list-ligands

# Design binder
python scripts/small_molecule_binder.py \
  --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb \
  --ligand PH2 \
  --min-length 30 \
  --max-length 100 \
  --num-designs 3 \
  --output results/binder_design
```

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name RFdiffusion2
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add RFdiffusion2 -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
# Should show "✓ Connected" for RFdiffusion2
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "RFdiffusion2": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/rfdiffusion2_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/rfdiffusion2_mcp/src/server.py"]
    }
  }
}
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from RFdiffusion2?
```

#### Basic Structure Prediction
```
Use predict_structure_fast with sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ"
```

#### Structure Prediction from File
```
Use submit_structure_prediction with input_file @examples/data/example_sequences.fasta and recycles 3
```

#### Long-Running Tasks (Submit API)
```
Submit structure prediction for @examples/data/example_sequences.fasta with high quality settings
Then check the job status
```

#### Enzyme Scaffolding
```
Submit enzyme scaffolding for @examples/data/M0584_1ldm.pdb with ligands "NAD,OXM" and 5 designs
```

#### Binder Design
```
Submit binder design for @examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb with ligand "PH2"
```

#### Batch Processing
```
Submit batch structure prediction for these files:
- @examples/data/example_sequences.fasta
```

#### Job Management
```
Get job status for job_id "abc123"
Get job result for job_id "abc123"
Get job logs for job_id "abc123"
List all running jobs
Cancel job "abc123"
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/example_sequences.fasta` | Reference a FASTA file |
| `@examples/data/M0584_1ldm.pdb` | Reference a PDB structure |
| `@configs/chai1_structure_prediction_config.json` | Reference a config file |
| `@results/` | Reference output directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "RFdiffusion2": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/rfdiffusion2_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/rfdiffusion2_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available?
> Use predict_structure_fast with sequence "MKLL..."
> Submit structure prediction for examples/data/example_sequences.fasta
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `predict_structure_fast` | Fast structure prediction with reduced quality | `sequence`, `input_file`, `output_dir`, `recycles=1`, `timesteps=50` |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (> 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `submit_structure_prediction` | High-quality structure prediction | `sequence`, `input_file`, `output_dir`, `recycles=3`, `timesteps=200`, `job_name` |
| `submit_enzyme_scaffolding` | Enzyme active site scaffolding | `input_file`, `ligands="NAD,OXM"`, `contigs`, `num_designs=5`, `output_dir`, `job_name` |
| `submit_binder_design` | Small molecule binder design | `input_file`, `ligand`, `min_length=30`, `max_length=100`, `num_designs=3`, `output_dir`, `job_name` |
| `submit_batch_structure_prediction` | Batch processing of multiple files | `input_files[]`, `recycles=3`, `timesteps=200`, `output_dir`, `job_name` |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress and status |
| `get_job_result` | Get results when completed |
| `get_job_log` | View execution logs |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs with optional status filter |

### Utility Tools

| Tool | Description |
|------|-------------|
| `check_dependencies` | Check available dependencies and installation status |
| `list_available_ligands` | Get available ligands for binder design |

---

## Examples

### Example 1: Quick Structure Prediction

**Goal:** Predict protein structure from a sequence quickly

**Using Script:**
```bash
python scripts/chai1_structure_prediction.py \
  --sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ" \
  --recycles 1 \
  --timesteps 50 \
  --output results/quick_pred/
```

**Using MCP (in Claude Code):**
```
Use predict_structure_fast with sequence "MKLLISGLVFGLVLALILSHQQAYEMAQ" and timesteps 50
```

**Expected Output:**
- Predicted structure in CIF format (~1-5 minutes)
- Confidence scores (pLDDT, pAE)
- Execution metadata

### Example 2: High-Quality Structure Prediction

**Goal:** High-quality structure prediction from FASTA file

**Using Script:**
```bash
python scripts/chai1_structure_prediction.py \
  --input examples/data/example_sequences.fasta \
  --recycles 5 \
  --timesteps 500 \
  --output results/high_quality/
```

**Using MCP (in Claude Code):**
```
Submit structure prediction for @examples/data/example_sequences.fasta with recycles 5 and timesteps 500
Then monitor the job status and get results when complete
```

**Workflow:**
1. Submit job → get job_id
2. Monitor status → "running"
3. Get results → structure files + confidence data

### Example 3: Enzyme Active Site Scaffolding

**Goal:** Design proteins around enzyme active site

**Using Script:**
```bash
python scripts/enzyme_active_site_scaffolding.py \
  --input examples/data/M0584_1ldm.pdb \
  --ligands "NAD,OXM" \
  --num-designs 3 \
  --output results/enzyme_scaffolds/
```

**Using MCP (in Claude Code):**
```
Submit enzyme scaffolding for @examples/data/M0584_1ldm.pdb with ligands "NAD,OXM" and 3 designs
```

**Expected Output:**
- 3 designed protein scaffolds in PDB format
- Trajectory and design metadata
- Execution logs with scaffolding details

### Example 4: Small Molecule Binder Design

**Goal:** Design protein binders for small molecules

**Using Script:**
```bash
# First list available ligands
python scripts/small_molecule_binder.py --list-ligands

# Design binders
python scripts/small_molecule_binder.py \
  --input examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb \
  --ligand PH2 \
  --min-length 50 \
  --max-length 120 \
  --num-designs 3 \
  --output results/binder_designs/
```

**Using MCP (in Claude Code):**
```
First list available ligands, then submit binder design for @examples/data/trimmed_ec2_M0151_NO_ORI_zero_com0.pdb with ligand "PH2"
```

### Example 5: Batch Processing

**Goal:** Process multiple sequences at once

**Using Script:**
```bash
for f in examples/data/*.fasta; do
  python scripts/chai1_structure_prediction.py --input "$f" --output results/batch/
done
```

**Using MCP (in Claude Code):**
```
Submit batch structure prediction for @examples/data/example_sequences.fasta
```

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With |
|------|-------------|----------|
| `example_sequences.fasta` | Multi-sequence FASTA for structure prediction | `chai1_structure_prediction.py` |
| `M0584_1ldm.pdb` | Enzyme with NAD/OXM ligands | `enzyme_active_site_scaffolding.py` |
| `M0024_1nzy.pdb` | Additional enzyme structure | `enzyme_active_site_scaffolding.py` |
| `M0058_1cju.pdb` | Additional enzyme structure | `enzyme_active_site_scaffolding.py` |
| `M0365_1pfk.pdb` | Additional enzyme structure | `enzyme_active_site_scaffolding.py` |
| `M0552_1fgh.pdb` | Additional enzyme structure | `enzyme_active_site_scaffolding.py` |
| `trimmed_ec2_M0151_NO_ORI_zero_com0.pdb` | Small molecule complex | `small_molecule_binder.py` |
| `1qys.pdb` | General protein structure | General testing |
| `1yzr_no_covalent_ORI_cm1.pdb` | Protein structure | General testing |
| `partial_T_example_mini.pdb` | Partial structure example | General testing |
| `ra_5an7_no_cov.pdb` | Protein structure | General testing |
| `two_chain.pdb` | Multi-chain protein | General testing |

---

## Configuration Files

The `configs/` directory contains configuration templates:

| Config | Description | Key Parameters |
|--------|-------------|----------------|
| `chai1_structure_prediction_config.json` | Chai1 model settings | `num_recycles`, `num_timesteps`, `device` |
| `enzyme_active_site_scaffolding_config.json` | Enzyme scaffolding parameters | `ligands`, `contigs`, `num_designs` |
| `small_molecule_binder_config.json` | Binder design settings | `min_length`, `max_length`, `radius` |
| `default_config.json` | Default settings | Common parameters |

### Config Example

```json
{
  "model": {
    "num_recycles": 3,
    "num_timesteps": 200,
    "seed": 42
  },
  "compute": {
    "device": "cuda:0",
    "force_cpu": false
  },
  "quality_profiles": {
    "fast": {"num_recycles": 1, "num_timesteps": 50},
    "standard": {"num_recycles": 3, "num_timesteps": 200},
    "high": {"num_recycles": 5, "num_timesteps": 500}
  }
}
```

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.11 -y
mamba activate ./env
pip install fastmcp loguru numpy pandas
```

**Problem:** Import errors
```bash
# Verify installation
python -c "from src.server import mcp; print('MCP server OK')"
python -c "from src.utils import validate_dependencies; print(validate_dependencies())"
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove RFdiffusion2
claude mcp add RFdiffusion2 -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
python -c "
from src.server import mcp
tools = mcp.list_tools()
print(f'Found {len(tools)} tools: {list(tools.keys())}')
"
```

### Dependency Issues

**Problem:** chai_lab not found
```bash
# Install Chai1 dependencies
pip install chai-lab

# Or in environment
mamba run -p ./env pip install chai-lab
```

**Problem:** RFdiffusion2 tools not working
```bash
# Check dependencies
mamba run -p ./env python -c "
from src.utils import validate_dependencies
print(validate_dependencies())
"

# Expected output shows missing apptainer and/or rfdf_repo
# Full RFdiffusion2 setup required for enzyme/binder tools
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# View job metadata
cat jobs/<job_id>/metadata.json
```

**Problem:** Job failed
```bash
# View job logs
cat jobs/<job_id>/job.log

# Or use MCP tool
get_job_log with job_id "<job_id>" and tail 100
```

**Problem:** Job directory full
```bash
# Clean old jobs
rm -rf jobs/*/

# Or clean specific job
rm -rf jobs/<job_id>/
```

### Performance Issues

**Problem:** Slow predictions
```bash
# Use fast settings
python scripts/chai1_structure_prediction.py --example --recycles 1 --timesteps 50

# Check GPU availability
nvidia-smi
```

**Problem:** Out of memory
```bash
# Force CPU usage
python scripts/chai1_structure_prediction.py --example --cpu

# Or reduce batch size for large sequences
```

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Test MCP server functionality
python -c "
from src.server import mcp
from src.utils import validate_dependencies
print('Dependencies:', validate_dependencies())
print('Tools:', len(mcp.list_tools()))
"

# Test job manager
python -c "
from src.jobs.manager import job_manager
print('Jobs:', job_manager.list_jobs())
"
```

### Starting Dev Server

```bash
# Run MCP server in dev mode
mamba run -p ./env fastmcp dev src/server.py

# Test with FastMCP dev tools
# Navigate to localhost:8000 for interactive testing
```

### Integration Testing

```bash
# Test Claude Code integration
claude mcp list | grep RFdiffusion2

# Should show "✓ Connected"
```

---

## License

Based on the RFdiffusion2 project. See original repository for license details.

## Credits

Based on [RFdiffusion2](https://github.com/baker-laboratory/RFdiffusion2) from the Baker Laboratory.

## Version History

- **v1.0.0** (2025-12-19): Initial release with 12 MCP tools
  - Structure prediction (Chai1)
  - Enzyme active site scaffolding (RFdiffusion2)
  - Small molecule binder design (RFdiffusion2)
  - Comprehensive job management system
  - Batch processing support