"""
Streamlit UI for ATS Resume Optimizer
======================================
Simple UI for inputting job descriptions, resumes, and skills,
then running the multi-agent optimization system.
"""

import streamlit as st
from pathlib import Path
import sys

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

from storage.local_storage import LocalStorage
from services.ats_scorer import ATSScorer

# Page config
st.set_page_config(
    page_title="ATS Resume Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .score-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .score-high {
        background-color: #1B5E20;
        border-left: 5px solid #4CAF50;
        color: #E8F5E9;
    }
    .score-high h2, .score-high p {
        color: #E8F5E9 !important;
    }
    .score-medium {
        background-color: #E65100;
        border-left: 5px solid #FF9800;
        color: #FFF3E0;
    }
    .score-medium h2, .score-medium p {
        color: #FFF3E0 !important;
    }
    .score-low {
        background-color: #B71C1C;
        border-left: 5px solid #F44336;
        color: #FFEBEE;
    }
    .score-low h2, .score-low p {
        color: #FFEBEE !important;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "storage" not in st.session_state:
        st.session_state.storage = LocalStorage()
    
    if "resume_text" not in st.session_state:
        # Try to load baseline resume (supports .docx, .pdf, .txt)
        baseline = st.session_state.storage.get_baseline_resume()
        st.session_state.resume_text = baseline or ""
        
        # Show which file was loaded
        if baseline:
            baseline_path = st.session_state.storage.get_baseline_path()
            if baseline_path:
                st.session_state.loaded_resume_file = baseline_path.name
    
    if "user_skills" not in st.session_state:
        skills = st.session_state.storage.get_user_skills()
        st.session_state.user_skills = skills
    
    if "jd_text" not in st.session_state:
        st.session_state.jd_text = ""
    
    if "optimization_result" not in st.session_state:
        st.session_state.optimization_result = None
    
    if "ats_report" not in st.session_state:
        st.session_state.ats_report = None


def render_sidebar():
    """Render the sidebar with settings and saved data."""
    with st.sidebar:
        # Show loaded resume info
        if st.session_state.get("loaded_resume_file"):
            st.success(f"Resume loaded: {st.session_state.loaded_resume_file}")
        elif st.session_state.resume_text:
            st.info("Resume: Custom text")
        else:
            st.warning("No resume loaded")
        
        st.markdown("---")
        st.markdown("### Settings")
        
        # Optimization mode
        mode = st.selectbox(
            "Optimization Mode",
            ["conservative", "balanced", "aggressive"],
            index=1,
            help="Conservative: Minimal changes. Balanced: Moderate optimization. Aggressive: Maximum keyword alignment."
        )
        st.session_state.mode = mode
        
        # Max iterations
        max_iter = st.slider(
            "Max Review Iterations",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum number of revision cycles before accepting result."
        )
        st.session_state.max_iterations = max_iter
        
        st.markdown("---")
        
        # Saved jobs
        st.markdown("### Saved Jobs")
        jobs = st.session_state.storage.list_jobs()
        
        if jobs:
            for job in jobs[:5]:  # Show last 5
                metadata = job.get("metadata", {})
                title = metadata.get("title", "Unknown Job")
                company = metadata.get("company", "Unknown Company")
                
                with st.expander(f"{title[:20]}... @ {company[:15]}"):
                    st.write(f"**Created:** {job.get('created_at', 'N/A')[:10]}")
                    st.write(f"**Versions:** {job.get('versions', 0)}")
                    
                    if st.button("Load", key=f"load_{job['hash']}"):
                        result = st.session_state.storage.get_job_result(job["hash"])
                        if result:
                            st.session_state.optimization_result = result
                            st.session_state.jd_text = job.get("jd_text", "")
                            st.rerun()
        else:
            st.info("No saved jobs yet.")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### Quick Actions")
        
        if st.button("Clear All Inputs"):
            st.session_state.jd_text = ""
            st.session_state.optimization_result = None
            st.session_state.ats_report = None
            st.rerun()
        
        if st.button("Reset to Baseline Resume"):
            baseline = st.session_state.storage.get_baseline_resume()
            if baseline:
                st.session_state.resume_text = baseline
                st.rerun()
            else:
                st.warning("No baseline resume saved.")


def render_input_section():
    """Render the input section for JD, resume, and skills."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            value=st.session_state.jd_text,
            height=400,
            placeholder="Paste the full job description including requirements, responsibilities, and qualifications...",
            key="jd_input"
        )
        st.session_state.jd_text = jd_text
        
        # Job metadata
        with st.expander("Job Details (Optional)"):
            job_title = st.text_input("Job Title", key="job_title")
            company = st.text_input("Company", key="company")
            location = st.text_input("Location", key="location")
            job_url = st.text_input("Job URL", key="job_url")
            
            st.session_state.job_metadata = {
                "title": job_title,
                "company": company,
                "location": location,
                "url": job_url,
            }
    
    with col2:
        st.markdown("### Your Resume")
        
        # Resume source selection
        resume_source = st.radio(
            "Resume Source",
            ["Default (from baseline folder)", "Upload File", "Paste Text"],
            horizontal=True,
            key="resume_source"
        )
        
        if resume_source == "Default (from baseline folder)":
            # Show available baseline files
            baseline_files = st.session_state.storage.get_all_baseline_files()
            
            if baseline_files:
                file_options = {f.name: f for f in baseline_files}
                selected_file = st.selectbox(
                    "Select baseline resume",
                    options=list(file_options.keys()),
                    key="baseline_file_select"
                )
                
                if st.button("Load Selected Resume", key="load_baseline_btn"):
                    file_path = file_options[selected_file]
                    content = st.session_state.storage._read_resume_file(file_path)
                    if content:
                        st.session_state.resume_text = content
                        st.success(f"Loaded: {selected_file}")
                        st.rerun()
                    else:
                        st.error(f"Failed to read {selected_file}")
                
                # Show current baseline info
                current_baseline = st.session_state.storage.get_baseline_path()
                if current_baseline:
                    st.caption(f"Current default: `{current_baseline.name}`")
            else:
                st.info("No resume files found in baseline folder. Upload one or paste text.")
        
        elif resume_source == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload your resume",
                type=["docx", "pdf", "txt"],
                key="resume_uploader"
            )
            
            if uploaded_file:
                if st.button("Parse Uploaded Resume", key="parse_upload_btn"):
                    with st.spinner("Parsing resume..."):
                        content = st.session_state.storage.parse_uploaded_file(uploaded_file)
                        if content:
                            st.session_state.resume_text = content
                            st.success(f"Successfully parsed: {uploaded_file.name}")
                            st.rerun()
                        else:
                            st.error("Failed to parse the uploaded file. Check file format.")
        
        # Always show the text area with current resume content
        resume_text = st.text_area(
            "Resume Content" if resume_source != "Paste Text" else "Paste your resume here",
            value=st.session_state.resume_text,
            height=350,
            placeholder="Resume content will appear here after loading...",
            key="resume_input"
        )
        st.session_state.resume_text = resume_text
        
        # Action buttons
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.button("Save as Baseline", key="save_baseline_btn"):
                if resume_text.strip():
                    st.session_state.storage.save_baseline_resume(resume_text)
                    st.success("Baseline resume saved!")
                else:
                    st.warning("Please enter resume text first.")
        
        with col_save2:
            if st.button("Clear Resume", key="clear_resume_btn"):
                st.session_state.resume_text = ""
                st.rerun()
    
    # Skills section
    st.markdown("### Your Skills")
    st.caption("Add skills you have that may not be explicitly listed in your resume. These can be added during optimization.")
    
    # Display current skills as tags
    current_skills = st.session_state.user_skills
    
    # Input for new skills
    new_skill = st.text_input(
        "Add a skill",
        placeholder="Type a skill and press Enter",
        key="new_skill_input"
    )
    
    col_skills1, col_skills2, col_skills3 = st.columns([2, 1, 1])
    
    with col_skills1:
        if new_skill and st.button("Add Skill"):
            if new_skill not in current_skills:
                current_skills.append(new_skill)
                st.session_state.user_skills = current_skills
                st.session_state.storage.save_user_skills(current_skills)
                st.rerun()
    
    with col_skills2:
        if st.button("Clear All Skills"):
            st.session_state.user_skills = []
            st.session_state.storage.save_user_skills([])
            st.rerun()
    
    # Display skills
    if current_skills:
        skills_display = " | ".join([f"`{skill}`" for skill in current_skills])
        st.markdown(f"**Current skills:** {skills_display}")
    else:
        st.info("No additional skills added. Skills from your resume will still be detected.")


def render_quick_score():
    """Render quick ATS score without full optimization."""
    st.markdown("### Quick ATS Score")
    
    if st.button("Calculate Quick Score", type="secondary"):
        if not st.session_state.jd_text.strip():
            st.warning("Please enter a job description.")
            return
        if not st.session_state.resume_text.strip():
            st.warning("Please enter your resume.")
            return
        
        with st.spinner("Calculating ATS score..."):
            scorer = ATSScorer()
            report = scorer.calculate_score(
                st.session_state.jd_text,
                st.session_state.resume_text,
                st.session_state.user_skills
            )
            st.session_state.ats_report = scorer.to_dict(report)
    
    # Display quick score results
    if st.session_state.ats_report:
        report = st.session_state.ats_report
        score = report["overall_score"]
        
        # Score card
        score_class = "score-high" if score >= 70 else ("score-medium" if score >= 50 else "score-low")
        
        st.markdown(f"""
        <div class="score-card {score_class}">
            <h2 style="margin:0;">ATS Score: {score}/100</h2>
            <p style="margin:0.5rem 0 0 0;">Keyword Match: {report['keyword_analysis']['match_percentage']}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Details in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Matched Keywords:**")
            matched = report["keyword_analysis"]["matched"][:10]
            if matched:
                st.success(", ".join(matched))
            else:
                st.info("No keywords matched")
        
        with col2:
            st.markdown("**Missing Keywords:**")
            missing = report["keyword_analysis"]["missing"][:10]
            if missing:
                st.error(", ".join(missing))
            else:
                st.success("No critical keywords missing!")
        
        # Recommendations
        if report["recommendations"]:
            st.markdown("**Recommendations:**")
            for rec in report["recommendations"]:
                st.markdown(f"- {rec}")


def render_optimization_section():
    """Render the optimization controls and results."""
    st.markdown("---")
    st.markdown("### Full Optimization")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        optimize_btn = st.button(
            "Optimize Resume",
            type="primary",
            help="Run the full multi-agent optimization pipeline"
        )
    
    with col2:
        st.caption(f"Mode: {st.session_state.get('mode', 'balanced')}")
    
    with col3:
        st.caption(f"Max iterations: {st.session_state.get('max_iterations', 3)}")
    
    if optimize_btn:
        if not st.session_state.jd_text.strip():
            st.warning("Please enter a job description.")
            return
        if not st.session_state.resume_text.strip():
            st.warning("Please enter your resume.")
            return
        
        # Run optimization
        with st.spinner("Initializing agents..."):
            try:
                from orchestrator import ATSOrchestrator
                orchestrator = ATSOrchestrator()
            except Exception as e:
                st.error(f"Failed to initialize agents: {e}")
                st.info("Make sure OPENROUTER_API_KEY is set in your .env file")
                return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Running ATS evaluation...")
        progress_bar.progress(20)
        
        try:
            result = orchestrator.optimize(
                jd_text=st.session_state.jd_text,
                resume_text=st.session_state.resume_text,
                user_skills=st.session_state.user_skills,
                job_metadata=st.session_state.get("job_metadata", {}),
                mode=st.session_state.get("mode", "balanced"),
                max_iterations=st.session_state.get("max_iterations", 3),
                save_results=True
            )
            
            progress_bar.progress(100)
            status_text.text("Optimization complete!")
            
            st.session_state.optimization_result = result
            
        except Exception as e:
            st.error(f"Optimization failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            return
    
    # Display optimization results
    if st.session_state.optimization_result:
        render_optimization_results()


def render_optimization_results():
    """Render the optimization results."""
    result = st.session_state.optimization_result
    
    st.markdown("---")
    st.markdown("### Optimization Results")
    
    # Decision badge
    decision = result.get("decision", "UNKNOWN")
    if decision == "APPROVED":
        st.success(f"Decision: {decision} - Resume optimization approved!")
    elif decision == "REJECTED":
        st.error(f"Decision: {decision} - Optimization was rejected")
    else:
        st.warning(f"Decision: {decision}")
    
    st.caption(f"Completed in {result.get('iterations', 'N/A')} iteration(s)")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Optimized Resume", "Review History", "Download"])
    
    with tab1:
        final_resume = result.get("final_resume", "")
        if final_resume:
            st.text_area(
                "Optimized Resume",
                value=final_resume,
                height=500,
                key="optimized_resume_display"
            )
        else:
            st.info("No optimized resume available.")
    
    with tab2:
        history = result.get("history", [])
        if history:
            for i, entry in enumerate(history):
                with st.expander(f"Iteration {entry.get('iteration', i+1)} - {entry.get('decision', 'N/A')}"):
                    st.markdown("**Review:**")
                    st.text(entry.get("review", "No review available")[:2000])
        else:
            st.info("No review history available.")
    
    with tab3:
        final_resume = result.get("final_resume", "")
        job_hash = result.get("job_hash", "")
        
        if final_resume:
            st.markdown("#### Download Optimized Resume")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                st.download_button(
                    label="Download TXT",
                    data=final_resume,
                    file_name="optimized_resume.txt",
                    mime="text/plain",
                    key="download_txt"
                )
            
            with col_dl2:
                st.download_button(
                    label="Download Markdown",
                    data=final_resume,
                    file_name="optimized_resume.md",
                    mime="text/markdown",
                    key="download_md"
                )
            
            with col_dl3:
                # Try to load DOCX file if it exists
                if job_hash:
                    from pathlib import Path
                    job_dir = st.session_state.storage.settings.jobs_dir / job_hash
                    docx_files = list(job_dir.glob("resume_v*.docx"))
                    
                    if docx_files:
                        latest_docx = sorted(docx_files)[-1]
                        with open(latest_docx, "rb") as f:
                            docx_data = f.read()
                        
                        st.download_button(
                            label="Download DOCX",
                            data=docx_data,
                            file_name="optimized_resume.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_docx"
                        )
                    else:
                        st.caption("DOCX not available")
                else:
                    st.caption("DOCX not available")
            
            st.markdown("---")
            st.markdown("**Tip:** DOCX format is best for ATS systems. Most job portals accept .docx files.")
        
        if result.get("saved_to"):
            st.info(f"Files saved to: {result['saved_to']}")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">ATS Resume Optimizer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent AI System for Resume Optimization</p>', unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content
    render_input_section()
    
    st.markdown("---")
    
    # Quick score section
    render_quick_score()
    
    # Full optimization section
    render_optimization_section()
    
    # Footer
    st.markdown("---")
    st.caption("ATS Resume Optimizer - Powered by Multi-Agent AI")


if __name__ == "__main__":
    main()
