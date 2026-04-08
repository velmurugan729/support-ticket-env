# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task manager for the ticket routing environment with deterministic graders.

Implements three task difficulty levels with different grading schemes:
- easy_routing: exact match = 1.0 else 0.0
- medium_routing: correct = 1.0, adjacent = 0.4, wrong = 0.0
- hard_routing: correct on step 1 = 1.0, step 2 = 0.7, step 3 = 0.4; penalize repeated wrong answers
"""

from typing import Dict, List, Optional


class TaskManager:
    """
    Manages task definitions and grading for ticket routing.
    
    Provides deterministic grading based on task difficulty and step count.
    """

    # Task definitions with max steps per task
    TASK_CONFIGS = {
        "easy_routing": {"max_steps": 1, "description": "Route tickets with obvious single-department issues"},
        "medium_routing": {"max_steps": 2, "description": "Route ambiguous tickets that could fit multiple departments"},
        "hard_routing": {"max_steps": 3, "description": "Route complex multi-issue tickets requiring reasoning"},
    }

    def __init__(self):
        """Initialize the task manager."""
        self._previous_wrong_answers: List[str] = []

    def get_task_config(self, task_name: str) -> Dict:
        """
        Get configuration for a specific task.
        
        Args:
            task_name: Name of the task (easy_routing, medium_routing, hard_routing)
            
        Returns:
            Dictionary with task configuration including max_steps and description
        """
        if task_name not in self.TASK_CONFIGS:
            raise ValueError(f"Unknown task: {task_name}")
        return self.TASK_CONFIGS[task_name]

    def reset_episode(self):
        """Reset episode-specific state like previous wrong answers."""
        self._previous_wrong_answers = []

    def grade_action(
        self,
        task_name: str,
        predicted_department: str,
        correct_department: str,
        adjacent_departments: List[str],
        step_count: int
    ) -> float:
        """
        Grade a routing action based on task difficulty and step count.
        
        Args:
            task_name: Name of the current task
            predicted_department: The department predicted by the agent
            correct_department: The correct department for the ticket
            adjacent_departments: List of departments that are considered adjacent/related
            step_count: Current step number (1-indexed)
            
        Returns:
            Grade between 0.0 and 1.0
        """
        self.reset_episode()
        
        if task_name == "easy_routing":
            return self._grade_easy_routing(predicted_department, correct_department)
        elif task_name == "medium_routing":
            return self._grade_medium_routing(predicted_department, correct_department, adjacent_departments)
        elif task_name == "hard_routing":
            return self._grade_hard_routing(predicted_department, correct_department, adjacent_departments, step_count)
        else:
            raise ValueError(f"Unknown task: {task_name}")

    def _grade_easy_routing(self, predicted: str, correct: str) -> float:
        """
        Grade easy routing task: exact match = 1.0 else 0.0.
        
        Args:
            predicted: Predicted department
            correct: Correct department
            
        Returns:
            1.0 if correct, 0.0 otherwise
        """
        return 1.0 if predicted.lower() == correct.lower() else 0.0

    def _grade_medium_routing(self, predicted: str, correct: str, adjacent: List[str]) -> float:
        """
        Grade medium routing task: correct = 1.0, adjacent = 0.4, wrong = 0.0.
        
        Args:
            predicted: Predicted department
            correct: Correct department
            adjacent: List of adjacent departments
            
        Returns:
            1.0 for correct, 0.4 for adjacent, 0.0 for wrong
        """
        if predicted.lower() == correct.lower():
            return 1.0
        elif predicted.lower() in [dept.lower() for dept in adjacent]:
            return 0.4
        else:
            return 0.0

    def _grade_hard_routing(
        self,
        predicted: str,
        correct: str,
        adjacent: List[str],
        step_count: int
    ) -> float:
        """
        Grade hard routing task with step-based decay and penalty for repeated wrong answers.
        
        - Step 1 correct: 1.0
        - Step 2 correct: 0.7
        - Step 3 correct: 0.4
        - Adjacent departments: 50% of the step value
        - Repeated wrong answers: additional -0.2 penalty
        
        Args:
            predicted: Predicted department
            correct: Correct department
            adjacent: List of adjacent departments
            step_count: Current step number (1-indexed)
            
        Returns:
            Grade between 0.0 and 1.0
        """
        # Check for repeated wrong answers
        if predicted.lower() != correct.lower():
            if predicted.lower() in self._previous_wrong_answers:
                # Penalize repeated wrong answers
                self._previous_wrong_answers.append(predicted.lower())
                return 0.0
            self._previous_wrong_answers.append(predicted.lower())
        
        # Base score based on step
        if step_count == 1:
            base_score = 1.0
        elif step_count == 2:
            base_score = 0.7
        elif step_count == 3:
            base_score = 0.4
        else:
            base_score = 0.0
        
        # Apply department match
        if predicted.lower() == correct.lower():
            return base_score
        elif predicted.lower() in [dept.lower() for dept in adjacent]:
            return base_score * 0.5
        else:
            return 0.0

    def is_done(self, task_name: str, step_count: int, grade: float) -> bool:
        """
        Determine if the episode is done based on task and grade.
        
        Args:
            task_name: Name of the current task
            step_count: Current step number
            grade: Grade from the last action
            
        Returns:
            True if episode should end, False otherwise
        """
        max_steps = self.TASK_CONFIGS[task_name]["max_steps"]
        
        # Episode ends if max steps reached or perfect score achieved
        if step_count >= max_steps:
            return True
        if grade == 1.0:
            return True
        
        return False
