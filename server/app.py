# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Support Ticket Envdir Environment.

This module creates an HTTP server that exposes the SupportTicketEnvdirEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

import os
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import TicketAction, TicketObservation
    from .support_ticket_envdir_environment import (
        SupportTicketEnvdirEnvironment,
        set_current_task,
        get_current_task,
        reset_ticket_index
    )
except (ModuleNotFoundError, ImportError):
    from models import TicketAction, TicketObservation
    from server.support_ticket_envdir_environment import (
        SupportTicketEnvdirEnvironment,
        set_current_task,
        get_current_task,
        reset_ticket_index
    )


# --- Gradio UI Logic ---

def create_gradio_ui():
    """Creates a professional, modern UI for the Support Ticket Environment."""
    
    # Enhanced CSS for professional competition-ready UI
    css = """
    .main-container { max-width: 1400px; margin: auto; padding: 20px; }
    
    /* Ticket Card Styling */
    .ticket-card { 
        padding: 28px; 
        border-radius: 16px; 
        border-left: 8px solid #1890ff; 
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); 
        box-shadow: 0 8px 32px rgba(0,0,0,0.12); 
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    .ticket-card::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 150px; height: 150px;
        background: linear-gradient(135deg, transparent 50%, rgba(24,144,255,0.03) 50%);
        border-radius: 0 0 0 100%;
    }
    .ticket-card h4 { margin-top: 0; color: #1f1f1f; font-size: 0.85em; letter-spacing: 1px; }
    .ticket-card h3 { margin: 0 0 18px 0; color: #262626; font-size: 1.4em; line-height: 1.4; }
    .ticket-card p { font-size: 1.05em; color: #434343; line-height: 1.7; }
    
    /* Enhanced Badge Styling */
    .badge-container { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .badge { 
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px; 
        border-radius: 24px; 
        font-weight: 700; 
        font-size: 0.7em; 
        text-transform: uppercase;
        letter-spacing: 0.8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        border: 2px solid;
    }
    /* Tier Badges */
    .badge-bronze { background: linear-gradient(135deg, #fff2e8, #fff7f0); color: #ad4e00; border-color: #ffa940; }
    .badge-silver { background: linear-gradient(135deg, #f5f5f5, #fafafa); color: #434343; border-color: #bfbfbf; }
    .badge-gold { background: linear-gradient(135deg, #fffbe6, #fffef0); color: #ad8b00; border-color: #fadb14; }
    .badge-platinum { background: linear-gradient(135deg, #e6f7ff, #f0faff); color: #0050b3; border-color: #40a9ff; }
    
    /* Priority Badges */
    .badge-high { background: linear-gradient(135deg, #fff1f0, #fff5f5); color: #a8071a; border-color: #ff4d4f; }
    .badge-medium { background: linear-gradient(135deg, #fff7e6, #fffbf0); color: #ad6800; border-color: #ffa940; }
    .badge-low { background: linear-gradient(135deg, #f6ffed, #fafff5); color: #237804; border-color: #73d13d; }
    
    /* Sentiment Badges */
    .badge-frustrated { background: linear-gradient(135deg, #fff1f0, #fff5f5); color: #cf1322; border-color: #ff7875; font-weight: 800; }
    .badge-neutral { background: linear-gradient(135deg, #e6f7ff, #f0faff); color: #096dd9; border-color: #69c0ff; }
    .badge-happy { background: linear-gradient(135deg, #f6ffed, #fafff5); color: #389e0d; border-color: #95de64; }
    
    /* Difficulty Badge */
    .badge-easy { background: linear-gradient(135deg, #f6ffed, #fafff5); color: #237804; border-color: #73d13d; }
    .badge-medium { background: linear-gradient(135deg, #fff7e6, #fffbf0); color: #ad6800; border-color: #ffa940; }
    .badge-hard { background: linear-gradient(135deg, #fff1f0, #fff5f5); color: #a8071a; border-color: #ff4d4f; }
    
    /* Escalation Badge */
    .escalation-badge { 
        background: linear-gradient(135deg, #cf1322, #ff4d4f); 
        color: white; 
        border-color: #ff7875; 
        font-weight: 800; 
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(207, 19, 34, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(207, 19, 34, 0); }
    }
    
    /* History Table */
    .history-section { margin-top: 35px; }
    .history-table { 
        border-radius: 12px; 
        overflow: hidden; 
        border: 1px solid #e8e8e8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .history-header {
        background: linear-gradient(135deg, #f5f5f5, #fafafa);
        padding: 16px 20px;
        font-weight: 700;
        color: #262626;
        border-bottom: 2px solid #e8e8e8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Reward Display */
    .reward-panel {
        background: linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%);
        padding: 24px;
        border-radius: 16px;
        border: 2px solid #91d5ff;
        text-align: center;
    }
    .reward-value { 
        font-size: 3.2em; 
        font-weight: 900; 
        background: linear-gradient(135deg, #1d39c4, #1890ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
    }
    .reward-label { color: #595959; font-size: 0.9em; font-weight: 600; letter-spacing: 1px; }
    
    /* Progress Bar */
    .progress-container {
        background: #f5f5f5;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }
    .progress-bar-bg {
        background: #d9d9d9;
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
        margin: 10px 0;
    }
    .progress-bar-fill {
        background: linear-gradient(90deg, #52c41a, #95de64);
        height: 100%;
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    .progress-text {
        display: flex;
        justify-content: space-between;
        font-size: 0.9em;
        color: #595959;
        font-weight: 600;
    }
    
    /* Status Banners */
    .status-banner { 
        padding: 14px 24px; 
        border-radius: 12px; 
        font-weight: 700; 
        margin-top: 18px; 
        text-align: center;
        font-size: 1.05em;
    }
    .status-progress { 
        background: linear-gradient(135deg, #e6f7ff, #f0faff); 
        color: #096dd9; 
        border: 2px solid #91d5ff; 
    }
    .status-success { 
        background: linear-gradient(135deg, #f6ffed, #fafff5); 
        color: #389e0d; 
        border: 2px solid #b7eb8f; 
    }
    .status-learning { 
        background: linear-gradient(135deg, #fffbe6, #fffef0); 
        color: #ad8b00; 
        border: 2px solid #ffe58f; 
    }
    
    /* Action Feedback */
    .feedback-box {
        background: #fafafa;
        border-left: 4px solid #1890ff;
        padding: 16px 20px;
        margin-top: 15px;
        border-radius: 0 8px 8px 0;
        font-size: 0.95em;
        color: #434343;
    }
    
    /* Step Counter */
    .step-counter {
        font-size: 1.4em;
        font-weight: 800;
        color: #262626;
    }
    .step-total {
        color: #8c8c8c;
        font-weight: 500;
    }
    """

    with gr.Blocks(css=css, title="Support Ticket Routing AI") as ui:
        # State to store env and history
        env_state = gr.State(lambda: SupportTicketEnvdirEnvironment())
        history_state = gr.State([])

        with gr.Column(elem_classes="main-container"):
            gr.HTML("""
                <div style='text-align: center; margin-bottom: 30px;'>
                    <h1 style='font-size: 2.5em; margin-bottom: 5px; color: #1f1f1f;'>🎫 Support Ticket Routing AI</h1>
                    <p style='font-size: 1.1em; color: #595959;'>Meta PyTorch OpenEnv Hackathon 2026 Submission</p>
                    <div style='height: 4px; width: 60px; background: #1890ff; margin: 20px auto;'></div>
                </div>
            """)

            with gr.Row(variant="compact"):
                with gr.Column(scale=2):
                    with gr.Group():
                        gr.HTML("<h3 style='margin-bottom: 15px;'>📋 Ticket Observation</h3>")
                        ticket_info = gr.HTML("<div class='ticket-card'>Initializing environment...</div>")
                        
                        with gr.Row():
                            with gr.Column():
                                gr.HTML("<div class='progress-info'>Cumulative Reward</div>")
                                reward_display = gr.HTML("<div class='reward-value'>$0.00</div>")
                            with gr.Column():
                                gr.HTML("<div class='progress-info'>Episode Progress</div>")
                                step_text = gr.HTML("<p style='font-size: 1.2em; font-weight: 600; margin: 10px 0;'>Step 0 / 0</p>")
                        
                        status_msg = gr.HTML("<div class='status-banner status-progress'>Status: Ready</div>")

                with gr.Column(scale=1):
                    with gr.Group():
                        gr.HTML("<h3 style='margin-bottom: 15px;'>🎮 Agent Controls</h3>")
                        
                        task_dropdown = gr.Dropdown(
                            choices=["easy_routing", "medium_routing", "hard_routing"],
                            value="easy_routing",
                            label="Task Difficulty",
                            info="Select the difficulty level for the next episode."
                        )
                        
                        gr.HTML("<div style='height: 15px;'></div>")
                        
                        dept_dropdown = gr.Dropdown(
                            choices=["Billing", "Technical", "Shipping", "Returns", "General"],
                            value="General",
                            label="Target Department",
                            info="Route the ticket to this department."
                        )
                        
                        confidence_slider = gr.Slider(0.0, 1.0, value=0.9, label="Confidence Score", step=0.05)
                        reasoning_input = gr.Textbox(placeholder="Reasoning for routing decision...", label="Agent Reasoning (Optional)")
                        
                        with gr.Row():
                            step_btn = gr.Button("Execute Step 🚀", variant="primary", scale=2)
                            reset_btn = gr.Button("Reset 🔄", variant="secondary", scale=1)

            # Bottom Section: Action History
            gr.HTML("<h3 style='margin-top: 40px; margin-bottom: 15px;'>📜 Interaction History & Feedback</h3>")
            history_table = gr.Dataframe(
                headers=["Step", "Department", "Reward", "Environment Feedback", "Done"],
                datatype=["number", "str", "number", "str", "bool"],
                value=[],
                interactive=False,
                elem_classes="history-table",
                wrap=True
            )

        def format_ticket_html(obs: TicketObservation, history=None):
            """Helper to update UI elements based on observation and history."""
            tier_class = f"badge-{obs.customer_tier.lower()}"
            priority_class = f"badge-{obs.priority.lower()}"
            sentiment_class = f"badge-{obs.sentiment.lower()}"
            difficulty_class = f"badge-{obs.task_difficulty.split('_')[0].lower()}"
            
            # Get emoji for sentiment
            sentiment_emoji = {"happy": "😊", "neutral": "😐", "frustrated": "😤"}.get(obs.sentiment.lower(), "😐")
            tier_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}.get(obs.customer_tier.lower(), "⭐")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(obs.priority.lower(), "⚪")
            
            # Build feedback display if there's history
            feedback_html = ""
            if obs.last_action:
                reward_color = "#52c41a" if obs.last_reward >= 0.5 else "#faad14" if obs.last_reward >= 0.3 else "#ff4d4f"
                feedback_html = f"""
                <div class='feedback-box'>
                    <strong>Last Action:</strong> {obs.last_action} → 
                    <span style='color: {reward_color}; font-weight: 700;'>Reward: {obs.last_reward:.2f}</span><br>
                    <strong>Feedback:</strong> {obs.reward_reason}
                </div>
                """
            
            # CLV Tier bonus indicator
            clv_html = ""
            if obs.customer_tier.lower() in ["gold", "platinum"]:
                bonus = {"gold": "+0.02", "platinum": "+0.03"}.get(obs.customer_tier.lower(), "")
                clv_html = f"""
                <div style='margin-top: 10px; padding: 8px 12px; background: linear-gradient(135deg, #e6f7ff, #f0faff); 
                           border-left: 3px solid #1890ff; border-radius: 6px; color: #0050b3; font-size: 0.85em;'>
                    💎 <strong>CLV Bonus Available:</strong> Correct routing of {obs.customer_tier.upper()} customer earns {bonus} bonus
                </div>
                """
            
            # Escalation warning
            escalation_html = ""
            if getattr(obs, 'escalation_triggered', False):
                escalation_html = """
                <div style='margin-top: 15px; padding: 12px 16px; background: linear-gradient(135deg, #fff1f0, #ffccc7); 
                           border-left: 4px solid #ff4d4f; border-radius: 8px; color: #cf1322; font-weight: 600;'>
                    🚨 <strong>TICKET ESCALATED TO MANAGER</strong><br>
                    <span style='font-size: 0.9em; font-weight: normal;'>Wrong routing + Frustrated customer + Low confidence = Escalation penalty applied (-0.10)</span>
                </div>
                """
            elif obs.sentiment.lower() == "frustrated":
                escalation_html = """
                <div style='margin-top: 15px; padding: 10px 14px; background: linear-gradient(135deg, #fffbe6, #fff7e6); 
                           border-left: 4px solid #ffa940; border-radius: 8px; color: #ad6800; font-size: 0.9em;'>
                    ⚠️ <strong>Frustrated Customer</strong> - Requires confidence ≥ 0.7 to avoid escalation!
                </div>
                """
            
            return f"""
            <div class='ticket-card'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;'>
                    <h4 style='color: #8c8c8c; font-size: 0.85em; letter-spacing: 1px;'>🎫 TICKET {obs.ticket_id}</h4>
                    <span class='badge {difficulty_class}'>📊 {obs.task_difficulty.replace('_', ' ').upper()}</span>
                </div>
                <h3>{obs.subject}</h3>
                <p>{obs.body}</p>
                <div class='badge-container'>
                    <span class='badge {tier_class}'>{tier_emoji} {obs.customer_tier.upper()} TIER</span>
                    <span class='badge {priority_class}'>{priority_emoji} {obs.priority.upper()} PRIORITY</span>
                    <span class='badge {sentiment_class}'>{sentiment_emoji} {obs.sentiment.upper()}</span>
                </div>
                {feedback_html}
                {clv_html}
                {escalation_html}
            </div>
            """

        def on_reset(task_name):
            """Handle environment reset."""
            set_current_task(task_name)
            reset_ticket_index()
            new_env = SupportTicketEnvdirEnvironment()
            obs = new_env.reset()
            history = []
            
            ticket_html = format_ticket_html(obs)
            
            # Enhanced reward panel
            reward_html = f"""
            <div class='reward-panel'>
                <div class='reward-label'>CUMULATIVE REWARD</div>
                <div class='reward-value'>0.00</div>
                <div class='progress-container'>
                    <div class='progress-text'><span>Progress</span><span>0%</span></div>
                    <div class='progress-bar-bg'><div class='progress-bar-fill' style='width: 0%'></div></div>
                </div>
            </div>
            """
            
            step_html = f"<div class='step-counter'>Step <span class='step-total'>0 / {obs.max_steps}</span></div>"
            status_html = "<div class='status-banner status-progress'>🚀 New Episode Started - Ready to Route!</div>"
            
            return new_env, history, ticket_html, reward_html, step_html, [], status_html

        def on_step(env, dept, conf, reasoning, history):
            """Handle environment step with enhanced feedback."""
            if env is None:
                return env, history, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            
            # Prevent steps after done
            if history and history[-1][4]:
                return env, history, gr.update(), gr.update(), gr.update(), gr.update(), "<div class='status-banner status-success'>✅ Episode Complete! Reset to start a new ticket.</div>"

            action = TicketAction(department=dept, confidence=conf, reasoning=reasoning)
            obs = env.step(action)
            
            # Add to history with enhanced step info
            new_row = [obs.steps_taken, dept, f"{obs.reward:.2f}", obs.reward_reason, obs.done]
            history.append(new_row)
            
            ticket_html = format_ticket_html(obs, history)
            
            # Calculate cumulative metrics
            cumulative_reward = sum(float(row[2]) for row in history)
            avg_reward = cumulative_reward / len(history) if history else 0
            progress_pct = min(100, (cumulative_reward / (obs.max_steps * 0.72)) * 100)  # Target: 0.72 per step
            
            # Enhanced reward panel with progress
            reward_color = "#52c41a" if avg_reward >= 0.5 else "#faad14" if avg_reward >= 0.3 else "#ff4d4f"
            reward_html = f"""
            <div class='reward-panel'>
                <div class='reward-label'>CUMULATIVE REWARD</div>
                <div class='reward-value' style='background: linear-gradient(135deg, {reward_color}, {reward_color}); -webkit-background-clip: text;'>{cumulative_reward:.2f}</div>
                <div style='font-size: 0.85em; color: #8c8c8c; margin-bottom: 10px;'>Avg: {avg_reward:.2f} per step</div>
                <div class='progress-container'>
                    <div class='progress-text'><span>Episode Progress</span><span>{progress_pct:.0f}%</span></div>
                    <div class='progress-bar-bg'><div class='progress-bar-fill' style='width: {progress_pct:.0f}%'></div></div>
                </div>
            </div>
            """
            
            step_html = f"<div class='step-counter'>Step <span class='step-total'>{obs.steps_taken} / {obs.max_steps}</span></div>"
            
            # Dynamic status based on reward quality
            if obs.done:
                if avg_reward >= 0.5:
                    status_html = f"<div class='status-banner status-success'>🎉 SUCCESS! Final Score: {cumulative_reward:.2f} (Avg: {avg_reward:.2f})</div>"
                else:
                    status_html = f"<div class='status-banner status-learning'>📚 Episode Complete. Score: {cumulative_reward:.2f} - Review feedback to improve!</div>"
            else:
                if obs.reward >= 0.5:
                    status_html = "<div class='status-banner status-success'>✅ Strong move! Good routing decision.</div>"
                elif obs.reward >= 0.3:
                    status_html = "<div class='status-banner status-learning'>⚡ Partial credit - getting closer!</div>"
                else:
                    status_html = "<div class='status-banner status-progress'>🔄 Learning... Check the feedback below.</div>"
            
            return env, history, ticket_html, reward_html, step_html, history, status_html

        # Wire up events
        reset_btn.click(
            on_reset,
            inputs=[task_dropdown],
            outputs=[env_state, history_state, ticket_info, reward_display, step_text, history_table, status_msg]
        )
        
        step_btn.click(
            on_step,
            inputs=[env_state, dept_dropdown, confidence_slider, reasoning_input, history_state],
            outputs=[env_state, history_state, ticket_info, reward_display, step_text, history_table, status_msg]
        )
        
        # Initial Reset on Load
        ui.load(
            on_reset,
            inputs=[task_dropdown],
            outputs=[env_state, history_state, ticket_info, reward_display, step_text, history_table, status_msg]
        )

    return ui


# --- FastAPI Application Setup ---

# Create the standard OpenEnv app for API compatibility
app = create_app(
    SupportTicketEnvdirEnvironment,
    TicketAction,
    TicketObservation,
    env_name="support-ticket-envdir-v2",
    max_concurrent_envs=1,
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remove OpenEnv's default UI routes to prevent override
# OpenEnv's create_app mounts its own generic UI at /
# We want to serve our custom Gradio UI instead
import logging
logger = logging.getLogger(__name__)

# API endpoints we need to preserve
API_ENDPOINTS = {"/reset", "/step", "/state", "/schema", "/openapi.json", "/docs", "/redoc"}

routes_to_remove = []
logger.info(f"Total routes before cleanup: {len(app.routes)}")

for route in app.routes:
    if hasattr(route, 'path'):
        path = route.path
        # Keep API endpoints
        if path in API_ENDPOINTS or path.startswith("/api"):
            continue
        # Remove root path GET handler (but keep for mounting Gradio)
        if path == "/":
            if hasattr(route, 'methods') and 'GET' in (route.methods or []):
                routes_to_remove.append(route)
                logger.info(f"Removing root GET route: {getattr(route, 'name', 'unknown')}")
        # Remove any UI-specific paths
        elif "ui" in path.lower() or "interface" in path.lower():
            routes_to_remove.append(route)
            logger.info(f"Removing UI route: {path}")

# Remove found routes
for route in routes_to_remove:
    try:
        app.routes.remove(route)
        logger.info(f"Removed route: {getattr(route, 'path', 'unknown')}")
    except ValueError:
        pass

logger.info(f"Routes after cleanup: {len(app.routes)}")

# Create and mount Gradio UI
# Hugging Face Spaces routes traffic through /web path
gradio_ui = create_gradio_ui()
app = gr.mount_gradio_app(app, gradio_ui, path="/web")
logger.info("Gradio UI mounted at /web")


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
