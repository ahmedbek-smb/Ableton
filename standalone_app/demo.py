#!/usr/bin/env python3
"""
AbletonMCP Demo Script

A demo mode for testing the standalone applications without requiring LLM API keys.
This simulates AI responses and tool calls to demonstrate the functionality.
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Any

# Demo responses for different types of user input
DEMO_RESPONSES = {
    "track": {
        "responses": [
            "I'll create a new MIDI track for you. Let me set it up with a suitable instrument.",
            "Creating a new track. I'll also load a good instrument to get you started.",
            "Perfect! I'll add a new MIDI track and configure it for music production."
        ],
        "tools": [
            {"name": "create_midi_track", "args": {"index": -1}},
            {"name": "load_instrument_or_effect", "args": {"track_index": 0, "uri": "query:Synths#Instrument%20Rack:Bass:FileId_5116"}}
        ]
    },
    "clip": {
        "responses": [
            "I'll create a new MIDI clip and add some musical content to it.",
            "Creating a clip with some notes. This will give you a good starting point.",
            "Let me set up a new clip with a simple musical pattern."
        ],
        "tools": [
            {"name": "create_clip", "args": {"track_index": 0, "clip_index": 0, "length": 4.0}},
            {"name": "add_notes_to_clip", "args": {
                "track_index": 0, 
                "clip_index": 0, 
                "notes": [
                    {"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100, "mute": False},
                    {"pitch": 64, "start_time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
                    {"pitch": 67, "start_time": 2.0, "duration": 0.5, "velocity": 100, "mute": False}
                ]
            }}
        ]
    },
    "tempo": {
        "responses": [
            "I'll adjust the tempo for you. This will affect the overall feel of your track.",
            "Setting the tempo. This will change how fast or slow your music plays.",
            "Tempo updated! This will give your track the right groove."
        ],
        "tools": [
            {"name": "set_tempo", "args": {"tempo": random.randint(100, 140)}}
        ]
    },
    "play": {
        "responses": [
            "Starting playback! You should hear your music playing now.",
            "Let's listen to what you've created. Starting playback.",
            "Playing your track. Enjoy the music!"
        ],
        "tools": [
            {"name": "start_playback", "args": {}}
        ]
    },
    "stop": {
        "responses": [
            "Stopping playback. Your music is now paused.",
            "Playback stopped. You can continue editing your track.",
            "Music stopped. Ready for more edits!"
        ],
        "tools": [
            {"name": "stop_playback", "args": {}}
        ]
    },
    "info": {
        "responses": [
            "Let me get the current session information for you.",
            "I'll check what's currently in your Ableton session.",
            "Gathering information about your current project."
        ],
        "tools": [
            {"name": "get_session_info", "args": {}}
        ]
    }
}

FALLBACK_RESPONSE = {
    "responses": [
        "I understand you want to work with Ableton Live. Let me help you with that.",
        "That's an interesting musical idea! Let me see what I can do.",
        "I'll help you create some music. Let me start with the basics."
    ],
    "tools": [
        {"name": "get_session_info", "args": {}}
    ]
}

class DemoLLMProvider:
    """Demo LLM provider that simulates AI responses"""
    
    def __init__(self, api_key: str = "demo", model: str = "demo-model"):
        self.api_key = api_key
        self.model = model
    
    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Simulate chat request with tools"""
        # Add a realistic delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break
        
        # Determine response type based on keywords
        response_type = "info"  # default
        
        if any(word in user_message for word in ["track", "create", "new", "add"]):
            response_type = "track"
        elif any(word in user_message for word in ["clip", "pattern", "notes", "chord"]):
            response_type = "clip"
        elif any(word in user_message for word in ["tempo", "bpm", "speed", "fast", "slow"]):
            response_type = "tempo"
        elif any(word in user_message for word in ["play", "start", "listen", "hear"]):
            response_type = "play"
        elif any(word in user_message for word in ["stop", "pause", "halt"]):
            response_type = "stop"
        elif any(word in user_message for word in ["info", "status", "session", "what"]):
            response_type = "info"
        
        # Get response template
        template = DEMO_RESPONSES.get(response_type, FALLBACK_RESPONSE)
        
        # Generate response
        content = random.choice(template["responses"])
        
        # Generate tool calls
        tool_calls = []
        for i, tool in enumerate(template["tools"]):
            tool_calls.append({
                "id": f"demo_call_{int(time.time())}_{i}",
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "arguments": json.dumps(tool["args"])
                }
            })
        
        return {
            "content": content,
            "tool_calls": tool_calls
        }

# Tool call results simulation
DEMO_TOOL_RESULTS = {
    "create_midi_track": "Created new MIDI track: Track 1",
    "create_clip": "Created new clip at track 0, slot 0 with length 4.0 beats",
    "add_notes_to_clip": "Added 3 notes to clip at track 0, slot 0",
    "set_tempo": lambda args: f"Set tempo to {args.get('tempo', 120)} BPM",
    "start_playback": "Started playback",
    "stop_playback": "Stopped playback",
    "load_instrument_or_effect": "Loaded instrument with URI 'query:Synths#Instrument%20Rack:Bass:FileId_5116' on track 0. New devices: Bass",
    "get_session_info": json.dumps({
        "tempo": 120.0,
        "signature_numerator": 4,
        "signature_denominator": 4,
        "track_count": 2,
        "return_track_count": 2,
        "master_track": {
            "name": "Master",
            "volume": 0.85,
            "panning": 0.0
        }
    }, indent=2),
    "get_track_info": json.dumps({
        "index": 0,
        "name": "Track 1",
        "is_audio_track": False,
        "is_midi_track": True,
        "mute": False,
        "solo": False,
        "arm": False,
        "volume": 0.85,
        "panning": 0.0,
        "clip_slots": [
            {
                "index": 0,
                "has_clip": True,
                "clip": {
                    "name": "Clip 1",
                    "length": 4.0,
                    "is_playing": False,
                    "is_recording": False
                }
            }
        ],
        "devices": [
            {
                "index": 0,
                "name": "Bass",
                "class_name": "InstrumentRack",
                "type": "instrument"
            }
        ]
    }, indent=2)
}

async def simulate_tool_call(tool_name: str, arguments: Dict) -> str:
    """Simulate a tool call and return a realistic result"""
    # Add a realistic delay
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    if tool_name in DEMO_TOOL_RESULTS:
        result = DEMO_TOOL_RESULTS[tool_name]
        if callable(result):
            return result(arguments)
        return result
    
    return f"Demo: Executed {tool_name} with arguments {arguments}"

# Demo tools list (matches the real MCP server tools)
DEMO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_session_info",
            "description": "Get detailed information about the current Ableton session",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "create_midi_track",
            "description": "Create a new MIDI track in the Ableton session",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "The index to insert the track at (-1 = end of list)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_clip", 
            "description": "Create a new MIDI clip in the specified track and clip slot",
            "parameters": {
                "type": "object",
                "properties": {
                    "track_index": {
                        "type": "integer",
                        "description": "The index of the track to create the clip in"
                    },
                    "clip_index": {
                        "type": "integer", 
                        "description": "The index of the clip slot to create the clip in"
                    },
                    "length": {
                        "type": "number",
                        "description": "The length of the clip in beats (default: 4.0)"
                    }
                },
                "required": ["track_index", "clip_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_notes_to_clip",
            "description": "Add MIDI notes to a clip",
            "parameters": {
                "type": "object", 
                "properties": {
                    "track_index": {
                        "type": "integer",
                        "description": "The index of the track containing the clip"
                    },
                    "clip_index": {
                        "type": "integer",
                        "description": "The index of the clip slot containing the clip"
                    },
                    "notes": {
                        "type": "array",
                        "description": "List of note dictionaries",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pitch": {"type": "integer"},
                                "start_time": {"type": "number"},
                                "duration": {"type": "number"}, 
                                "velocity": {"type": "integer"},
                                "mute": {"type": "boolean"}
                            }
                        }
                    }
                },
                "required": ["track_index", "clip_index", "notes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_tempo",
            "description": "Set the tempo of the Ableton session",
            "parameters": {
                "type": "object",
                "properties": {
                    "tempo": {
                        "type": "number",
                        "description": "The new tempo in BPM"
                    }
                },
                "required": ["tempo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_playback",
            "description": "Start playing the Ableton session",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_playback", 
            "description": "Stop playing the Ableton session",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_instrument_or_effect",
            "description": "Load an instrument or effect onto a track using its URI",
            "parameters": {
                "type": "object",
                "properties": {
                    "track_index": {
                        "type": "integer",
                        "description": "The index of the track to load the instrument on"
                    },
                    "uri": {
                        "type": "string", 
                        "description": "The URI of the instrument or effect to load"
                    }
                },
                "required": ["track_index", "uri"]
            }
        }
    }
]

def is_demo_mode() -> bool:
    """Check if we should run in demo mode"""
    import os
    return os.environ.get("ABLETON_MCP_DEMO", "false").lower() == "true"

def main():
    """Demo mode information"""
    print("🎵 AbletonMCP Demo Mode")
    print("")
    print("This demo simulates the AbletonMCP functionality without requiring:")
    print("  • LLM API keys")
    print("  • Ableton Live running")
    print("  • The MCP server")
    print("")
    print("To run the standalone apps in demo mode:")
    print("  export ABLETON_MCP_DEMO=true")
    print("  ableton-mcp-app")
    print("")
    print("Or:")
    print("  export ABLETON_MCP_DEMO=true") 
    print("  ableton-mcp-web")
    print("")
    print("Demo features:")
    print("  ✓ Simulated AI responses")
    print("  ✓ Fake tool executions")
    print("  ✓ Realistic delays")
    print("  ✓ Full UI functionality")

if __name__ == "__main__":
    main()