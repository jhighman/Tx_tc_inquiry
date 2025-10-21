"""
Gradio UI for Texas Extract.

This module provides a web UI for searching names in arrest records.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import gradio as gr

from arrestx.config import load_config, Config
from arrestx.api import search_name, SearchResult

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging.
    
    Args:
        level: Logging level
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def search_handler(name: str, config_path: str = "config.yaml", force_update: bool = False) -> Tuple[str, str]:
    """
    Handle search requests.
    
    Args:
        name: Name to search for
        config_path: Path to configuration file
        force_update: Force update of the report
        
    Returns:
        Tuple of (alerts_html, raw_json)
    """
    if not name:
        return "Please enter a name to search for.", "{}"
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Search for the name
        result = search_name(name, config, force_update)
        
        # Generate alerts HTML
        alerts_html = generate_alerts_html(result)
        
        # Generate raw JSON
        raw_json = json.dumps(result.to_dict(), indent=2)
        
        return alerts_html, raw_json
    except Exception as e:
        logger.exception(f"Error searching for {name}: {e}")
        return f"Error: {str(e)}", "{}"

def generate_alerts_html(result: SearchResult) -> str:
    """
    Generate HTML for alerts.
    
    Args:
        result: Search result
        
    Returns:
        HTML string
    """
    html = f"<h2>Search Results for: {result.name}</h2>"
    
    if result.alerts:
        html += f"<div style='color: red; font-weight: bold; margin: 10px 0;'>{result.get_due_diligence_message()}</div>"
        
        html += "<div style='margin-top: 20px;'>"
        for i, alert in enumerate(result.alerts, 1):
            html += f"<div style='background-color: #ffeeee; padding: 15px; margin-bottom: 15px; border-radius: 5px; border-left: 5px solid red;'>"
            html += f"<h3>Match {i}</h3>"
            html += f"<p><strong>Name:</strong> {alert.name}</p>"
            html += f"<p><strong>Booking #:</strong> {alert.booking_no}</p>"
            html += f"<p><strong>Charge:</strong> {alert.description}</p>"
            html += f"<p><strong>Identifier:</strong> {alert.identifier}</p>"
            html += f"<p><strong>Book-in Date:</strong> {alert.book_in_date}</p>"
            html += f"<p><strong>Source:</strong> {alert.source}</p>"
            html += "</div>"
        html += "</div>"
    else:
        html += f"<div style='color: green; font-weight: bold; margin: 10px 0;'>{result.get_due_diligence_message()}</div>"
    
    html += f"<p style='margin-top: 20px;'><em>Last updated: {result.last_update}</em></p>"
    
    return html

def create_ui() -> gr.Blocks:
    """
    Create the Gradio UI.
    
    Returns:
        Gradio Blocks interface
    """
    with gr.Blocks(title="Texas Extract - Name Search") as ui:
        gr.Markdown("# Texas Extract - Name Search")
        gr.Markdown("Search for names in Tarrant County arrest records.")
        
        with gr.Row():
            with gr.Column(scale=3):
                name_input = gr.Textbox(
                    label="Name",
                    placeholder="Enter name (First Middle Last or Last, First Middle)",
                    info="Enter the name you want to search for"
                )
                config_input = gr.Textbox(
                    label="Config Path",
                    value="config.yaml",
                    info="Path to configuration file"
                )
                force_update = gr.Checkbox(
                    label="Force Update",
                    value=False,
                    info="Force update of the report even if it's current"
                )
                search_button = gr.Button("Search", variant="primary")
        
        with gr.Tabs():
            with gr.TabItem("Alerts"):
                alerts_output = gr.HTML()
            with gr.TabItem("Raw JSON"):
                json_output = gr.JSON()
        
        search_button.click(
            fn=search_handler,
            inputs=[name_input, config_input, force_update],
            outputs=[alerts_output, json_output]
        )
        
        gr.Markdown("""
        ## How to Use
        
        1. Enter a name in the search box (either "First Middle Last" or "Last, First Middle" format)
        2. Optionally, provide a path to a custom configuration file
        3. Click the "Search" button
        4. View the results in the "Alerts" and "Raw JSON" tabs
        
        ## About
        
        This tool searches for names in Tarrant County arrest records. It checks if the latest report has been pulled for the day, and if not, it will fetch the latest report before searching.
        
        If a match is found, an alert will be displayed with details about the arrest. If no match is found, a due diligence message will be displayed indicating that the name was not found in the records.
        """)
    
    return ui

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Texas Extract UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the UI on")
    parser.add_argument("--share", action="store_true", help="Create a public link")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    try:
        # Create the UI
        ui = create_ui()
        
        # Launch the UI
        ui.launch(server_port=args.port, share=args.share)
        
        return 0
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())