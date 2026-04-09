# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task manager for the ticket routing environment with deterministic graders.

Implements three task difficulty levels with different grading schemes:
- easy_routing: exact match = 0.94 else 0.06
- medium_routing: correct = 0.91, adjacent = 0.46, wrong = 0.07
- hard_routing: correct on step 1 = 0.87, step 2 = 0.66, step 3 = 0.42; penalize repeated wrong answers
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
        if hasattr(self, '_previous_actions'):
            self._previous_actions = []

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
        """
        # We don't call reset_episode here as it would clear previous_actions mid-episode
        
        if task_name == "easy_routing":
            return self.grade_easy(predicted_department, correct_department)
        elif task_name == "medium_routing":
            return self.grade_medium(predicted_department, correct_department, adjacent_departments)
        elif task_name == "hard_routing":
            if not hasattr(self, '_previous_actions'):
                self._previous_actions = []
            reward = self.grade_hard(predicted_department, correct_department, step_count, self._previous_actions)
            self._previous_actions.append(predicted_department)
            return reward
        else:
            raise ValueError(f"Unknown task: {task_name}")

    def grade_easy(self, action_dept: str, correct_dept: str) -> float: 
        """Easy: exact match = 0.94, else 0.06."""
        if not action_dept:
            return 0.06
        if str(action_dept).strip().lower() == str(correct_dept).strip().lower(): 
            return 0.94 
        return 0.06 

    def grade_medium(self, action_dept: str, correct_dept: str, adjacent_depts: list) -> float: 
        """Medium: correct = 0.91, adjacent = 0.46, wrong = 0.07."""
        if not action_dept:
            return 0.07
        action_dept_clean = str(action_dept).strip().lower()
        if action_dept_clean == str(correct_dept).strip().lower(): 
            return 0.91 
        elif any(action_dept_clean == str(d).strip().lower() for d in adjacent_depts): 
            return 0.46 
        return 0.07 

    def grade_hard(self, action_dept: str, correct_dept: str, step_number: int, previous_actions: list) -> float: 
        """Hard: step-based partial (0.87/0.66/0.42), wrong = 0.12, repeated = 0.05."""
        if not action_dept:
            return 0.12
        action_dept_clean = str(action_dept).strip().lower()
        correct_dept_clean = str(correct_dept).strip().lower()
        
        if action_dept_clean == correct_dept_clean: 
            if step_number <= 1: 
                return 0.87 
            elif step_number == 2: 
                return 0.66 
            else: 
                return 0.42 
        else: 
            # Check for repeated wrong answers
            if previous_actions and any(action_dept_clean == str(a).strip().lower() for a in previous_actions): 
                return 0.05
            return 0.12

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
        
        # Episode ends if max steps reached or if correctly routed (high reward)
        if step_count >= max_steps:
            return True
        
        # Define "successful routing" threshold per task
        success_threshold = 0.85 # Covers all correct routing values (0.94, 0.91, 0.87)
        if grade >= success_threshold:
            return True
        
        return False
