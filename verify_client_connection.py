
import sys
import os
import asyncio

# Add current directory to path to handle imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Handle the relative import issue in client.py
import client
import models
client.TicketAction = models.TicketAction
client.TicketObservation = models.TicketObservation

from client import SupportTicketEnvdirEnv
from models import TicketAction

async def test_client_connection():
    print("Connecting to the server at http://localhost:8000...")
    # Using http://localhost:8000 as the server is running there
    async with SupportTicketEnvdirEnv(base_url="http://localhost:8000") as client:
        print("Resetting environment via client...")
        result = await client.reset()
        print(f"Initial Observation: {result.observation.subject}")
        
        print("Taking a step with action 'Billing'...")
        action = TicketAction(department="Billing", confidence=0.9, reasoning="Payment issue test")
        step_result = await client.step(action)
        print(f"Step Result - Reward: {step_result.reward}, Done: {step_result.done}")
        print(f"Observation Subject: {step_result.observation.subject}")
        
    print("Client connection test completed successfully!")

if __name__ == "__main__":
    try:
        # Run the async code in a synchronous context for simplicity
        asyncio.run(test_client_connection())
    except Exception as e:
        print(f"Error during client connection test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
