"""
Main orchestrator for MindAware Agent system.
Runs the agent loop with simulators and API server.
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.agent import CognitivePolicy, DroneTools, DecisionLogger, AgentMemory, LLMAgent
from src.sim import EEGSimulator, DroneSimulator
from src.sim.eeg_adapter import RealEEGAdapter, get_adapter
from src.api import setup_websocket_routes, broadcast_cognitive_state, broadcast_decision, broadcast_telemetry


class MindAwareAgent:
    """Main agent orchestrator."""
    
    def __init__(self, scenario: str = "normal", use_llm: bool = False, use_real_eeg: bool = False):
        """
        Initialize the agent system.
        
        Args:
            scenario: EEG simulation scenario (if not using real EEG)
            use_llm: Whether to use LLM reasoning (requires API key)
            use_real_eeg: Whether to use real EEG hardware (via API ingestion)
        """
        print("[INIT] Initializing MindAware Agent...")
        
        # Core components
        self.policy = CognitivePolicy()
        self.tools = DroneTools()
        self.logger = DecisionLogger()
        self.memory = AgentMemory()
        self.use_llm = use_llm
        self.use_real_eeg = use_real_eeg
        
        # Initialize voice confirmation (independent of LLM)
        try:
            from agent.voice_confirmer import VoiceConfirmer
            self.voice_confirmer = VoiceConfirmer()
            print("[INIT] Voice confirmation system initialized")
        except Exception as e:
            print(f"[INIT] Voice confirmation unavailable: {e}")
            self.voice_confirmer = None
        
        if use_llm:
            try:
                self.llm_agent = LLMAgent(self.tools, self.memory)
                print("[INIT] LLM agent enabled (using OpenAI API)")
            except ValueError as e:
                print(f"[INIT] Could not initialize LLM agent: {e}")
                print("[INIT] Falling back to policy-only mode")
                self.llm_agent = None
                self.use_llm = False
        else:
            self.llm_agent = None
            print("[INIT] Running in policy-only mode (no LLM)")
        
        # EEG Source (real hardware or simulator)
        if use_real_eeg:
            self.eeg_sim = get_adapter()
            print("[INIT] 🔴 Real EEG mode enabled - waiting for data from hardware")
            print("[INIT] Partner should POST to /eeg/ingest endpoint")
        else:
            self.eeg_sim = EEGSimulator(scenario=scenario)
            print(f"[INIT] EEG simulator: {scenario} scenario")
        
        # Drone simulator
        self.drone_sim = DroneSimulator()
        
        print("[INIT] Drone simulator: ready")
        print("[INIT] Agent initialization complete\n")
    
    def process_cognitive_state(self, cognitive_state: dict) -> dict:
        """
        Process a cognitive state through the agent pipeline.
        
        Args:
            cognitive_state: Dict with focus, fatigue, overload, stress
        
        Returns:
            Decision dictionary
        """
        # Add to memory
        self.memory.add_cognitive_state(cognitive_state)
        
        # Get policy recommendations
        policy_result = self.policy.evaluate(cognitive_state)
        
        print(f"\n[POLICY] Severity: {policy_result['severity']}")
        print(f"[POLICY] Recommendations: {len(policy_result['recommendations'])}")
        
        # GUARD: If normal operation with no recommendations, maintain current state
        if policy_result['severity'] == 'normal' and len(policy_result['recommendations']) == 0:
            print("[AGENT] Normal operation - maintaining current state, no actions needed")
            
            decision = {
                "cognitive_state": cognitive_state,
                "policy_recommendations": [],
                "llm_reasoning": "Normal operation - maintaining current state",
                "actions_taken": [],
                "model": "policy_guard",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Log decision
            self.logger.log_decision(decision)
            self.memory.add_decision(decision)
            
            return decision
        
        # Decide using LLM or policy
        if self.use_llm and self.llm_agent:
            decision = self.llm_agent.reason_about_state(
                cognitive_state,
                policy_result["recommendations"]
            )
        else:
            # Fallback to policy-only mode (but still with voice confirmation if enabled)
            actions_taken = []
            
            for rec in policy_result["recommendations"][:2]:  # Take top 2
                # Voice handling: inform for takeoff, confirm for landing
                if self.voice_confirmer and self.voice_confirmer.enabled:
                    action = rec["action"]
                    is_urgent = rec.get("urgent", False)
                    
                    if action == "takeoff" and is_urgent:
                        # Automatic takeoff - just inform pilot
                        self.voice_confirmer.inform_pilot(action, cognitive_state)
                    elif action == "land" and not is_urgent:
                        # Landing requires confirmation
                        print(f"[VOICE] Requesting confirmation for: {action}")
                        
                        confirmed = self.voice_confirmer.ask_confirmation(
                            action=action,
                            context=cognitive_state
                        )
                        
                        if not confirmed:
                            print(f"[VOICE] User denied {action}")
                            actions_taken.append({
                                "tool": action,
                                "arguments": rec.get("parameters", {}),
                                "result": {"cancelled": True, "reason": "User denied via voice"},
                                "reason": rec["reason"],
                                "voice_confirmed": False
                            })
                            continue  # Skip this action
                        
                        print(f"[VOICE] User confirmed {action}")
                    elif is_urgent:
                        # Other urgent actions bypass voice
                        print(f"[VOICE] Bypassing voice for urgent action: {action}")
                
                # Execute the tool
                result = self.tools.execute_tool(rec["action"], rec.get("parameters", {}))
                actions_taken.append({
                    "tool": rec["action"],
                    "arguments": rec.get("parameters", {}),
                    "result": result,
                    "reason": rec["reason"],
                    "voice_confirmed": self.voice_confirmer.enabled if self.voice_confirmer else False
                })
            
            decision = {
                "cognitive_state": cognitive_state,
                "policy_recommendations": policy_result["recommendations"],
                "llm_reasoning": "Policy-only mode (no LLM)",
                "actions_taken": actions_taken,
                "model": "policy_only",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Log decision
        self.logger.log_decision(decision)
        self.memory.add_decision(decision)
        
        # Store drone command for partner's hardware
        if decision['actions_taken']:
            from src.api.eeg_ingestion import set_latest_drone_command
            
            # Get the primary action (should only be one in binary mode)
            primary_action = decision['actions_taken'][0]
            command = primary_action['tool']
            
            set_latest_drone_command(
                command=command,
                reasoning=decision['llm_reasoning'],
                metadata={
                    'cognitive_state': cognitive_state,
                    'altitude': primary_action['result'].get('new_altitude_m'),
                    'rotation': primary_action['result'].get('new_rotation_deg')
                }
            )
            print(f"[DRONE] Command stored: {command}")
        else:
            from src.api.eeg_ingestion import set_latest_drone_command
            set_latest_drone_command(
                command='maintain',
                reasoning='Normal operation - no action needed',
                metadata={'cognitive_state': cognitive_state}
            )
        
        print(f"[DECISION] Actions taken: {len(decision['actions_taken'])}")
        
        return decision
    
    async def _broadcast_updates(self, cognitive_state: dict, telemetry: dict, decision: dict):
        """Broadcast updates to WebSocket clients."""
        from src.api.websocket import broadcast_cognitive_state, broadcast_decision, broadcast_telemetry
        
        try:
            await broadcast_cognitive_state(cognitive_state)
            await broadcast_telemetry(telemetry)
            await broadcast_decision(decision)
        except Exception as e:
            # Silently skip if WebSocket not available
            pass
    
    def run_simulation_loop(self, iterations: int = 20, interval: float = 3.0):
        """
        Run the simulation loop.
        
        Args:
            iterations: Number of iterations to run
            interval: Seconds between iterations
        """
        print(f"\n{'='*60}")
        print("STARTING SIMULATION LOOP")
        print(f"{'='*60}\n")
        
        for i in range(iterations):
            print(f"\n{'─'*60}")
            print(f"ITERATION {i+1}/{iterations}")
            print(f"{'─'*60}")
            
            # Get simulated EEG state
            cognitive_state = self.eeg_sim.get_cognitive_state()
            print(f"\n[EEG] Focus: {cognitive_state['focus']:.3f} | "
                  f"Fatigue: {cognitive_state['fatigue']:.3f} | "
                  f"Overload: {cognitive_state['overload']:.3f} | "
                  f"Stress: {cognitive_state['stress']:.3f}")
            
            # Get drone telemetry
            telemetry = self.drone_sim.get_telemetry()
            print(f"[DRONE] Altitude: {telemetry['altitude_m']:.2f}m | "
                  f"Rotation: {telemetry['rotation_deg']:.0f}° | "
                  f"Battery: {telemetry['battery']}%")
            
            # Process through agent
            decision = self.process_cognitive_state(cognitive_state)
            
            # Update drone based on actions
            if decision['actions_taken']:
                for action in decision['actions_taken']:
                    # Update drone simulator to match tool actions
                    if action['tool'] in ['takeoff', 'land']:
                        new_altitude = action['result'].get('new_altitude_m', 0)
                        self.drone_sim.update_altitude(new_altitude)
                    elif action['tool'] == 'yaw_right':
                        new_rotation = action['result'].get('new_rotation_deg', 0)
                        self.drone_sim.update_rotation(new_rotation)
            
            # Broadcast to WebSocket (run in background)
            asyncio.run(self._broadcast_updates(cognitive_state, telemetry, decision))
            
            print(f"\n[STATUS] Altitude: {self.drone_sim.get_altitude():.2f}m | "
                  f"Rotation: {self.drone_sim.get_rotation():.0f}°")
            print(f"[STATUS] Memory: {len(self.memory.cognitive_history)} states, "
                  f"{len(self.memory.decision_history)} decisions")
            
            # Sleep between iterations
            if i < iterations - 1:
                time.sleep(interval)
        
        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE")
        print(f"{'='*60}\n")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print a summary of the simulation."""
        context = self.memory.get_context_summary()
        recent_decisions = self.logger.get_recent_decisions(5)
        
        print("\nSUMMARY:")
        print(f"  Total states processed: {context['state_count']}")
        print(f"  Total decisions made: {context['decision_count']}")
        print(f"  Total actions taken: {len(self.tools.action_history)}")
        print(f"  Final altitude: {self.tools.current_altitude:.2f}m")
        print(f"\nRecent decisions logged to: data/logs/decisions.jsonl\n")


async def run_with_websocket(agent: MindAwareAgent, iterations: int = 20, interval: float = 3.0):
    """
    Run agent loop with WebSocket broadcasting.
    
    Args:
        agent: MindAwareAgent instance
        iterations: Number of iterations
        interval: Seconds between iterations
    """
    print("\n[WS] WebSocket broadcasting enabled")
    
    for i in range(iterations):
        print(f"\n{'─'*60}")
        print(f"ITERATION {i+1}/{iterations}")
        print(f"{'─'*60}")
        
        # Get states
        cognitive_state = agent.eeg_sim.get_cognitive_state()
        
        print(f"\n[EEG] Focus: {cognitive_state['focus']:.3f} | "
              f"Fatigue: {cognitive_state['fatigue']:.3f}")
        
        # Process decision
        decision = agent.process_cognitive_state(cognitive_state)
        
        # Update drone based on actions
        if decision['actions_taken']:
            for action in decision['actions_taken']:
                if action['tool'] in ['takeoff', 'land']:
                    new_altitude = action['result'].get('new_altitude_m', 0)
                    agent.drone_sim.update_altitude(new_altitude)
                elif action['tool'] == 'yaw_right':
                    new_rotation = action['result'].get('new_rotation_deg', 0)
                    agent.drone_sim.update_rotation(new_rotation)
        
        # Get updated telemetry
        telemetry = agent.drone_sim.get_telemetry()
        
        # Broadcast to connected clients
        await broadcast_cognitive_state(cognitive_state)
        await broadcast_telemetry(telemetry)
        await broadcast_decision(decision)
        
        # Wait
        await asyncio.sleep(interval)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MindAware Agent System")
    parser.add_argument("--scenario", default="normal", 
                       choices=["normal", "fatigue", "stress", "degrading"],
                       help="EEG simulation scenario")
    parser.add_argument("--iterations", type=int, default=10,
                       help="Number of simulation iterations")
    parser.add_argument("--interval", type=float, default=3.0,
                       help="Seconds between iterations")
    parser.add_argument("--llm", action="store_true",
                       help="Enable LLM reasoning (requires OPENAI_API_KEY)")
    parser.add_argument("--real-eeg", action="store_true",
                       help="Use real EEG hardware (data via /eeg/ingest API)")
    parser.add_argument("--no-sim", action="store_true",
                       help="Skip simulation (for API-only mode)")
    
    args = parser.parse_args()
    
    # Check for API key if LLM mode
    if args.llm:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️  WARNING: OPENAI_API_KEY not set")
            print("   LLM reasoning will fall back to policy-only mode")
            print("   Set your API key: export OPENAI_API_KEY=sk-...\n")
    
    # Create agent
    try:
        agent = MindAwareAgent(
            scenario=args.scenario, 
            use_llm=args.llm,
            use_real_eeg=args.real_eeg
        )
    except ValueError as e:
        print(f"\n❌ Error initializing agent: {e}")
        print("   Falling back to policy-only mode\n")
        agent = MindAwareAgent(
            scenario=args.scenario, 
            use_llm=False,
            use_real_eeg=args.real_eeg
        )
    
    # Run simulation if not skipped
    if not args.no_sim:
        agent.run_simulation_loop(
            iterations=args.iterations,
            interval=args.interval
        )
    else:
        print("\n[INFO] Simulation skipped. Agent ready for API requests.")
        print("[INFO] Use POST /agent endpoint to process cognitive states.")


if __name__ == "__main__":
    main()

