# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task manager for the ticket routing environment with deterministic graders.

Implements three task difficulty levels with dense reward signals:
- easy_routing: correct = 0.94, wrong = 0.06
- medium_routing: correct = 0.91, adjacent = 0.52, wrong = 0.08
- hard_routing: correct step1 = 0.88, step2 = 0.68, step3 = 0.48; wrong = 0.13, repeated wrong = 0.05
"""

from typing import Dict, List, Optional


class TaskManager:
    """
    Manages task definitions and grading for ticket routing.
    
    Provides deterministic grading based on task difficulty and step count.
    """

    # Task definitions with max steps per task
    TASK_CONFIGS = {
        "easy_routing": {"max_steps": 3, "description": "Route tickets with obvious single-department issues"},
        "medium_routing": {"max_steps": 5, "description": "Route ambiguous tickets that could fit multiple departments"},
        "hard_routing": {"max_steps": 8, "description": "Route complex multi-issue tickets requiring reasoning"},
    }

    def __init__(self):
        """Initialize the task manager."""
        self._previous_wrong_answers: List[str] = []

    def get_task_config(self, task_name: str) -> Dict:
        """
        Get configuration for a specific task.
        """
        if task_name not in self.TASK_CONFIGS:
            raise ValueError(f"Unknown task: {task_name}")
        return self.TASK_CONFIGS[task_name]

    def reset_episode(self):
        """Reset episode-specific state."""
        self._previous_wrong_answers = []
        if hasattr(self, '_previous_actions'):
            self._previous_actions = []

    def grade_easy(self, action_dept: str, correct_dept: str) -> float: 
        """Easy: exact match = 0.94, else 0.06."""
        if not action_dept:
            return 0.06
        action_dept_clean = str(action_dept).strip().lower()
        correct_dept_clean = str(correct_dept).strip().lower()
        if action_dept_clean == correct_dept_clean: 
            return 0.94 
        return 0.06 

    def grade_medium(self, action_dept: str, correct_dept: str, adjacent_depts: list) -> float: 
        """Medium: correct = 0.91, adjacent = 0.52, wrong = 0.08."""
        if not action_dept:
            return 0.08
        action_dept_clean = str(action_dept).strip().lower()
        correct_dept_clean = str(correct_dept).strip().lower()
        if action_dept_clean == correct_dept_clean: 
            return 0.91 
        elif any(action_dept_clean == str(d).strip().lower() for d in adjacent_depts): 
            return 0.52 
        return 0.08 

    def grade_hard(self, action_dept: str, correct_dept: str, step_number: int, previous_actions: list) -> float: 
        """Hard: step1 correct = 0.88, step2 = 0.68, step3 = 0.48; wrong = 0.13, repeated wrong = 0.05."""
        if not action_dept:
            return 0.13
        action_dept_clean = str(action_dept).strip().lower()
        correct_dept_clean = str(correct_dept).strip().lower()
        
        if action_dept_clean == correct_dept_clean: 
            if step_number <= 1: 
                return 0.88 
            elif step_number == 2: 
                return 0.68 
            else: 
                return 0.48 
        else: 
            # Check for repeated wrong answers
            if previous_actions and any(action_dept_clean == str(a).strip().lower() for a in previous_actions): 
                return 0.05
            return 0.13

    def is_done(self, task_name: str, step_count: int, grade: float) -> bool:
        """
        Determine if the episode is done.
        """
        max_steps = self.TASK_CONFIGS[task_name]["max_steps"]
        if step_count >= max_steps:
            return True
        success_threshold = 0.85
        if grade >= success_threshold:
            return True
        return False
