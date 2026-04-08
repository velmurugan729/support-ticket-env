# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Support Ticket Envdir Environment Implementation.

A customer support ticket routing environment that tests AI agents' ability
to classify and route tickets to appropriate departments.
"""

import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import SupportTicketEnvdirAction, SupportTicketEnvdirObservation, TicketAction, TicketObservation, TicketState
    from ..tasks import TaskManager
    from ..data.tickets import TICKETS
except ImportError:
    from models import SupportTicketEnvdirAction, SupportTicketEnvdirObservation, TicketAction, TicketObservation, TicketState
    from tasks import TaskManager
    from data.tickets import TICKETS


# Global state for task and ticket selection
_current_task_name = "easy_routing"
_current_ticket_index = 0
_task_manager = TaskManager()

# Tickets filtered by difficulty
_EASY_TICKETS = [t for t in TICKETS if t["difficulty"] == "easy"]
_MEDIUM_TICKETS = [t for t in TICKETS if t["difficulty"] == "medium"]
_HARD_TICKETS = [t for t in TICKETS if t["difficulty"] == "hard"]


def set_current_task(task_name: str):
    """Set the current task for the environment."""
    global _current_task_name
    if task_name not in ["easy_routing", "medium_routing", "hard_routing"]:
        raise ValueError(f"Invalid task: {task_name}")
    _current_task_name = task_name


def get_current_task() -> str:
    """Get the current task name."""
    return _current_task_name


def reset_ticket_index():
    """Reset the ticket index to 0."""
    global _current_ticket_index
    _current_ticket_index = 0


def increment_ticket_index():
    """Increment the ticket index for the current task."""
    global _current_ticket_index
    _current_ticket_index += 1


def get_ticket_for_task(task_name: str, index: int):
    """Get a ticket for the specified task at the given index."""
    if task_name == "easy_routing":
        tickets = _EASY_TICKETS
    elif task_name == "medium_routing":
        tickets = _MEDIUM_TICKETS
    elif task_name == "hard_routing":
        tickets = _HARD_TICKETS
    else:
        raise ValueError(f"Invalid task: {task_name}")
    
    # Wrap around if index exceeds available tickets
    return tickets[index % len(tickets)]


class SupportTicketEnvdirEnvironment(Environment):
    """
    A customer support ticket routing environment.

    This environment presents tickets to agents and evaluates their routing
    decisions based on task difficulty. It supports three difficulty levels:
    - easy_routing: Obvious single-department issues
    - medium_routing: Ambiguous tickets that could fit multiple departments
    - hard_routing: Complex multi-issue tickets requiring reasoning

    The environment uses global state for task and ticket selection to ensure
    deterministic behavior across episodes.
    """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the support_ticket_envdir environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        self._current_ticket_data = None
        self._cumulative_reward = 0.0
        self._step_rewards = []
        self._episode_done = False

    def reset(self) -> TicketObservation:
        """
        Reset the environment for a new episode.

        Returns:
            TicketObservation with the current ticket information
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count += 1
        self._cumulative_reward = 0.0
        self._step_rewards = []
        self._episode_done = False
        _task_manager.reset_episode()

        # Get current task and ticket
        task_name = get_current_task()
        self._current_ticket_data = get_ticket_for_task(task_name, _current_ticket_index)
        increment_ticket_index()

        task_config = _task_manager.get_task_config(task_name)
        max_steps = task_config["max_steps"]

        return TicketObservation(
            ticket_id=self._current_ticket_data["ticket_id"],
            subject=self._current_ticket_data["subject"],
            body=self._current_ticket_data["body"],
            customer_tier=self._current_ticket_data["customer_tier"],
            priority=self._current_ticket_data["priority"],
            task_difficulty=self._current_ticket_data["difficulty"],
            steps_taken=0,
            max_steps=max_steps,
            done=False,
            reward=0.0,
        )

    def step(self, action: TicketAction) -> TicketObservation:  # type: ignore[override]
        """
        Execute a step in the environment by evaluating a routing decision.

        Args:
            action: TicketAction containing the department, confidence, and reasoning

        Returns:
            TicketObservation with updated state and reward
        """
        if self._episode_done:
            # Episode already done, return terminal observation
            return self._get_current_observation()

        self._state.step_count += 1

        # Grade the action
        task_name = get_current_task()
        grade = _task_manager.grade_action(
            task_name=task_name,
            predicted_department=action.department,
            correct_department=self._current_ticket_data["correct_department"],
            adjacent_departments=self._current_ticket_data["adjacent_departments"],
            step_count=self._state.step_count
        )

        # Update rewards
        self._cumulative_reward += grade
        self._step_rewards.append(grade)

        # Check if episode is done
        task_config = _task_manager.get_task_config(task_name)
        self._episode_done = _task_manager.is_done(
            task_name=task_name,
            step_count=self._state.step_count,
            grade=grade
        )

        return self._get_current_observation()

    def _get_current_observation(self) -> TicketObservation:
        """Get the current observation with updated state."""
        task_name = get_current_task()
        task_config = _task_manager.get_task_config(task_name)
        max_steps = task_config["max_steps"]

        return TicketObservation(
            ticket_id=self._current_ticket_data["ticket_id"],
            subject=self._current_ticket_data["subject"],
            body=self._current_ticket_data["body"],
            customer_tier=self._current_ticket_data["customer_tier"],
            priority=self._current_ticket_data["priority"],
            task_difficulty=self._current_ticket_data["difficulty"],
            steps_taken=self._state.step_count,
            max_steps=max_steps,
            done=self._episode_done,
            reward=self._cumulative_reward if self._episode_done else 0.0,
            metadata={
                "step_rewards": self._step_rewards,
                "correct_department": self._current_ticket_data["correct_department"],
                "task_name": task_name,
            },
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
