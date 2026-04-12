"""
Standalone Gradio UI for Support Ticket Environment.
This runs as the main Hugging Face Space entry point.
"""
import gradio as gr
from server.support_ticket_envdir_environment import (
    SupportTicketEnvdirEnvironment, 
    set_current_task, 
    reset_ticket_index
)
from models import TicketAction, TicketObservation

# Enhanced CSS for professional UI
css = """
.ticket-card {
    background: linear-gradient(135deg, #ffffff, #f8f9fa);
    border-radius: 12px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-left: 5px solid #1890ff;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.ticket-card h3 {
    color: #1f1f1f;
    margin-bottom: 12px;
    font-size: 1.3em;
    font-weight: 600;
}
.ticket-card p {
    color: #595959;
    line-height: 1.6;
    margin-bottom: 16px;
}
.badge-container {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 12px;
}
.badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.8em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-tier-platinum { background: linear-gradient(135deg, #e6f7ff, #bae7ff); color: #0050b3; border: 1px solid #91d5ff; }
.badge-tier-gold { background: linear-gradient(135deg, #fff7e6, #ffe7ba); color: #ad6800; border: 1px solid #ffd591; }
.badge-tier-silver { background: linear-gradient(135deg, #f6ffed, #d9f7ba); color: #389e0d; border: 1px solid #b7eb8f; }
.badge-tier-bronze { background: linear-gradient(135deg, #fff2e8, #ffdbba); color: #873800; border: 1px solid #ffbb96; }
.badge-priority-high { background: #ff4d4f; color: white; }
.badge-priority-medium { background: #faad14; color: white; }
.badge-priority-low { background: #52c41a; color: white; }
.badge-sentiment-frustrated { background: #ff4d4f; color: white; animation: pulse 2s infinite; }
.badge-sentiment-neutral { background: #8c8c8c; color: white; }
.badge-sentiment-happy { background: #52c41a; color: white; }
.badge-difficulty-easy { background: #52c41a; color: white; }
.badge-difficulty-medium { background: #faad14; color: white; }
.badge-difficulty-hard { background: #ff4d4f; color: white; }
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
.main-container {
    max-width: 1200px;
    margin: 0 auto;
}
.feedback-box {
    margin-top: 16px;
    padding: 14px 18px;
    background: #f6ffed;
    border-radius: 8px;
    border-left: 4px solid #52c41a;
    font-size: 0.95em;
    color: #135200;
}
.feedback-box.error {
    background: #fff2e8;
    border-left-color: #ff4d4f;
    color: #871400;
}
.progress-info {
    font-size: 0.85em;
    color: #8c8c8c;
    margin-bottom: 4px;
}
.reward-value {
    font-size: 1.5em;
    font-weight: 700;
    color: #1890ff;
}
.status-banner {
    padding: 12px 16px;
    border-radius: 8px;
    font-weight: 600;
    margin-top: 16px;
}
.status-success { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.status-error { background: #fff2e8; color: #ff4d4f; border: 1px solid #ffbb96; }
.status-progress { background: #e6f7ff; color: #1890ff; border: 1px solid #91d5ff; }
"""

def format_ticket_html(obs):
    """Format ticket observation as professional HTML."""
    if obs is None:
        return "<div class='ticket-card'>No active ticket. Click Reset to start.</div>"
    
    tier_class = f"badge-tier-{obs.customer_tier.lower()}"
    priority_class = f"badge-priority-{obs.priority.lower()}"
    sentiment_class = f"badge-sentiment-{obs.sentiment.lower()}"
    difficulty_class = f"badge-difficulty-{obs.task_difficulty.split('_')[0].lower()}"
    
    tier_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}.get(obs.customer_tier.lower(), "")
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(obs.priority.lower(), "")
    sentiment_emoji = {"frustrated": "😤", "neutral": "😐", "happy": "😊"}.get(obs.sentiment.lower(), "")
    
    # Build feedback section
    feedback_html = ""
    if hasattr(obs, 'last_action') and obs.last_action:
        reward_color = "#52c41a" if (obs.last_reward or 0) > 0.5 else "#faad14" if (obs.last_reward or 0) > 0.3 else "#ff4d4f"
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

def create_gradio_ui():
    """Creates the professional Gradio UI."""
    
    with gr.Blocks(css=css, title="Support Ticket Routing AI") as ui:
        env_state = gr.State(lambda: SupportTicketEnvdirEnvironment())
        history_state = gr.State([])
        
        with gr.Column(elem_classes="main-container"):
            gr.HTML("""
                <div style='text-align: center; margin-bottom: 30px;'>
                    <h1 style='font-size: 2.5em; margin-bottom: 5px; color: #1f1f1f;'>🎫 Support Ticket Routing AI</h1>
                    <p style='font-size: 1.1em; color: #595959;'>Meta PyTorch OpenEnv Hackathon 2026 - Bangalore Finale</p>
                </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Group():
                        gr.HTML("<h3 style='margin-bottom: 15px;'>📋 Ticket Observation</h3>")
                        ticket_info = gr.HTML("<div class='ticket-card'>Click Reset to load a ticket...</div>")
                        
                        with gr.Row():
                            with gr.Column():
                                gr.HTML("<div class='progress-info'>Cumulative Reward</div>")
                                reward_display = gr.HTML("<div class='reward-value'>0.00</div>")
                            with gr.Column():
                                gr.HTML("<div class='progress-info'>Episode Progress</div>")
                                step_text = gr.HTML("<p style='font-size: 1.2em; font-weight: 600; margin: 10px 0;'>Step 0 / 0</p>")
                        
                        status_msg = gr.HTML("<div class='status-banner status-progress'>Status: Ready - Click Reset to start</div>")
                
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.HTML("<h3 style='margin-bottom: 15px;'>🎮 Agent Controls</h3>")
                        
                        task_dropdown = gr.Dropdown(
                            choices=["easy_routing", "medium_routing", "hard_routing"],
                            value="easy_routing",
                            label="Task Difficulty"
                        )
                        
                        dept_dropdown = gr.Dropdown(
                            choices=["Billing", "Technical", "Shipping", "Returns", "General"],
                            value="General",
                            label="Target Department"
                        )
                        
                        confidence_slider = gr.Slider(0.0, 1.0, value=0.9, label="Confidence Score", step=0.05)
                        reasoning_input = gr.Textbox(placeholder="Reasoning for routing decision...", label="Agent Reasoning (Optional)")
                        
                        with gr.Row():
                            step_btn = gr.Button("Execute Step 🚀", variant="primary")
                            reset_btn = gr.Button("Reset 🔄", variant="secondary")
            
            # Action History
            gr.HTML("<h3 style='margin-top: 40px; margin-bottom: 15px;'>📜 Interaction History & Feedback</h3>")
            history_table = gr.Dataframe(
                headers=["Step", "Department", "Reward", "Environment Feedback", "Done"],
                datatype=["number", "str", "number", "str", "bool"],
                value=[],
                wrap=True
            )
        
        # Event handlers
        def on_reset(task_name):
            set_current_task(task_name)
            reset_ticket_index()
            env = SupportTicketEnvdirEnvironment()
            obs = env.reset(task_name)
            history = []
            
            ticket_html = format_ticket_html(obs)
            reward_val = f"{getattr(obs, 'cumulative_reward', 0.0):.2f}"
            step_str = f"Step {obs.steps_taken} / {obs.max_steps}"
            status = "<div class='status-banner status-progress'>Status: Active - Route the ticket to the correct department</div>"
            
            return env, history, ticket_html, reward_val, step_str, history, status
        
        def on_step(env, dept, conf, reasoning, history):
            if env is None:
                return env, history, gr.update(), gr.update(), gr.update(), gr.update(), "<div class='status-banner status-error'>Error: Environment not initialized. Click Reset first.</div>"
            
            if history and history[-1][4]:  # Done flag
                return env, history, gr.update(), gr.update(), gr.update(), gr.update(), "<div class='status-banner status-success'>✅ Episode Complete! Reset to start a new ticket.</div>"
            
            action = TicketAction(department=dept, confidence=conf, reasoning=reasoning)
            obs = env.step(action)
            
            # Update history
            step_num = obs.steps_taken
            reward = obs.reward or 0.0
            done = obs.done
            reason = obs.reward_reason or "No feedback"
            
            history.append([step_num, dept, round(reward, 2), reason, done])
            
            ticket_html = format_ticket_html(obs)
            reward_val = f"{getattr(obs, 'cumulative_reward', 0.0):.2f}"
            step_str = f"Step {obs.steps_taken} / {obs.max_steps}"
            
            if done:
                status = f"<div class='status-banner status-success'>✅ Episode Complete! Final Score: {getattr(obs, 'cumulative_reward', 0.0):.2f}</div>"
            else:
                status = "<div class='status-banner status-progress'>Status: Active - Continue routing or finish</div>"
            
            return env, history, ticket_html, reward_val, step_str, history, status
        
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
        
        # Auto-load on startup
        ui.load(on_reset, inputs=[task_dropdown], outputs=[env_state, history_state, ticket_info, reward_display, step_text, history_table, status_msg])
    
    return ui

# Create and launch the app
app = create_gradio_ui()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
