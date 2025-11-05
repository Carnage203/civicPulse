import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from llm import agents, prompts, chat
from mongodb.handlers import create_complaint  

st.set_page_config(layout="wide")



def report_complaint_tab():
    st.header("Report a Civic Complaint")

    name = st.text_input("Your Name")
    location = st.text_input("Block of your residence")
    complaint_text = st.text_area("Describe your complaint in detail")

    user_data = {
        "resident_name": name,
        "block": location,
        "description": complaint_text
    }

    if st.button("Submit Complaint"):
        if name and location and complaint_text:
            with st.spinner("Processing your complaint..."):
                try:
                    processed_complaint = agents.analyze_complaint(user_data)
                    try:
                        create_complaint(processed_complaint)
                    except Exception as db_error:
                        st.error(f"Error saving complaint to database: {str(db_error)}")
                        return
                    st.success("Complaint submitted successfully!")
                except Exception as e:
                    st.error(f"Error processing complaint: {str(e)}")
        else:
            st.warning("Please fill in all fields")



def admin_analytics_tab():
    st.header("Admin Analytics Dashboard")

    st.markdown("### 🧭 Overview")
    st.write("Below is a block-wise summary of major complaints reported by residents.")

    if st.button("Generate Summaries"):
        with st.spinner("Generating summaries for all blocks..."):
            try:
                summaries = agents.summarize_block_issues()

                if not summaries:
                    st.warning("No complaint data found to summarize.")
                    return

                
                for summary in summaries:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 1px solid #ccc;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 10px;
                                background-color: #f9f9f9;">
                                <h4 style='margin-bottom: 5px; color: #2C3E50;'>🏢 Block {summary['block']}</h4>
                                <p style='color: #34495E; margin-top: 0;'>{summary['summary']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            except Exception as e:
                st.error(f"Error generating summaries: {str(e)}")
    else:
        st.info("Click 'Generate Summaries' to view summarized block issues.")



def chat_tab():
    st.header("CivicPulse Chat Assistant")

    query = st.text_area("Ask a question about city issues or complaints:")

    if st.button("Send Query"):
        if not query.strip():
            st.warning("Please enter a message before sending.")
            return

        with st.spinner("Getting response..."):
            try:
                response = chat.chatbot(query)

                if isinstance(response, dict) and "error" in response:
                    st.error("There are no complaints for this query.")
                else:
                    st.subheader("Response:")
                    st.write(response)

            except Exception as e:
                st.error(f"Chatbot error: {str(e)}")



def main():
    st.title("CivicPulse - Citizen Complaint Portal")

    tab1, tab2, tab3 = st.tabs(["Report Complaint", "Admin Analytics", "Chat Assistant"])

    with tab1:
        report_complaint_tab()
    with tab2:
        admin_analytics_tab()
    with tab3:
        chat_tab()


if __name__ == "__main__":
    main()
