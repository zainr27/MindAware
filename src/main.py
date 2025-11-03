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
    
    def __init__(self, scenario: str = "normal", use_llm: bool = True, use_real_eeg: bool = False, drone_base_url: str = None):
        """
        Initialize the agent system.
        
        Args:
            scenario: EEG simulation scenario (if not using real EEG)
            use_llm: Whether to use LLM reasoning (default: True, requires API key)
            use_real_eeg: Whether to use real EEG hardware (via API ingestion)
            drone_base_url: Base URL for drone control API (optional, can also use DRONE_BASE_URL env var)
        """
        print("[INIT] Initializing MindAware Agent...")
        
        # Core components
        self.policy = CognitivePolicy()
        self.tools = DroneTools(drone_base_url=drone_base_url)
        self.logger = DecisionLogger()
        self.memory = AgentMemory()
        self.use_llm = use_llm
        self.use_real_eeg = use_real_eeg
        
        # Initialize voice confirmation (always enabled if available)
        try:
            from src.agent.voice_confirmer import VoiceConfirmer
            self.voice_confirmer = VoiceConfirmer()
            if self.voice_confirmer.enabled:
                print("[INIT] ✅ Voice confirmation system initialized and enabled")
            else:
                print("[INIT] ⚠️  Voice confirmation initialized but disabled")
        except Exception as e:
            print(f"[INIT] ⚠️  Voice confirmation unavailable: {e}")
            self.voice_confirmer = None
        
        # Initialize LLM agent (enabled by default)
        if use_llm:
            try:
                self.llm_agent = LLMAgent(self.tools, self.memory)
                print("[INIT] ✅ LLM agent enabled (using OpenAI API)")
            except ValueError as e:
                print(f"[INIT] ⚠️  Could not initialize LLM agent: {e}")
                print("[INIT] Falling back to policy-only mode")
                self.llm_agent = None
                self.use_llm = False
        else:
            self.llm_agent = None
            print("[INIT] LLM disabled (policy-only mode)")
        
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
        
        # Get policy recommendations (pass current altitude for grounded check)
        current_altitude = self.tools.get_status()["altitude_m"]
        policy_result = self.policy.evaluate(cognitive_state, current_altitude)
        
        print(f"\n[POLICY] Severity: {policy_result['severity']}")
        print(f"[POLICY] Recommendations: {len(policy_result['recommendations'])}")
        
        # GUARD: If normal/grounded operation with no recommendations, maintain current state
        if (policy_result['severity'] in ['normal', 'grounded']) and len(policy_result['recommendations']) == 0:
            if policy_result['severity'] == 'grounded':
                print("[AGENT] 🔴 Drone GROUNDED - Regain focus to fly again")
                # Voice announcement for grounded state
                if self.voice_confirmer:
                    self.voice_confirmer.announce_status(
                        "Drone is grounded. All parameters are critical. Regain focus to fly again."
                    )
            else:
                if current_altitude > 0.1:
                    print("[AGENT] ✈️ Drone is in the air (mixed parameters)")
                    # Voice announcement for in-air status
                    if self.voice_confirmer:
                        self.voice_confirmer.announce_status(
                            "Drone is in the air. Mixed parameters detected. Maintaining altitude."
                        )
                else:
                    print("[AGENT] ⏸️ Drone on ground - waiting for optimal conditions")
                    # Voice announcement for waiting on ground
                    if self.voice_confirmer:
                        self.voice_confirmer.announce_status(
                            "Drone is on the ground. Waiting for optimal conditions to take off."
                        )
            
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
            
            # Apply voice confirmation to LLM decisions
            if self.voice_confirmer and self.voice_confirmer.enabled and decision.get('actions_taken'):
                decision['actions_taken'] = self._apply_voice_confirmation(
                    decision['actions_taken'],
                    cognitive_state
            )
        else:
            # Fallback to policy-only mode (but still with voice confirmation if enabled)
            actions_taken = []
            
            for rec in policy_result["recommendations"][:2]:  # Take top 2
                action = rec["action"]
                is_urgent = rec.get("urgent", False)
                needs_confirmation = True
                
                # CRITICAL: Landing ALWAYS requires confirmation (safety-critical)
                if action == 'land':
                    if self.voice_confirmer and self.voice_confirmer.enabled:
                        print(f"[VOICE] 🔴 SAFETY: Landing requires confirmation")
                        confirmed = self.voice_confirmer.ask_confirmation(
                            action=action,
                            context=cognitive_state
                        )
                        if not confirmed:
                            print(f"[VOICE] ❌ User denied {action}")
                            actions_taken.append({
                                "tool": action,
                                "arguments": rec.get("parameters", {}),
                                "result": {"cancelled": True, "reason": "User denied via voice"},
                                "reason": rec["reason"],
                                "voice_confirmed": False
                            })
                            continue  # Skip executing landing action
                        print(f"[VOICE] ✅ User confirmed {action}")
                        needs_confirmation = True
                    else:
                        # Voice disabled - still require explicit confirmation
                        print(f"\n🔴 ⚠️  WARNING: Low focus detected - Landing requested")
                        print(f"   Voice confirmation disabled. Would land drone.")
                        print(f"   To enable voice confirmation: set VOICE_CONFIRMATION_ENABLED=true in .env")
                        # Don't execute without confirmation
                        actions_taken.append({
                            "tool": action,
                            "arguments": rec.get("parameters", {}),
                            "result": {"cancelled": True, "reason": "Voice confirmation disabled - landing blocked for safety"},
                            "reason": rec["reason"],
                            "voice_confirmed": False
                        })
                        continue  # Skip executing landing action when voice is disabled
                
                # Check voice confirmation for other actions
                elif self.voice_confirmer and self.voice_confirmer.enabled:
                    if is_urgent:
                        print(f"[VOICE] Bypassing confirmation for urgent action: {action}")
                        needs_confirmation = True  # Execute urgent actions (like takeoff)
                    else:
                        print(f"[VOICE] Requesting confirmation for: {action}")
                        confirmed = self.voice_confirmer.ask_confirmation(
                            action=action,
                            context=cognitive_state
                        )
                        if not confirmed:
                            print(f"[VOICE] ❌ User denied {action}")
                            actions_taken.append({
                                "tool": action,
                                "arguments": rec.get("parameters", {}),
                                "result": {"cancelled": True, "reason": "User denied via voice"},
                                "reason": rec["reason"],
                                "voice_confirmed": False
                            })
                            continue  # Skip executing this action
                        print(f"[VOICE] ✅ User confirmed {action}")
                        needs_confirmation = True
                
                # Execute the tool (only if confirmed or urgent)
                if needs_confirmation:
                    result = self.tools.execute_tool(action, rec.get("parameters", {}))
                actions_taken.append({
                        "tool": action,
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
    
    def _apply_voice_confirmation(self, actions_taken: list, cognitive_state: dict) -> list:
        """
        Apply voice confirmation to actions.
        Returns filtered list of confirmed actions.
        
        Args:
            actions_taken: List of actions from decision
            cognitive_state: Current cognitive state for context
            
        Returns:
            List of confirmed actions (denied actions are removed)
        """
        if not self.voice_confirmer or not self.voice_confirmer.enabled:
            return actions_taken
        
        confirmed_actions = []
        
        for action in actions_taken:
            tool_name = action.get('tool', '')
            is_urgent = action.get('result', {}).get('urgent', False)
            
            # CRITICAL: Landing ALWAYS requires confirmation (safety-critical)
            if tool_name == 'land':
                if self.voice_confirmer and self.voice_confirmer.enabled:
                    print(f"[VOICE] 🔴 SAFETY: Landing requires confirmation")
                    confirmed = self.voice_confirmer.ask_confirmation(
                        action=tool_name,
                        context=cognitive_state
                    )
                    
                    if confirmed:
                        print(f"[VOICE] ✅ User confirmed {tool_name}")
                        action['voice_confirmed'] = True
                        confirmed_actions.append(action)
                    else:
                        print(f"[VOICE] ❌ User denied {tool_name}")
                        action['voice_confirmed'] = False
                        action['result'] = {"cancelled": True, "reason": "User denied via voice"}
                        # Still add to list for logging, but mark as cancelled
                        confirmed_actions.append(action)
                else:
                    # Voice disabled - block landing for safety
                    print(f"[VOICE] 🔴 ⚠️  Landing blocked: Voice confirmation disabled")
                    action['voice_confirmed'] = False
                    action['result'] = {"cancelled": True, "reason": "Voice confirmation disabled - landing blocked for safety"}
                    confirmed_actions.append(action)
                continue
            
            # Urgent actions (like takeoff) can bypass confirmation
            if is_urgent:
                print(f"[VOICE] Bypassing confirmation for urgent action: {tool_name}")
                confirmed_actions.append(action)
                continue
            
            # Request confirmation for all other non-urgent actions
            print(f"[VOICE] Requesting confirmation for: {tool_name}")
            
            confirmed = self.voice_confirmer.ask_confirmation(
                action=tool_name,
                context=cognitive_state
            )
            
            if confirmed:
                print(f"[VOICE] ✅ User confirmed {tool_name}")
                action['voice_confirmed'] = True
                confirmed_actions.append(action)
            else:
                print(f"[VOICE] ❌ User denied {tool_name}")
                action['voice_confirmed'] = False
                action['result'] = {"cancelled": True, "reason": "User denied via voice"}
                # Still add to list for logging, but mark as cancelled
                confirmed_actions.append(action)
        
        return confirmed_actions
    
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
                    elif action['tool'] == 'maintain_altitude':
                        # No action needed - altitude maintained
                        pass  # Yaw controlled by EEG
            
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
    
    def run_real_eeg_loop(self, interval: float = 3.0):
        """
        Run continuous loop for real EEG data.
        Processes incoming EEG data from hardware indefinitely.
        
        Args:
            interval: Seconds between processing cycles
        """
        print(f"\n{'='*60}")
        print("STARTING REAL EEG LOOP")
        print(f"{'='*60}\n")
        print("[INFO] Waiting for EEG data from hardware...")
        print("[INFO] Partner should POST to /eeg/ingest endpoint")
        print(f"[INFO] Processing every {interval} seconds\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n{'─'*60}")
                print(f"CYCLE {iteration} - Processing Real EEG Data")
                print(f"{'─'*60}")
                
                # Get cognitive state from real EEG adapter
                cognitive_state = self.eeg_sim.get_cognitive_state()
                
                # Check if we have enough data
                if cognitive_state.get('status') == 'insufficient_data':
                    print(f"[WAIT] Waiting for more EEG data... ({cognitive_state.get('buffer_size', 0)} readings)")
                    time.sleep(interval)
                    continue
                
                print(f"\n[EEG] Focus: {cognitive_state['focus']:.3f} | "
                      f"Fatigue: {cognitive_state['fatigue']:.3f} | "
                      f"Overload: {cognitive_state['overload']:.3f} | "
                      f"Stress: {cognitive_state['stress']:.3f}")
                print(f"[EEG] Calibrated: {cognitive_state.get('calibrated', False)} | "
                      f"Buffer: {cognitive_state.get('buffer_size', 0)} readings")
                
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
                        elif action['tool'] == 'maintain_altitude':
                            # No action needed - altitude maintained
                            pass  # Yaw controlled by EEG
                
                # Broadcast to WebSocket
                asyncio.run(self._broadcast_updates(cognitive_state, telemetry, decision))
                
                print(f"\n[STATUS] Altitude: {self.drone_sim.get_altitude():.2f}m | "
                      f"Rotation: {self.drone_sim.get_rotation():.0f}°")
                print(f"[STATUS] Memory: {len(self.memory.cognitive_history)} states, "
                      f"{len(self.memory.decision_history)} decisions")
                
                # Sleep before next cycle
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print("REAL EEG LOOP STOPPED")
            print(f"{'='*60}\n")
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
                elif action['tool'] == 'maintain_altitude':
                    # No action needed - altitude maintained
                    pass  # Yaw controlled by EEG
        
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
    import threading
    import uvicorn
    
    parser = argparse.ArgumentParser(description="MindAware Agent System")
    parser.add_argument("--scenario", default="normal", 
                       choices=["normal", "fatigue", "stress", "degrading"],
                       help="EEG simulation scenario")
    parser.add_argument("--iterations", type=int, default=10,
                       help="Number of simulation iterations")
    parser.add_argument("--interval", type=float, default=3.0,
                       help="Seconds between iterations")
    parser.add_argument("--no-llm", action="store_true",
                       help="Disable LLM reasoning (default: enabled, requires OPENAI_API_KEY)")
    parser.add_argument("--real-eeg", action="store_true",
                       help="Use real EEG hardware (data via /eeg/ingest API)")
    parser.add_argument("--no-sim", action="store_true",
                       help="Skip simulation (for API-only mode)")
    parser.add_argument("--api-port", type=int, default=8000,
                       help="Port for API server (default: 8000)")
    parser.add_argument("--drone-url", type=str, default=None,
                       help="Base URL for drone control API (e.g., http://192.168.86.139:8080). "
                            "Can also set DRONE_BASE_URL environment variable. "
                            "Defaults to http://192.168.86.139:8080")
    
    args = parser.parse_args()
    
    # Determine LLM usage (enabled by default, disabled with --no-llm)
    use_llm = not args.no_llm
    
    # Check for API key if LLM mode
    if use_llm:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️  WARNING: OPENAI_API_KEY not set")
            print("   LLM reasoning will fall back to policy-only mode")
            print("   Set your API key: export OPENAI_API_KEY=sk-...\n")
    
    # Create agent (LLM enabled by default, voice confirmation always attempted)
    try:
        agent = MindAwareAgent(
            scenario=args.scenario, 
            use_llm=use_llm,
            use_real_eeg=args.real_eeg,
            drone_base_url=args.drone_url
        )
    except ValueError as e:
        print(f"\n❌ Error initializing agent: {e}")
        print("   Falling back to policy-only mode\n")
        agent = MindAwareAgent(
            scenario=args.scenario, 
            use_llm=False,
            use_real_eeg=args.real_eeg,
            drone_base_url=args.drone_url
        )
    
    # Start API server in background thread (for real EEG mode or API-only mode)
    if args.real_eeg or args.no_sim:
        print(f"\n🚀 Starting API server on port {args.api_port}...")
        
        # Share agent's tools instance with API server
        def run_api():
            from src.api import server
            # Replace API's tools instance with agent's (so they share state)
            server.tools = agent.tools
            server.memory = agent.memory
            server.logger = agent.logger
            server.policy = agent.policy
            uvicorn.run(server.app, host="127.0.0.1", port=args.api_port, log_level="info")
        
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        
        # Give API server a moment to start
        time.sleep(2)
        print(f"✅ API server running at http://127.0.0.1:{args.api_port}")
        print(f"   EEG endpoint: http://127.0.0.1:{args.api_port}/eeg/ingest")
        print(f"   Command endpoint: http://127.0.0.1:{args.api_port}/drone/command\n")
    
    # Run simulation if not skipped
    if not args.no_sim:
        if args.real_eeg:
            # Real EEG mode: continuous loop processing hardware data
            agent.run_real_eeg_loop(interval=args.interval)
        else:
            # Simulation mode: fixed iterations
            agent.run_simulation_loop(
                iterations=args.iterations,
                interval=args.interval
            )
    else:
        print("\n[INFO] Simulation skipped. Agent ready for API requests.")
        print("[INFO] Use POST /agent endpoint to process cognitive states.")
        print("[INFO] Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")


if __name__ == "__main__":
    main()

