FROM ghcr.io/astral-sh/uv:0.6.6 AS uv

# First, bundle the dependencies into the task root.
FROM public.ecr.aws/lambda/python:3.12 AS builder

# Enable bytecode compilation, to improve cold-start performance.
ENV UV_COMPILE_BYTECODE=1

# Disable installer metadata, to create a deterministic layer.
ENV UV_NO_INSTALLER_METADATA=1

# Enable copy mode to support bind mount caching.
ENV UV_LINK_MODE=copy

# Bundle the dependencies into the Lambda task root via `uv pip install --target`.
#
# Omit any local packages (`--no-emit-workspace`) and development dependencies (`--no-dev`).
# This ensures that the Docker layer cache is only invalidated when the `pyproject.toml` or `uv.lock`
# files change, but remains robust to changes in the application code.
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Stage to install Git, Node.js and Claude Code CLI using AL2023
FROM public.ecr.aws/lambda/python:3.12 AS node-builder

RUN set -eux \
 && dnf -y update \
 && dnf -y install nodejs npm git \
 && npm install -g @anthropic-ai/claude-code \
 # Discover npm paths
 && NPM_BIN="$(npm bin -g)" \
 && NPM_PREFIX="$(npm prefix -g)" \
 # Staging dirs we’ll copy out later ─
 && mkdir -p /nodejs/bin /nodejs/lib /nodejs/lib64 /git \
 # Copy executables: node, npm, claude, claude-code
 && cp -a "${NPM_BIN}/." /nodejs/bin/ \
 && cp /usr/bin/node /usr/bin/npm /nodejs/bin/ \
 # Copy global node_modules tree (CLI code)
 && cp -a "${NPM_PREFIX}/lib/node_modules" /nodejs/lib/ \
 # Node’s shared library + its own deps
 && cp /usr/lib64/libnode.so* /nodejs/lib64/ \
 && for lib in $(ldd /usr/lib64/libnode.so* | awk '/=>/ {print $3}' | sort -u); do \
        [ -f "$lib" ] && cp "$lib" /nodejs/lib64/; \
    done \
 # Copy Git binary and its dependencies (minimal Git for HTTPS interactions)
 && cp /usr/bin/git /git/ \
 && cp /usr/libexec/git-core/git-remote-https /git/ \
 && for lib in $(ldd /usr/bin/git /usr/libexec/git-core/git-remote-https | \
                awk '/=>/ {print $3}' | sort -u); do \
        [ -f "$lib" ] && cp "$lib" /git/; \
    done

###############################################################################
# 3 ▸ final runtime layer                                                     #
###############################################################################
FROM public.ecr.aws/lambda/python:3.12

# Copy the runtime dependencies from the builder stage.
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Copy the application code.
COPY ./src/issue_solver ${LAMBDA_TASK_ROOT}/issue_solver

# Node, Claude CLI, Node shared libs, Git
COPY --from=node-builder /nodejs/bin/              /usr/local/bin/
COPY --from=node-builder /nodejs/lib/node_modules  /usr/local/lib/node_modules
COPY --from=node-builder /nodejs/lib64/            /usr/lib64/
COPY --from=node-builder /git/                     /usr/local/git/

# Ensure binaries are in PATH
ENV PATH="/usr/local/bin:/usr/local/git:${PATH}" \
    NODE_PATH="/usr/local/lib/node_modules"

# Create a directory with appropriate permissions for Git operations
RUN mkdir -p /tmp/repo && chmod 777 /tmp/repo

ENV HOME=/tmp
RUN mkdir -p "$HOME"

CMD ["issue_solver.worker.lambda_handler.handler"]