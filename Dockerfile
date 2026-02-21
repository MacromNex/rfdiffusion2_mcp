# ==============================================================================
# RFdiffusion2 MCP Server Docker Image
# ==============================================================================
# Provides a GPU-enabled environment with:
#   - RFdiffusion2 repository + model weights (pre-downloaded)
#   - Chai-1 for structure prediction
#   - FastMCP server framework
#
# Build:  docker build -t rfdiffusion2-mcp .
# Run:    docker run --gpus all -p 8000:8000 rfdiffusion2-mcp
# ==============================================================================

FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git wget curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --------------------------------------------------------------------------
# 1. Clone RFdiffusion2 repository (with retries for network resilience)
# --------------------------------------------------------------------------
RUN mkdir -p repo && \
    for attempt in 1 2 3; do \
      echo "Clone attempt $attempt/3"; \
      git clone --depth 1 --single-branch \
        https://github.com/baker-laboratory/RFdiffusion2.git repo/RFdiffusion2 && break; \
      if [ $attempt -lt 3 ]; then \
        echo "Clone failed, waiting 5 seconds before retry..."; \
        sleep 5; \
      else \
        echo "ERROR: Failed to clone RFdiffusion2 after 3 attempts"; \
        echo "Please check internet connection or visit: https://github.com/baker-laboratory/RFdiffusion2"; \
        exit 1; \
      fi; \
    done && \
    chmod -R a+r /app/repo/

# --------------------------------------------------------------------------
# 2. Install PyTorch Geometric / graph dependencies (CUDA 12.1)
# --------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    --find-links https://data.pyg.org/whl/torch-2.4.0+cu121.html \
    pyg-lib torch-scatter torch-sparse torch-cluster torch-spline-conv

RUN pip install --no-cache-dir \
    --find-links https://data.dgl.ai/wheels/torch-2.4/cu121/repo.html \
    dgl==2.4.0

RUN pip install --no-cache-dir \
    --extra-index-url https://pypi.anaconda.org/rapidsai-wheels-nightly/simple \
    "pylibcugraphops-cu12>=24.6.0a24" || true

# --------------------------------------------------------------------------
# 3. Install RFdiffusion2 Python requirements
# --------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    hydra-core==1.3.1 \
    ml-collections==0.1.1 \
    addict==2.4.0 \
    assertpy==1.1.0 \
    biopython==1.83 \
    colorlog \
    compact-json \
    cython==3.0.0 \
    cytoolz==0.12.3 \
    deepdiff==6.3.0 \
    dm-tree==0.1.8 \
    e3nn==0.5.1 \
    einops==0.7.0 \
    fire==0.6.0 \
    GPUtil==1.4.0 \
    icecream==2.1.3 \
    mdtraj==1.10.0 \
    numba \
    omegaconf==2.3.0 \
    opt_einsum==3.3.0 \
    rdkit==2024.3.5 \
    scipy==1.13.1 \
    seaborn==0.13.2 \
    submitit \
    sympy==1.13.2 \
    tmtools \
    tqdm==4.65.0 \
    typer==0.12.5 \
    biotite \
    torchdata==0.9.0

# --------------------------------------------------------------------------
# 4. Install MCP server dependencies
# --------------------------------------------------------------------------
RUN pip install --no-cache-dir fastmcp loguru numpy pandas tqdm
RUN pip install --no-cache-dir chai-lab
RUN pip install --no-cache-dir --ignore-installed fastmcp
RUN pip install --no-cache-dir -U cryptography certifi

# --------------------------------------------------------------------------
# 5. Install RFdiffusion2 package (editable)
# --------------------------------------------------------------------------
RUN cd repo/RFdiffusion2 && pip install --no-cache-dir -e .

# --------------------------------------------------------------------------
# 6. Pre-download model weights / checkpoints into the image
#    This avoids repetitive downloading at runtime.
# --------------------------------------------------------------------------
RUN mkdir -p repo/RFdiffusion2/rf_diffusion/model_weights \
             repo/RFdiffusion2/rf_diffusion/third_party_model_weights/ligand_mpnn \
    && wget -q --show-progress \
       https://files.ipd.uw.edu/pub/rfdiffusion2/model_weights/RFD_173.pt \
       -O repo/RFdiffusion2/rf_diffusion/model_weights/RFD_173.pt \
    && wget -q --show-progress \
       https://files.ipd.uw.edu/pub/rfdiffusion2/model_weights/RFD_140.pt \
       -O repo/RFdiffusion2/rf_diffusion/model_weights/RFD_140.pt \
    && wget -q --show-progress \
       https://files.ipd.uw.edu/pub/rfdiffusion2/third_party_model_weights/ligand_mpnn/s25_r010_t300_p.pt \
       -O repo/RFdiffusion2/rf_diffusion/third_party_model_weights/ligand_mpnn/s25_r010_t300_p.pt \
    && wget -q --show-progress \
       https://files.ipd.uw.edu/pub/rfdiffusion2/third_party_model_weights/ligand_mpnn/s_300756.pt \
       -O repo/RFdiffusion2/rf_diffusion/third_party_model_weights/ligand_mpnn/s_300756.pt

# --------------------------------------------------------------------------
# 7. Create mamba wrapper for job manager compatibility
#    The job manager calls: mamba run -p /app/env python script.py ...
#    In Docker, all packages are installed globally, so we just forward
#    the command after stripping "run -p <path>".
# --------------------------------------------------------------------------
RUN printf '#!/bin/bash\n\
if [ "$1" = "run" ] && [ "$2" = "-p" ]; then\n\
    shift 3\n\
fi\n\
exec "$@"\n' > /usr/local/bin/mamba && chmod +x /usr/local/bin/mamba

# Create env directory structure for path compatibility
RUN mkdir -p env/bin && ln -s /opt/conda/bin/python env/bin/python

# --------------------------------------------------------------------------
# 8. Copy MCP server source and supporting files
# --------------------------------------------------------------------------
COPY src/ ./src/
RUN chmod -R a+r /app/src/
COPY scripts/ ./scripts/
RUN chmod -R a+r /app/scripts/
COPY configs/ ./configs/
RUN chmod -R a+r /app/configs/

RUN mkdir -p jobs tmp/inputs tmp/outputs

ENV PYTHONPATH=/app

CMD ["python", "src/server.py"]
