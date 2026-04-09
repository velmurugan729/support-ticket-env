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
    from ..models import TicketAction, TicketObservation, TicketState
    from ..tasks import TaskManager
    from ..data.tickets import TICKETS
except ImportError:
    from models import TicketAction, TicketObservation, TicketState
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
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._cumulative_reward = 0.0
        self._step_rewards = []
        self._episode_done = False
        _task_manager.reset_episode()

        # Get current task and ticket
        task_name = get_current_task()
        try:
            self._current_ticket_data = get_ticket_for_task(task_name, _current_ticket_index)
            increment_ticket_index()
        except Exception:
            # Fallback ticket data if something goes wrong
            self._current_ticket_data = {
                "ticket_id": f"ERR-{uuid4().hex[:4]}",
                "subject": "System Reset Error",
                "body": "There was an error retrieving the ticket data.",
                "customer_tier": "bronze",
                "priority": "low",
                "difficulty": task_name,
                "correct_department": "General",
                "adjacent_departments": []
            }

        return self._get_current_observation(reward=0.05, done=False)

    def step(self, action_data) -> TicketObservation:  # type: ignore[override]
        """
        Execute a step in the environment by evaluating a routing decision.
        """
        # Safe parsing with fallback 
        try: 
            if isinstance(action_data, TicketAction):
                action = action_data
            elif isinstance(action_data, dict):
                action = TicketAction(**action_data)
            else:
                action = TicketAction()
        except Exception: 
            action = TicketAction()  # defaults to General 

        dept = (action.department or "").strip().lower() 

        # Empty or default department → light penalty, continue episode 
        if not dept or dept == "general": 
            reward = 0.05 
            done = False 
            # Do not increment step_count for invalid actions 
        else: 
            # Real department → call grader 
            task_name = get_current_task()
            correct_dept = self._current_ticket_data.get("correct_department", "General") 
            adjacent_depts = self._current_ticket_data.get("adjacent_departments", []) 

            if task_name == "easy_routing": 
                reward = _task_manager.grade_easy(dept, correct_dept)
            elif task_name == "medium_routing": 
                reward = _task_manager.grade_medium(dept, correct_dept, adjacent_depts) 
            else: 
                # For hard_routing, handle previous_actions
                if not hasattr(_task_manager, '_previous_actions'):
                    _task_manager._previous_actions = []
                # Use current step_count + 1 as the step number for the grader
                reward = _task_manager.grade_hard(dept, correct_dept, self._state.step_count + 1, _task_manager._previous_actions) 
                _task_manager._previous_actions.append(dept)

            reward = max(0.05, min(0.95, float(reward))) 
            
            task_config = _task_manager.get_task_config(task_name)
            max_steps = task_config.get("max_steps", 5)
            done = (reward >= 0.85) or (self._state.step_count >= max_steps) 

            # Update state 
            self._state.step_count += 1 
            self._cumulative_reward += reward 
            self._episode_done = done

        return self._get_current_observation(reward=float(reward), done=bool(done))

    def _get_current_observation(self, reward: float = 0.05, done: bool = False) -> TicketObservation:
        """Get the current observation with updated state."""
        task_name = get_current_task()
        if not self._current_ticket_data:
            self._current_ticket_data = get_ticket_for_task(task_name, _current_ticket_index)

        task_config = _task_manager.get_task_config(task_name)
        max_steps = task_config.get("max_steps", 1)

        # Ensure reward is a float and within bounds [0.05, 0.95]
        final_reward = float(max(0.05, min(0.95, reward)))

        return TicketObservation(
            ticket_id=str(self._current_ticket_data.get("ticket_id", "unknown")),
            subject=str(self._current_ticket_data.get("subject", "No Subject")),
            body=str(self._current_ticket_data.get("body", "No Body")),
            customer_tier=str(self._current_ticket_data.get("customer_tier", "bronze")),
            priority=str(self._current_ticket_data.get("priority", "low")),
            task_difficulty=str(self._current_ticket_data.get("difficulty", task_name)),
            steps_taken=int(self._state.step_count),
            max_steps=int(max_steps),
            reward=final_reward,
            done=bool(done or self._episode_done),
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
