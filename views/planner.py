# views/planner.py (UPDATED with Date Range Filter)
import streamlit as st
from datetime import date
# Using relative import (dot) since database.py is in the same folder
from .database import save_plan, get_data 
import pandas as pd

def show_page():
    st.header("📅 Daily Session Plan")
    st.info("Plan the structure of the daily session.")

    # Form to capture all planning inputs from Daily Session Plan.csv
    with st.form("session_plan_form"):
        st.subheader("General Session Details")
        col1, col2 = st.columns(2)
        
        with col1:
            plan_date = st.date_input("Date of Session", date.today())
            session_lead = st.selectbox("Session Lead (ECE Lead / Therapist)", 
                                        ["ECE - Lead", "Lead OT", "SLP - Lead", "BC - Lead", "Assistant/BI"])
        
        with col2:
            # Using multiselect for support staff, as per your workflow
            support_staff = st.multiselect("Support Staff (Assistants, etc.)", 
                                           ["Assistant/BI", "Volunteer", "OT-Assistant", "SLP-Assistant", "None"])
            materials_needed = st.text_input("Materials Needed", 
                                             placeholder="e.g., Sensory bins, laminated schedule, weighted blanket")

        st.divider()
        st.subheader("Core Session Blocks")

        warm_up = st.text_area("Warm-Up Activity", 
                               placeholder="e.g., 10 min obstacle course (Gross Motor focus)", 
                               height=100)
        
        learning_block = st.text_area("Learning Block (Main Activity)", 
                                      placeholder="e.g., Circle Time: Reading a story about emotions (Communication/Behavior focus)", 
                                      height=100)

        col3, col4 = st.columns(2)
        with col3:
            regulation_break = st.text_area("Regulation Break", 
                                            placeholder="e.g., 5 min in the sensory tent (Regulation focus)", 
                                            height=100)
        with col4:
            social_play = st.text_area("Small Group / Social Play", 
                                       placeholder="e.g., Turn-taking game with peer (Social Play focus)", 
                                       height=100)

        closing_routine = st.text_area("Closing Routine", 
                                       placeholder="e.g., Tidy up song & farewell", 
                                       height=50)

        internal_notes = st.text_area("Internal Notes for Staff", 
                                      placeholder="e.g., Focus specifically on Tony's visual schedule use today.", 
                                      height=70)

        submitted = st.form_submit_button("📅 Finalize Daily Plan")
        
        if submitted:
            staff_list = ", ".join(support_staff)
            
            save_plan(
                plan_date.isoformat(), 
                session_lead, 
                staff_list, 
                warm_up, 
                learning_block, 
                regulation_break, 
                social_play,
                closing_routine,
                materials_needed,
                internal_notes
            )
            st.success(f"Daily Session Plan for {plan_date.isoformat()} finalized by {session_lead}!")

    st.divider()
    
    # --- Session Plan View and Export (WITH NEW DATE FILTER) ---
    st.subheader("🗓️ All Daily Plans")
    
    try:
        df_plans = get_data("session_plans")
        
        if df_plans.empty:
            st.warning("No session plans saved yet.")
            return

        # Convert date column to datetime objects for filtering
        df_plans['date'] = pd.to_datetime(df_plans['date'])
        
        # --- NEW DATE RANGE FILTER ---
        with st.expander("🔎 Filter Daily Plans by Date Range", expanded=True):
            col_start, col_end = st.columns(2)
            
            # Determine min and max dates in the data
            min_date = df_plans['date'].min().date()
            max_date = df_plans['date'].max().date()

            start_date = col_start.date_input("Start Date", min_date)
            end_date = col_end.date_input("End Date", max_date)
            
            # Ensure start is before end
            if start_date > end_date:
                st.error("Error: Start Date cannot be after End Date.")
                return

        # Apply date filter
        # .dt.date converts the datetime object to just the date component for comparison
        df_filtered = df_plans[
            (df_plans['date'].dt.date >= start_date) & 
            (df_plans['date'].dt.date <= end_date)
        ]

        st.dataframe(df_filtered.sort_values(by="date", ascending=False), use_container_width=True)
        
        # Export function
        if not df_filtered.empty:
            csv_export = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Session Plans to CSV",
                data=csv_export,
                file_name=f'TILP_Session_Plans_{date.today().isoformat()}.csv',
                mime='text/csv',
                help="Download all session plan data as a CSV file."
            )
        
    except Exception as e:
        st.warning(f"Error loading data: {e}")