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
from models import TicketAction 

# Required environment variables (defaults provided) 
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1") 
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct") 
HF_TOKEN = os.getenv("HF_TOKEN") 

if not HF_TOKEN: 
    raise ValueError("HF_TOKEN is required") 

TASKS = ["easy_routing", "medium_routing", "hard_routing"] 
MAX_STEPS_PER_TASK = 8 

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN) 

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
            # Get action from LLM 
            response = client.chat.completions.create( 
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": f"Route this ticket to the correct department.\nTicket: {obs}"}], 
                temperature=0.7, 
                max_tokens=100 
            ) 
            action_text = response.choices[0].message.content.strip() 
 
            # Parse action 
            action = TicketAction(department=action_text) 
 
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

        score = sum(rewards) / (MAX_STEPS_PER_TASK * 1.0) if rewards else 0.0 
        score = min(max(score, 0.0), 1.0) 
        success = score >= 0.5 

    finally: 
        rewards_str = ",".join(f"{r:.2f}" for r in rewards) 
        # EXACT official [END] line
        print(f"[END] success={str(success).lower()} steps={steps_taken} score={score:.3f} rewards={rewards_str}", flush=True) 
        return success, score

def main(): 
    results = []
    for task in TASKS: 
        success, score = run_task(task) 
        results.append((task, success, score))
    
    # Official [SUMMARY] line
    total_score = sum(r[2] for r in results) / len(results) if results else 0.0
    success_count = sum(1 for r in results if r[1])
    print(f"[SUMMARY] tasks_completed={len(results)} success_count={success_count} avg_score={total_score:.3f}", flush=True)

if __name__ == "__main__": 
    main()
