import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

# --- Path setup ---
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Imports ---
from llm import agents, chat
from mongodb.handlers import (
    create_complaint,
    get_complaints_by_status,
    update_complaint_status
)

# --- Streamlit page setup ---
st.set_page_config(page_title="CivicPulse Dashboard", layout="wide")

# --- Fixed Light Theme Colors ---
bg_color = "#f9fafc"
card_bg = "#ffffff"
text_color = "#1a1a1a"
accent_gradient = "linear-gradient(90deg, #4A00E0, #8E2DE2)"  # purple-blue

# --- Global Styling ---
st.markdown(f"""
    <style>
        .block-container {{
            padding-top: 2.5rem;
            padding-bottom: 3rem;
            font-family: 'Inter', sans-serif;
            background: {bg_color};
        }}

        h1 {{
            font-size: 2.4rem;
            text-align: center;
            background: -webkit-{accent_gradient};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }}

        h2, h3, h4 {{
            color: {text_color};
        }}

        .subheading {{
            text-align: center;
            color: {text_color};
            font-size: 1.05rem;
            margin-top: -10px;
            opacity: 0.8;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #e9ecef;
            padding: 8px 22px;
            border-radius: 12px;
            font-weight: 500;
            color: #1B2631;
            transition: 0.3s;
        }}
        .stTabs [aria-selected="true"] {{
            background: {accent_gradient} !important;
            color: white !important;
            font-weight: 600;
            transform: scale(1.05);
        }}

        /* Buttons */
        div.stButton > button {{
            background: {accent_gradient};
            color: white;
            font-weight: 600;
            border-radius: 10px;
            padding: 0.6rem 1.5rem;
            border: none;
            transition: all 0.3s ease;
        }}
        div.stButton > button:hover {{
            opacity: 0.9;
            transform: scale(1.03);
        }}

        /* Cards */
        .complaint-card {{
            background: {card_bg};
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 14px;
            padding: 18px 25px;
            margin-bottom: 16px;
            box-shadow: 0px 4px 14px rgba(0,0,0,0.1);
            transition: 0.3s ease;
        }}
        .complaint-card:hover {{
            box-shadow: 0px 6px 20px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }}
        .complaint-card h4 {{
            color: {text_color};
            margin-bottom: 8px;
        }}
        .complaint-card p {{
            color: {text_color};
            opacity: 0.9;
        }}

        /* Chat bubble */
        .ai-response {{
            background: rgba(72,61,139,0.1);
            border-left: 4px solid #8E2DE2;
            border-radius: 10px;
            padding: 12px 15px;
            margin-top: 10px;
            color: {text_color};
        }}
    </style>
""", unsafe_allow_html=True)


# =====================================================
# 📝 Report Complaint
# =====================================================
def report_complaint_tab():
    st.subheader("📢 Report a Civic Complaint")
    st.markdown("Submit your civic concerns quickly and transparently 👇")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Your Name")
    with col2:
        location = st.text_input("🏢 Block of Residence")

    complaint_text = st.text_area("📝 Describe your complaint in detail")

    user_data = {
        "resident_name": name,
        "block": location,
        "description": complaint_text
    }

    if st.button("🚀 Submit Complaint"):
        if name and location and complaint_text:
            with st.spinner("Processing your complaint..."):
                try:
                    processed_complaint = agents.analyze_complaint(user_data)
                    create_complaint(processed_complaint)
                    st.success("✅ Complaint submitted successfully!")
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
        else:
            st.warning("⚠️ Please fill all required fields before submitting.")


# =====================================================
# 🗂️ Cards Dashboard
# =====================================================
def cards_dashboard_tab():
    st.subheader("🗂️ Complaint Status Dashboard")
    st.markdown("Manage and monitor civic complaints by their current status 🔍")

    tab1, tab2, tab3 = st.tabs(["📋 Pending", "✅ Resolved", "🚮 Junk"])

    # Pending Complaints
    with tab1:
        pending = get_complaints_by_status("open")
        if not pending:
            st.info("🎉 No pending complaints right now.")
        else:
            for c in pending:
                st.markdown(f"""
                <div class='complaint-card'>
                    <h4>🧑 {c['resident_name']} (Block: {c['block']})</h4>
                    <p><b>Description:</b> {c['description']}</p>
                    <p><b>Category:</b> {c['category']} | <b>Severity:</b> {c['severity_level']}</p>
                </div>
                """, unsafe_allow_html=True)

                action = st.selectbox("Change status:", ["-- Select Action --", "✅ Mark as Resolved", "🚮 Move to Junk"], key=str(c["_id"]))
                if action == "✅ Mark as Resolved":
                    update_complaint_status(str(c["_id"]), "closed")
                    st.success("✅ Complaint marked as Resolved!")
                    st.rerun()
                elif action == "🚮 Move to Junk":
                    update_complaint_status(str(c["_id"]), "junk")
                    st.warning("🚮 Complaint moved to Junk!")
                    st.rerun()

    # Resolved Complaints (sorted newest first)
    with tab2:
        resolved = get_complaints_by_status("closed")
        if not resolved:
            st.info("No resolved complaints yet.")
        else:
            # Sort newest first using updated_at or _id timestamp
            resolved_sorted = sorted(
                resolved,
                key=lambda c: c.get("updated_at", str(c["_id"])),
                reverse=True
            )

            for c in resolved_sorted:
                st.markdown(f"""
                <div class='complaint-card'>
                    <h4>✅ {c['resident_name']} (Block: {c['block']})</h4>
                    <p><b>Description:</b> {c['description']}</p>
                    <p><b>Resolved At:</b> {c.get('resolved_at', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

    # Junk Complaints (sorted newest first)
    with tab3:
        junk = get_complaints_by_status("junk")
        if not junk:
            st.info("No junk complaints found.")
        else:
            # Sort newest first using updated_at or _id timestamp
            junk_sorted = sorted(
                junk,
                key=lambda c: c.get("updated_at", str(c["_id"])),
                reverse=True
            )

            for c in junk_sorted:
                st.markdown(f"""
                <div class='complaint-card'>
                    <h4>🚮 {c['resident_name']} (Block: {c['block']})</h4>
                    <p><b>Description:</b> {c['description']}</p>
                </div>
                """, unsafe_allow_html=True)


# =====================================================
# 📊 Analytics
# =====================================================
def admin_analytics_tab():
    st.subheader("📊 Admin Analytics Dashboard")
    st.markdown("Get AI-generated summaries of block-level complaints 📈")

    if st.button("📈 Generate Summaries"):
        with st.spinner("Analyzing complaint data..."):
            try:
                summaries = agents.summarize_block_issues()
                for s in summaries:
                    st.markdown(f"""
                    <div class='complaint-card'>
                        <h4>🏢 Block {s['block']}</h4>
                        <p>{s['summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.info("Click 'Generate Summaries' to view block summaries.")


# =====================================================
# 💬 Chat Assistant
# =====================================================
def chat_tab():
    st.subheader("💬 CivicPulse Chat Assistant")
    st.markdown("Ask questions about civic issues or complaint patterns 🧠")

    query = st.text_area("Type your question here:")
    if st.button("Ask"):
        if not query.strip():
            st.warning("Please enter a valid question.")
            return
        with st.spinner("🤔 Thinking..."):
            try:
                response = chat.chatbot(query)
                st.markdown(f"<div class='ai-response'><b>💡 AI Response:</b><br>{response}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")


# =====================================================
# 🚀 Main App
# =====================================================
def main():
    st.title("CivicPulse - Citizen Complaint Portal")
    st.markdown("<p class='subheading'>The AI-powered platform for smarter community complaint management and analysis</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Report Complaint",
        "🗂️ Cards Dashboard",
        "📊 Admin Analytics",
        "🤖 Chat Assistant"
    ])

    with tab1:
        report_complaint_tab()
    with tab2:
        cards_dashboard_tab()
    with tab3:
        admin_analytics_tab()
    with tab4:
        chat_tab()


if __name__ == "__main__":
    main()
