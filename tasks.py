# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task manager for multi-objective ticket routing with escalation mechanics.

Three scoring dimensions (multi-objective RL):
1. ROUTING ACCURACY (70% weight): Correct department identification
2. CUSTOMER HANDLING (20% weight): Sentiment-aware confidence thresholds
3. EFFICIENCY (10% weight): Step minimization with progressive penalties

Implements escalation mechanic: frustrated customers require confidence >= 0.7
Escalation triggers when: wrong_department AND frustrated_sentiment AND confidence < 0.7

Reward structure optimized for 0.50-0.75 baseline with educational feedback.
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

    # Define semantically close departments for partial credit
    CLOSE_DEPARTMENTS = {
        "billing": ["returns"],  # Both involve money/transactions
        "returns": ["billing", "shipping"],  # Returns involve shipping and refunds
        "shipping": ["returns"],  # Both involve physical goods movement
        "technical": ["billing"],  # Technical issues can cause billing problems
    }

    def grade_easy(self, action_dept: str, correct_dept: str, sentiment: str = "neutral", 
                   confidence: float = 0.5, step_number: int = 1, 
                   escalation_triggered: bool = False, customer_tier: str = "bronze") -> tuple[float, str, dict]:
        """
        Easy routing with 4D multi-objective scoring:
        - Accuracy (70%): Correct = 0.92, Wrong = 0.08
        - Sentiment handling (15%): Frustrated + correct = bonus 0.04
        - Customer Lifetime Value (5%): Platinum/Gold bonus for high-value customers
        - Efficiency (10%): Step 1 = full, Step 2+ = penalty -0.02 per step
        
        Returns: (reward, reason, metadata_dict)
        """
        metadata = {"accuracy_score": 0.0, "sentiment_bonus": 0.0, "tier_bonus": 0.0, "efficiency_penalty": 0.0}
        
        # 1. ACCURACY COMPONENT (70% weight)
        if not action_dept or str(action_dept).strip().lower() == "general":
            base_reward = 0.08
            accuracy_reason = "No department selected. Single-issue tickets require specific routing."
        else:
            action_dept_clean = str(action_dept).strip().lower()
            correct_dept_clean = str(correct_dept).strip().lower()
            
            if action_dept_clean == correct_dept_clean:
                base_reward = 0.92
                accuracy_reason = f"✅ EXCELLENT: '{action_dept}' perfectly matches this '{correct_dept}' issue."
                metadata["accuracy_score"] = 0.92
            else:
                base_reward = 0.08
                accuracy_reason = f"❌ INCORRECT: '{action_dept}' is wrong for this '{correct_dept}' ticket."
                metadata["accuracy_score"] = 0.08
        
        # 2. SENTIMENT HANDLING (15% weight) - Bonus for handling frustrated customers correctly
        sentiment_bonus = 0.0
        sentiment_reason = ""
        if sentiment.lower() == "frustrated" and base_reward >= 0.9:
            sentiment_bonus = 0.04
            sentiment_reason = " 🎯 SENTIMENT BONUS: Successfully handled frustrated customer with precise routing!"
            metadata["sentiment_bonus"] = 0.04
        elif sentiment.lower() == "frustrated" and base_reward < 0.9:
            sentiment_bonus = -0.02
            sentiment_reason = " ⚠️ SENTIMENT PENALTY: Frustrated customer needs correct routing urgently."
            metadata["sentiment_bonus"] = -0.02
        
        # 3. CUSTOMER LIFETIME VALUE (5% weight) - Clever mechanic: High-tier customers matter more
        tier_bonus = 0.0
        tier_reason = ""
        tier_value = {"bronze": 0.0, "silver": 0.01, "gold": 0.02, "platinum": 0.03}.get(customer_tier.lower(), 0.0)
        if base_reward >= 0.9 and tier_value > 0:
            tier_bonus = tier_value
            tier_reason = f" 💎 CLV BONUS: {customer_tier.upper()} customer retained with excellent service!"
            metadata["tier_bonus"] = tier_bonus
        
        # 4. EFFICIENCY (10% weight) - Step penalty for delayed decisions
        efficiency_penalty = 0.0
        efficiency_reason = ""
        if step_number > 1:
            efficiency_penalty = -0.02 * (step_number - 1)
            efficiency_reason = f" ⏱️ EFFICIENCY: Step {step_number} incurs small delay penalty."
            metadata["efficiency_penalty"] = efficiency_penalty
        else:
            efficiency_reason = " ⚡ EFFICIENCY: First-try success!"
        
        # 5. ESCALATION PENALTY (if triggered)
        escalation_penalty = 0.0
        escalation_reason = ""
        if escalation_triggered:
            escalation_penalty = -0.10
            escalation_reason = " 🚨 ESCALATION: Ticket escalated due to frustration + wrong routing + low confidence."
            metadata["escalated"] = True
        
        total_reward = max(0.06, min(0.94, base_reward + sentiment_bonus + tier_bonus + efficiency_penalty + escalation_penalty))
        full_reason = f"{accuracy_reason}{sentiment_reason}{tier_reason}{efficiency_reason}{escalation_reason}"
        
        return total_reward, full_reason, metadata

    def grade_medium(self, action_dept: str, correct_dept: str, adjacent_depts: list,
                     sentiment: str = "neutral", confidence: float = 0.5, step_number: int = 1,
                     escalation_triggered: bool = False) -> tuple[float, str, dict]:
        """
        Medium routing with multi-objective scoring and semantic partial credit:
        - Accuracy: Correct=0.88, Adjacent=0.52, Wrong=0.09, Semantic=0.35
        - Sentiment: Frustrated handling bonus/penalty
        - Efficiency: Progressive step penalty
        """
        metadata = {"accuracy_score": 0.0, "adjacent_used": False, "semantic_match": False}
        
        # 1. ACCURACY with TIERED PARTIAL CREDIT
        if not action_dept or str(action_dept).strip().lower() == "general":
            base_reward = 0.09
            accuracy_reason = "❌ NO ROUTING: 'General' is insufficient for ambiguous tickets. Identify the PRIMARY issue."
            metadata["accuracy_score"] = 0.09
        else:
            action_dept_clean = str(action_dept).strip().lower()
            correct_dept_clean = str(correct_dept).strip().lower()
            
            if action_dept_clean == correct_dept_clean:
                base_reward = 0.88
                accuracy_reason = f"✅ PERFECT: '{action_dept}' correctly identifies the ROOT CAUSE among multiple concerns."
                metadata["accuracy_score"] = 0.88
            elif any(action_dept_clean == str(d).strip().lower() for d in adjacent_depts):
                base_reward = 0.52
                accuracy_reason = f"🟡 PARTIAL CREDIT: '{action_dept}' is a VALID secondary concern (0.52), but '{correct_dept}' addresses the PRIMARY issue."
                metadata["accuracy_score"] = 0.52
                metadata["adjacent_used"] = True
            else:
                # Check semantic closeness
                close_depts = self.CLOSE_DEPARTMENTS.get(correct_dept_clean, [])
                if action_dept_clean in close_depts:
                    base_reward = 0.35
                    accuracy_reason = f"🟠 SEMANTIC MATCH: '{action_dept}' is thematically related (0.35) but misses the specific department. Primary: '{correct_dept}'."
                    metadata["accuracy_score"] = 0.35
                    metadata["semantic_match"] = True
                else:
                    base_reward = 0.09
                    accuracy_reason = f"❌ WRONG: '{action_dept}' doesn't address this ticket's concerns. The PRIMARY department is '{correct_dept}'."
                    metadata["accuracy_score"] = 0.09
        
        # 2. SENTIMENT HANDLING
        sentiment_bonus = 0.0
        sentiment_reason = ""
        if sentiment.lower() == "frustrated":
            if base_reward >= 0.88:
                sentiment_bonus = 0.04
                sentiment_reason = " 🎯 FRUSTRATED CUSTOMER HANDLED: Correct routing under pressure!"
            elif base_reward >= 0.50:
                sentiment_bonus = 0.02
                sentiment_reason = " 🟡 Acceptable routing for frustrated customer."
            else:
                sentiment_bonus = -0.03
                sentiment_reason = " ⚠️ URGENT: Frustrated customer needs IMMEDIATE correct routing."
        
        # 3. EFFICIENCY
        efficiency_penalty = max(0, -0.015 * (step_number - 1))
        efficiency_reason = f" ⏱️ Step {step_number}: {'First try!' if step_number == 1 else 'Efficiency penalty applied.'}"
        
        # 4. CONFIDENCE BONUS (novel feature)
        confidence_bonus = 0.0
        if confidence >= 0.8 and base_reward >= 0.50:
            confidence_bonus = 0.02
            efficiency_reason += " High confidence bonus!"
        
        # 5. ESCALATION
        escalation_penalty = -0.10 if escalation_triggered else 0.0
        escalation_reason = " 🚨 ESCALATED: Manager intervention required." if escalation_triggered else ""
        
        total_reward = max(0.06, min(0.94, base_reward + sentiment_bonus + efficiency_penalty + confidence_bonus + escalation_penalty))
        full_reason = f"{accuracy_reason}{sentiment_reason}{efficiency_reason}{escalation_reason}"
        
        return total_reward, full_reason, metadata

    def grade_hard(self, action_dept: str, correct_dept: str, step_number: int, previous_actions: list, 
                   adjacent_depts: list = None, sentiment: str = "neutral", confidence: float = 0.5,
                   escalation_triggered: bool = False) -> tuple[float, str, dict]:
        """
        Hard multi-objective grading with learning penalties:
        - Step-based accuracy: Step1=0.85, Step2=0.68, Step3=0.48
        - Repeated mistake penalty: 0.05 (learning failure detection)
        - Adjacent credit: 0.52 for secondary concerns
        - Sentiment + Escalation modifiers
        """
        metadata = {"step_bonus": 0.0, "repeated_mistake": False, "learning_penalty": 0.0}
        
        if not action_dept or str(action_dept).strip().lower() == "general":
            return 0.12, "❌ NO ROUTING: Complex multi-issue tickets require SPECIFIC department assignment. Analyze the ROOT CAUSE.", metadata

        action_dept_clean = str(action_dept).strip().lower()
        correct_dept_clean = str(correct_dept).strip().lower()

        # 1. STEP-BASED ACCURACY (progressive decay)
        if action_dept_clean == correct_dept_clean:
            if step_number <= 1:
                base_reward = 0.85
                accuracy_reason = f"🏆 EXCELLENT STEP 1: '{action_dept}' identified ROOT CAUSE immediately! Multi-issue tickets solved on first try."
                metadata["step_bonus"] = 0.85
            elif step_number == 2:
                base_reward = 0.68
                accuracy_reason = f"✅ GOOD STEP 2: '{action_dept}' correct! Agent adapted from previous feedback. Learning demonstrated."
                metadata["step_bonus"] = 0.68
            else:
                base_reward = 0.48
                accuracy_reason = f"🟡 OK STEP {step_number}: '{action_dept}' correct, but inefficient reasoning. Review pattern recognition."
                metadata["step_bonus"] = 0.48
        else:
            # 2. REPEATED MISTAKE PENALTY (learning detection)
            if previous_actions and any(action_dept_clean == str(a).strip().lower() for a in previous_actions):
                base_reward = 0.05
                accuracy_reason = f"❌❌ LEARNING FAILURE: Repeated '{action_dept}' after previous low reward. Agent should try different reasoning."
                metadata["repeated_mistake"] = True
                metadata["learning_penalty"] = -0.10
            # 3. ADJACENT DEPARTMENT (partial credit)
            elif adjacent_depts and any(action_dept_clean == str(d).strip().lower() for d in adjacent_depts):
                base_reward = 0.52
                accuracy_reason = f"🟡 PARTIAL CREDIT: '{action_dept}' handles a VALID SECONDARY issue (0.52), but ROOT CAUSE is '{correct_dept}'."
            # 4. SEMANTIC MATCH
            else:
                close_depts = self.CLOSE_DEPARTMENTS.get(correct_dept_clean, [])
                if action_dept_clean in close_depts:
                    base_reward = 0.28
                    accuracy_reason = f"🟠 SEMANTIC: '{action_dept}' related to '{correct_dept}' issues (0.28), but not the specific department."
                else:
                    base_reward = 0.12
                    accuracy_reason = f"❌ INCORRECT: '{action_dept}' is not a valid concern for this ticket. Primary: '{correct_dept}'."
        
        # 5. SENTIMENT MODIFIER for hard tickets
        sentiment_bonus = 0.0
        sentiment_reason = ""
        if sentiment.lower() == "frustrated":
            if base_reward >= 0.68:
                sentiment_bonus = 0.05
                sentiment_reason = " 🎯 STRESS HANDLING: Correct routing despite frustrated customer!"
            elif base_reward >= 0.48:
                sentiment_bonus = 0.02
                sentiment_reason = " 🟡 Adequate handling of frustrated customer."
            else:
                sentiment_bonus = -0.05
                sentiment_reason = " ⚠️ CRITICAL: Frustrated customer needs IMMEDIATE escalation if wrong."
        
        # 6. CONFIDENCE THRESHOLD for frustrated
        confidence_penalty = 0.0
        if sentiment.lower() == "frustrated" and confidence < 0.7 and base_reward < 0.5:
            confidence_penalty = -0.05
            sentiment_reason += " Low confidence on frustrated customer."
        
        # 7. ESCALATION
        escalation_penalty = -0.12 if escalation_triggered else 0.0
        escalation_reason = " 🚨 MANAGER ESCALATION: Ticket requires human intervention." if escalation_triggered else ""
        
        total_reward = max(0.06, min(0.94, base_reward + sentiment_bonus + confidence_penalty + escalation_penalty))
        full_reason = f"{accuracy_reason}{sentiment_reason}{escalation_reason}"
        
        return total_reward, full_reason, metadata

    def is_done(self, task_name: str, step_count: int, grade: float) -> bool:
        """
        Determine if the episode is done.
        """
        max_steps = self.TASK_CONFIGS[task_name]["max_steps"]
        if step_count >= max_steps:
            return True
        success_threshold = 0.62
        if grade >= success_threshold:
            return True
        return False
