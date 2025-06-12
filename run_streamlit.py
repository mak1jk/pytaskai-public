#!/usr/bin/env python3
"""
PyTaskAI - Streamlit App Runner

Simple script to launch the Streamlit frontend application.
"""

import os
import sys
import subprocess


def main():
    """Launch the Streamlit application."""

    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the Streamlit app
    app_path = os.path.join(script_dir, "frontend", "streamlit_app.py")

    # Check if the app exists
    if not os.path.exists(app_path):
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)

    # Launch Streamlit
    print("🚀 Starting PyTaskAI Streamlit App...")
    print(f"📁 App location: {app_path}")
    print("🌐 The app will open in your browser automatically.")
    print("💡 Use Ctrl+C to stop the server.")
    print()

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                app_path,
                "--server.headless",
                "false",
                "--server.address",
                "localhost",
                "--server.port",
                "8501",
                "--browser.gatherUsageStats",
                "false",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it with: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()
