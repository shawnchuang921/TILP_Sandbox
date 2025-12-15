# views/planner.py
import streamlit as st
import pandas as pd
from views import database as db # Required to save/load data
from views import admin_tool # Required if planner needs user info from admin_tool

def show_session_planning():
    """
    Displays the interface for creating and viewing session plans.
    """
    st.markdown("### Create New Session Plan")

    with st.form("session_plan_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date of Session", pd.Timestamp.today())
            lead_staff = st.text_input("Lead Staff (Your Name)")
            support_staff = st.text_input("Support Staff")

        with col2:
            # Fetch children list for selection
            children_df = db.get_data('children')
            child_names = children_df['child_name'].unique().tolist()
            selected_child = st.selectbox("Select Child", child_names)
        
        st.markdown("---")
        st.subheader("Plan Components")

        warm_up = st.text_area("Warm-up Activity")
        learning_block = st.text_area("Learning Block/Main Activity")
        regulation_break = st.text_area("Regulation Break Activity")
        social_play = st.text_area("Social Play/Integration")
        closing_routine = st.text_area("Closing Routine")
        
        materials_needed = st.text_input("Materials Needed (Comma separated)")
        internal_notes = st.text_area("Internal Notes/Reflections")
        
        submitted = st.form_submit_button("Save Session Plan")

        if submitted:
            new_plan = {
                'date': date, 
                'lead_staff': lead_staff, 
                'support_staff': support_staff, 
                'warm_up': warm_up, 
                'learning_block': learning_block, 
                'regulation_break': regulation_break, 
                'social_play': social_play, 
                'closing_routine': closing_routine, 
                'materials_needed': materials_needed, 
                'internal_notes': internal_notes
            }
            if db.add_data('session_plans', new_plan):
                st.success("Session Plan saved successfully! Remember to click 'Save Data to GitHub Permanently' in the sidebar.")
            else:
                st.error("Failed to save session plan.")

    st.markdown("---")
    st.markdown("### Saved Session Plans")
    session_plans_df = db.get_data('session_plans')
    
    if not session_plans_df.empty:
        # Display plan details, perhaps with an option to delete
        st.dataframe(session_plans_df.sort_values(by='date', ascending=False))
    else:
        st.info("No session plans found.")
