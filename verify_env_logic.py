
import sys
import os

# Add current directory to path to handle imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.support_ticket_envdir_environment import SupportTicketEnvdirEnvironment
from models import TicketAction

def test_environment():
    print("Initializing environment...")
    env = SupportTicketEnvdirEnvironment()
    
    print("Resetting environment...")
    obs = env.reset()
    print(f"Observation: {obs.subject} (ID: {obs.ticket_id})")
    
    print("Taking a step with action 'Technical'...")
    action = TicketAction(department="Technical", confidence=0.9, reasoning="Testing")
    result_obs = env.step(action)
    print(f"Step Result - Reward: {result_obs.reward}, Done: {result_obs.done}")
    print(f"Last Action: {result_obs.last_action}, Last Reward: {result_obs.last_reward}")
    
    print("Environment test completed successfully!")

if __name__ == "__main__":
    try:
        test_environment()
    except Exception as e:
        print(f"Error during environment test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
