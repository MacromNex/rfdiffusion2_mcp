"""
Shared I/O functions for RFdiffusion2 MCP scripts.

These are extracted and simplified from repo code to minimize dependencies.
"""
import json
from pathlib import Path
from typing import Union, Any, List, Dict
import tempfile
import shutil


def ensure_path(file_path: Union[str, Path]) -> Path:
    """Convert string to Path object."""
    return Path(file_path) if isinstance(file_path, str) else file_path


def load_json(file_path: Union[str, Path]) -> dict:
    """Load JSON file."""
    with open(file_path) as f:
        return json.load(f)


def save_json(data: dict, file_path: Union[str, Path]) -> None:
    """Save data to JSON file."""
    file_path = ensure_path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def read_fasta(file_path: Union[str, Path]) -> str:
    """Read FASTA file content."""
    with open(file_path, 'r') as f:
        return f.read().strip()


def write_fasta(content: str, file_path: Union[str, Path]) -> None:
    """Write FASTA content to file."""
    file_path = ensure_path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)


def create_temp_file(content: str, suffix: str = '.tmp') -> Path:
    """Create temporary file with content and return path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        return Path(tmp.name)


def copy_to_output(src: Union[str, Path], dest_dir: Union[str, Path], name: str = None) -> Path:
    """Copy file to output directory with optional rename."""
    src = ensure_path(src)
    dest_dir = ensure_path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_name = name if name else src.name
    dest_path = dest_dir / dest_name

    shutil.copy2(src, dest_path)
    return dest_path


def list_files(directory: Union[str, Path], pattern: str = '*') -> List[Path]:
    """List files in directory matching pattern."""
    directory = ensure_path(directory)
    if not directory.exists():
        return []

    return list(directory.glob(pattern))


def file_exists(file_path: Union[str, Path]) -> bool:
    """Check if file exists."""
    return ensure_path(file_path).exists()


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    path = ensure_path(file_path)
    return path.stat().st_size if path.exists() else 0