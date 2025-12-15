import streamlit as st
import pandas as pd
import os
import hashlib
from github import Github

# --- CORRECTED IMPORTS USING YOUR FILE NAMES ---
# IMPORTANT: Removed the non-existent 'user_management' module.
from views import admin_tool # admin_tool handles login/child/user management
from views import database as db # database handles persistence and will be used for analytics
from views import dashboard, planner, tracker # These map to progress_charts, session_planning, progress_tracking
# ---------------------------------------------


# --- NEW FUNCTION TO COMMIT CHANGES TO GITHUB ---
def commit_to_github():
    """Uses PyGithub to commit the local CSV files back to the repository."""

    # Check if running in Streamlit Cloud (where GITHUB_TOKEN is available)
    if "GITHUB_TOKEN" not in st.secrets:
        st.error("Error: GITHUB_TOKEN not found in secrets. Cannot save to GitHub.")
        return False

    try:
        # 1. Initialize GitHub connection
        g = Github(st.secrets["GITHUB_TOKEN"])
        
        # Use the environment variable to get the current repo name (Format: owner/repo)
        repo_name = os.environ["STREAMLIT_GITHUB_REPO"]
        repo = g.get_repo(repo_name)
        
        # 2. Iterate through data files and commit
        files_to_commit = [f for f in os.listdir("data") if f.endswith(".csv")]
        
        for file_name in files_to_commit:
            full_path = os.path.join("data", file_name)
            
            # Read the content of the file saved on the Streamlit server
            with open(full_path, "r") as file:
                content = file.read()

            # Get the existing file SHA to update it (required by GitHub API)
            try:
                # Get the existing file contents object
                contents = repo.get_contents(full_path, ref="main")
                
                # Update the file
                repo.update_file(
                    path=contents.path, 
                    message=f"AUTO-SAVE: Updated {file_name} from Streamlit app", 
                    content=content, 
                    sha=contents.sha, 
                    branch="main"
                )
            except Exception:
                # If file doesn't exist, create it 
                repo.create_file(
                    path=full_path, 
                    message=f"AUTO-SAVE: Created {file_name} from Streamlit app", 
                    content=content, 
                    branch="main"
                )

        st.session_state["save_status"] = "✅ Successfully saved all data to GitHub!"
        return True

    except Exception as e:
        # st.exception(e) # Uncomment for detailed error logging
        st.session_state["save_status"] = f"❌ Error saving to GitHub: {e.__class__.__name__}. Check token permissions."
        return False
# --- END NEW FUNCTION ---


def main():
    """Main function to run the TILP Connect App."""
    st.set_page_config(layout="wide", page_title="TILP Connect App", page_icon="🧩")

    # --- INITIAL SETUP & STATE MANAGEMENT ---
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['user_role'] = None
        st.session_state['username'] = None

    # Check for default menu setting
    if 'menu_selection' not in st.session_state:
        st.session_state['menu_selection'] = 'Dashboard'
        
    # Check for child filtering setting
    if 'child_link' not in st.session_state:
        st.session_state['child_link'] = 'All'


    # --- AUTHENTICATION ---
    
    if not st.session_state['authenticated']:
        # Calls the login function from your admin_tool module
        admin_tool.show_login_page() 
        return

    # --- SIDEBAR LAYOUT & MENU ---
    with st.sidebar:
        st.title("TILP Connect 🧩")
        st.header(f"Welcome, {st.session_state['username']}!")
        
        # Determine available menu options based on role
        if st.session_state['user_role'] == 'admin':
            menu_options = [
                "Dashboard", 
                "Progress Tracking", 
                "Session Planning", 
                "Data & Analytics", 
                "User Management", # Keep the menu option
                "Child Management"
            ]
        # ... (other roles remain the same)
        elif st.session_state['user_role'] == 'staff':
            menu_options = [
                "Dashboard", 
                "Progress Tracking", 
                "Session Planning",
                "Data & Analytics"
            ]
        elif st.session_state['user_role'] == 'parent':
            menu_options = [
                "Dashboard", 
                "Progress Tracking", 
                "Data & Analytics"
            ]
        else: # Should not happen
             menu_options = ["Dashboard"]

        # Menu Selection
        st.session_state['menu_selection'] = st.radio(
            "Navigation", 
            menu_options,
            index=menu_options.index(st.session_state['menu_selection']) if st.session_state['menu_selection'] in menu_options else 0
        )

        # Child Filter (Available to all roles who can see data)
        if st.session_state['user_role'] in ['admin', 'staff']:
            children_df = db.get_data('children')
            child_names = children_df['child_name'].tolist()
            child_filter_list = ['All'] + sorted(child_names)
            
            # Use st.session_state['child_link'] as the default value to maintain selection
            default_index = child_filter_list.index(st.session_state['child_link']) if st.session_state['child_link'] in child_filter_list else 0
            
            st.session_state['child_link'] = st.selectbox(
                "Filter by Child", 
                child_filter_list,
                index=default_index
            )
        else: # Parents only see their own children
            st.session_state['child_link'] = st.session_state.get('child_link', 'All') # Default to what was set during login

        
        # --- LOGOUT BUTTON ---
        st.sidebar.markdown("---")
        if st.button("Logout"):
            # Calls the logout function from your admin_tool module
            admin_tool.logout_user()


        # --- DATA MANAGEMENT (GITHUB SAVE) ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("💾 Data Persistence")

        if st.sidebar.button("Save Data to GitHub Permanently"):
            with st.spinner("Committing changes to repository..."):
                commit_to_github()
                
        # Display the result of the save operation
        if "save_status" in st.session_state:
            st.sidebar.info(st.session_state["save_status"])


    # --- PAGE ROUTING ---
    
    if st.session_state['menu_selection'] == 'Dashboard':
        st.header("Dashboard")
        
        # Only show charts if a specific child is selected
        if st.session_state['child_link'] != 'All':
            # Uses your dashboard module
            dashboard.display_child_dashboard(st.session_state['child_link'])
        else:
            st.info("Select a child from the filter to view their individual dashboard.")
            
    elif st.session_state['menu_selection'] == 'Progress Tracking':
        st.header("Progress Tracking")
        # Uses your tracker module
        tracker.show_progress_tracking()
        
    elif st.session_state['menu_selection'] == 'Session Planning':
        st.header("Session Planning")
        # Uses your planner module
        planner.show_session_planning()

    elif st.session_state['menu_selection'] == 'Data & Analytics':
        if st.session_state['user_role'] in ['admin', 'staff']:
            st.header("Data & Analytics")
            # Uses your database module (or the correct module)
            db.show_data_analytics() 
        else:
            st.error("Access Denied. You do not have permission to view this page.")

    elif st.session_state['menu_selection'] == 'User Management':
        if st.session_state['user_role'] == 'admin':
            st.header("User Management")
            # Since user_management.py doesn't exist, we assume this function is in admin_tool.py
            admin_tool.show_user_management() 
        else:
            st.error("Access Denied. You do not have permission to view this page.")

    elif st.session_state['menu_selection'] == 'Child Management':
        if st.session_state['user_role'] == 'admin':
            st.header("Child Management")
            # Uses your admin_tool module
            admin_tool.show_child_management()
        else:
            st.error("Access Denied. You do not have permission to view this page.")


# Run the application
if __name__ == '__main__':
    main()
