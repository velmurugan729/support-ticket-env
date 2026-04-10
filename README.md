---
sdk: docker
app_port: 7860
---

# Support Ticket Routing Environment (v2)

## 1. Environment Description & Motivation

Customer support ticket routing is a critical real-world task that requires understanding natural language, context, and business rules. This environment provides a realistic simulation where AI agents must route tickets to one of five departments:

- **Billing**: Payment issues, invoices, refunds, subscription charges
- **Technical**: Software bugs, login issues, application errors
- **Shipping**: Package delivery, address corrections, tracking issues
- **Returns**: Product returns, exchanges, damaged items
- **General**: General inquiries, feedback, other issues

The environment includes three difficulty levels with dense reward signals and multi-step reasoning requirements.

## Action/Observation Spaces

### Action Space
**TicketAction**: The agent provides a routing decision with:
- `department` (str): Target department - Billing, Technical, Shipping, Returns, or General.
- `confidence` (float): Confidence score between 0.0 and 1.0.
- `reasoning` (str): Text explanation for the routing decision.

### Observation Space
**TicketObservation**: The agent receives ticket information:
- `ticket_id` (str): Unique identifier for the ticket.
- `subject` (str): Ticket subject line.
- `body` (str): Full ticket body text.
- `customer_tier` (str): Customer tier (bronze, silver, gold, platinum).
- `priority` (str): Ticket priority level (low, medium, high).
- `task_difficulty` (str): Current task difficulty (easy_routing, medium_routing, hard_routing).
- `steps_taken` (int): Number of steps taken in the current episode.
- `max_steps` (int): Maximum steps allowed for this task.
- `reward` (float): The reward received for the *current* step.
- `done` (bool): Whether the episode is complete.
- `last_action` (str): The department selected in the previous step (empty for first step).
- `last_reward` (float): The reward received for the previous action.

## Task Descriptions

### Easy Routing
- **Description**: Route tickets with obvious single-department issues.
- **Max Steps**: 3
- **Grading**: Correct = 0.94, Wrong = 0.06.

### Medium Routing
- **Description**: Route ambiguous tickets that could fit multiple departments.
- **Max Steps**: 5
- **Grading**: Correct = 0.91, Adjacent = 0.52, Wrong = 0.08.

### Hard Routing
- **Description**: Route complex multi-issue tickets requiring reasoning.
- **Max Steps**: 8
- **Grading**: Step 1 correct = 0.88, Step 2 = 0.68, Step 3 = 0.48; Adjacent = 0.35; Wrong = 0.13.
- **Penalty**: Repeated wrong answers receive a penalty reward of 0.05.

## Reward Function & Termination

The environment uses a **dense reward signal** strictly clamped between **0.05 and 0.95** to ensure stable training and evaluation.

### Invalid Actions
Actions with an empty department or "General" are considered invalid/default. They receive a minimum reward of **0.05** and **do not consume a step**, allowing the agent to retry until it provides a specific department.

### Termination
An episode ends when:
1. A correct routing decision is made (Reward ≥ 0.85).
2. The maximum number of valid steps for the task difficulty is reached.

## Local Setup & Validation

### Installation
```bash
pip install -r requirements.txt
```

### Run Server
```bash
python -m server.app
```

### Run Validation
```bash
python inference.py
```
This script runs 3 tasks and produces a `[SUMMARY]` line with average scores and success counts.
