# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Support Ticket Envdir Environment.

This module creates an HTTP server that exposes the SupportTicketEnvdirEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import TicketAction, TicketObservation
    from .support_ticket_envdir_environment import SupportTicketEnvdirEnvironment
except (ModuleNotFoundError, ImportError):
    from models import TicketAction, TicketObservation
    from server.support_ticket_envdir_environment import SupportTicketEnvdirEnvironment


# --- FastAPI Application Setup ---

# Create the standard OpenEnv app for API compatibility
app = create_app(
    SupportTicketEnvdirEnvironment,
    TicketAction,
    TicketObservation,
    env_name="support-ticket-envdir-v2",
    max_concurrent_envs=1,
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
