"""
LLM-powered agent for advanced reasoning about cognitive states.
"""

import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI


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
The drone provides binary control reflecting the operator's wellness:

RULES:
- ALL GOOD (focus ≥0.6 + fatigue/overload/stress ≤0.4) → takeoff() to 1m
- ALL BAD (focus ≤0.4 + fatigue/overload/stress ≥0.6) → land() to ground
- Mixed state (some good, some bad) → turn_around() 180° (visual indicator)

You have access to exactly THREE tools:
- takeoff: Binary takeoff to 1 meter when ALL parameters are optimal
- land: Binary landing to ground (0m) when ALL parameters are critical
- turn_around: Rotate 180° for mixed states or when no altitude change needed

DECISION RULES:
1. You will ONLY be called when policy recommendations are provided.
2. Follow the policy recommendations - they already checked ALL parameters.
3. Use takeoff() ONLY when ALL parameters are good (not just some).
4. Use land() ONLY when ALL parameters are bad (not just some).
5. Use turn_around() for mixed states or when maintaining current state.

The drone provides clear visual feedback: at 1m = operator excellent, at ground = operator critical, rotating = mixed state."""
        
        # Build user message with context
        user_message = f"""Current Cognitive State:
- Focus: {cognitive_state.get('focus', 0):.2f}
- Fatigue: {cognitive_state.get('fatigue', 0):.2f}
- Overload: {cognitive_state.get('overload', 0):.2f}
- Stress: {cognitive_state.get('stress', 0):.2f}

Policy Recommendations:
{json.dumps(policy_recommendations, indent=2)}

Recent Context:
{json.dumps(context['trends'], indent=2)}

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
            
            # Process function calls
            actions_taken = []
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    result = self.tools.execute_tool(function_name, function_args)
                    actions_taken.append({
                        "tool": function_name,
                        "arguments": function_args,
                        "result": result
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
                result = self.tools.execute_tool(rec["action"], rec.get("parameters", {}))
                actions_taken.append({
                    "tool": rec["action"],
                    "arguments": rec.get("parameters", {}),
                    "result": result,
                    "reason": rec["reason"]
                })
            
            return {
                "cognitive_state": cognitive_state,
                "policy_recommendations": policy_recommendations,
                "llm_reasoning": f"Fallback mode - using policy recommendations due to: {str(e)}",
                "actions_taken": actions_taken,
                "model": "policy_fallback"
            }
    
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

