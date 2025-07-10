# AbletonMCP Standalone Applications Setup Guide

This guide will help you set up and use the standalone applications for AbletonMCP, allowing you to interact directly with LLM APIs to control Ableton Live without needing Claude Desktop or Cursor.

## 🎯 What You'll Get

Two standalone applications that let you:
- **Desktop App** (Tkinter): Native GUI application
- **Web App** (Flask): Browser-based interface

Both applications:
- ✅ Connect directly to OpenAI or Anthropic APIs
- ✅ Use your existing MCP server and Ableton Remote Script (no changes needed!)
- ✅ Chat with AI to control Ableton Live in natural language
- ✅ Real-time tool execution and feedback

## 📋 Prerequisites

1. **Existing AbletonMCP Setup**: You should already have:
   - Ableton Live with the AbletonMCP Remote Script installed and working
   - The MCP Server code (your existing `MCP_Server/` directory)

2. **Python 3.10+** with `uv` package manager installed

3. **LLM API Key**: Either:
   - OpenAI API key (for GPT-4/GPT-3.5)
   - Anthropic API key (for Claude)

## 🚀 Installation

### Option 1: Install with Standalone Dependencies

```bash
# Install with desktop app dependencies
uv pip install -e ".[standalone]"

# Or install with web app dependencies  
uv pip install -e ".[web]"

# Or install both
uv pip install -e ".[standalone,web]"
```

### Option 2: Manual Installation

```bash
# Install base package
uv pip install -e .

# Install additional dependencies for standalone apps
cd standalone_app
uv pip install -r requirements.txt
```

## 🎯 Demo Mode

Want to try the apps without API keys or Ableton Live? Use **Demo Mode**!

```bash
# Try demo mode first
export ABLETON_MCP_DEMO=true
ableton-mcp-app

# Or use the launcher
ableton-mcp-launch desktop --demo
ableton-mcp-launch web --demo
```

**Demo Mode Features:**
- ✅ No API keys required
- ✅ No Ableton Live required  
- ✅ Simulated AI responses
- ✅ Fake tool executions with realistic delays
- ✅ Full UI functionality testing

## 🖥️ Desktop Application

### Running the Desktop App

```bash
# If installed via pip
ableton-mcp-app

# Or run directly
python -m standalone_app.main

# Or use the launcher
ableton-mcp-launch desktop

# With demo mode
ableton-mcp-launch desktop --demo
```

### Desktop App Features

- **Clean GUI Interface**: Tkinter-based native application
- **Real-time Chat**: See AI responses and tool executions in real-time
- **Tool Discovery**: View all available Ableton controls
- **Cross-platform**: Works on Windows, macOS, and Linux

### Desktop App Usage

1. **Launch the app** using one of the methods above
2. **Configure Connection**:
   - Select your LLM Provider (OpenAI or Anthropic)
   - Enter your API key
   - Click "Connect"
3. **Start Chatting**: Type natural language commands like:
   - "Create a new MIDI track with a bass instrument"
   - "Add a simple drum pattern to track 1"
   - "Set the tempo to 120 BPM and start playback"

## 🌐 Web Application

### Running the Web App

```bash
# If installed via pip
ableton-mcp-web

# Or run directly
python -m standalone_app.web_app

# Or use the launcher
ableton-mcp-launch web

# With demo mode
ableton-mcp-launch web --demo
```

The web app will start at: **http://127.0.0.1:5000**

### Web App Features

- **Modern Web Interface**: Clean, responsive design
- **Real-time Updates**: WebSocket-based communication
- **Mobile Friendly**: Works on tablets and phones
- **Easy Sharing**: Share the URL with others on your local network

### Web App Usage

1. **Open your browser** to http://127.0.0.1:5000
2. **Configure Connection**:
   - Select your LLM Provider (OpenAI or Anthropic)
   - Enter your API key
   - Click "Connect"
3. **Start Chatting**: Use the chat interface to control Ableton Live

## 🔧 Configuration

### API Keys

Both applications support:

- **OpenAI**: Use models like `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic**: Use models like `claude-3-sonnet-20241022`, `claude-3-haiku-20240307`

### Model Selection

The applications default to:
- OpenAI: `gpt-4`
- Anthropic: `claude-3-sonnet-20241022`

To use different models, you can modify the provider classes in the source code.

## 🛠️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Standalone App  │───▶│   LLM API       │───▶│   MCP Server     │───▶│ Ableton Live    │
│ (Desktop/Web)   │    │ (OpenAI/Claude) │    │ (Your Existing)  │    │ (Your Existing) │
└─────────────────┘    └─────────────────┘    └──────────────────┘    └─────────────────┘
```

Your existing code remains unchanged! The standalone apps act as new client interfaces.

## 🎵 Example Commands

Once connected, try these natural language commands:

### Track Creation
- "Create a new MIDI track"
- "Add a synth bass to track 2"
- "Create an audio track for recording vocals"

### Clip Creation
- "Create a 4-bar MIDI clip in track 1, slot 0"
- "Add a C major chord to the clip"
- "Create a simple kick drum pattern"

### Session Control
- "Set the tempo to 128 BPM"
- "Start playback"
- "Fire the clip in track 2, slot 1"

### Browser Integration
- "Load a 808 drum rack"
- "Add reverb to the selected track"
- "Load a piano instrument"

## 🔍 Troubleshooting

### Connection Issues

1. **"Failed to connect to MCP server"**
   - Ensure your existing MCP Server code is working
   - Check that the `MCP_Server` directory is in your Python path
   - Try running `python -m MCP_Server.server` directly

2. **"Not connected to Ableton"**
   - Make sure Ableton Live is running
   - Verify the AbletonMCP Remote Script is loaded in Ableton
   - Check that Ableton shows "AbletonMCP: Listening for commands on port 9877"

3. **LLM API Errors**
   - Verify your API key is correct
   - Check your API quota/billing status
   - Ensure you have access to the selected model

### Performance Issues

1. **Slow Responses**
   - Try using a faster model (e.g., `gpt-3.5-turbo` instead of `gpt-4`)
   - Check your internet connection
   - Monitor API rate limits

2. **Memory Usage**
   - The conversation history grows over time
   - Restart the app periodically for long sessions

## 🚨 Security Notes

- **API Keys**: Are stored in memory only, not persisted to disk
- **Local Only**: Both apps run locally by default
- **No Authentication**: The web app doesn't require login (intended for local use)

For production use, consider:
- Adding authentication to the web app
- Using environment variables for API keys
- Implementing rate limiting

## 📁 File Structure

After setup, your project structure will look like:

```
your-project/
├── AbletonMCP_Remote_Script/     # Your existing remote script
├── MCP_Server/                   # Your existing MCP server
├── standalone_app/               # New standalone applications
│   ├── __init__.py
│   ├── main.py                   # Desktop app
│   ├── web_app.py               # Web app
│   ├── requirements.txt
│   └── templates/
│       └── index.html           # Web interface
├── pyproject.toml               # Updated with new dependencies
└── STANDALONE_SETUP.md          # This guide
```

## 🎉 Next Steps

1. **Try Both Interfaces**: Test both desktop and web apps to see which you prefer
2. **Customize Models**: Experiment with different LLM models for your workflow
3. **Extend Functionality**: The code is modular and easy to extend with new features
4. **Share Your Experience**: Let others know how the standalone apps work for you!

## 💡 Tips

- **Use Ctrl+Enter** in text areas to send messages quickly
- **Monitor the Tools Panel** to see what capabilities are available
- **Start Simple**: Begin with basic commands before trying complex arrangements
- **Save Your Work**: Always save your Ableton project before experimenting
- **Check Logs**: Both apps log detailed information for debugging

Happy music making! 🎶