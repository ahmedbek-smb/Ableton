#!/usr/bin/env python3
"""
AbletonMCP Standalone Launcher

Simple launcher script for the AbletonMCP standalone applications.
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Launch AbletonMCP Standalone Applications")
    parser.add_argument(
        "app",
        choices=["desktop", "web", "demo"],
        help="Application to launch: 'desktop' for GUI app, 'web' for web app, 'demo' for demo info"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode (simulates LLM and Ableton without API keys)"
    )
    
    args = parser.parse_args()
    
    # Set demo mode environment variable if requested
    if args.demo:
        os.environ["ABLETON_MCP_DEMO"] = "true"
        print("🎵 Demo mode enabled!")
        print("   • No API keys required")
        print("   • No Ableton Live required")
        print("   • Simulated responses and tool calls")
        print()
    
    if args.app == "demo":
        from standalone_app.demo import main as demo_main
        demo_main()
    elif args.app == "desktop":
        print("🖥️  Launching Desktop App...")
        if args.demo:
            print("   Running in demo mode")
        from standalone_app.main import main as desktop_main
        desktop_main()
    elif args.app == "web":
        print("🌐 Launching Web App...")
        if args.demo:
            print("   Running in demo mode")
        print("   Open your browser to: http://127.0.0.1:5000")
        from standalone_app.web_app import main as web_main
        web_main()

if __name__ == "__main__":
    main()