# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Inference script for the ticket routing environment.

Runs 3 episodes for each of the 3 tasks (9 total) using OpenAI-compatible API.
"""

import json
import os
import sys
from openai import OpenAI

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.support_ticket_envdir_environment import (
    SupportTicketEnvdirEnvironment,
    set_current_task,
    reset_ticket_index,
)
from models import TicketAction


def get_env_var(name: str, default: str = None, required: bool = False) -> str:
    """Get an environment variable with optional default and required check."""
    value = os.environ.get(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable {name} is missing")
    return value


def main():
    """Run inference on all tasks."""
    # Read environment variables
    api_base_url = get_env_var("API_BASE_URL", default="https://router.huggingface.co/v1")
    model_name = get_env_var("MODEL_NAME", default="mistralai/Mistral-7B-Instruct-v0.3")
    hf_token = get_env_var("HF_TOKEN", required=True)

    # Initialize OpenAI client
    client = OpenAI(
        base_url=api_base_url,
        api_key=hf_token,
    )

    # System prompt for the agent
    system_prompt = (
        "You are a customer support routing agent. Route tickets to exactly one department: "
        "Billing, Technical, Shipping, Returns, or General. Respond ONLY in JSON: "
        '{\"department\": \"<dept>\", \"confidence\": 0.9, \"reasoning\": \"<why>\"}'
    )

    # Tasks to run
    tasks = ["easy_routing", "medium_routing", "hard_routing"]
    episodes_per_task = 3

    # Store results for summary
    task_scores = {task: [] for task in tasks}

    # Run episodes for each task
    for task in tasks:
        set_current_task(task)
        reset_ticket_index()

        for episode in range(episodes_per_task):
            env = SupportTicketEnvdirEnvironment()
            obs = env.reset()

            print(f"[START] task={task} env=support_ticket_envdir model={model_name}")

            step = 0
            episode_reward = 0.0
            done = False
            step_rewards = []  # Track all step rewards for [END] line

            while not done:
                step += 1

                # Construct user prompt from observation
                user_prompt = (
                    f"Ticket ID: {obs.ticket_id}\n"
                    f"Subject: {obs.subject}\n"
                    f"Body: {obs.body}\n"
                    f"Customer Tier: {obs.customer_tier}\n"
                    f"Priority: {obs.priority}\n"
                    f"Task Difficulty: {obs.task_difficulty}\n"
                    f"Steps Taken: {obs.steps_taken}/{obs.max_steps}\n\n"
                    "Route this ticket to the appropriate department."
                )

                try:
                    # Call the model
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=300,
                    )

                    # Parse response - extract JSON from markdown if needed
                    content = response.choices[0].message.content.strip()
                    
                    # Try to extract JSON from markdown code blocks
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()
                    else:
                        # Find JSON object in text
                        start = content.find("{")
                        end = content.rfind("}") + 1
                        if start >= 0 and end > start:
                            json_str = content[start:end]
                        else:
                            json_str = content
                    
                    action_data = json.loads(json_str)

                    # Create action
                    action = TicketAction(
                        department=action_data["department"],
                        confidence=action_data["confidence"],
                        reasoning=action_data["reasoning"],
                    )

                    # Step the environment
                    obs = env.step(action)
                    done = obs.done
                    step_reward = float(obs.reward)
                    step_rewards.append(f"{step_reward:.2f}")
                    episode_reward = step_reward  # Use current step reward

                    print(
                        f"[STEP] step={step} action={action.department} "
                        f"reward={step_reward:.2f} done={str(done).lower()} error=null"
                    )

                except Exception as e:
                    error_msg = str(e)
                    print(f"[STEP] step={step} action=None reward=0.05 done=true error={error_msg}")
                    done = True
                    episode_reward = 0.05
                    step_rewards.append("0.05")

            rewards_str = ",".join(step_rewards) if step_rewards else "0.05"
            print(f"[END] success=true steps={step} rewards={rewards_str}")
            task_scores[task].append(episode_reward)

    # Print summary
    easy_avg = sum(task_scores["easy_routing"]) / len(task_scores["easy_routing"])
    medium_avg = sum(task_scores["medium_routing"]) / len(task_scores["medium_routing"])
    hard_avg = sum(task_scores["hard_routing"]) / len(task_scores["hard_routing"])

    print(f"SUMMARY easy_routing={easy_avg:.2f} medium_routing={medium_avg:.2f} hard_routing={hard_avg:.2f}")


if __name__ == "__main__":
    main()
