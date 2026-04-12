# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Unit tests for TaskManager grading functions.

Tests verify:
- Correct reward values for each difficulty level
- Edge cases (empty departments, repeated mistakes)
- Step-based progression for hard tasks
"""

import pytest
from tasks import TaskManager


class TestTaskManager:
    """Test suite for TaskManager grading functions."""

    @pytest.fixture
    def task_manager(self):
        """Fixture to create a fresh TaskManager instance."""
        return TaskManager()

    def test_easy_correct_routing(self, task_manager):
        """Test Easy: Correct department = 0.92 reward."""
        reward, reason, metadata = task_manager.grade_easy("Billing", "Billing")
        assert reward == 0.92
        assert "EXCELLENT" in reason
        assert metadata["accuracy_score"] == 0.92

    def test_easy_wrong_routing(self, task_manager):
        """Test Easy: Wrong department = 0.08 reward."""
        reward, reason, metadata = task_manager.grade_easy("Technical", "Billing")
        assert reward == 0.08
        assert "INCORRECT" in reason

    def test_easy_general_fallback(self, task_manager):
        """Test Easy: General/Empty = 0.08 reward."""
        reward, reason, metadata = task_manager.grade_easy("General", "Billing")
        assert reward == 0.08

    def test_medium_correct_routing(self, task_manager):
        """Test Medium: Correct department = 0.88 reward."""
        reward, reason, metadata = task_manager.grade_medium("Billing", "Billing", ["Technical", "Shipping"])
        assert reward == 0.88
        assert "PERFECT" in reason
        assert metadata["accuracy_score"] == 0.88

    def test_medium_adjacent_routing(self, task_manager):
        """Test Medium: Adjacent department = 0.52 reward."""
        reward, reason, metadata = task_manager.grade_medium("Technical", "Billing", ["Technical", "Shipping"])
        assert reward == 0.52
        assert "PARTIAL CREDIT" in reason
        assert metadata["adjacent_used"] is True

    def test_medium_wrong_routing(self, task_manager):
        """Test Medium: Wrong department = 0.09 reward."""
        reward, reason, metadata = task_manager.grade_medium("Returns", "Billing", ["Technical"])
        assert reward == 0.09
        assert "WRONG" in reason

    def test_hard_step1_correct(self, task_manager):
        """Test Hard: Step 1 correct = 0.85 reward."""
        reward, reason, metadata = task_manager.grade_hard("Billing", "Billing", 1, [], ["Technical"])
        assert reward == 0.85
        assert "EXCELLENT" in reason
        assert metadata["step_bonus"] == 0.85

    def test_hard_step2_correct(self, task_manager):
        """Test Hard: Step 2 correct = 0.68 reward."""
        reward, reason, metadata = task_manager.grade_hard("Billing", "Billing", 2, ["Technical"], ["Technical"])
        assert reward == 0.68
        assert "GOOD" in reason

    def test_hard_step3_correct(self, task_manager):
        """Test Hard: Step 3+ correct = 0.48 reward."""
        reward, reason, metadata = task_manager.grade_hard("Billing", "Billing", 3, ["Technical", "Shipping"], ["Technical"])
        assert reward == 0.48

    def test_hard_adjacent_routing(self, task_manager):
        """Test Hard: Adjacent department = 0.52 reward."""
        reward, reason, metadata = task_manager.grade_hard("Technical", "Billing", 1, [], ["Technical", "Shipping"])
        assert reward == 0.52
        assert "PARTIAL CREDIT" in reason

    def test_hard_repeated_mistake(self, task_manager):
        """Test Hard: Repeated mistake = 0.05 penalty."""
        reward, reason, metadata = task_manager.grade_hard("Technical", "Billing", 2, ["Technical"], ["Shipping"])
        assert reward == 0.05
        assert "LEARNING FAILURE" in reason
        assert metadata["repeated_mistake"] is True

    def test_is_done_max_steps(self, task_manager):
        """Test episode termination at max steps."""
        assert task_manager.is_done("easy_routing", 3, 0.5) is True
        assert task_manager.is_done("easy_routing", 2, 0.5) is False

    def test_is_done_success_threshold(self, task_manager):
        """Test episode termination at success threshold (0.62)."""
        assert task_manager.is_done("easy_routing", 1, 0.65) is True
        assert task_manager.is_done("easy_routing", 1, 0.60) is False

    def test_multi_objective_scoring(self, task_manager):
        """Test multi-objective scoring with sentiment bonus."""
        # Frustrated customer + correct routing should get bonus
        reward, reason, metadata = task_manager.grade_easy(
            "Billing", "Billing", sentiment="frustrated", confidence=0.9, step_number=1
        )
        assert reward > 0.92  # Should be 0.92 + 0.05 bonus
        assert "SENTIMENT BONUS" in reason
        
    def test_escalation_penalty(self, task_manager):
        """Test escalation penalty is applied."""
        reward, reason, metadata = task_manager.grade_easy(
            "Technical", "Billing", sentiment="frustrated", confidence=0.5, 
            step_number=1, escalation_triggered=True
        )
        assert reward < 0.08  # Should be 0.08 - 0.10 escalation penalty
        assert "ESCALATION" in reason

    def test_customer_lifetime_value_bonus(self, task_manager):
        """Test CLV bonus for high-tier customers."""
        # Platinum customer with correct routing should get +0.03 bonus
        reward, reason, metadata = task_manager.grade_easy(
            "Billing", "Billing", sentiment="neutral", confidence=0.9, 
            step_number=1, escalation_triggered=False, customer_tier="platinum"
        )
        assert reward == 0.95  # 0.92 + 0.03
        assert "CLV BONUS" in reason
        assert metadata["tier_bonus"] == 0.03
        
        # Gold customer should get +0.02
        reward, reason, metadata = task_manager.grade_easy(
            "Billing", "Billing", customer_tier="gold"
        )
        assert reward == 0.94  # 0.92 + 0.02
        assert metadata["tier_bonus"] == 0.02
        
        # Bronze customer gets no bonus
        reward, reason, metadata = task_manager.grade_easy(
            "Billing", "Billing", customer_tier="bronze"
        )
        assert reward == 0.92  # No bonus
        assert metadata["tier_bonus"] == 0.0

    def test_max_possible_score(self, task_manager):
        """Test maximum possible score with all bonuses."""
        # Platinum + Frustrated + Correct = 0.92 + 0.04 + 0.03 = 0.99
        reward, reason, metadata = task_manager.grade_easy(
            "Billing", "Billing", sentiment="frustrated", confidence=0.9,
            step_number=1, escalation_triggered=False, customer_tier="platinum"
        )
        assert reward == 0.95  # Capped at 0.95 per spec
        assert "SENTIMENT BONUS" in reason
        assert "CLV BONUS" in reason


class TestTaskConfigs:
    """Test task configuration validation."""

    @pytest.fixture
    def task_manager(self):
        return TaskManager()

    def test_easy_config(self, task_manager):
        """Test easy_routing task configuration."""
        config = task_manager.get_task_config("easy_routing")
        assert config["max_steps"] == 3
        assert "obvious" in config["description"].lower()

    def test_medium_config(self, task_manager):
        """Test medium_routing task configuration."""
        config = task_manager.get_task_config("medium_routing")
        assert config["max_steps"] == 5
        assert "ambiguous" in config["description"].lower()

    def test_hard_config(self, task_manager):
        """Test hard_routing task configuration."""
        config = task_manager.get_task_config("hard_routing")
        assert config["max_steps"] == 8
        assert "complex" in config["description"].lower()

    def test_invalid_task(self, task_manager):
        """Test that invalid tasks raise ValueError."""
        with pytest.raises(ValueError, match="Unknown task"):
            task_manager.get_task_config("invalid_task")
