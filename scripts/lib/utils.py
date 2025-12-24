"""
General utilities for RFdiffusion2 MCP scripts.

These are simplified utility functions extracted from the repository code.
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


def setup_repo_paths(script_file: str) -> Dict[str, Path]:
    """Setup paths to repository components."""
    script_dir = Path(script_file).parent.absolute()
    mcp_root = script_dir.parent
    repo_root = mcp_root / "repo" / "RFdiffusion2"

    paths = {
        "script_dir": script_dir,
        "mcp_root": mcp_root,
        "repo_root": repo_root,
        "examples_data": mcp_root / "examples" / "data",
        "configs": mcp_root / "configs",
        "results": mcp_root / "results"
    }

    return paths


def add_repo_to_path(repo_root: Path) -> None:
    """Add repository to Python path for imports."""
    repo_path = str(repo_root)
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)

    # Also update PYTHONPATH environment variable
    current_path = os.environ.get('PYTHONPATH', '')
    if repo_path not in current_path:
        os.environ['PYTHONPATH'] = f"{repo_path}:{current_path}" if current_path else repo_path


def check_file_exists(file_path: Path, description: str = "file") -> bool:
    """Check if required file exists with user-friendly error message."""
    if not file_path.exists():
        print(f"❌ Missing {description}: {file_path}")
        return False
    return True


def check_required_files(files: Dict[str, Path]) -> List[str]:
    """Check multiple required files and return list of missing ones."""
    missing = []
    for description, file_path in files.items():
        if not file_path.exists():
            missing.append(f"{description}: {file_path}")
    return missing


def validate_numeric_param(value: Any, name: str, min_val: int, max_val: int) -> int:
    """Validate numeric parameter is within range."""
    try:
        val = int(value)
        if val < min_val or val > max_val:
            raise ValueError(f"{name} must be {min_val}-{max_val}, got: {val}")
        return val
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {name}: {value}")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def print_section_header(title: str, icon: str = "🔷") -> None:
    """Print a formatted section header."""
    print(f"\n{icon} {title}")
    print("=" * (len(title) + 3))


def print_step(step: str, status: str = "info") -> None:
    """Print a formatted step with appropriate icon."""
    icons = {
        "info": "ℹ️ ",
        "success": "✅",
        "warning": "⚠️ ",
        "error": "❌",
        "progress": "🔄"
    }
    icon = icons.get(status, "•")
    print(f"{icon} {step}")


def merge_configs(default_config: Dict[str, Any], user_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Merge configuration dictionaries with precedence: kwargs > user_config > default_config."""
    result = default_config.copy()

    if user_config:
        result.update(user_config)

    result.update(kwargs)
    return result


def parse_sequence_type(header: str) -> str:
    """Parse sequence type from FASTA header."""
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


def parse_fasta_content(content: str) -> List[Dict[str, Any]]:
    """Parse FASTA content and return sequences with metadata."""
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