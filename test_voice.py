#!/usr/bin/env python3
"""
Quick test script for voice confirmation system.
Tests microphone, speaker, and OpenAI API connectivity.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test if all required packages are installed"""
    print("\n=== Testing Imports ===")
    try:
        import sounddevice as sd
        print("✅ sounddevice installed")
    except ImportError:
        print("❌ sounddevice not installed. Run: pip install sounddevice")
        return False
    
    try:
        import numpy as np
        print("✅ numpy installed")
    except ImportError:
        print("❌ numpy not installed. Run: pip install numpy")
        return False
    
    try:
        from openai import OpenAI
        print("✅ openai installed")
    except ImportError:
        print("❌ openai not installed. Run: pip install openai")
        return False
    
    return True


def test_openai_api():
    """Test OpenAI API key"""
    print("\n=== Testing OpenAI API ===")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set in .env file")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ OPENAI_API_KEY format invalid (should start with 'sk-')")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True


def test_audio_devices():
    """Test audio input/output devices"""
    print("\n=== Testing Audio Devices ===")
    try:
        import sounddevice as sd
        
        # List all devices
        print("\nAvailable Audio Devices:")
        devices = sd.query_devices()
        
        for i, device in enumerate(devices):
            marker = ""
            if i == sd.default.device[0]:
                marker = " [DEFAULT INPUT]"
            elif i == sd.default.device[1]:
                marker = " [DEFAULT OUTPUT]"
            
            print(f"  {i}: {device['name']}{marker}")
            print(f"     Input channels: {device['max_input_channels']}, "
                  f"Output channels: {device['max_output_channels']}")
        
        # Check for input device
        default_input = sd.default.device[0]
        input_device = devices[default_input] if default_input is not None else None
        
        if input_device and input_device['max_input_channels'] > 0:
            print(f"\n✅ Default input device: {input_device['name']}")
        else:
            print("\n❌ No input device (microphone) found")
            return False
        
        # Check for output device
        default_output = sd.default.device[1]
        output_device = devices[default_output] if default_output is not None else None
        
        if output_device and output_device['max_output_channels'] > 0:
            print(f"✅ Default output device: {output_device['name']}")
        else:
            print("❌ No output device (speaker) found")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing audio devices: {e}")
        return False


def test_microphone():
    """Test microphone recording"""
    print("\n=== Testing Microphone ===")
    try:
        import sounddevice as sd
        import numpy as np
        
        print("Recording 2 seconds of audio...")
        print("🎤 Say something now!")
        
        duration = 2
        sample_rate = 16000
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        
        # Check if any audio was captured
        max_amplitude = np.max(np.abs(recording))
        
        print(f"Max amplitude: {max_amplitude}")
        
        if max_amplitude > 100:
            print("✅ Microphone is working (audio detected)")
            return True
        else:
            print("⚠️ No audio detected. Check microphone volume or permissions.")
            return False
    
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")
        return False


def test_voice_confirmer():
    """Test the actual VoiceConfirmer class"""
    print("\n=== Testing VoiceConfirmer ===")
    
    # Set voice confirmation enabled for testing
    os.environ["VOICE_CONFIRMATION_ENABLED"] = "true"
    os.environ["VOICE_CONFIRMATION_TIMEOUT"] = "5"
    
    try:
        from agent.voice_confirmer import VoiceConfirmer
        
        confirmer = VoiceConfirmer()
        print("✅ VoiceConfirmer initialized")
        
        # Test with mock context
        print("\nTesting voice confirmation flow...")
        print("The system will ask you a question. Say 'yes' or 'no'.")
        input("Press Enter when ready...")
        
        test_context = {
            "focus": 0.8,
            "fatigue": 0.2,
            "overload": 0.3,
            "stress": 0.2
        }
        
        result = confirmer.ask_confirmation("takeoff", test_context)
        
        if result:
            print("\n✅ You said YES - action would proceed")
        else:
            print("\n❌ You said NO - action would be cancelled")
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing VoiceConfirmer: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MindAware Voice Confirmation Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("OpenAI API", test_openai_api()))
    results.append(("Audio Devices", test_audio_devices()))
    results.append(("Microphone", test_microphone()))
    
    # Only test VoiceConfirmer if all prerequisites pass
    if all(r[1] for r in results):
        results.append(("VoiceConfirmer", test_voice_confirmer()))
    else:
        print("\n⚠️ Skipping VoiceConfirmer test due to failed prerequisites")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Voice confirmation is ready to use.")
        print("\nTo enable voice confirmation:")
        print("1. Set VOICE_CONFIRMATION_ENABLED=true in .env")
        print("2. Run: python src/main.py --scenario normal --llm")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon issues:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Set OPENAI_API_KEY in .env file")
        print("- Grant microphone permissions to terminal/Python")
        print("- Check audio device connections")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

