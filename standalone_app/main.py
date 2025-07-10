#!/usr/bin/env python3
"""
AbletonMCP Standalone Application

A standalone GUI application that allows direct interaction with LLM APIs
that support MCP (Model Context Protocol) to control Ableton Live.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import queue

# MCP imports
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, ImageContent, EmbeddedResource

# LLM API imports
import openai
from anthropic import Anthropic

# Demo imports
from .demo import DemoLLMProvider, simulate_tool_call, DEMO_TOOLS, is_demo_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class MCPClient:
    """MCP Client to communicate with the existing MCP server"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.tools: List[Dict] = []
        self.demo_mode = is_demo_mode()
    
    async def connect(self):
        """Connect to the MCP server (existing server.py) or use demo mode"""
        if self.demo_mode:
            logger.info("Running in demo mode - simulating MCP server")
            self.tools = DEMO_TOOLS
            return True
        
        try:
            # Start the MCP server process
            server_cmd = [sys.executable, "-m", "MCP_Server.server"]
            
            # Create stdio client connection
            async with stdio_client(server_cmd) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    
                    # Initialize the session
                    await session.initialize()
                    
                    # Get available tools
                    tools_response = await session.list_tools()
                    self.tools = self._convert_tools_to_openai_format(tools_response.tools)
                    
                    logger.info(f"Connected to MCP server with {len(self.tools)} tools")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    def _convert_tools_to_openai_format(self, mcp_tools) -> List[Dict]:
        """Convert MCP tools to OpenAI tools format"""
        openai_tools = []
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on the MCP server or simulate in demo mode"""
        try:
            if self.demo_mode:
                return await simulate_tool_call(tool_name, arguments)
            
            if not self.session:
                raise Exception("Not connected to MCP server")
            
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "No result"
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            raise

class AbletonMCPApp:
    """Main standalone application"""
    
    def __init__(self):
        self.root = tk.Tk()
        title = "AbletonMCP Standalone (Demo Mode)" if is_demo_mode() else "AbletonMCP Standalone"
        self.root.title(title)
        self.root.geometry("1000x700")
        
        # Application state
        self.llm_provider: Optional[LLMProvider] = None
        self.mcp_client = MCPClient()
        self.conversation_history = []
        self.message_queue = queue.Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Start background thread for async operations
        self.async_thread = None
        self.loop = None
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # LLM Provider Selection
        ttk.Label(config_frame, text="LLM Provider:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.provider_var = tk.StringVar(value="openai")
        provider_combo = ttk.Combobox(config_frame, textvariable=self.provider_var, 
                                     values=["openai", "anthropic"], state="readonly")
        provider_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # API Key
        ttk.Label(config_frame, text="API Key:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(config_frame, textvariable=self.api_key_var, width=30, show="*")
        api_key_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # Connect Button
        self.connect_btn = ttk.Button(config_frame, text="Connect", command=self.connect_services)
        self.connect_btn.grid(row=0, column=4, padx=(0, 10))
        
        # Status
        initial_status = "Demo Mode - Disconnected" if is_demo_mode() else "Disconnected"
        self.status_var = tk.StringVar(value=initial_status)
        status_label = ttk.Label(config_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=5)
        
        # Chat Interface
        chat_frame = ttk.LabelFrame(main_frame, text="Chat with Ableton", padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat History
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=20, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Input Frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X)
        
        # User Input
        self.user_input = tk.Text(input_frame, height=3)
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Send Button
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.user_input.bind("<Control-Return>", lambda e: self.send_message())
        
        # Tools Display
        tools_frame = ttk.LabelFrame(main_frame, text="Available Tools", padding=10)
        tools_frame.pack(fill=tk.X)
        
        self.tools_display = scrolledtext.ScrolledText(tools_frame, height=5, state=tk.DISABLED)
        self.tools_display.pack(fill=tk.BOTH, expand=True)
    
    def connect_services(self):
        """Connect to LLM provider and MCP server"""
        if not self.api_key_var.get() and not is_demo_mode():
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        # Start async connection in background thread
        if self.async_thread and self.async_thread.is_alive():
            return
        
        self.async_thread = threading.Thread(target=self._connect_async)
        self.async_thread.daemon = True
        self.async_thread.start()
        
        self.status_var.set("Connecting...")
        self.connect_btn.config(state=tk.DISABLED)
    
    def _connect_async(self):
        """Async connection logic"""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Connect to services
            success = self.loop.run_until_complete(self._do_connect())
            
            if success:
                status_msg = "Demo Mode - Connected" if is_demo_mode() else "Connected"
                self.message_queue.put(("status", status_msg))
                self.message_queue.put(("tools", self.mcp_client.tools))
            else:
                status_msg = "Demo Mode - Connection Failed" if is_demo_mode() else "Connection Failed"
                self.message_queue.put(("status", status_msg))
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.message_queue.put(("status", f"Error: {str(e)}"))
        
        # Schedule UI updates
        self.root.after(100, self._check_message_queue)
    
    async def _do_connect(self):
        """Actual async connection logic"""
        # Initialize LLM provider
        provider = self.provider_var.get()
        api_key = self.api_key_var.get()
        
        if is_demo_mode():
            logger.info("Running in demo mode - simulating LLM provider")
            self.llm_provider = DemoLLMProvider(api_key)
        elif provider == "openai":
            self.llm_provider = OpenAIProvider(api_key)
        elif provider == "anthropic":
            self.llm_provider = AnthropicProvider(api_key)
        
        # Connect to MCP server
        success = await self.mcp_client.connect()
        return success
    
    def _check_message_queue(self):
        """Check for messages from background thread"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_var.set(data)
                    if data == "Connected":
                        self.connect_btn.config(state=tk.NORMAL)
                    elif "Error" in data or "Failed" in data:
                        self.connect_btn.config(state=tk.NORMAL)
                
                elif msg_type == "tools":
                    self._update_tools_display(data)
                
                elif msg_type == "chat":
                    self._add_to_chat(data["role"], data["content"])
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._check_message_queue)
    
    def _update_tools_display(self, tools):
        """Update the tools display"""
        self.tools_display.config(state=tk.NORMAL)
        self.tools_display.delete(1.0, tk.END)
        
        tools_text = f"Connected with {len(tools)} tools:\n"
        for tool in tools:
            tools_text += f"• {tool['function']['name']}: {tool['function']['description']}\n"
        
        self.tools_display.insert(tk.END, tools_text)
        self.tools_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """Send user message to LLM"""
        user_text = self.user_input.get(1.0, tk.END).strip()
        if not user_text:
            return
        
        if not self.llm_provider or not self.mcp_client.tools:
            messagebox.showerror("Error", "Please connect to services first")
            return
        
        # Clear input
        self.user_input.delete(1.0, tk.END)
        
        # Add to chat
        self._add_to_chat("user", user_text)
        
        # Process in background
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._process_message(user_text), self.loop)
    
    async def _process_message(self, user_text: str):
        """Process user message with LLM and execute tools"""
        try:
            # Add user message to conversation
            self.conversation_history.append({"role": "user", "content": user_text})
            
            # Send to LLM with tools
            response = await self.llm_provider.chat_with_tools(
                messages=self.conversation_history,
                tools=self.mcp_client.tools
            )
            
            # Handle response
            if response.get("content"):
                self.message_queue.put(("chat", {"role": "assistant", "content": response["content"]}))
            
            # Execute tool calls
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    self.message_queue.put(("chat", {"role": "system", "content": f"Executing: {tool_name}"}))
                    
                    # Call the tool
                    result = await self.mcp_client.call_tool(tool_name, arguments)
                    self.message_queue.put(("chat", {"role": "tool", "content": f"Result: {result}"}))
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            self.message_queue.put(("chat", {"role": "system", "content": f"Error: {str(e)}"}))
    
    def _add_to_chat(self, role: str, content: str):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        colors = {
            "user": "blue",
            "assistant": "green", 
            "system": "orange",
            "tool": "purple"
        }
        
        # Insert message
        self.chat_display.insert(tk.END, f"[{timestamp}] {role.upper()}: ", colors.get(role, "black"))
        self.chat_display.insert(tk.END, f"{content}\n\n")
        
        # Configure colors
        for color_role, color in colors.items():
            self.chat_display.tag_config(color, foreground=color)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def run(self):
        """Start the application"""
        self._check_message_queue()  # Start message queue checking
        self.root.mainloop()

def main():
    """Main entry point"""
    app = AbletonMCPApp()
    app.run()

if __name__ == "__main__":
    main()