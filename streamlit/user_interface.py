import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
import streamlit as st

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from llm import agents, chat
from mongodb.handlers import (
    create_complaint,
    get_complaints_by_status,
    update_complaint_status,
    find_similar_complaints
)
from mongodb.clustering_pipeline import run_clustering_pipeline
from mongodb.analytics import get_analytics_data
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="CivicPulse Dashboard", layout="wide")


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
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
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

        /* Action recommendation box */
        .action-box {
            background-color: rgba(52, 152, 219, 0.18);
            border-left: 4px solid #3498DB;
            padding: 6px 10px;
            border-radius: 6px;
            margin-top: 6px;
            color: #EAF2F8;
            font-weight:500;
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
            color: #a5b4fc;
            text-align: left;
            margin-top: -10px;
            margin-bottom: 30px;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)


def report_complaint_tab():
    st.header("📢 Report a Civic Complaint")
    st.markdown("Submit your civic concerns quickly and transparently below 👇")

    with st.container():
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
                        st.error(f"⚠️ Error processing complaint: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all required fields.")





@st.cache_data(ttl=300)
def fetch_complaints_cached(status):
    return get_complaints_by_status(status)


def cards_dashboard_tab():
    if "similar_complaints" not in st.session_state:
        st.session_state.similar_complaints = {}
               

    st.header("📊 Complaint Status Dashboard")
    st.markdown("Manage all complaints from one place ⚡")

    if "refresh_dashboard" not in st.session_state:
        st.session_state.refresh_dashboard = False

    pending = sorted(fetch_complaints_cached("open"), key=lambda c: c.get("updated_at", datetime.now(timezone.utc)), reverse=True)
    resolved = sorted(fetch_complaints_cached("closed"), key=lambda c: c.get("resolved_at", datetime.now(timezone.utc)), reverse=True)
    junk = sorted(fetch_complaints_cached("junk"), key=lambda c: c.get("updated_at", datetime.now(timezone.utc)), reverse=True)

    def display_status_label(status):
        return {"open": "Pending", "closed": "Resolved", "junk": "Junk"}.get(status, "Unknown")

    col1, col2, col3 = st.columns(3)
    
    ITEMS_PER_PAGE = 6
    
    if "page_pending" not in st.session_state: st.session_state.page_pending = 0
    if "page_resolved" not in st.session_state: st.session_state.page_resolved = 0
    if "page_junk" not in st.session_state: st.session_state.page_junk = 0

    def paginate_list(data, page_key):
        total_pages = max(1, (len(data) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        if st.session_state[page_key] >= total_pages:
            st.session_state[page_key] = max(0, total_pages - 1)
        start = st.session_state[page_key] * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        return data[start:end], total_pages

    p_pending, total_pending = paginate_list(pending, "page_pending")
    p_resolved, total_resolved = paginate_list(resolved, "page_resolved")
    p_junk, total_junk = paginate_list(junk, "page_junk")


       
    with col1:
        st.markdown("<div class='kanban-header'>📋 Pending</div>", unsafe_allow_html=True)
        for c in p_pending:
            with st.container(border=True):
                st.markdown(f"<h4>🧑 {c['resident_name']} (Block: {c['block']})</h4>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Complaints:</b> {c['description']}</p>", unsafe_allow_html=True)

                
                summary_text = c["llm_summary"]
                st.markdown(f"<div class='summary-box'><b>🧾 Complaint Summary:</b> {summary_text}</div>", unsafe_allow_html=True)

                action_text = c.get("action_recommendation", "No action recommendation available.")
                st.markdown(f"<div class='action-box'><b>🛠 Recommended Action:</b> {action_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Category:</b> {c['category']} | <b>Severity:</b> {c['severity_level']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Status:</b> {display_status_label(c['status'])}</p>", unsafe_allow_html=True)
                st.markdown(
                    f"<small><i>Last Updated: {c.get('updated_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S')}</i></small>",
                    unsafe_allow_html=True
                )

                if st.button("🔍 Similar Cases", key=f"sim_{c['_id']}"):
                    st.session_state.similar_complaints[c["_id"]] = find_similar_complaints(
                        str(c["_id"]), top_k=5
                    )


                if c["_id"] in st.session_state.similar_complaints:
                       with st.expander("Similar Complaints"):
                            for s in st.session_state.similar_complaints[c["_id"]]:
                                st.markdown(f"**👤 {s['name']}**  \n{s['description']}")   

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✅ Move to Resolve", key=f"res_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "closed",
                            {"resolved_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
                with b2:
                    if st.button("🚮 Move to Junk", key=f"jnk_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "junk",
                            {"updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
            st.markdown("")
        
        if total_pending > 1:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("Previous", key="prev_pend", disabled=st.session_state.page_pending==0):
                    st.session_state.page_pending -= 1
                    st.rerun()
            with c3:
                if st.button("Next", key="next_pend", disabled=st.session_state.page_pending==total_pending-1):
                    st.session_state.page_pending += 1
                    st.rerun()
            st.caption(f"Page {st.session_state.page_pending + 1} of {total_pending}")

    with col2:
        st.markdown("<div class='kanban-header'>✅ Resolved</div>", unsafe_allow_html=True)
        for c in p_resolved:
            with st.container(border=True):
                st.markdown(f"<h4>🧑 {c['resident_name']} (Block: {c['block']})</h4>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Complaints:</b> {c['description']}</p>", unsafe_allow_html=True)

                summary_text = c["llm_summary"]
                st.markdown(f"<div class='summary-box'><b>🧾 Complaint Summary:</b> {summary_text}</div>", unsafe_allow_html=True)

                action_text = c.get("action_recommendation", "No action recommendation available.")
                st.markdown(f"<div class='action-box'><b>🛠 Recommended Action:</b> {action_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Category:</b> {c['category']} | <b>Severity:</b> {c['severity_level']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Status:</b> {display_status_label(c['status'])}</p>", unsafe_allow_html=True)
                st.markdown(
                    f"<small><i>Last Updated: {c.get('resolved_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S')}</i></small>",
                    unsafe_allow_html=True
                )

                if st.button("🔍 Similar Cases", key=f"sim_{c['_id']}"):
                    st.session_state.similar_complaints[c["_id"]] = find_similar_complaints(
                        str(c["_id"]), top_k=5
                    )


                if c["_id"] in st.session_state.similar_complaints:
                       with st.expander("Similar Complaints"):
                            for s in st.session_state.similar_complaints[c["_id"]]:
                                st.markdown(f"**👤 {s['name']}**  \n{s['description']}")

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("↩️ Move to Pending", key=f"pend_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "open",
                            {"updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
                with b2:
                    if st.button("🚮 Move to Junk", key=f"jnk_r_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "junk",
                            {"updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
            st.markdown("")
        
        if total_resolved > 1:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("Previous", key="prev_res", disabled=st.session_state.page_resolved==0):
                    st.session_state.page_resolved -= 1
                    st.rerun()
            with c3:
                if st.button("Next", key="next_res", disabled=st.session_state.page_resolved==total_resolved-1):
                    st.session_state.page_resolved += 1
                    st.rerun()
            st.caption(f"Page {st.session_state.page_resolved + 1} of {total_resolved}")

    with col3:
        st.markdown("<div class='kanban-header'>🚮 Junk</div>", unsafe_allow_html=True)
        for c in p_junk:
            with st.container(border=True):
                st.markdown(f"<h4>🧑 {c['resident_name']} (Block: {c['block']})</h4>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Complaints:</b> {c['description']}</p>", unsafe_allow_html=True)

                summary_text = c["llm_summary"]
                st.markdown(f"<div class='summary-box'><b>🧾 Complaint Summary:</b> {summary_text}</div>", unsafe_allow_html=True)

                action_text = c.get("action_recommendation", "No action recommendation available.")
                st.markdown(f"<div class='action-box'><b>🛠 Recommended Action:</b> {action_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Category:</b> {c['category']} | <b>Severity:</b> {c['severity_level']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><b>Status:</b> {display_status_label(c['status'])}</p>", unsafe_allow_html=True)
                st.markdown(
                    f"<small><i>Last Updated: {c.get('updated_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S')}</i></small>",
                    unsafe_allow_html=True
                )

                if st.button("🔍 Similar Cases", key=f"sim_{c['_id']}"):
                    st.session_state.similar_complaints[c["_id"]] = find_similar_complaints(
                        str(c["_id"]), top_k=5
                    )


                if c["_id"] in st.session_state.similar_complaints:
                       with st.expander("Similar Complaints"):
                            for s in st.session_state.similar_complaints[c["_id"]]:
                                st.markdown(f"**👤 {s['name']}**  \n{s['description']}")

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("↩️ Move to Pending", key=f"pend_j_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "open",
                            {"updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
                with b2:
                    if st.button("✅ Move to Resolve", key=f"res_j_{c['_id']}", use_container_width=True):
                        update_complaint_status(
                            str(c["_id"]),
                            "closed",
                            {"resolved_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)},
                        )
                        fetch_complaints_cached.clear()
                        st.session_state.refresh_dashboard = True
            st.markdown("")
        
        if total_junk > 1:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("Previous", key="prev_junk", disabled=st.session_state.page_junk==0):
                    st.session_state.page_junk -= 1
                    st.rerun()
            with c3:
                if st.button("Next", key="next_junk", disabled=st.session_state.page_junk==total_junk-1):
                    st.session_state.page_junk += 1
                    st.rerun()
            st.caption(f"Page {st.session_state.page_junk + 1} of {total_junk}")

    if st.session_state.refresh_dashboard:
        with st.spinner("Updating complaint status...."):
            time.sleep(0.3)
        st.session_state.refresh_dashboard = False
        st.toast("Complaint status updated successfully!", icon="🟢")
        st.rerun()


def admin_analytics_tab():
    st.header("📊 Admin Analytics Dashboard")
    st.markdown("Gain actionable insights across all civic complaint data 📈")

    analytics = get_analytics_data()
    
    # Layout: Main Content (3 units) + Right Sidebar (1 unit)
    main_col, sidebar_col = st.columns([3, 1])

    with sidebar_col:
        with st.expander("📊 Analytics & Metrics", expanded=True):
            # --- Sidebar Style ---
            st.markdown(
                """
                <style>
                .metric-card {
                    background-color: #f8f9fa;
                    border-left: 5px solid #6366f1;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 15px;
                }
                .metric-title {
                    color: #64748b;
                    font-size: 0.9rem;
                    font-weight: 600;
                    margin-bottom: 5px;
                }
                .metric-value {
                    color: #1e293b;
                    font-size: 1.8rem;
                    font-weight: 700;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            st.markdown("### 📈 Key Metrics")
            
            # Display Metrics
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Complaints</div>
                <div class="metric-value">{analytics['total_complaints']}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #ef4444;">
                    <div class="metric-title">Open</div>
                    <div class="metric-value">{analytics['open_complaints']}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #22c55e;">
                    <div class="metric-title">Resolved</div>
                    <div class="metric-value">{analytics['resolved_complaints']}</div>
                </div>
                """, unsafe_allow_html=True)

            if analytics['average_resolution_time']:
                art = analytics['average_resolution_time']
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #eab308;">
                    <div class="metric-title">Avg Resolution Time</div>
                    <div class="metric-value">{art['hours']} hrs <span style='font-size:0.8rem text-muted'>({art['days']} days)</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📊 Visualizations")
            
            # Donut Chart: Category
            if analytics['category_counts']:
                df_cat = pd.DataFrame(list(analytics['category_counts'].items()), columns=['Category', 'Count'])
                fig_cat = px.pie(df_cat, names='Category', values='Count', hole=0.4, title="Complaints by Category")
                fig_cat.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0), showlegend=False)
                st.plotly_chart(fig_cat, use_container_width=True)

            # Pie Chart: Severity
            if analytics['severity_counts']:
                df_sev = pd.DataFrame(list(analytics['severity_counts'].items()), columns=['Severity', 'Count'])
                fig_sev = px.pie(df_sev, names='Severity', values='Count', title="Severity Distribution")
                fig_sev.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0), showlegend=True)
                st.plotly_chart(fig_sev, use_container_width=True)

            # Bar Chart: Block
            if analytics['block_counts']:
                df_block = pd.DataFrame(list(analytics['block_counts'].items()), columns=['Block', 'Count'])
                # SORTING: Sort by Block name alphabetically
                df_block = df_block.sort_values(by='Block')
                
                fig_block = px.bar(df_block, x='Block', y='Count', title="Complaints by Block", text='Count', color='Count')
                fig_block.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_block, use_container_width=True)


    with main_col:
        
        st.markdown("### 🏘️ Block Issue Summaries")
        st.markdown("Overview of complaints aggregated by residential blocks.")
        
        
        if "block_summaries" not in st.session_state:
            st.session_state.block_summaries = None
        if "page_blocks" not in st.session_state:
            st.session_state.page_blocks = 0
            
        ITEMS_PER_PAGE = 8

        if st.button("📈 Generate Summaries"):
            with st.spinner("Analyzing complaints across all blocks..."):
                st.session_state.block_summaries = agents.summarize_block_issues()
                st.session_state.page_blocks = 0
                
        if st.session_state.block_summaries:
            summaries = st.session_state.block_summaries
            total_pages = max(1, (len(summaries) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            
            
            if st.session_state.page_blocks >= total_pages:
                st.session_state.page_blocks = total_pages - 1
            
            start_idx = st.session_state.page_blocks * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            current_summaries = summaries[start_idx:end_idx]
            
            cols = st.columns(2)
            for i, s in enumerate(current_summaries):
                with cols[i % 2]:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 1px solid #e0e0e0;
                                border-radius: 12px;
                                padding: 20px;
                                margin-bottom: 20px;
                                background-color: #ffffff;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                                height: 100%;
                                transition: transform 0.2s;
                            ">
                                <h4 style='margin-bottom: 15px; color: #1e293b; font-size: 1.1rem; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;'>
                                    🏢 Block {s['block']}
                                </h4>
                                <p style='color: #475569; font-size: 0.95rem; line-height: 1.6; margin: 0;'>
                                    {s['summary']}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            
            if total_pages > 1:
                c1, c2, c3 = st.columns([1, 2, 1])
                with c1:
                    if st.button("Previous", key="prev_blocks", disabled=st.session_state.page_blocks==0):
                        st.session_state.page_blocks -= 1
                        st.rerun()
                with c3:
                    if st.button("Next", key="next_blocks", disabled=st.session_state.page_blocks==total_pages-1):
                        st.session_state.page_blocks += 1
                        st.rerun()
                st.caption(f"Page {st.session_state.page_blocks + 1} of {total_pages}")
        else:
            if not st.session_state.get("block_summaries"): 
                 st.info("🧠 Click **'Generate Summaries'** to view summarized block issues.")

        st.markdown("---")
        
        json_path = Path(project_root) / "mongodb" / "clusters.json"

        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("### 🧭 Major Community Issues")
            st.write("Below are the identified themes from the complaints.")

        with col2:
            st.write("") 
            if st.button("Update Themes"):
                with st.spinner("Analyzing complaints to identify new themes... This process may take a few minutes."):
                    try:
                        run_clustering_pipeline()
                        st.success("Themes updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating themes: {str(e)}")

        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    clusters = json.load(f)
                
                if not clusters:
                    st.warning("No clusters found in the file.")
                else:
                    ITEMS_PER_PAGE_CLUSTERS = 8
                    if "page_clusters" not in st.session_state:
                        st.session_state.page_clusters = 0
                    
                    total_pages_c = max(1, (len(clusters) + ITEMS_PER_PAGE_CLUSTERS - 1) // ITEMS_PER_PAGE_CLUSTERS)
                    
                    if st.session_state.page_clusters >= total_pages_c:
                         st.session_state.page_clusters = total_pages_c - 1
                    
                    start_c = st.session_state.page_clusters * ITEMS_PER_PAGE_CLUSTERS
                    end_c = start_c + ITEMS_PER_PAGE_CLUSTERS
                    current_clusters = clusters[start_c:end_c]

                    cols = st.columns(2)
                    for i, cluster in enumerate(current_clusters):
                        with cols[i % 2]:
                            with st.container():
                                st.markdown(
                                    f"""
                                    <div style="
                                        border: 1px solid #e0e0e0;
                                        border-radius: 12px;
                                        padding: 20px;
                                        margin-bottom: 20px;
                                        background-color: #ffffff;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                                        height: 100%;
                                        transition: transform 0.2s;
                                    ">
                                        <h4 style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; color: #1e293b; font-size: 1.1rem; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;'>
                                            {cluster['cluster_name']}
                                            <span style='background-color: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 20px; font-size: 0.75em; font-weight: 600;'>
                                                {cluster['count']} complaints
                                            </span>
                                        </h4>
                                        <p style='color: #475569; font-size: 0.95rem; line-height: 1.6; margin: 0;'>
                                            {cluster['cluster_summary']}
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    
                    
                    if total_pages_c > 1:
                        c1, c2, c3 = st.columns([1, 2, 1])
                        with c1:
                            if st.button("Previous", key="prev_clusters", disabled=st.session_state.page_clusters==0):
                                st.session_state.page_clusters -= 1
                                st.rerun()
                        with c3:
                            if st.button("Next", key="next_clusters", disabled=st.session_state.page_clusters==total_pages_c-1):
                                st.session_state.page_clusters += 1
                                st.rerun()
                        st.caption(f"Page {st.session_state.page_clusters + 1} of {total_pages_c}")
            except Exception as e:
                st.error(f"Error reading clusters file: {str(e)}")
        else:
            st.warning("Clusters file not found. Please click 'Update Themes' to generate.")

def chat_tab():
    st.header("🤖 CivicPulse Chat Assistant")
    st.markdown("Ask questions about civic issues or complaint statistics 💬")

    query = st.text_area("💬 Enter your question here:")
    if st.button("Send Query"):
        if not query.strip():
            st.warning("⚠️ Please enter a valid question.")
            return
        with st.spinner("🤔 Thinking..."):
            response = chat.chatbot(query)
            with st.container(border=True):
                st.markdown("#### 💡 AI Response:")
                st.markdown(response)


def main():
    st.title("🏙️ CivicPulse - Citizen Complaint Portal")
    st.markdown(
        "<div class='subheading'>The AI-powered platform for smarter community complaint management and analysis.</div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📝 Report Complaint",
            "🗂️ Cards Dashboard",
            "📊 Admin Analytics",
            "🤖 Chat Assistant",
        ]
    )

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