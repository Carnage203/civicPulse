from mongodb.handlers import create_complaint
import streamlit as st
from llm import agents
import sys
from pathlib import Path


def report_complaint_tab():
    st.header("📢 Report a Civic Complaint")
    st.markdown("Submit your civic concerns quickly and transparently below 👇")

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 Your Name")
        with col2:
            location = st.selectbox(
                "🏢 Block of Residence",
                options=[
                    "A1", "A2", "A3", "A4", "A5",
                    "B1", "B2", "B3", "B4", "B5"
                ]
            )

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
                        st.error(f"⚠️ Error processing complaint: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all required fields.")

