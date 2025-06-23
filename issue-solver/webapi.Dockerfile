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

# Stage to install Git using amazonlinux:2
FROM amazonlinux:2 AS git-builder
RUN yum install -y git && \
    # Copy git binary and its dependencies to a temporary directory
    mkdir /git && \
    cp /usr/bin/git /git/ && \
    # Copy only the essential git executables needed for HTTPS
    cp /usr/libexec/git-core/git-remote-https /git/ && \
    # Copy required libraries
    for lib in $(ldd /usr/bin/git /usr/libexec/git-core/git-remote-https | grep "=>" | awk '{print $3}' | sort -u); do \
        if [ -f "$lib" ]; then cp "$lib" /git/; fi; \
    done

FROM public.ecr.aws/lambda/python:3.12

# Copy the runtime dependencies from the builder stage.
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Copy the application code.
COPY ./src/issue_solver ${LAMBDA_TASK_ROOT}/issue_solver

# Copy the Git binary and its dependencies to the Lambda task root.
COPY --from=git-builder /git/ /usr/local/git/

# Ensure the Git binary is in your PATH
ENV PATH="/usr/local/git:${PATH}"

# Create a directory with appropriate permissions for Git operations
RUN mkdir -p /tmp/repo && \
    chmod 777 /tmp/repo

    
# Set the AWS Lambda handler.
CMD ["issue_solver.webapi.lambda_handler.handler"]