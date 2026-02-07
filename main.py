import streamlit as st
import requests
import os

st.set_page_config(page_title="🧠 MoodyBot Enterprise", layout="wide")

API_URL = os.getenv("MOODYBOT_API_URL", "http://localhost:8000")

@st.cache_data(ttl=300)
def call_langgraph_api(text: str):
    try:
        response = requests.post(
            f"{API_URL}/langgraph/analyze",
            json={"input": text},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    st.markdown("# 🧠 MoodyBot Enterprise")
    st.caption("🏢 LangChain + LangGraph + Multi-Agent Production System")

    # Status dashboard
    col1, col2, col3 = st.columns(3)
    with col1: st.success("✅ LangGraph Multi-Agent")
    with col2: st.success("✅ Ollama Llama3.2")
    with col3: st.success("✅ FastAPI Backend")

    # Initialize session state
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    # Main interface
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_area(
            "💭 Describe your current state...",
            placeholder="Stuck on login bug for hours, feeling drained...",
            height=120,
            key="input_text"
        )

    if st.button("🚀 Run LangGraph Agent", type="primary"):
        if not user_input.strip():
            st.warning("Please enter some context first.")
        else:
            with st.spinner("🧠 Multi-agent analysis running..."):
                result = call_langgraph_api(user_input)
                if "error" in result:
                    st.error(f"Backend error: {result['error']}")
                else:
                    display_langgraph_result(result)

    # Demo buttons
    st.markdown("### 🎬 Quick Demos")
    demos = [
        "Stuck on login bug for 2 hours",
        "Exhausted from debugging all night",
        "URGENT deploy to production NOW"
    ]

    cols = st.columns(3)
    for i, demo in enumerate(demos):
        if cols[i].button(f"📱 {demo[:28]}..."):
            st.session_state.input_text = demo
            st.rerun()

def display_langgraph_result(result: dict):
    st.success("🎯 LangGraph Multi-Agent Analysis Complete!")

    # Agent workflow
    st.markdown("### 🛤️ Agent Execution Path")
    for step in result.get("agent_path", []):
        with st.expander(f"👤 {step.get('agent', 'Unknown Agent')}"):
            st.write(f"**Action**: {step.get('action', '-')}")
            st.write(f"**Output**: {step.get('output', '-')}")

    # Final recommendations
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🧠 Primary Mood", result.get("mood", "N/A"))
        st.metric("📅 Scheduled", result.get("scheduled_time", "N/A"))
    with col2:
        success = result.get("success_prob", 0)
        st.metric("🎯 Success Rate", f"{success:.1%}")
        st.metric("💡 Tactic", result.get("tactic", "N/A"))

    st.balloons()

if __name__ == "__main__":
    main()
