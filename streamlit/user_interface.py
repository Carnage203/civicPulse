from pathlib import Path
import sys
import streamlit as st

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

st.set_page_config(layout="wide")

from llm import agents, prompts
from mongodb.handlers import create_complaint

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
                    processed_complaint = agents.analyze_complaint(
                        user_data
                    )                                   
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
    st.header("Admin Analytics")
    st.info("Analytics dashboard coming soon...")

def main():
    st.title("CivicPulse - Citizen Complaint Portal")
    
    tab1, tab2 = st.tabs(["Report Complaint", "Admin Analytics"])
    
    with tab1:
        report_complaint_tab()
    
    with tab2:
        admin_analytics_tab()

if __name__ == "__main__":
    main()

