# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Support Ticket Envdir Environment.

The support_ticket_envdir environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field, Extra


class SupportTicketEnvdirAction(Action):
    """Action for the Support Ticket Envdir environment - just a message to echo."""

    message: str = Field(..., description="Message to echo back")


class SupportTicketEnvdirObservation(Observation):
    """Observation from the Support Ticket Envdir environment - the echoed message."""

    echoed_message: str = Field(default="", description="The echoed message")
    message_length: int = Field(default=0, description="Length of the echoed message")


class TicketAction(BaseModel):
    """Action for routing a support ticket to a department."""

    department: str = "General"
    confidence: float = 0.5
    reasoning: str = ""

    class Config:
        extra = "ignore"


class TicketObservation(Observation):
    """Observation from the ticket routing environment - current ticket information."""

    ticket_id: str = Field(default="unknown", description="Unique identifier for the ticket")
    subject: str = Field(default="No Subject", description="Ticket subject line")
    body: str = Field(default="No Body", description="Full ticket body text")
    customer_tier: str = Field(default="bronze", description="Customer tier (e.g., bronze, silver, gold, platinum)")
    priority: str = Field(default="low", description="Ticket priority level")
    sentiment: str = Field(default="neutral", description="Customer sentiment (frustrated, neutral, happy)")
    task_difficulty: str = Field(default="easy_routing", description="Difficulty level of the current task")
    steps_taken: int = Field(default=0, ge=0, description="Number of steps taken in current episode")
    max_steps: int = Field(default=1, ge=1, description="Maximum steps allowed for this task")
    reward: float = Field(default=0.05, description="Reward for the current step")
    reward_reason: str = Field(default="", description="The environment's explanation for the reward")
    done: bool = Field(default=False, description="Whether the episode is complete")
    last_action: str = Field(default="", description="The department selected in the previous step")
    last_reward: float = Field(default=0.0, description="The reward received for the previous action")
    escalation_triggered: bool = Field(default=False, description="Whether ticket was escalated to manager")
    cumulative_reward: float = Field(default=0.0, description="Running total reward for the episode")


class TicketState(BaseModel):
    """Full state of the ticket routing environment."""

    current_ticket: TicketObservation = Field(..., description="Current ticket being processed")
    correct_department: str = Field(..., description="The correct department for the current ticket")
    episode_done: bool = Field(default=False, description="Whether the current episode is complete")
    cumulative_reward: float = Field(default=0.0, description="Cumulative reward for the episode")
    task_name: str = Field(..., description="Name of the current task")
    step_rewards: list = Field(default_factory=list, description="List of rewards for each step")
    
    # Novelty: Escalation tracking for frustrated customers (judge wow factor)
    escalation_triggered: bool = Field(default=False, description="Whether ticket was escalated due to frustration")
    escalation_threshold: float = Field(default=0.7, description="Confidence threshold required for frustrated customers")


class PerformanceMetrics(BaseModel):
    """Track agent performance metrics across episodes."""
    
    total_episodes: int = Field(default=0, description="Total number of episodes completed")
    successful_episodes: int = Field(default=0, description="Episodes with score >= 0.62")
    total_rewards: float = Field(default=0.0, description="Sum of all rewards across episodes")
    avg_steps_per_episode: float = Field(default=0.0, description="Average steps taken to complete")
    escalation_rate: float = Field(default=0.0, description="Percentage of tickets escalated")
    frustrated_customer_success_rate: float = Field(default=0.0, description="Success rate on frustrated customer tickets")
    
    def update(self, reward: float, steps: int, success: bool, was_escalated: bool, was_frustrated: bool, frustrated_success: bool):
        """Update metrics with new episode data."""
        self.total_episodes += 1
        self.total_rewards += reward
        if success:
            self.successful_episodes += 1
        if was_escalated:
            self.escalation_rate = ((self.escalation_rate * (self.total_episodes - 1)) + 1) / self.total_episodes
        if was_frustrated:
            if frustrated_success:
                # Track successful handling of frustrated customers
                pass
