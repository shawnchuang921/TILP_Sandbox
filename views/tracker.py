# views/tracker.py
import streamlit as st
import pandas as pd
from views import database as db # Required to save/load data

def show_progress_tracking():
    """
    Displays the interface for recording progress notes.
    """
    
    # 1. Load list data from the database
    disciplines_df = db.get_list_data('disciplines')
    goal_areas_df = db.get_list_data('goal_areas')
    children_df = db.get_data('children')

    discipline_list = disciplines_df['name'].unique().tolist() if not disciplines_df.empty and 'name' in disciplines_df.columns else []
    goal_area_list = goal_areas_df['name'].unique().tolist() if not goal_areas_df.empty and 'name' in goal_areas_df.columns else []
    child_list = children_df['child_name'].unique().tolist() if not children_df.empty and 'child_name' in children_df.columns else []
    
    # 2. Form for New Progress Note
    st.markdown("### Record New Progress Note")
    
    with st.form("progress_note_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", pd.Timestamp.today())
            child_name = st.selectbox("Select Child", child_list)
            discipline = st.selectbox("Discipline", discipline_list)
            
        with col2:
            goal_area = st.selectbox("Goal Area", goal_area_list)
            status = st.selectbox("Status", ["Met Goal", "Working Towards", "Not Observed"])
            
        notes = st.text_area("Progress Notes")
        
        # NOTE: Media path handling is simplified for now as file storage on Streamlit is complex
        media_path = st.text_input("Media Path/Link (Optional)")
        
        submitted = st.form_submit_button("Save Progress Note")

        if submitted:
            new_note = {
                'date': date, 
                'child_name': child_name, 
                'discipline': discipline, 
                'goal_area': goal_area, 
                'status': status, 
                'notes': notes, 
                'media_path': media_path
            }
            if db.add_data('progress', new_note):
                st.success("Progress Note saved successfully! Remember to click 'Save Data to GitHub Permanently' in the sidebar.")
            else:
                st.error("Failed to save progress note.")

    # 3. Display Existing Notes
    st.markdown("---")
    st.markdown("### Recent Progress Entries")
    
    progress_df = db.get_data('progress')
    
    if not progress_df.empty:
        st.dataframe(progress_df.sort_values(by='date', ascending=False))
    else:
        st.info("No progress entries found.")
