import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path
from mongodb.analytics import get_analytics_data
from llm import agents
from mongodb.clustering_pipeline import run_clustering_pipeline
from mongodb.analytics import get_analytics_data
import sys



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
                 st.info("Click **'Generate Summaries'** to view summarized block issues.")

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