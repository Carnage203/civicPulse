import sys
from pathlib import Path
import streamlit as st
from llm import chat

st.set_page_config(page_title="CivicPulse Dashboard", layout="wide")

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from report_complaint import report_complaint_tab
from cards_dasboard import cards_dashboard_tab
from admin_analytics import admin_analytics_tab



st.markdown("""
    <style>
        h1, h2, h3, h4, h5 {
            font-family: 'Segoe UI', sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
            
        .updated-card{
            animation: flash 0.8s ease-in-out;
        }
        @keyframes flash {
            0%{ background-color: #d1fae5;}
            100% {background-color: transparent;}
        }    

        /* Header styling */
        .kanban-header {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
            text-align: center;
            color: white !important;
            background-color: #4f46e5;
            border-radius: 10px;
            padding: 10px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }

        /* Card text styling */
        div[data-testid="stVerticalBlockBorderWrapper"] h4 {
            margin-bottom: 5px;
            color: #154360;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] p {
            margin: 2px 0;
            color: #1C1C1C;
        }

        /* Complaint summary highlight */
        .summary-box {
            background-color: rgba(255, 255, 200, 0.4);
            border-left: 4px solid #facc15;
            padding: 6px 10px;
            border-radius: 6px;
            margin-top: 6px;
        }

      .action-box {
            background-color: #e0f2fe;       
            border-left: 4px solid #0284c7;  
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 6px;
            color: #0f172a;                 
            font-weight: 500;
        }

        /* Background color by status */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(p:contains("Pending")) {
            background-color: #FFFFFF !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(p:contains("Resolved")) {
            background-color: #E8F8F5 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(p:contains("Junk")) {
            background-color: #FDEDEC !important;
        }

        /* Button styling */
        .stButton>button {
            border-radius: 6px;
            padding: 0.3rem 0.8rem;
            font-size: 13px !important;
        }

        /* Subheading styling */
        .subheading {
            font-size: 18px;
            color: #818CF8;
            text-align: left;
            margin-top: -10px;
            margin-bottom: 30px;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)



def chat_tab():
    st.header("🤖 CivicPulse Chat Assistant")
    st.markdown("Ask questions about civic issues or complaint statistics 💬")

    query = st.text_area("💬 Enter your question here:")
    if st.button("Send Query"):
        if not query.strip():
            st.warning("⚠️ Please enter a valid question.")
            return
        with st.spinner("Thinking..."):
            response = chat.chatbot(query)
            with st.container(border=True):
                st.markdown("#### 💡 AI Response:")
                st.markdown(response)


def set_resident():
        st.session_state.user_role = "resident"

def set_admin():
        st.session_state.user_role = "admin"    

def landing_page():
    st.markdown("""
    <div style="text-align:center; margin-top: 80px;">
        <h1>👋 Welcome to CivicPulse</h1>
        <p style="font-size:18px; color:#6b7280;">
            Please select how you want to continue
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.button(
            "👤 I am a Resident",
            use_container_width=True,
            on_click=set_resident
        )

    with col2:
        st.button(
            "🛡️ I am an Admin",
            use_container_width=True,
            on_click=set_admin
        )


def admin_login():
    st.subheader("Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.admin_auth = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def main():
    if "user_role" not in st.session_state:
        landing_page()
        return

    if st.session_state.user_role == "resident":
        st.title("🏙️ CivicPulse - Resident Portal")
        st.markdown(
            "<div class='subheading'>Submit and track civic complaints easily.</div>",
            unsafe_allow_html=True,
        )

        report_complaint_tab()

        if st.button("🔙 Back"):
            del st.session_state.user_role
            st.rerun()

    elif st.session_state.user_role == "admin":

        if not st.session_state.get("admin_auth", False):
            admin_login()
            return

        st.title("🏙️ CivicPulse - Admin Dashboard")

        tab1, tab2, tab3 = st.tabs(
            ["🗂️ Complaints", "📊 Analytics", "🤖 Chat Assistant"]
        )

        with tab1:
            cards_dashboard_tab()
        with tab2:
            admin_analytics_tab()
        with tab3:
            chat_tab()

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
