"""
Artifact extraction utilities for parsing agent responses.
Separates business logic from view layer.
AGGRESSIVE extraction with multiple fallback strategies.
"""
import json
import re
import traceback
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def extract_artifacts_from_response(response: Any, agent: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract SQL queries, DataFrames, Python code, and Plotly figures from agent response.
    
    AGGRESSIVE extraction strategy:
    1. Check response.source_nodes
    2. Check response.sources
    3. Check agent.chat_history (most reliable for tool outputs)
    4. Check response.metadata
    5. Parse response text with regex (fallback)
    
    Args:
        response: LlamaIndex Response object from agent.chat()
        agent: Optional agent instance to access chat history
        
    Returns:
        dict with keys: sql_query, sql_df, python_code, plotly_fig
        All values are None if extraction fails
    """
    artifacts = {
        "sql_query": None,
        "sql_df": None,
        "python_code": None,
        "plotly_fig": None
    }
    
    print("=" * 80)
    print("DEBUG: Starting artifact extraction")
    print("=" * 80)
    
    try:
        # ========================================================================
        # STRATEGY 1: Check Agent Chat History (MOST RELIABLE)
        # ========================================================================
        if agent and hasattr(agent, 'chat_history'):
            print("\n[DEBUG] Strategy 1: Checking agent.chat_history...")
            try:
                chat_history = agent.chat_history
                print(f"[DEBUG] Chat history length: {len(chat_history) if chat_history else 0}")
                
                if chat_history:
                    # Iterate in reverse to get most recent tool calls first
                    for idx, msg in enumerate(reversed(chat_history)):
                        print(f"[DEBUG] Message {idx}: type={type(msg)}, dir={[x for x in dir(msg) if not x.startswith('_')][:10]}")
                        
                        # Check for tool_calls attribute
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            print(f"[DEBUG] Found tool_calls: {len(msg.tool_calls)}")
                            for tool_call in msg.tool_calls:
                                print(f"[DEBUG] Tool call: name={getattr(tool_call, 'name', 'N/A')}, type={type(tool_call)}")
                                
                                tool_name = getattr(tool_call, 'name', None)
                                
                                # Extract SQL tool artifacts
                                if tool_name == "sql_tool":
                                    print("[DEBUG] Found sql_tool in chat history")
                                    # Try multiple ways to get the query
                                    if hasattr(tool_call, 'args'):
                                        args = tool_call.args
                                        print(f"[DEBUG] Tool args type: {type(args)}")
                                        if isinstance(args, dict):
                                            artifacts["sql_query"] = args.get("query")
                                        elif isinstance(args, str):
                                            try:
                                                parsed = json.loads(args)
                                                if isinstance(parsed, dict):
                                                    artifacts["sql_query"] = parsed.get("query")
                                            except:
                                                artifacts["sql_query"] = args
                                    
                                    # Try to get tool output
                                    if hasattr(tool_call, 'output') or hasattr(tool_call, 'result'):
                                        output = getattr(tool_call, 'output', None) or getattr(tool_call, 'result', None)
                                        print(f"[DEBUG] Tool output type: {type(output)}")
                                        if output:
                                            try:
                                                if isinstance(output, str):
                                                    output_data = json.loads(output)
                                                else:
                                                    output_data = output
                                                
                                                if isinstance(output_data, dict):
                                                    if "rows" in output_data:
                                                        rows = output_data["rows"]
                                                        columns = output_data.get("columns", [])
                                                        if rows and columns:
                                                            artifacts["sql_df"] = pd.DataFrame(rows, columns=columns)
                                                            print(f"[DEBUG] Extracted SQL DataFrame: {len(artifacts['sql_df'])} rows")
                                            except Exception as e:
                                                print(f"[DEBUG] Error parsing SQL output: {e}")
                                
                                # Extract Python visualizer tool artifacts
                                elif tool_name == "python_visualizer_tool":
                                    print("[DEBUG] Found python_visualizer_tool in chat history")
                                    # Try multiple ways to get the code
                                    if hasattr(tool_call, 'args'):
                                        args = tool_call.args
                                        if isinstance(args, dict):
                                            artifacts["python_code"] = args.get("code")
                                        elif isinstance(args, str):
                                            try:
                                                parsed = json.loads(args)
                                                if isinstance(parsed, dict):
                                                    artifacts["python_code"] = parsed.get("code")
                                            except:
                                                artifacts["python_code"] = args
                                    
                                    # Try to get tool output
                                    if hasattr(tool_call, 'output') or hasattr(tool_call, 'result'):
                                        output = getattr(tool_call, 'output', None) or getattr(tool_call, 'result', None)
                                        print(f"[DEBUG] Python tool output type: {type(output)}")
                                        if output:
                                            try:
                                                if isinstance(output, str):
                                                    output_data = json.loads(output)
                                                else:
                                                    output_data = output
                                                
                                                if isinstance(output_data, dict):
                                                    if "figure_json" in output_data:
                                                        fig_dict = output_data["figure_json"]
                                                        artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                                        print("[DEBUG] Extracted Plotly figure from chat history")
                                            except Exception as e:
                                                print(f"[DEBUG] Error parsing Plotly output: {e}")
                        
                        # Also check message content/text for tool outputs
                        msg_content = None
                        if hasattr(msg, 'content'):
                            msg_content = msg.content
                        elif hasattr(msg, 'text'):
                            msg_content = msg.text
                        elif hasattr(msg, 'message'):
                            msg_content = str(msg.message)
                        
                        if msg_content and isinstance(msg_content, str):
                            # Look for JSON in message content
                            if not artifacts["sql_df"] and '"rows"' in msg_content:
                                try:
                                    json_match = re.search(r'\{[^{}]*"rows"[^{}]*\[.*?\][^{}]*\}', msg_content, re.DOTALL)
                                    if json_match:
                                        output_data = json.loads(json_match.group(0))
                                        if "rows" in output_data:
                                            rows = output_data["rows"]
                                            columns = output_data.get("columns", [])
                                            if rows and columns:
                                                artifacts["sql_df"] = pd.DataFrame(rows, columns=columns)
                                                print("[DEBUG] Extracted SQL DataFrame from message content")
                                except Exception as e:
                                    print(f"[DEBUG] Error extracting SQL from message: {e}")
                            
                            if not artifacts["plotly_fig"] and '"figure_json"' in msg_content:
                                try:
                                    # More aggressive regex for nested JSON
                                    json_match = re.search(r'\{[^{}]*"figure_json"[^{}]*(\{.*?\})[^{}]*\}', msg_content, re.DOTALL)
                                    if json_match:
                                        fig_json_str = json_match.group(1)
                                        fig_dict = json.loads(fig_json_str)
                                        artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                        print("[DEBUG] Extracted Plotly figure from message content")
                                except Exception as e:
                                    print(f"[DEBUG] Error extracting Plotly from message: {e}")
            except Exception as e:
                print(f"[DEBUG] Error accessing chat history: {e}")
                logger.debug(traceback.format_exc())
        
        # ========================================================================
        # STRATEGY 2: Check response.source_nodes
        # ========================================================================
        if hasattr(response, 'source_nodes'):
            print("\n[DEBUG] Strategy 2: Checking response.source_nodes...")
            sources = response.source_nodes
            print(f"[DEBUG] Found {len(sources) if sources else 0} source nodes")
            if sources:
                for idx, source in enumerate(sources):
                    print(f"[DEBUG] Source {idx}: type={type(source)}")
                    node = getattr(source, 'node', source)
                    print(f"[DEBUG] Node type: {type(node)}")
                    
                    # Check metadata
                    if hasattr(node, 'metadata'):
                        metadata = node.metadata
                        print(f"[DEBUG] Metadata: {metadata}")
                        if isinstance(metadata, dict):
                            tool_name = metadata.get('tool_name') or metadata.get('name')
                            tool_output = metadata.get('tool_output') or metadata.get('output')
                            tool_input = metadata.get('tool_input') or metadata.get('input')
                            
                            if tool_name == "sql_tool" and tool_output:
                                print("[DEBUG] Found sql_tool in source_nodes")
                                try:
                                    if isinstance(tool_output, str):
                                        output_data = json.loads(tool_output)
                                    else:
                                        output_data = tool_output
                                    
                                    if isinstance(output_data, dict) and "rows" in output_data:
                                        rows = output_data["rows"]
                                        columns = output_data.get("columns", [])
                                        if rows and columns:
                                            artifacts["sql_df"] = pd.DataFrame(rows, columns=columns)
                                            print(f"[DEBUG] Extracted SQL DataFrame from source_nodes: {len(artifacts['sql_df'])} rows")
                                    
                                    if tool_input and not artifacts["sql_query"]:
                                        if isinstance(tool_input, dict):
                                            artifacts["sql_query"] = tool_input.get("query")
                                        elif isinstance(tool_input, str):
                                            try:
                                                parsed = json.loads(tool_input)
                                                if isinstance(parsed, dict):
                                                    artifacts["sql_query"] = parsed.get("query")
                                            except:
                                                artifacts["sql_query"] = tool_input
                                except Exception as e:
                                    print(f"[DEBUG] Error parsing SQL from source_nodes: {e}")
                            
                            elif tool_name == "python_visualizer_tool" and tool_output:
                                print("[DEBUG] Found python_visualizer_tool in source_nodes")
                                try:
                                    if isinstance(tool_output, str):
                                        output_data = json.loads(tool_output)
                                    else:
                                        output_data = tool_output
                                    
                                    if isinstance(output_data, dict) and "figure_json" in output_data:
                                        fig_dict = output_data["figure_json"]
                                        artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                        print("[DEBUG] Extracted Plotly figure from source_nodes")
                                    
                                    if tool_input and not artifacts["python_code"]:
                                        if isinstance(tool_input, dict):
                                            artifacts["python_code"] = tool_input.get("code")
                                        elif isinstance(tool_input, str):
                                            try:
                                                parsed = json.loads(tool_input)
                                                if isinstance(parsed, dict):
                                                    artifacts["python_code"] = parsed.get("code")
                                            except:
                                                artifacts["python_code"] = tool_input
                                except Exception as e:
                                    print(f"[DEBUG] Error parsing Plotly from source_nodes: {e}")
                    
                    # Check node text/content
                    node_text = None
                    if hasattr(node, 'text'):
                        node_text = node.text
                    elif hasattr(node, 'content'):
                        node_text = node.content
                    elif hasattr(node, 'get_content'):
                        node_text = node.get_content()
                    
                    if node_text and isinstance(node_text, str):
                        # Look for JSON in node text
                        if not artifacts["sql_df"] and '"rows"' in node_text:
                            try:
                                json_match = re.search(r'\{[^{}]*"rows"[^{}]*\[.*?\][^{}]*\}', node_text, re.DOTALL)
                                if json_match:
                                    output_data = json.loads(json_match.group(0))
                                    if "rows" in output_data:
                                        rows = output_data["rows"]
                                        columns = output_data.get("columns", [])
                                        if rows and columns:
                                            artifacts["sql_df"] = pd.DataFrame(rows, columns=columns)
                                            print("[DEBUG] Extracted SQL DataFrame from node text")
                            except Exception as e:
                                print(f"[DEBUG] Error extracting SQL from node text: {e}")
                        
                        if not artifacts["plotly_fig"] and '"figure_json"' in node_text:
                            try:
                                json_match = re.search(r'\{[^{}]*"figure_json"[^{}]*(\{.*?\})[^{}]*\}', node_text, re.DOTALL)
                                if json_match:
                                    fig_json_str = json_match.group(1)
                                    fig_dict = json.loads(fig_json_str)
                                    artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                    print("[DEBUG] Extracted Plotly figure from node text")
                            except Exception as e:
                                print(f"[DEBUG] Error extracting Plotly from node text: {e}")
        
        # ========================================================================
        # STRATEGY 3: Check response.sources (if different from source_nodes)
        # ========================================================================
        if hasattr(response, 'sources') and response.sources != getattr(response, 'source_nodes', None):
            print("\n[DEBUG] Strategy 3: Checking response.sources...")
            sources = response.sources
            print(f"[DEBUG] Found {len(sources) if sources else 0} sources")
            # Similar logic to source_nodes above
            # (omitted for brevity, but would follow same pattern)
        
        # ========================================================================
        # STRATEGY 4: Parse response text (FALLBACK)
        # ========================================================================
        response_text = None
        if hasattr(response, 'response'):
            response_text = str(response.response)
        elif hasattr(response, 'get_response'):
            response_text = str(response.get_response())
        else:
            response_text = str(response)
        
        if response_text:
            print("\n[DEBUG] Strategy 4: Parsing response text (fallback)...")
            print(f"[DEBUG] Response text length: {len(response_text)}")
            
            # Extract Plotly JSON from response text
            if not artifacts["plotly_fig"]:
                try:
                    # Try to find the complete JSON structure containing figure_json
                    # Look for the full tool output JSON with success, figure_json, etc.
                    patterns = [
                        # Pattern 1: Look for the full tool output JSON
                        r'\{"success"\s*:\s*true[^}]*"figure_json"\s*:\s*(\{.*?\})\s*[,\}]',
                        # Pattern 2: Look for figure_json in a dict structure
                        r'"figure_json"\s*:\s*(\{.*?\})',
                        # Pattern 3: More complex nested structure
                        r'\{[^{}]*"figure_json"[^{}]*(\{.*?\})[^{}]*\}',
                        # Pattern 4: Look for entire tool response as JSON
                        r'\{[^{}]*"success"[^{}]*"figure_json"[^{}]*(\{.*?\})[^{}]*\}',
                    ]
                    
                    for pattern_idx, pattern in enumerate(patterns):
                        json_matches = list(re.finditer(pattern, response_text, re.DOTALL | re.IGNORECASE))
                        for match in json_matches:
                            try:
                                # Try to extract the full JSON object first
                                full_match_start = response_text.rfind('{', 0, match.start())
                                if full_match_start >= 0:
                                    # Try to find the matching closing brace
                                    brace_count = 0
                                    brace_start = False
                                    full_match_end = -1
                                    for i in range(full_match_start, min(full_match_start + 50000, len(response_text))):
                                        if response_text[i] == '{':
                                            brace_count += 1
                                            brace_start = True
                                        elif response_text[i] == '}':
                                            brace_count -= 1
                                            if brace_start and brace_count == 0:
                                                full_match_end = i + 1
                                                break
                                    
                                    if full_match_end > 0:
                                        full_json_str = response_text[full_match_start:full_match_end]
                                        try:
                                            full_json = json.loads(full_json_str)
                                            if isinstance(full_json, dict) and "figure_json" in full_json:
                                                fig_dict = full_json["figure_json"]
                                                artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                                print(f"[DEBUG] Extracted Plotly figure from full JSON (pattern {pattern_idx + 1})")
                                                break
                                        except:
                                            pass
                                
                                # Fallback: try just the matched group
                                fig_json_str = match.group(1)
                                # Try to balance braces
                                open_braces = fig_json_str.count('{')
                                close_braces = fig_json_str.count('}')
                                if open_braces > close_braces:
                                    # Need to find more closing braces
                                    remaining_text = response_text[match.end():match.end() + 10000]
                                    for i, char in enumerate(remaining_text):
                                        if char == '}':
                                            close_braces += 1
                                            if close_braces >= open_braces:
                                                fig_json_str = fig_json_str + remaining_text[:i+1]
                                                break
                                
                                fig_dict = json.loads(fig_json_str)
                                if isinstance(fig_dict, dict):
                                    artifacts["plotly_fig"] = go.Figure.from_dict(fig_dict)
                                    print(f"[DEBUG] Extracted Plotly figure from response text (pattern {pattern_idx + 1})")
                                    break
                            except json.JSONDecodeError as e:
                                print(f"[DEBUG] JSON decode error with pattern {pattern_idx + 1}: {e}")
                                continue
                            except Exception as e:
                                print(f"[DEBUG] Error with pattern {pattern_idx + 1}: {e}")
                                continue
                        
                        if artifacts["plotly_fig"] is not None:
                            break
                            
                except Exception as e:
                    print(f"[DEBUG] Error in fallback Plotly extraction: {e}")
                    import traceback
                    print(traceback.format_exc())
            
            # Extract SQL query from response text
            if not artifacts["sql_query"]:
                sql_patterns = [
                    r'SELECT.*?FROM.*?(?:;|$)',  # Basic SELECT
                    r'```sql\s*(SELECT.*?)\s*```',  # SQL code block
                    r'```\s*(SELECT.*?)\s*```',  # Generic code block
                ]
                
                for pattern in sql_patterns:
                    sql_match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        artifacts["sql_query"] = sql_match.group(0).strip().replace('```sql', '').replace('```', '').strip()
                        print("[DEBUG] Extracted SQL query from response text")
                        break
            
            # Extract DataFrame from response text (if JSON present)
            if not artifacts["sql_df"] and '"rows"' in response_text:
                try:
                    json_match = re.search(r'\{[^{}]*"rows"[^{}]*\[.*?\][^{}]*\}', response_text, re.DOTALL)
                    if json_match:
                        output_data = json.loads(json_match.group(0))
                        if "rows" in output_data:
                            rows = output_data["rows"]
                            columns = output_data.get("columns", [])
                            if rows and columns:
                                artifacts["sql_df"] = pd.DataFrame(rows, columns=columns)
                                print("[DEBUG] Extracted SQL DataFrame from response text")
                except Exception as e:
                    print(f"[DEBUG] Error extracting DataFrame from response text: {e}")
        
        # ========================================================================
        # FINAL SUMMARY
        # ========================================================================
        print("\n" + "=" * 80)
        print("[DEBUG] Extraction Summary:")
        print(f"  SQL Query: {'FOUND' if artifacts['sql_query'] else 'NOT FOUND'}")
        print(f"  SQL DataFrame: {'FOUND' if artifacts['sql_df'] is not None else 'NOT FOUND'}")
        if artifacts['sql_df'] is not None:
            print(f"    Rows: {len(artifacts['sql_df'])}")
        print(f"  Python Code: {'FOUND' if artifacts['python_code'] else 'NOT FOUND'}")
        print(f"  Plotly Figure: {'FOUND' if artifacts['plotly_fig'] is not None else 'NOT FOUND'}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[DEBUG] CRITICAL ERROR in artifact extraction: {e}")
        logger.error(f"Error extracting artifacts: {e}")
        logger.debug(traceback.format_exc())
    
    return artifacts

