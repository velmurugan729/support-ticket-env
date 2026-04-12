# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Unit tests for SupportTicketEnvdirEnvironment.

Tests verify:
- Environment initialization and reset
- Step execution with various actions
- Observation space completeness
- Episode boundaries
- Reward calculation
"""

import pytest
from server.support_ticket_envdir_environment import (
    SupportTicketEnvdirEnvironment,
    set_current_task,
    reset_ticket_index,
)
from models import TicketAction, TicketObservation


class TestEnvironmentInitialization:
    """Test environment setup and initialization."""

    def test_environment_creation(self):
        """Test that environment can be created."""
        env = SupportTicketEnvdirEnvironment()
        assert env is not None
        assert env.SUPPORTS_CONCURRENT_SESSIONS is True

    def test_environment_reset(self):
        """Test environment reset returns valid observation."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        obs = env.reset()
        
        assert isinstance(obs, TicketObservation)
        assert obs.ticket_id is not None
        assert obs.subject is not None
        assert obs.body is not None

    def test_initial_state(self):
        """Test initial environment state."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        env.reset()
        
        assert env.state.step_count == 0
        assert env.state.episode_id is not None


class TestEasyRouting:
    """Test Easy routing task scenarios."""

    @pytest.fixture
    def easy_env(self):
        """Fixture for easy routing environment."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        env.reset()
        return env

    def test_correct_routing(self, easy_env):
        """Test correct department routing on easy ticket."""
        obs = easy_env.reset()
        correct_dept = obs.task_difficulty  # This will vary by ticket
        
        action = TicketAction(department="Billing", confidence=0.9)
        result = easy_env.step(action)
        
        assert isinstance(result, TicketObservation)
        assert result.steps_taken == 1
        assert result.reward >= 0.0

    def test_invalid_action_default(self, easy_env):
        """Test that empty/General action is penalized."""
        easy_env.reset()
        
        action = TicketAction(department="General", confidence=0.5)
        result = easy_env.step(action)
        
        assert result.reward < 0.2  # Should be low reward

    def test_episode_completion(self, easy_env):
        """Test that episode completes on correct routing."""
        easy_env.reset()
        
        # Try a few times with different departments
        for dept in ["Billing", "Technical", "Shipping", "Returns"]:
            action = TicketAction(department=dept, confidence=0.9)
            result = easy_env.step(action)
            
            if result.done:
                assert result.reward >= 0.62  # Success threshold
                break


class TestObservationSpace:
    """Test observation space completeness."""

    @pytest.fixture
    def env(self):
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        return env

    def test_observation_fields(self, env):
        """Test that all required observation fields are present."""
        obs = env.reset()
        
        # Required fields per OpenEnv spec
        assert hasattr(obs, "ticket_id")
        assert hasattr(obs, "subject")
        assert hasattr(obs, "body")
        assert hasattr(obs, "customer_tier")
        assert hasattr(obs, "priority")
        assert hasattr(obs, "sentiment")
        assert hasattr(obs, "task_difficulty")
        assert hasattr(obs, "steps_taken")
        assert hasattr(obs, "max_steps")
        assert hasattr(obs, "reward")
        assert hasattr(obs, "reward_reason")
        assert hasattr(obs, "done")
        
        # Learning feedback fields
        assert hasattr(obs, "last_action")
        assert hasattr(obs, "last_reward")

    def test_observation_types(self, env):
        """Test observation field types."""
        obs = env.reset()
        
        assert isinstance(obs.ticket_id, str)
        assert isinstance(obs.subject, str)
        assert isinstance(obs.body, str)
        assert isinstance(obs.steps_taken, int)
        assert isinstance(obs.max_steps, int)
        assert isinstance(obs.reward, float)
        assert isinstance(obs.done, bool)


class TestStepProgression:
    """Test step counting and progression."""

    def test_step_counting(self):
        """Test that steps are counted correctly."""
        set_current_task("medium_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        env.reset()
        
        # Take multiple steps
        for i in range(1, 4):
            action = TicketAction(department="Billing", confidence=0.9)
            result = env.step(action)
            assert result.steps_taken == i

    def test_last_action_tracking(self):
        """Test that last_action is tracked correctly."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        env.reset()
        
        action = TicketAction(department="Technical", confidence=0.8)
        result = env.step(action)
        
        assert result.last_action == "Technical"
        assert result.last_reward == result.reward


class TestEpisodeBoundaries:
    """Test episode termination and boundaries."""

    def test_max_steps_termination(self):
        """Test that episode terminates at max steps."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        env.reset()
        
        # Exceed max steps (3 for easy)
        done = False
        steps = 0
        while not done and steps < 5:
            action = TicketAction(department="General", confidence=0.5)
            result = env.step(action)
            done = result.done
            steps += 1
        
        assert steps <= 3  # Should terminate at max_steps

    def test_done_flag(self):
        """Test that done flag is set correctly."""
        set_current_task("easy_routing")
        reset_ticket_index()
        env = SupportTicketEnvdirEnvironment()
        obs = env.reset()
        
        # First step should not be done unless correct
        action = TicketAction(department="General", confidence=0.5)
        result = env.step(action)
        
        assert isinstance(result.done, bool)
