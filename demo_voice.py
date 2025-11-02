#!/usr/bin/env python3
"""
Quick demo of voice confirmation system.
Tests yes/no detection with clear prompts.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable voice confirmation
os.environ["VOICE_CONFIRMATION_ENABLED"] = "true"
os.environ["VOICE_CONFIRMATION_TIMEOUT"] = "5"

from agent.voice_confirmer import VoiceConfirmer

def main():
    print("=" * 60)
    print("Voice Confirmation Demo")
    print("=" * 60)
    print()
    
    confirmer = VoiceConfirmer()
    
    print("This demo will test the voice confirmation system.")
    print("You'll hear a question through your speakers.")
    print("Respond with 'yes' or 'no' clearly.\n")
    
    # Test scenarios
    scenarios = [
        {
            "action": "takeoff",
            "context": {"focus": 0.8, "fatigue": 0.2, "overload": 0.3, "stress": 0.2},
            "description": "Optimal state - recommending takeoff"
        },
        {
            "action": "land",
            "context": {"focus": 0.3, "fatigue": 0.8, "overload": 0.7, "stress": 0.9},
            "description": "Critical state - recommending landing"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}/2: {scenario['description']}")
        print(f"{'─' * 60}\n")
        
        input("Press Enter when ready to hear the question...")
        
        result = confirmer.ask_confirmation(
            action=scenario['action'],
            context=scenario['context']
        )
        
        results.append({
            "scenario": scenario['description'],
            "action": scenario['action'],
            "confirmed": result
        })
        
        print(f"\n→ Result: {'✅ CONFIRMED' if result else '❌ DENIED'}\n")
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        status = "✅ CONFIRMED" if result['confirmed'] else "❌ DENIED"
        print(f"{i}. {result['scenario']}")
        print(f"   Action: {result['action']}")
        print(f"   Result: {status}\n")
    
    print("=" * 60)
    print("Voice confirmation system is working!")
    print()
    print("Tips:")
    print("- Speak clearly during the 5-second recording window")
    print("- Reduce background noise for better accuracy")
    print("- Say exactly 'yes' or 'no' for best results")
    print("- Unclear responses default to 'no' for safety")
    print("=" * 60)

if __name__ == "__main__":
    main()

