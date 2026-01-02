from mongodb.handlers import (
    get_complaints_by_status,
    update_complaint_status,
    find_similar_complaints
)
import streamlit as st
from datetime import datetime, timezone
import time


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
                st.markdown(f"<p><b>Complaint:</b> {c['description']}</p>", unsafe_allow_html=True)

                
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
                st.markdown(f"<p><b>Complaint:</b> {c['description']}</p>", unsafe_allow_html=True)

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
                st.markdown(f"<p><b>Complaint:</b> {c['description']}</p>", unsafe_allow_html=True)

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