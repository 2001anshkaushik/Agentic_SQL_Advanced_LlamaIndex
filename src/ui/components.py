"""
UI components for rendering Streamlit interface elements.
"""
import streamlit as st
import pandas as pd


def render_sidebar():
    """Render the sidebar with branding and controls."""
    with st.sidebar:
        # Branding
        st.markdown("""
        <div class="sidebar-branding">
            <h1 class="sidebar-title">🤖 Robot Vacuum Depot</h1>
            <p class="sidebar-tagline">AI-Powered Data Analytics Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Clear Chat Button
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        
        # Sample Query Buttons
        st.header("📊 Sample Queries")
        st.markdown("Click any button to get started:")
        
        sample_queries = [
            ("📊 Pie Chart: Delivery Status", "Show me a pie chart of delivery status distribution"),
            ("📈 Line Chart: Monthly Revenue", "Show me a line chart of monthly revenue trends over time"),
            ("📊 Bar Chart: Revenue by Carrier", "Show me a bar chart of total revenue by shipping carrier"),
            ("📋 Table: Distribution Centers", "Create a table showing all distribution centers and their locations")
        ]
        
        for label, query in sample_queries:
            if st.button(label, key=f"sidebar_btn_{hash(query)}", use_container_width=True):
                st.session_state.auto_query = query
                st.rerun()
        
        st.markdown("---")
        
        # About Section
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant can:
        - Answer questions about orders
        - Generate dynamic visualizations
        - Analyze shipping and delivery data
        - Provide warehouse insights
        """)


def render_welcome_screen():
    """Render welcome screen when no messages exist."""
    st.markdown("""
    <div class="welcome-section">
        <h1 class="welcome-heading">👋 Welcome to Robot Vacuum Depot Analytics</h1>
        <p class="welcome-text">Ask questions about your data or try one of the sample queries in the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Example questions
    st.markdown("### 💡 Example Questions:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- How many orders do we have?")
        st.markdown("- Show me revenue trends")
        st.markdown("- Which carrier is most popular?")
    with col2:
        st.markdown("- Create a pie chart of delivery status")
        st.markdown("- What's our average order value?")
        st.markdown("- Show all distribution centers")


def _detect_chart_type(python_code: str) -> str:
    """
    Detect chart type from Python code.
    
    Args:
        python_code: Python code string
        
    Returns:
        Chart type string (Pie, Bar, Line, Scatter, Histogram, or "Chart")
    """
    if not python_code:
        return None
    
    code_lower = python_code.lower()
    
    if "px.pie" in code_lower or "go.pie" in code_lower:
        return "Pie"
    elif "px.bar" in code_lower or "go.bar" in code_lower:
        return "Bar"
    elif "px.line" in code_lower or "go.line" in code_lower or "go.scatter" in code_lower:
        return "Line"
    elif "px.scatter" in code_lower:
        return "Scatter"
    elif "px.histogram" in code_lower or "go.histogram" in code_lower:
        return "Histogram"
    else:
        return "Chart"


def render_chat_message(message: dict, message_index: int):
    """
    Render a single chat message with collapsible "View Logic: SQL & Data" section.
    
    Args:
        message: Message dictionary with content, artifacts, and metadata
        message_index: Index of message in history (for unique keys)
    """
    role = message["role"]
    
    with st.chat_message(role):
        # Display message content
        st.markdown(message["content"])
        
        # Show error details if this is an error message
        if message.get("error"):
            with st.expander("🔍 Debug Details", expanded=False):
                st.markdown("**Error Type:**")
                st.code(type(message["error"]).__name__, language='text')
                st.markdown("**Error Message:**")
                st.code(str(message["error"]), language='text')
                if message.get("traceback"):
                    st.markdown("**Full Traceback:**")
                    st.code(message["traceback"], language='text')
        
        # Extract artifacts
        sql_query = message.get("sql_query")
        sql_df = message.get("sql_df")
        python_code = message.get("python_code")
        plotly_fig = message.get("plotly_fig")
        
        # Show Plotly chart if available (always visible in Answer section)
        if plotly_fig is not None:
            st.plotly_chart(plotly_fig, use_container_width=True, key=f"plotly_chart_{message_index}")
        elif python_code:
            # Debug: Show message if chart is missing
            st.warning("⚠️ Chart was generated but could not be displayed. Check View Logic section for the Python code.")
        elif sql_df is not None and plotly_fig is None:
            # If we have data but no chart, show info message
            st.info("No visualization was generated for this query.")
        
        # Collapsible "View Logic" section
        if sql_query or sql_df is not None or python_code:
            with st.expander("📊 View Logic", expanded=False):
                # 1. SQL Query Results (DataFrame) - FIRST
                if sql_df is not None:
                    st.markdown("**SQL Query Results:**")
                    st.dataframe(sql_df, use_container_width=True)
                    st.caption(f"Query returned {len(sql_df)} rows")
                
                # 2. Generated SQL Query - SECOND
                if sql_query:
                    st.markdown("**Generated SQL:**")
                    st.code(sql_query, language='sql')
                
                # 3. Chart Type (if visualization) - THIRD
                if plotly_fig is not None and python_code:
                    chart_type = _detect_chart_type(python_code)
                    if chart_type:
                        st.markdown(f"**Chart Type:** {chart_type}")
                
                # 4. Generated Python Code - FOURTH
                if python_code:
                    st.markdown("**Generated Python Code:**")
                    st.code(python_code, language='python')

