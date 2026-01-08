import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from resume_parser import extract_resume_data
from job_matcher import score_resume, generate_improvement_suggestions

# Set page configuration
st.set_page_config(
    page_title="ATS Resume Analyzer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .suggestion-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        margin: 10px 0;
    }
    .suggestion-medium {
        background-color: #fff8e1;
        border-left: 5px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
    }
    .suggestion-low {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 10px;
        margin: 10px 0;
    }
    .skill-tag {
        background-color: #e3f2fd;
        border-radius: 15px;
        padding: 5px 10px;
        margin: 5px;
        display: inline-block;
    }
    .missing-skill-tag {
        background-color: #ffebee;
        border-radius: 15px;
        padding: 5px 10px;
        margin: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("<h1 class='main-header'>ATS Resume Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload your resume and paste job description to analyze compatibility</p>", unsafe_allow_html=True)
    
    # Create sidebar for navigation
    st.sidebar.title("Navigation")
    pages = ["Home", "How It Works", "About"]
    selection = st.sidebar.radio("Go to", pages)
    
    if selection == "Home":
        home_page()
    elif selection == "How It Works":
        how_it_works_page()
    else:
        about_page()

def home_page():
    # Create two columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='sub-header'>Upload Resume</h3>", unsafe_allow_html=True)
        resume_file = st.file_uploader("Upload PDF resume", type=["pdf"])
        
        if resume_file:
            st.success("Resume uploaded successfully!")
            # Preview option
            if st.checkbox("Preview Resume Data"):
                with st.spinner("Extracting resume data..."):
                    resume_data = extract_resume_data(resume_file)
                    
                    # Display basic resume info
                    st.subheader("Resume Information")
                    if resume_data["email"]:
                        st.write(f"📧 Email: {resume_data['email']}")
                    if resume_data["phone"]:
                        st.write(f"📞 Phone: {resume_data['phone']}")
                    
                    # Display skills
                    st.subheader("Skills Detected")
                    skill_html = ""
                    for skill in resume_data["skills"][:15]:  # Limit to top 15 skills
                        skill_html += f"<span class='skill-tag'>{skill}</span>"
                    st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                    
                    # Display experience
                    st.subheader("Experience")
                    if resume_data["experience"]["duration"]:
                        st.write(f"🕒 Years of Experience: {resume_data['experience']['duration']}")
                    if resume_data["experience"]["positions"]:
                        st.write("🏢 Positions Held:", ", ".join(resume_data["experience"]["positions"][:3]))
                    
                    # Display education
                    st.subheader("Education")
                    if resume_data["education"]["degrees"]:
                        st.write("🎓 Degrees:", ", ".join(resume_data["education"]["degrees"][:2]))
                    if resume_data["education"]["institutions"]:
                        st.write("🏫 Institutions:", ", ".join(resume_data["education"]["institutions"][:2]))
    
    with col2:
        st.markdown("<h3 class='sub-header'>Job Description</h3>", unsafe_allow_html=True)
        job_description = st.text_area("Paste Job Description here", height=300)
        
        # Keywords extraction option
        if job_description:
            if st.checkbox("Extract Key Requirements"):
                with st.spinner("Analyzing job description..."):
                    from job_matcher import extract_jd_skills, extract_experience_requirements, extract_education_requirements
                    
                    jd_skills = extract_jd_skills(job_description)
                    exp_requirements = extract_experience_requirements(job_description)
                    edu_requirements = extract_education_requirements(job_description)
                    
                    # Display must-have skills
                    st.subheader("Required Skills")
                    must_have = [skill for skill, imp in jd_skills.items() if imp == "must_have"]
                    preferred = [skill for skill, imp in jd_skills.items() if imp == "preferred"]
                    
                    if must_have:
                        st.markdown("**Must Have:**")
                        st.write(", ".join(must_have))
                    
                    if preferred:
                        st.markdown("**Preferred:**")
                        st.write(", ".join(preferred))
                    
                    # Display experience requirements
                    if exp_requirements:
                        st.subheader("Experience Requirements")
                        for skill, years in exp_requirements:
                            st.write(f"• {years}+ years of {skill}")
                    
                    # Display education requirements
                    st.subheader("Education Requirements")
                    if edu_requirements["degree_required"]:
                        st.write(f"• Degree Required: Yes")
                        if edu_requirements["degree_level"]:
                            st.write(f"• Level: {edu_requirements['degree_level'].title()}")
                        if edu_requirements["field"]:
                            st.write(f"• Field: {edu_requirements['field'].title()}")
                    else:
                        st.write("• No specific degree requirement detected")
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button("Analyze Resume", use_container_width=True)
    
    # Results section
    if analyze_button:
        if resume_file and job_description:
            with st.spinner("Analyzing your resume against the job description..."):
                # Extract resume data
                resume_data = extract_resume_data(resume_file)
                
                # Score resume
                result = score_resume(resume_data, job_description)
                
                # Generate suggestions
                suggestions = generate_improvement_suggestions(result)
                
                # Display Results in tabs
                tab1, tab2, tab3, tab4 = st.tabs(["Overall Score", "Detail Analysis", "Skills Match", "Improvement Plan"])
                
                with tab1:
                    st.markdown("<h2 style='text-align: center;'>Resume ATS Score</h2>", unsafe_allow_html=True)
                    
                    # Display score with gauge
                    score = result["score"]
                    
                    # Create three columns for the score display
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        # Score gauge chart
                        fig = px.pie(values=[score, 100-score], 
                                    names=['Score', 'Gap'],
                                    hole=0.7,
                                    color_discrete_sequence=['#1E88E5', '#F5F5F5'])
                        fig.update_layout(
                            annotations=[dict(text=f"{score}%", x=0.5, y=0.5, font_size=40, showarrow=False)],
                            showlegend=False,
                            height=300,
                            margin=dict(l=0, r=0, t=0, b=0),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Score interpretation
                    if score >= 80:
                        st.success("Excellent match! Your resume is well-aligned with this job.")
                    elif score >= 60:
                        st.info("Good match. Some improvements could help strengthen your application.")
                    else:
                        st.warning("Moderate to low match. Consider significant updates to improve your chances.")
                    
                    # Quick summary
                    st.subheader("Quick Summary")
                    col1, col2 = st.columns(2)
                    
                    matched_skills_count = sum(len(skills) for skills in result["matched_skills"].values())
                    missing_skills_count = sum(len(skills) for skills in result["missing_skills"].values())
                    
                    with col1:
                        st.metric("Skills Matched", f"{matched_skills_count} skills")
                        st.metric("Missing Skills", f"{missing_skills_count} skills")
                    
                    with col2:
                        st.metric("Experience Match", f"{result['component_scores']['experience_match']}%")
                        st.metric("Education Match", f"{result['component_scores']['education_match']}%")
                
                with tab2:
                    st.markdown("<h2 style='text-align: center;'>Detailed Analysis</h2>", unsafe_allow_html=True)
                    
                    # Component scores visualization
                    st.subheader("Component Scores")
                    
                    # Prepare data for radar chart
                    categories = list(result["component_scores"].keys())
                    categories = [cat.replace('_', ' ').title() for cat in categories]
                    values = list(result["component_scores"].values())
                    
                    # Create radar chart
                    fig = px.line_polar(
                        r=values,
                        theta=categories,
                        line_close=True,
                        range_r=[0, 100],
                        start_angle=0,
                    )
                    fig.update_traces(fill='toself')
                    st.plotly_chart(fig)
                    
                    # Component scores details
                    for category, score in result["component_scores"].items():
                        st.write(f"**{category.replace('_', ' ').title()}**: {score}%")
                    
                    # Keyword analysis
                    st.subheader("Keyword Analysis")
                    
                    # Convert to dataframe for visualization
                    keyword_data = {
                        "Keyword": list(result["keyword_analysis"].keys()),
                        "Occurrences": list(result["keyword_analysis"].values())
                    }
                    
                    # Filter to top keywords for better visualization
                    keyword_df = pd.DataFrame(keyword_data)
                    keyword_df = keyword_df.sort_values("Occurrences", ascending=False).head(10)
                    
                    # Create horizontal bar chart
                    fig = px.bar(
                        keyword_df,
                        x="Occurrences",
                        y="Keyword",
                        orientation='h',
                        title="Top 10 Keywords Occurrence in Your Resume",
                        color="Occurrences",
                        color_continuous_scale=px.colors.sequential.Blues
                    )
                    st.plotly_chart(fig)
                
                with tab3:
                    st.markdown("<h2 style='text-align: center;'>Skills Assessment</h2>", unsafe_allow_html=True)
                    
                    # Matched Skills
                    st.subheader("Matched Skills")
                    
                    # Must have skills
                    if result["matched_skills"]["must_have"]:
                        st.markdown("**Critical Skills (Must Have):**")
                        skill_html = ""
                        for skill in result["matched_skills"]["must_have"]:
                            skill_html += f"<span class='skill-tag'><b>{skill}</b></span>"
                        st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                    
                    # Preferred skills
                    if result["matched_skills"]["preferred"]:
                        st.markdown("**Preferred Skills:**")
                        skill_html = ""
                        for skill in result["matched_skills"]["preferred"]:
                            skill_html += f"<span class='skill-tag'>{skill}</span>"
                        st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                    
                    # Standard skills
                    if result["matched_skills"]["standard"]:
                        st.markdown("**Other Matched Skills:**")
                        skill_html = ""
                        for skill in result["matched_skills"]["standard"]:
                            skill_html += f"<span class='skill-tag'>{skill}</span>"
                        st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                    
                    # Missing Skills
                    st.subheader("Missing Skills")
                    
                    # Must have missing skills
                    if result["missing_skills"]["must_have"]:
                        st.markdown("**Critical Skills (Must Have):**")
                        skill_html = ""
                        for skill in result["missing_skills"]["must_have"]:
                            skill_html += f"<span class='missing-skill-tag'><b>{skill}</b></span>"
                        st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                    
                    # Preferred missing skills
                    if result["missing_skills"]["preferred"]:
                        st.markdown("**Preferred Skills:**")
                        skill_html = ""
                        for skill in result["missing_skills"]["preferred"]:
                            skill_html += f"<span class='missing-skill-tag'>{skill}</span>"
                        st.markdown(f"<div>{skill_html}</div>", unsafe_allow_html=True)
                
                with tab4:
                    st.markdown("<h2 style='text-align: center;'>Improvement Plan</h2>", unsafe_allow_html=True)
                    
                    if not suggestions:
                        st.success("Great job! Your resume is well-optimized for this position.")
                    else:
                        # Group suggestions by priority
                        high_priority = [s for s in suggestions if s["priority"] == "High"]
                        medium_priority = [s for s in suggestions if s["priority"] == "Medium"]
                        low_priority = [s for s in suggestions if s["priority"] == "Low"]
                        
                        # Display high priority suggestions
                        if high_priority:
                            st.subheader("Critical Improvements")
                            for suggestion in high_priority:
                                st.markdown(f"""
                                <div class='suggestion-high'>
                                    <h4>{suggestion['category']}</h4>
                                    <p>{suggestion['message']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display medium priority suggestions
                        if medium_priority:
                            st.subheader("Recommended Improvements")
                            for suggestion in medium_priority:
                                st.markdown(f"""
                                <div class='suggestion-medium'>
                                    <h4>{suggestion['category']}</h4>
                                    <p>{suggestion['message']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display low priority suggestions
                        if low_priority:
                            st.subheader("Minor Improvements")
                            for suggestion in low_priority:
                                st.markdown(f"""
                                <div class='suggestion-low'>
                                    <h4>{suggestion['category']}</h4>
                                    <p>{suggestion['message']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # General advice for ATS optimization
                        st.subheader("ATS Optimization Tips")
                        st.markdown("""
                        * **Use standard section headers** like "Experience," "Education," and "Skills"
                        * **Mirror keywords** from the job description in your resume
                        * **Use standard formatting** and avoid tables, images, or special characters
                        * **Quantify achievements** with numbers and metrics when possible
                        * **Be specific** about technologies, methodologies, and tools you've used
                        * **Submit in PDF format** to preserve formatting across different systems
                        """)
        else:
            st.error("Please upload your resume and provide a job description first.")

def how_it_works_page():
    st.markdown("<h2 class='main-header'>How It Works</h2>", unsafe_allow_html=True)
    
    st.write("""
    Our ATS Resume Analyzer uses advanced natural language processing to evaluate how well your resume matches a specific job description. 
    Here's how the process works:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Resume Analysis")
        st.markdown("""
        1. **Text Extraction**: We extract text from your PDF resume
        2. **Information Parsing**: We identify key sections like education, experience, and skills
        3. **Skills Detection**: We detect technical and soft skills present in your resume
        4. **Experience Analysis**: We analyze your work history and experience level
        5. **Education Assessment**: We evaluate your educational background
        """)
    
    with col2:
        st.markdown("### Job Description Analysis")
        st.markdown("""
        1. **Requirements Extraction**: We identify must-have and preferred skills
        2. **Keyword Analysis**: We determine important keywords and their frequency
        3. **Experience Requirements**: We detect required years of experience
        4. **Education Requirements**: We identify degree requirements
        5. **Critical Skills Identification**: We determine which skills are most important
        """)
    
    st.markdown("### Scoring System")
    st.markdown("""
    Your resume is scored based on multiple factors with the following weights:
    
    * **Skills Match**: 40% - How well your skills align with job requirements
    * **Keyword Coverage**: 20% - Presence of important job description keywords
    * **Content Relevance**: 15% - Overall similarity between resume and job description
    * **Experience Match**: 15% - Alignment with required experience level
    * **Education Match**: 10% - Alignment with educational requirements
    
    Based on these factors, we generate a comprehensive score and provide detailed feedback to help you optimize your resume.
    """)

def about_page():
    st.markdown("<h2 class='main-header'>About ATS Resume Analyzer</h2>", unsafe_allow_html=True)
    
    st.write("""
    ### What is an ATS?
    
    An Applicant Tracking System (ATS) is software used by employers to manage and filter job applications. 
    These systems scan resumes to determine which candidates most closely match the job requirements before 
    a human recruiter reviews them.
    
    ### Why Use Our Analyzer?
    
    Our ATS Resume Analyzer helps you:
    
    * **Understand how ATS systems view your resume**
    * **Identify missing keywords and skills**
    * **Optimize your resume for specific job descriptions**
    * **Increase your chances of getting past the initial screening**
    * **Receive personalized suggestions for improvements**
    
    ### Privacy
    
    We take your privacy seriously. All resume analysis is done in your browser, and we do not store 
    your resume or job description data after your session ends.
    """)

if __name__ == "__main__":
    main()