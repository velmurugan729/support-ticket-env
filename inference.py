# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os 
import sys
from typing import List, Optional 
from openai import OpenAI 

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your environment components
from server.support_ticket_envdir_environment import (
    SupportTicketEnvdirEnvironment as TicketEnv,
    set_current_task,
    reset_ticket_index,
) 
from models import TicketAction, TicketObservation 

from metrics import PerformanceReporter

# Required environment variables (defaults provided) 
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1") 
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct") 
HF_TOKEN = os.getenv("HF_TOKEN") 

if not HF_TOKEN: 
    raise ValueError("HF_TOKEN is required") 

TASKS = ["easy_routing", "medium_routing", "hard_routing"] 
MAX_STEPS_PER_TASK = 8 

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN) 
reporter = PerformanceReporter(MODEL_NAME)

VALID_DEPARTMENTS = ["Billing", "Technical", "Shipping", "Returns", "General"]

def parse_department(raw_response: str) -> str:
    """
    Parse the LLM response to extract only the clean department name.
    Handles cases where LLM adds reasoning or extra text.
    """
    if not raw_response:
        return "General"
    
    # Clean the response
    cleaned = raw_response.strip()
    
    # Try to find an exact department match (case-insensitive)
    cleaned_lower = cleaned.lower()
    
    # Check for exact match first
    for dept in VALID_DEPARTMENTS:
        if cleaned_lower == dept.lower():
            return dept
    
    # Check if any department name appears in the response
    for dept in VALID_DEPARTMENTS:
        if dept.lower() in cleaned_lower:
            return dept
    
    # Default to General if no match found
    return "General"

def get_model_message(obs: TicketObservation) -> tuple[str, float]:
    """
    Get the routing decision and confidence from the LLM.
    
    This function implements a 'Mistake-Aware' reasoning loop with multi-objective 
    scoring. It provides the model with:
    - Previous action and educational feedback
    - Customer sentiment context (frustrated requires higher confidence)
    - Escalation warnings for wrong + frustrated + low-confidence combinations
    
    Returns: (department_name, confidence_score)
    """
    # Enhanced system prompt with multi-objective context
    system_prompt = (
        "You are a ticket routing expert with confidence estimation.\n"
        "Respond in this exact format: DEPARTMENT|CONFIDENCE\n"
        "DEPARTMENT: One of Billing, Technical, Shipping, Returns, General\n"
        "CONFIDENCE: 0.0 to 1.0 (your certainty in this decision)\n"
        "Example: Billing|0.95\n"
        "No extra text, explanations, or formatting."
    )
    
    # Build mistake-aware context with last_action, last_reward, and escalation warnings
    feedback_context = ""
    if obs.last_action and obs.last_reward > 0:
        if obs.last_reward >= 0.85:
            feedback_context = f"✅ Previous '{obs.last_action}' was excellent ({obs.last_reward:.2f}). Continue this approach. "
        elif obs.last_reward >= 0.50:
            feedback_context = f"🟡 Previous '{obs.last_action}' was acceptable ({obs.last_reward:.2f}) but could improve. "
        else:
            feedback_context = f"❌ Previous '{obs.last_action}' failed ({obs.last_reward:.2f}). CHANGE STRATEGY: {obs.reward_reason[:100]}. "
    
    # Escalation warning for frustrated customers
    escalation_warning = ""
    if obs.sentiment.lower() == "frustrated":
        escalation_warning = (
            "🚨 ESCALATION RISK: Frustrated customer detected! "
            "If you route WRONG with confidence < 0.7, ticket escalates to manager (-0.10 penalty). "
            "Be HIGHLY confident or you will escalate! "
        )
    
    user_content = (
        f"=== TICKET ===\n"
        f"Subject: {obs.subject}\n"
        f"Body: {obs.body}\n\n"
        f"=== CONTEXT ===\n"
        f"Customer: {obs.customer_tier} tier, {obs.priority} priority, {obs.sentiment}\n"
        f"Task Type: {obs.task_difficulty}\n"
        f"Step: {obs.steps_taken + 1}/{obs.max_steps}\n"
        f"Cumulative Reward: {obs.cumulative_reward:.2f}\n\n"
        f"=== FEEDBACK ===\n"
        f"{obs.reward_reason if obs.reward_reason else 'First attempt - analyze carefully'}\n"
        f"{feedback_context}"
        f"{escalation_warning}\n\n"
        f"Reply with: DEPARTMENT|CONFIDENCE (e.g., Billing|0.92)"
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.1,
        max_tokens=15
    )
    
    raw_output = response.choices[0].message.content.strip()
    
    # Parse department and confidence
    parts = raw_output.split("|")
    clean_dept = parse_department(parts[0]) if parts else "General"
    
    # Extract confidence if provided
    confidence = 0.5
    if len(parts) >= 2:
        try:
            confidence = float(parts[1])
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except ValueError:
            confidence = 0.5
    
    # Debug logging
    if raw_output != clean_dept:
        print(f"[PARSE] Raw: '{raw_output}' -> Dept: '{clean_dept}', Conf: {confidence:.2f}", flush=True)
    
    return clean_dept, confidence

def run_task(task_name: str): 
    set_current_task(task_name)
    reset_ticket_index()
    
    env = TicketEnv() 
    rewards: List[float] = [] 
    steps_taken = 0 
    success = False
    score = 0.0

    # EXACT official [START] line
    print(f"[START] task={task_name} env=support-ticket-envdir-v2 model={MODEL_NAME}", flush=True) 
 
    try: 
        obs = env.reset() 
        for step in range(1, MAX_STEPS_PER_TASK + 1): 
            # Get action and confidence from LLM 
            action_text, confidence = get_model_message(obs)
 
            # Parse action with confidence
            action = TicketAction(department=action_text, confidence=confidence) 
 
            result = env.step(action) 
            reward = result.reward or 0.0 
            done = result.done 
 
            rewards.append(reward) 
            steps_taken = step 
 
            # EXACT official [STEP] line
            print(f"[STEP] step={step} action={action_text} reward={reward:.2f} done={str(done).lower()} error=null", flush=True) 
 
            if done: 
                break 
 
            obs = result 

        score = sum(rewards) / len(rewards) if rewards else 0.06 
        score = max(0.06, min(0.94, score)) 
        success = score >= 0.5 

    finally: 
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) 
        # EXACT official [END] line
        print(f"[END] success={str(success).lower()} steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True) 
        reporter.add_result(task_name, success, score, steps_taken, rewards_str)
        return success, score

def main(): 
    results = []
    for task in TASKS: 
        success, score = run_task(task) 
        results.append((task, success, score))
    
    # Official [SUMMARY] line
    total_score = sum(r[2] for r in results) / len(results) if results else 0.05
    success_count = sum(1 for r in results if r[1])
    print(f"[SUMMARY] tasks_completed={len(results)} success_count={success_count} avg_score={total_score:.3f}", flush=True)
    
    # Generate detailed report
    reporter.generate_summary()

if __name__ == "__main__": 
    main()
