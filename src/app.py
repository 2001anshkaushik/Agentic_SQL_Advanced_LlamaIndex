"""
Streamlit Frontend for Robot Vacuum Depot - LlamaIndex ReAct Agent
Main application file handling session state and orchestration.
"""
import streamlit as st
import traceback
import logging
import warnings
import json
import re
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Filter out LlamaIndex deprecation warnings and user warnings for cleaner terminal
warnings.filterwarnings("ignore", category=DeprecationWarning, module="llama_index")
warnings.filterwarnings("ignore", category=UserWarning, module="llama_index")
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*DeprecationWarning.*")

# Add src to path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from agent.agent_factory import create_agent
from ui.styles import get_dark_mode_css
from ui.components import render_sidebar, render_welcome_screen, render_chat_message
from utils.parsing import extract_artifacts_from_response

# Configure logging (filter out warnings)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Filter out verbose warnings from llama_index
logging.getLogger("llama_index").setLevel(logging.ERROR)
logging.getLogger("deprecated").setLevel(logging.ERROR)

# Page configuration
st.set_page_config(
    page_title="Robot Vacuum Depot - AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        logger.info("Initializing ReAct Agent...")
        st.session_state.agent = create_agent(verbose=False)  # Set to False to reduce console noise
        logger.info("Agent initialized successfully")


def main():
    """Main Streamlit application."""
    # Inject dark mode CSS
    st.markdown(get_dark_mode_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Welcome screen (if no messages)
    if len(st.session_state.messages) == 0:
        render_welcome_screen()
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        render_chat_message(message, idx)
    
    # Handle auto-query from sample buttons
    user_input = None
    if "auto_query" in st.session_state:
        user_input = st.session_state.auto_query
        del st.session_state.auto_query
    
    # Chat input
    if user_input is None:
        user_input = st.chat_input("Ask a question about the data...")
    
    # Process user input
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "sql_query": None,
            "sql_df": None,
            "python_code": None,
            "plotly_fig": None
        })
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process with agent
        with st.status("Agent is reasoning...", expanded=True) as status:
            try:
                # Clear any previous temp artifacts
                if 'temp_plot_json' in st.session_state:
                    del st.session_state['temp_plot_json']
                if 'temp_code' in st.session_state:
                    del st.session_state['temp_code']
                if 'temp_sql_df' in st.session_state:
                    del st.session_state['temp_sql_df']
                if 'temp_sql_query' in st.session_state:
                    del st.session_state['temp_sql_query']
                
                # Execute agent query
                response = st.session_state.agent.chat(user_input)
                
                # Get response text immediately for debugging
                response_text = None
                if hasattr(response, 'response'):
                    response_text = str(response.response)
                elif hasattr(response, 'get_response'):
                    response_text = str(response.get_response())
                else:
                    response_text = str(response)
                
                logger.debug(f"Response text preview: {response_text[:500]}")
                
                # DIRECT INJECTION: Check session state for artifacts (primary method)
                artifacts = {
                    "sql_query": None,
                    "sql_df": None,
                    "python_code": None,
                    "plotly_fig": None
                }
                
                logger.info("Checking session state for injected artifacts...")
                
                # CRITICAL: Also check response object directly for tool outputs before session state
                # Sometimes tools execute but session state injection fails
                try:
                    # Try to get tool outputs from response immediately
                    if hasattr(response, 'source_nodes') and response.source_nodes:
                        logger.info(f"Found {len(response.source_nodes)} source nodes in response")
                        for source in response.source_nodes:
                            node = getattr(source, 'node', source)
                            if hasattr(node, 'metadata'):
                                metadata = node.metadata
                                if isinstance(metadata, dict):
                                    tool_name = metadata.get('tool_name') or metadata.get('name')
                                    tool_output = metadata.get('tool_output') or metadata.get('output')
                                    
                                    if tool_name == "python_visualizer_tool" and tool_output:
                                        logger.info("Found python_visualizer_tool output in response.source_nodes")
                                        try:
                                            if isinstance(tool_output, str):
                                                output_data = json.loads(tool_output)
                                            else:
                                                output_data = tool_output
                                            
                                            if isinstance(output_data, dict) and "figure_json" in output_data:
                                                fig_dict = output_data["figure_json"]
                                                artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                                logger.info("Successfully extracted Plotly figure from response.source_nodes")
                                                break
                                        except Exception as e:
                                            logger.warning(f"Failed to extract figure from source_nodes: {e}")
                except Exception as e:
                    logger.debug(f"Could not check source_nodes: {e}")
                
                # Extract from session state (direct injection from tools)
                if 'temp_sql_df' in st.session_state:
                    artifacts["sql_df"] = st.session_state['temp_sql_df']
                    logger.info(f"Found SQL DataFrame: {artifacts['sql_df'].shape}")
                    del st.session_state['temp_sql_df']
                
                if 'temp_sql_query' in st.session_state:
                    artifacts["sql_query"] = st.session_state['temp_sql_query']
                    logger.info(f"Found SQL query: {artifacts['sql_query'][:50]}...")
                    del st.session_state['temp_sql_query']
                
                if 'temp_plot_json' in st.session_state:
                    try:
                        fig_dict = st.session_state['temp_plot_json']
                        logger.info(f"Found temp_plot_json, type: {type(fig_dict)}")
                        # Ensure fig_dict is a dict (not a string)
                        if isinstance(fig_dict, str):
                            logger.info("Converting temp_plot_json from string to dict")
                            fig_dict = json.loads(fig_dict)
                        elif not isinstance(fig_dict, dict):
                            logger.error(f"temp_plot_json is not a dict or string: {type(fig_dict)}")
                            raise ValueError(f"Expected dict or string, got {type(fig_dict)}")
                        
                        # Reconstruct Plotly figure from dict
                        # Plotly figure dict has 'data' and 'layout' keys
                        if isinstance(fig_dict, dict) and 'data' in fig_dict:
                            artifacts["plotly_fig"] = go.Figure(
                                data=fig_dict.get('data', []),
                                layout=fig_dict.get('layout', {})
                            )
                            logger.info("Successfully reconstructed Plotly figure from session state")
                        else:
                            raise ValueError(f"Invalid figure dict format: {type(fig_dict)}")
                        del st.session_state['temp_plot_json']
                    except Exception as e:
                        logger.error(f"Failed to reconstruct Plotly figure: {e}", exc_info=True)
                        # Keep the dict in session state for debugging
                        if 'temp_plot_json' in st.session_state:
                            temp_content = st.session_state['temp_plot_json']
                            logger.error(f"temp_plot_json type: {type(temp_content)}")
                            if isinstance(temp_content, dict):
                                logger.error(f"temp_plot_json keys: {list(temp_content.keys())[:10]}")
                            else:
                                logger.error(f"temp_plot_json content (first 500 chars): {str(temp_content)[:500]}")
                
                if 'temp_code' in st.session_state:
                    artifacts["python_code"] = st.session_state['temp_code']
                    logger.info(f"Found Python code ({len(artifacts['python_code'])} chars)")
                    del st.session_state['temp_code']
                
                # FALLBACK 1: Try parsing response with aggressive extraction
                if artifacts["plotly_fig"] is None:
                    logger.warning("Direct injection did not yield Plotly figure, attempting fallback parsing...")
                    fallback_artifacts = extract_artifacts_from_response(response, agent=st.session_state.agent)
                    # Only use fallback if primary method failed
                    if artifacts["sql_query"] is None and fallback_artifacts["sql_query"]:
                        artifacts["sql_query"] = fallback_artifacts["sql_query"]
                        logger.info("Extracted SQL query from fallback parsing")
                    if artifacts["sql_df"] is None and fallback_artifacts["sql_df"] is not None:
                        artifacts["sql_df"] = fallback_artifacts["sql_df"]
                        logger.info("Extracted SQL DataFrame from fallback parsing")
                    if artifacts["python_code"] is None and fallback_artifacts["python_code"]:
                        artifacts["python_code"] = fallback_artifacts["python_code"]
                        logger.info("Extracted Python code from fallback parsing")
                    if artifacts["plotly_fig"] is None and fallback_artifacts["plotly_fig"] is not None:
                        artifacts["plotly_fig"] = fallback_artifacts["plotly_fig"]
                        logger.info("Extracted Plotly figure from fallback parsing")
                
                # FALLBACK 2: If we have Python code and DataFrame but no figure, try re-executing
                if artifacts["plotly_fig"] is None and artifacts["python_code"] and artifacts["sql_df"] is not None:
                    logger.warning("Attempting to re-execute Python code to generate figure...")
                    try:
                        # Use module-level imports (px and go already imported at top)
                        # Prepare execution environment
                        exec_vars = {
                            'pd': pd,
                            'px': px,
                            'go': go,  # Use module-level import
                            'df': artifacts["sql_df"]
                        }
                        
                        # Clean code (remove imports, remove fig.show())
                        code_to_exec = artifacts["python_code"]
                        code_to_exec = re.sub(r'^import\s+plotly\.express.*$', '', code_to_exec, flags=re.MULTILINE)
                        code_to_exec = re.sub(r'^import\s+plotly\.graph_objects.*$', '', code_to_exec, flags=re.MULTILINE)
                        code_to_exec = re.sub(r'fig\.show\(\)', '', code_to_exec)
                        
                        # Execute
                        exec(code_to_exec, {"__builtins__": __builtins__}, exec_vars)
                        
                        if 'fig' in exec_vars:
                            artifacts["plotly_fig"] = exec_vars['fig']
                            logger.info("✅ Successfully generated Plotly figure by re-executing Python code!")
                        else:
                            logger.warning("Re-execution completed but 'fig' variable not found")
                    except Exception as e:
                        logger.error(f"Failed to re-execute Python code: {e}", exc_info=True)
                
                # Response text already extracted above
                
                # Update status
                status.update(label="Query processed successfully!", state="complete")
                
                # Add assistant message with artifacts
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "sql_query": artifacts["sql_query"],
                    "sql_df": artifacts["sql_df"],
                    "python_code": artifacts["python_code"],
                    "plotly_fig": artifacts["plotly_fig"]
                })
                
                logger.info("Query processed successfully")
                
            except Exception as e:
                # Error handling
                error_msg = "An error occurred while processing your query."
                status.update(label="Error occurred", state="error")
                
                # Add error message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sql_query": None,
                    "sql_df": None,
                    "python_code": None,
                    "plotly_fig": None,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
        
        # Rerun to update display
        st.rerun()


if __name__ == "__main__":
    main()
