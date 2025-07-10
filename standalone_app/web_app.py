#!/usr/bin/env python3
"""
AbletonMCP Web Application

A web-based interface that allows direct interaction with LLM APIs
to control Ableton Live through the Model Context Protocol.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import queue
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import requests

# MCP imports
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

# LLM API imports
import openai
from anthropic import Anthropic

# Demo imports
from .demo import DemoLLMProvider, simulate_tool_call, DEMO_TOOLS, is_demo_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ableton-mcp-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
class AppState:
    def __init__(self):
        self.llm_provider: Optional[Any] = None
        self.mcp_session: Optional[ClientSession] = None
        self.tools: List[Dict] = []
        self.conversation_history: List[Dict] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False

app_state = AppState()

# LLM Provider Classes (reusing from main.py)
class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Send a chat request with available tools"""
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI API provider with MCP tool support"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key)
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Send chat request to OpenAI with tools"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class AnthropicProvider(LLMProvider):
    """Anthropic API provider with MCP tool support"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20241022"):
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Send chat request to Anthropic with tools"""
        try:
            # Convert tools to Anthropic format
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
            
            response = await self.client.messages.create(
                model=self.model,
                messages=messages,
                tools=anthropic_tools,
                max_tokens=4096
            )
            
            tool_calls = []
            for content in response.content:
                if content.type == "tool_use":
                    tool_calls.append({
                        "id": content.id,
                        "type": "function",
                        "function": {
                            "name": content.name,
                            "arguments": json.dumps(content.input)
                        }
                    })
            
            text_content = ""
            for content in response.content:
                if content.type == "text":
                    text_content += content.text
            
            return {
                "content": text_content,
                "tool_calls": tool_calls
            }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

async def connect_to_mcp():
    """Connect to the MCP server or use demo mode"""
    if is_demo_mode():
        logger.info("Running in demo mode - simulating MCP server")
        app_state.tools = DEMO_TOOLS
        app_state.connected = True
        return True
    
    try:
        # Start the MCP server process
        server_cmd = [sys.executable, "-m", "MCP_Server.server"]
        
        # Create stdio client connection
        async with stdio_client(server_cmd) as (read, write):
            async with ClientSession(read, write) as session:
                app_state.mcp_session = session
                
                # Initialize the session
                await session.initialize()
                
                # Get available tools
                tools_response = await session.list_tools()
                
                # Convert tools to OpenAI format
                openai_tools = []
                for tool in tools_response.tools:
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    }
                    openai_tools.append(openai_tool)
                
                app_state.tools = openai_tools
                app_state.connected = True
                
                logger.info(f"Connected to MCP server with {len(app_state.tools)} tools")
                return True
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        app_state.connected = False
        return False

async def call_mcp_tool(tool_name: str, arguments: Dict) -> Any:
    """Call a tool on the MCP server or simulate in demo mode"""
    try:
        if is_demo_mode():
            return await simulate_tool_call(tool_name, arguments)
        
        if not app_state.mcp_session:
            raise Exception("Not connected to MCP server")
        
        result = await app_state.mcp_session.call_tool(tool_name, arguments)
        return result.content[0].text if result.content else "No result"
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise

# Flask Routes
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to LLM provider and MCP server"""
    data = request.json
    provider = data.get('provider')
    api_key = data.get('api_key')
    
    if not api_key and not is_demo_mode():
        return jsonify({'error': 'API key required'}), 400
    
    try:
        # Initialize LLM provider
        if is_demo_mode():
            logger.info("Running in demo mode - simulating LLM provider")
            app_state.llm_provider = DemoLLMProvider(api_key)
        elif provider == 'openai':
            app_state.llm_provider = OpenAIProvider(api_key)
        elif provider == 'anthropic':
            app_state.llm_provider = AnthropicProvider(api_key)
        else:
            return jsonify({'error': 'Unsupported provider'}), 400
        
        # Connect to MCP in background thread
        def connect_async():
            if not app_state.loop:
                app_state.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(app_state.loop)
            
            success = app_state.loop.run_until_complete(connect_to_mcp())
            
            # Emit connection status to all clients
            socketio.emit('connection_status', {
                'connected': success,
                'tools': app_state.tools if success else []
            })
        
        thread = threading.Thread(target=connect_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'connecting'})
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message"""
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    if not app_state.llm_provider or not app_state.connected:
        return jsonify({'error': 'Not connected to services'}), 400
    
    # Process message in background
    def process_async():
        if not app_state.loop:
            return
        
        asyncio.run_coroutine_threadsafe(
            process_message(message), 
            app_state.loop
        )
    
    thread = threading.Thread(target=process_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'processing'})

async def process_message(user_text: str):
    """Process user message with LLM and execute tools"""
    try:
        # Add user message to conversation
        app_state.conversation_history.append({"role": "user", "content": user_text})
        
        # Emit user message
        socketio.emit('chat_message', {
            'role': 'user',
            'content': user_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to LLM with tools
        response = await app_state.llm_provider.chat_with_tools(
            messages=app_state.conversation_history,
            tools=app_state.tools
        )
        
        # Handle response
        if response.get("content"):
            socketio.emit('chat_message', {
                'role': 'assistant',
                'content': response["content"],
                'timestamp': datetime.now().isoformat()
            })
        
        # Execute tool calls
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                
                socketio.emit('chat_message', {
                    'role': 'system',
                    'content': f"Executing: {tool_name}",
                    'timestamp': datetime.now().isoformat()
                })
                
                # Call the tool
                result = await call_mcp_tool(tool_name, arguments)
                socketio.emit('chat_message', {
                    'role': 'tool',
                    'content': f"Result: {result}",
                    'timestamp': datetime.now().isoformat()
                })
        
    except Exception as e:
        logger.error(f"Message processing error: {e}")
        socketio.emit('chat_message', {
            'role': 'system',
            'content': f"Error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        })

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connection_status', {
        'connected': app_state.connected,
        'tools': app_state.tools
    })

def main():
    """Main entry point for the web app"""
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create static directory if it doesn't exist  
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    print("🎵 Starting AbletonMCP Web App...")
    print("📱 Open your browser to: http://127.0.0.1:5000")
    print("⚠️  Make sure Ableton Live is running with the AbletonMCP Remote Script")
    
    socketio.run(app, debug=False, host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main()