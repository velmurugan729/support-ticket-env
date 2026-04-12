# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Support Ticket Envdir Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import TicketAction, TicketObservation
except (ImportError, ValueError):
    from models import TicketAction, TicketObservation


class SupportTicketEnvdirEnv(
    EnvClient[TicketAction, TicketObservation, State]
):
    """
    Client for the Support Ticket Envdir Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with SupportTicketEnvdirEnv(base_url="http://localhost:7860") as client:
        ...     result = client.reset()
        ...     print(result.observation.subject)
        ...
        ...     result = client.step(TicketAction(department="Billing", confidence=0.9, reasoning="Payment issue"))
        ...     print(result.observation.ticket_id)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = SupportTicketEnvdirEnv.from_docker_image("support_ticket_envdir-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(TicketAction(department="Technical", confidence=0.8, reasoning="Bug report"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: TicketAction) -> Dict:
        """
        Convert TicketAction to JSON payload for step message.

        Args:
            action: TicketAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "department": action.department,
            "confidence": action.confidence,
            "reasoning": action.reasoning,
        }

    def _parse_result(self, payload: Dict) -> StepResult[TicketObservation]:
        """
        Parse server response into StepResult[TicketObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with TicketObservation
        """
        obs_data = payload.get("observation", {})
        observation = TicketObservation(
            ticket_id=obs_data.get("ticket_id", ""),
            subject=obs_data.get("subject", ""),
            body=obs_data.get("body", ""),
            customer_tier=obs_data.get("customer_tier", ""),
            priority=obs_data.get("priority", ""),
            task_difficulty=obs_data.get("task_difficulty", ""),
            steps_taken=obs_data.get("steps_taken", 0),
            max_steps=obs_data.get("max_steps", 1),
            reward=obs_data.get("reward", 0.0),
            done=obs_data.get("done", False),
        )

        # Reward comes from observation to ensure it's never null
        reward = float(observation.reward) if observation.reward is not None else 0.0

        return StepResult(
            observation=observation,
            reward=reward,
            done=observation.done,
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
