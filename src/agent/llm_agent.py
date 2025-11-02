"""
LLM-powered agent for advanced reasoning about cognitive states.
"""

import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
# from .voice_confirmer import VoiceConfirmer  # Not implemented yet


class LLMAgent:
    """Agent using OpenAI API for reasoning about pilot cognitive state."""
    
    def __init__(self, tools_instance, memory_instance):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it with: export OPENAI_API_KEY=sk-..."
            )
        self.client = OpenAI(api_key=api_key)
        self.tools = tools_instance
        self.memory = memory_instance
        self.model = "gpt-4-turbo-preview"
        
        # Initialize voice confirmation system
        try:
            self.voice_confirmer = VoiceConfirmer()
            print(f"[LLM] Voice confirmation system initialized")
        except Exception as e:
            print(f"[LLM] Warning: Voice confirmation unavailable: {e}")
            self.voice_confirmer = None
    
    def reason_about_state(
        self,
        cognitive_state: Dict[str, Any],
        policy_recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM to reason about cognitive state and decide on actions.
        
        Args:
            cognitive_state: Current cognitive metrics
            policy_recommendations: Rule-based policy recommendations
        
        Returns:
            Decision dictionary with actions and reasoning
        """
        # GUARD: If no policy recommendations, maintain current state
        if len(policy_recommendations) == 0:
            print("[LLM] No policy recommendations - maintaining current state")
            return {
                "cognitive_state": cognitive_state,
                "policy_recommendations": [],
                "llm_reasoning": "No policy recommendations - maintaining current state, no actions needed",
                "actions_taken": [],
                "model": "llm_guard"
            }
        
        # Get context from memory
        context = self.memory.get_context_summary()
        
        # Build system prompt
        system_prompt = """You are an AI assistant monitoring a drone operator's cognitive state via EEG.
The drone provides binary altitude control based SOLELY on FOCUS level.

PARTNER'S DRONE COMMANDS: ["TAKEOFF", "LAND", "FLAND"]
YAW is controlled passively by the EEG (head turning left/right), NOT by commands.

CRITICAL: FOCUS IS THE ONLY DETERMINANT FOR ALTITUDE CONTROL
- HIGH FOCUS (≥0.6) → takeoff() to 1m [maps to TAKEOFF]
- LOW FOCUS (≤0.4) in air → land() to ground [maps to LAND]
- LOW FOCUS (≤0.4) on ground → No action (display "GROUNDED - Regain focus to fly")
- MID FOCUS (0.4 < focus < 0.6) → No action (maintain altitude)

OTHER METRICS (fatigue, overload, stress):
- These are MONITORED and DISPLAYED for operator awareness
- They DO NOT affect takeoff/land decisions
- Only mention them for context, not as decision factors

You have access to exactly TWO tools:
- takeoff: Binary takeoff to 1 meter when focus ≥0.6 → executes TAKEOFF step
- land: Binary landing to ground (0m) when focus ≤0.4 in air → executes LAND step

DECISION RULES:
1. You will ONLY be called when policy recommendations are provided.
2. Follow the policy recommendations - they already checked FOCUS level.
3. Use takeoff() ONLY when focus ≥0.6 (not based on other metrics).
4. Use land() ONLY when focus ≤0.4 AND drone is in the air.
5. Do NOT command actions for mid-range focus - just note "drone is in the air" if airborne.
6. Mention other metrics (fatigue/overload/stress) for context, but emphasize focus is the decision factor.

The drone provides clear visual feedback: at 1m = high focus, at ground = low focus."""
        
        # Build user message with context
        user_message = f"""Current Cognitive State:
- Focus: {cognitive_state.get('focus', 0):.2f}
- Fatigue: {cognitive_state.get('fatigue', 0):.2f}
- Overload: {cognitive_state.get('overload', 0):.2f}
- Stress: {cognitive_state.get('stress', 0):.2f}

Policy Recommendations:
{json.dumps(policy_recommendations, indent=2)}

Recent Context:
- States processed: {context.get('state_count', 0)}
- Decisions made: {context.get('decision_count', 0)}
- Recent states: {json.dumps(context.get('recent_states', []), indent=2)}

Based on this information, decide what actions to take (if any) and explain your reasoning."""
        
        try:
            # Call OpenAI API with function calling
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # Process function calls WITH VOICE CONFIRMATION
            actions_taken = []
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # NEW: Voice handling - inform for takeoff, confirm for landing
                    if self.voice_confirmer and self.voice_confirmer.enabled:
                        # Check if this is takeoff (automatic) or landing (requires confirmation)
                        is_takeoff = function_name == "takeoff"
                        requires_confirmation = self._requires_confirmation(function_name, policy_recommendations)
                        
                        if is_takeoff and not requires_confirmation:
                            # Automatic takeoff - just inform pilot
                            self.voice_confirmer.inform_pilot(function_name, cognitive_state)
                        elif requires_confirmation:
                            # Landing or other actions that need confirmation
                            print(f"[VOICE] Requesting confirmation for: {function_name}")
                            
                            confirmed = self.voice_confirmer.ask_confirmation(
                                action=function_name,
                                context=cognitive_state
                            )
                            
                            if not confirmed:
                                print(f"[VOICE] User denied {function_name}")
                                actions_taken.append({
                                    "tool": function_name,
                                    "arguments": function_args,
                                    "result": {"cancelled": True, "reason": "User denied via voice"},
                                    "voice_confirmed": False
                                })
                                continue  # Skip this action
                            
                            print(f"[VOICE] User confirmed {function_name}")
                    
                    # Execute the tool
                    result = self.tools.execute_tool(function_name, function_args)
                    actions_taken.append({
                        "tool": function_name,
                        "arguments": function_args,
                        "result": result,
                        "voice_confirmed": self.voice_confirmer.enabled if self.voice_confirmer else False
                    })
            
            return {
                "cognitive_state": cognitive_state,
                "policy_recommendations": policy_recommendations,
                "llm_reasoning": assistant_message.content or "Actions taken based on state analysis",
                "actions_taken": actions_taken,
                "model": self.model
            }
        
        except Exception as e:
            print(f"[LLM] Error during reasoning: {e}")
            # Fallback to policy recommendations
            actions_taken = []
            for rec in policy_recommendations[:2]:  # Take top 2 recommendations
                # Voice handling in fallback mode: inform for takeoff, confirm for landing
                if self.voice_confirmer and self.voice_confirmer.enabled:
                    action = rec["action"]
                    is_takeoff = action == "takeoff"
                    requires_confirmation = self._requires_confirmation(action, policy_recommendations)
                    
                    if is_takeoff and not requires_confirmation:
                        # Automatic takeoff - just inform pilot
                        self.voice_confirmer.inform_pilot(action, cognitive_state)
                    elif requires_confirmation:
                        # Landing or other actions that need confirmation
                        confirmed = self.voice_confirmer.ask_confirmation(
                            action=action,
                            context=cognitive_state
                        )
                        if not confirmed:
                            actions_taken.append({
                                "tool": action,
                                "arguments": rec.get("parameters", {}),
                                "result": {"cancelled": True, "reason": "User denied via voice"},
                                "voice_confirmed": False
                            })
                            continue
                
                result = self.tools.execute_tool(rec["action"], rec.get("parameters", {}))
                actions_taken.append({
                    "tool": rec["action"],
                    "arguments": rec.get("parameters", {}),
                    "result": result,
                    "reason": rec["reason"],
                    "voice_confirmed": self.voice_confirmer.enabled if self.voice_confirmer else False
                })
            
            return {
                "cognitive_state": cognitive_state,
                "policy_recommendations": policy_recommendations,
                "llm_reasoning": f"Fallback mode - using policy recommendations due to: {str(e)}",
                "actions_taken": actions_taken,
                "model": "policy_fallback"
            }
    
    def _requires_confirmation(self, action: str, recommendations: list) -> bool:
        """
        Determine if action needs voice confirmation.
        
        Rules:
        - takeoff: Never requires confirmation (auto-execute)
        - land: Always requires confirmation (even if marked urgent)
        - Other actions: Check urgent flag
        
        Args:
            action: Action name (takeoff, land, turn_around)
            recommendations: List of policy recommendations
        
        Returns:
            True if confirmation required, False if auto-execute
        """
        if action == "takeoff":
            # Takeoff is automatic - no confirmation needed
            return False
        
        if action == "land":
            # Landing always requires confirmation
            return True
        
        # Other actions: check urgent flag
        for rec in recommendations:
            if rec.get("action") == action and rec.get("urgent"):
                return False
        
        # Default: require confirmation
        return True
    
    def simple_reasoning(self, cognitive_state: Dict[str, Any]) -> str:
        """
        Simple reasoning without function calling for quick responses.
        
        Args:
            cognitive_state: Current cognitive metrics
        
        Returns:
            Text reasoning about the state
        """
        prompt = f"""Briefly analyze this pilot's cognitive state:
Focus: {cognitive_state.get('focus', 0):.2f}
Fatigue: {cognitive_state.get('fatigue', 0):.2f}
Overload: {cognitive_state.get('overload', 0):.2f}
Stress: {cognitive_state.get('stress', 0):.2f}

Provide a 1-2 sentence assessment."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Unable to analyze state: {str(e)}"

