---
sdk: docker
app_port: 7860
---

# Support Ticket Routing Environment

## 1. Environment Description & Motivation

Customer support ticket routing is a critical real-world task that requires understanding natural language, context, and business rules. This environment provides a realistic simulation where AI agents must route tickets to one of five departments:

- **Billing**: Payment issues, invoices, refunds, subscription charges
- **Technical**: Software bugs, login issues, application errors
- **Shipping**: Package delivery, address corrections, tracking issues
- **Returns**: Product returns, exchanges, damaged items
- **General**: General inquiries, feedback, other issues

The environment includes three difficulty levels to test different aspects of routing capability:
- **Easy**: Obvious single-department issues with clear keywords
- **Medium**: Ambiguous tickets that could fit multiple departments
- **Hard**: Complex multi-issue tickets requiring reasoning about multiple factors

## Action/Observation Spaces

### Action Space
**TicketAction**: The agent provides a routing decision with:
- `department` (str): Target department - must be one of: Billing, Technical, Shipping, Returns, or General
- `confidence` (float): Confidence score between 0.0 and 1.0
- `reasoning` (str): Text explanation for the routing decision

### Observation Space
**TicketObservation**: The agent receives ticket information:
- `ticket_id` (str): Unique identifier for the ticket
- `subject` (str): Ticket subject line
- `body` (str): Full ticket body text
- `customer_tier` (str): Customer tier (bronze, silver, gold, platinum)
- `priority` (str): Ticket priority level (low, medium, high)
- `task_difficulty` (str): Current task difficulty (easy, medium, hard)
- `steps_taken` (int): Number of steps taken in current episode
- `max_steps` (int): Maximum steps allowed for this task
- `done` (bool): Whether the episode is complete
- `reward` (float): Cumulative reward for the episode (only provided when done=True)
- `metadata` (dict): Additional information including step_rewards, correct_department, task_name

## Task Descriptions

### Easy Routing
- **Description**: Route tickets with obvious single-department issues
- **Max Steps**: 1
- **Characteristics**: Clear keywords and unambiguous intent
- **Example**: "Credit card charge not showing on my account" → Billing

### Medium Routing
- **Description**: Route ambiguous tickets that could fit multiple departments
- **Max Steps**: 2
- **Characteristics**: Overlapping concepts, may require prioritization
- **Example**: "Product stopped working after 2 weeks" → Returns (could also be Technical)

### Hard Routing
- **Description**: Route complex multi-issue tickets requiring reasoning
- **Max Steps**: 3
- **Characteristics**: Multiple issues, conflicting information, requires prioritization
- **Example**: "Order cancelled but charged, and replacement never sent" → Billing (involves Shipping, Returns, Technical)

## Reward Function

The reward function is deterministic and varies by task difficulty:

### Easy Routing
- **Correct department**: 1.0
- **Incorrect department**: 0.0

### Medium Routing
- **Correct department**: 1.0
- **Adjacent department** (related but not correct): 0.4
- **Wrong department**: 0.0

### Hard Routing
Rewards decay based on step number (encourages quick correct answers):
- **Step 1 correct**: 1.0
- **Step 2 correct**: 0.7
- **Step 3 correct**: 0.4
- **Adjacent department**: 50% of step value
- **Repeated wrong answers**: Additional -0.2 penalty (prevents guessing)

The episode ends when:
- Max steps are reached, OR
- A perfect score (1.0) is achieved

## Setup Instructions

### Local Setup

1. **Install dependencies**:
```bash
uv sync
```

2. **Run the server locally**:
```bash
uvicorn server.app:app --reload
```

3. **Run inference**:
```bash
# Set required environment variables
export HF_TOKEN="your_huggingface_token"
export API_BASE_URL="https://api-inference.huggingface.co/v1"  # optional, default provided
export MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.3"  # optional, default provided

# Run inference script
python inference.py
```

### Docker Setup

1. **Build the Docker image**:
```bash
docker build -t support-ticket-envdir .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 support-ticket-envdir
```

3. **Run inference with Docker**:
```bash
docker run -e HF_TOKEN="your_token" support-ticket-envdir python inference.py
```

## Baseline Scores

Results from running `inference.py` with `openai/gpt-oss-120b` model via Hugging Face Router API:

| Task | Score |
|------|-------|
| **Easy Routing** | 1.00 |
| **Medium Routing** | 0.93 |
| **Hard Routing** | 1.00 |

**Model**: openai/gpt-oss-120b (via Hugging Face Router with Groq provider)

Expected performance ranges:
- **Easy Routing**: 0.8-1.0 (should be near-perfect with good LLMs)
- **Medium Routing**: 0.6-0.9 (requires understanding ambiguity)
- **Hard Routing**: 0.4-0.8 (challenging multi-step reasoning)

## Quick Start Example

```python
from support_ticket_envdir.server.support_ticket_envdir_environment import (
    SupportTicketEnvdirEnvironment,
    set_current_task,
)
from support_ticket_envdir.models import TicketAction

# Set the task
set_current_task("easy_routing")

# Create environment
env = SupportTicketEnvdirEnvironment()

# Reset to get a ticket
obs = env.reset()
print(f"Ticket: {obs.subject}")
print(f"Body: {obs.body}")

# Route the ticket
action = TicketAction(
    department="Billing",
    confidence=0.9,
    reasoning="The ticket mentions credit card charges and billing discrepancy."
)

# Step the environment
result = env.step(action)
print(f"Reward: {result.reward}")
print(f"Done: {result.done}")
```

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

The `openenv push` command will:
1. Validate that the directory is an OpenEnv environment (checks for `openenv.yaml`)
2. Prepare a custom build for Hugging Face Docker space (enables web interface)
3. Upload to Hugging Face (ensuring you're logged in)

### Prerequisites

- Authenticate with Hugging Face: The command will prompt for login if not already authenticated

### Options

- `--directory`, `-d`: Directory containing the OpenEnv environment (defaults to current directory)
- `--repo-id`, `-r`: Repository ID in format 'username/repo-name' (defaults to 'username/env-name' from openenv.yaml)
- `--base-image`, `-b`: Base Docker image to use (overrides Dockerfile FROM)
- `--private`: Deploy the space as private (default: public)

After deployment, your space will be available at:
`https://huggingface.co/spaces/<repo-id>`

The deployed space includes:
- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring
- **WebSocket** at `/ws` - Persistent session endpoint for low-latency interactions

## Development & Testing

### Direct Environment Testing

Test the environment logic directly without starting the HTTP server:

```bash
# From the server directory
python3 server/support_ticket_envdir_environment.py
```

This verifies that:
- Environment resets correctly
- Step executes actions properly
- State tracking works
- Rewards are calculated correctly

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

### Validation

Validate the environment configuration:

```bash
openenv validate
```

## Project Structure

```
support_ticket_envdir/
├── data/
│   └── tickets.py              # Synthetic ticket data (28 tickets)
├── server/
│   ├── __init__.py              # Server module exports
│   ├── support_ticket_envdir_environment.py  # Core environment logic
│   ├── app.py                   # FastAPI application (HTTP + WebSocket endpoints)
│   ├── Dockerfile               # Container image definition
│   └── requirements.txt         # Server dependencies
├── __init__.py                  # Module exports
├── README.md                    # This file
├── openenv.yaml                 # OpenEnv manifest
├── pyproject.toml               # Project metadata and dependencies
├── client.py                    # SupportTicketEnvdirEnv client
├── models.py                    # Action and Observation models
├── tasks.py                     # Task manager and grading logic
└── inference.py                 # Inference script for evaluation
```
