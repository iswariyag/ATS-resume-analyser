
# job_matcher.py

import re
import spacy
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from resume_parser import SKILLS_DB, ALL_SKILLS  # Fixed import statement (was 'enhanced_resume_parser')

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Define keywords categories and importance weights
KEYWORD_WEIGHTS = {
    'must_have': 2.0,    # Keywords that appear in requirements with "must", "required", etc.
    'preferred': 1.5,    # Keywords that appear in preferences with "preferred", "nice to have", etc.
    'experience': 1.8,   # Keywords related to years of experience
    'education': 1.3,    # Keywords related to education requirements
    'standard': 1.0      # All other keywords
}

def clean_text(text):
    """Clean and normalize text."""
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_jd_skills(jd_text):
    """Extract skills from job description with importance levels."""
    jd_text_clean = clean_text(jd_text)
    doc = nlp(jd_text_clean)
    
    # Create phrase matcher for skills
    from spacy.matcher import PhraseMatcher
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(skill) for skill in ALL_SKILLS]
    matcher.add("SKILLS", None, *patterns)
    
    # Find matches
    matches = matcher(doc)
    skills_found = {}
    
    for match_id, start, end in matches:
        span = doc[start:end]
        skill = span.text
        
        # Determine importance level based on context
        context_start = max(0, start - 10)
        context_end = min(len(doc), end + 10)
        context = doc[context_start:context_end].text
        
        if any(req in context for req in ["must", "required", "essential", "necessary"]):
            importance = "must_have"
        elif any(pref in context for pref in ["preferred", "nice to have", "plus", "desirable"]):
            importance = "preferred"
        else:
            importance = "standard"
            
        skills_found[skill] = importance
    
    # Also check for skills directly with word boundaries
    for skill in ALL_SKILLS:
        if skill not in skills_found and re.search(r'\b' + re.escape(skill) + r'\b', jd_text_clean):
            # Determine context for importance
            match = re.search(r'.{0,50}\b' + re.escape(skill) + r'\b.{0,50}', jd_text_clean)
            if match:
                context = match.group(0)
                if any(req in context for req in ["must", "required", "essential", "necessary"]):
                    importance = "must_have"
                elif any(pref in context for pref in ["preferred", "nice to have", "plus", "desirable"]):
                    importance = "preferred"
                else:
                    importance = "standard"
                skills_found[skill] = importance
    
    return skills_found

def extract_experience_requirements(jd_text):
    """Extract experience requirements from job description."""
    years_pattern = r'(\d+)[\+]?\s*(?:-|\s*to\s*)?(?:\d+\s*)?(?:years|year|yr|yrs)(?:\s*of\s*experience)?'
    matches = re.finditer(years_pattern, jd_text.lower())
    
    exp_requirements = []
    for match in matches:
        # Get some context around the match
        start = max(0, match.start() - 50)
        end = min(len(jd_text), match.end() + 50)
        context = jd_text[start:end]
        
        # Extract the years
        years = int(match.group(1))
        
        # Try to determine what the experience is for
        for skill in ALL_SKILLS:
            if skill in context.lower():
                exp_requirements.append((skill, years))
                
    # If no specific skill experience found, look for general experience
    if not exp_requirements:
        general_exp = re.search(years_pattern, jd_text.lower())
        if general_exp:
            exp_requirements.append(("general", int(general_exp.group(1))))
            
    return exp_requirements

def extract_education_requirements(jd_text):
    """Extract education requirements from job description."""
    jd_lower = jd_text.lower()
    
    education_req = {
        "degree_required": False,
        "degree_level": None,
        "field": None
    }
    
    # Check if degree is required
    degree_req_pattern = r"(?:degree required|bachelors? required|masters? required|phd required)"
    if re.search(degree_req_pattern, jd_lower):
        education_req["degree_required"] = True
    
    # Determine degree level
    degree_level_pattern = r"(?:associate|bachelor(?:'s)?|master(?:'s)?|phd|doctorate)"
    degree_match = re.search(degree_level_pattern, jd_lower)
    if degree_match:
        education_req["degree_level"] = degree_match.group(0)
    
    # Try to determine field of study
    field_pattern = r'(?:degree|bachelor|master|phd|doctorate) (?:in|of) ([a-z ]+)'
    field_match = re.search(field_pattern, jd_lower)
    if field_match:
        education_req["field"] = field_match.group(1).strip()
    
    return education_req

def calculate_content_similarity(resume_text, jd_text):
    """Calculate content similarity using TF-IDF and cosine similarity."""
    # Clean texts
    clean_resume = clean_text(resume_text)
    clean_jd = clean_text(jd_text)
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Transform texts to TF-IDF vectors
    tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_jd])
    
    # Calculate cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    return similarity

def calculate_keyword_frequency(resume_text, jd_text):
    """Calculate keyword frequency in resume vs job description."""
    # Extract important keywords from job description
    doc = nlp(jd_text.lower())
    keywords = [token.text for token in doc if not token.is_stop and not token.is_punct and len(token.text) > 2]
    keyword_counts = Counter(keywords)
    
    # Get top keywords
    top_keywords = [word for word, count in keyword_counts.most_common(20)]
    
    # Check presence in resume
    resume_lower = resume_text.lower()
    keyword_presence = {}
    
    for keyword in top_keywords:
        # Count occurrences in resume
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', resume_lower))
        keyword_presence[keyword] = count
    
    # Calculate percentage of important keywords present
    keywords_found = sum(1 for count in keyword_presence.values() if count > 0)
    keyword_coverage = keywords_found / len(top_keywords) if top_keywords else 0
    
    return {
        "keyword_presence": keyword_presence,
        "keyword_coverage": keyword_coverage,
        "top_keywords": top_keywords
    }

def evaluate_experience_match(resume_exp, jd_requirements):
    """Evaluate if resume experience matches job requirements."""
    if not resume_exp.get("duration") or not jd_requirements:
        return 0.5  # Neutral score if can't determine
    
    # Get general experience requirement if any
    general_req = next((years for skill, years in jd_requirements if skill == "general"), 0)
    
    # Compare total experience with requirement
    if general_req > 0:
        resume_years = resume_exp.get("duration", 0)
        if resume_years >= general_req:
            return 1.0
        elif resume_years >= general_req * 0.7:  # 70% of required experience
            return 0.7
        else:
            return 0.4
    
    return 0.5  # No clear requirement

def evaluate_education_match(resume_edu, jd_edu_req):
    """Evaluate if resume education matches job requirements."""
    if not jd_edu_req.get("degree_required", False):
        return 1.0  # No degree required
    
    if not resume_edu.get("degrees"):
        return 0.0  # Degree required but none found
    
    # Check degree level match
    required_level = jd_edu_req.get("degree_level")
    if not required_level:
        return 0.8  # Degree required but no specific level
    
    # Map degree levels to numeric values for comparison
    degree_levels = {
        "associate": 1,
        "bachelor": 2, 
        "bachelors": 2,
        "masters": 3,
        "master": 3,
        "phd": 4,
        "doctorate": 4
    }
    
    # Get highest degree in resume
    resume_degrees = resume_edu.get("degrees", [])
    highest_degree = 0
    
    for degree in resume_degrees:
        for level, value in degree_levels.items():
            if level in degree.lower():
                highest_degree = max(highest_degree, value)
    
    # Get required level numeric value
    req_level_value = 0
    for level, value in degree_levels.items():
        if level in required_level.lower():
            req_level_value = value
            break
    
    # Compare
    if highest_degree >= req_level_value:
        return 1.0
    elif highest_degree == req_level_value - 1:  # One level below
        return 0.7
    else:
        return 0.3

def score_resume(resume_data, jd_text):
    """Score resume against job description with detailed metrics."""
    # Extract job description data
    jd_skills_with_importance = extract_jd_skills(jd_text)
    jd_exp_requirements = extract_experience_requirements(jd_text)
    jd_edu_requirements = extract_education_requirements(jd_text)
    
    # Get resume skills
    resume_skills = set(resume_data['skills'])
    
    # Calculate skills match with importance weighting
    total_weight = 0
    matched_weight = 0
    
    must_have_skills = []
    preferred_skills = []
    standard_skills = []
    
    for skill, importance in jd_skills_with_importance.items():
        weight = KEYWORD_WEIGHTS[importance]
        total_weight += weight
        
        if skill in resume_skills:
            matched_weight += weight
            
            if importance == "must_have":
                must_have_skills.append(skill)
            elif importance == "preferred":
                preferred_skills.append(skill)
            else:
                standard_skills.append(skill)
    
    # Calculate skills match percentage
    skills_match = (matched_weight / total_weight) * 100 if total_weight > 0 else 0
    
    # Calculate content similarity
    content_similarity = calculate_content_similarity(resume_data['text'], jd_text) * 100
    
    # Calculate keyword frequency match
    keyword_data = calculate_keyword_frequency(resume_data['text'], jd_text)
    
    # Evaluate experience match
    exp_match = evaluate_experience_match(resume_data['experience'], jd_exp_requirements) * 100
    
    # Evaluate education match
    edu_match = evaluate_education_match(resume_data['education'], jd_edu_requirements) * 100
    
    # Calculate missing important skills
    missing_must_have = [skill for skill, imp in jd_skills_with_importance.items() 
                         if imp == "must_have" and skill not in resume_skills]
    
    missing_preferred = [skill for skill, imp in jd_skills_with_importance.items() 
                         if imp == "preferred" and skill not in resume_skills]
    
    # Calculate final weighted score
    weights = {
        "skills": 0.40,
        "keywords": 0.20,
        "content": 0.15,
        "experience": 0.15,
        "education": 0.10
    }
    
    final_score = (
        skills_match * weights["skills"] +
        keyword_data["keyword_coverage"] * 100 * weights["keywords"] +
        content_similarity * weights["content"] +
        exp_match * weights["experience"] +
        edu_match * weights["education"]
    )
    
    return {
        "score": round(final_score, 1),
        "component_scores": {
            "skills_match": round(skills_match, 1),
            "keyword_match": round(keyword_data["keyword_coverage"] * 100, 1),
            "content_similarity": round(content_similarity, 1),
            "experience_match": round(exp_match, 1),
            "education_match": round(edu_match, 1)
        },
        "matched_skills": {
            "must_have": must_have_skills,
            "preferred": preferred_skills,
            "standard": standard_skills
        },
        "missing_skills": {
            "must_have": missing_must_have,
            "preferred": missing_preferred
        },
        "keyword_analysis": keyword_data["keyword_presence"],
        "top_keywords": keyword_data["top_keywords"],
        "experience_requirements": jd_exp_requirements,
        "education_requirements": jd_edu_requirements
    }

def generate_improvement_suggestions(analysis_result):
    """Generate suggestions to improve resume match."""
    suggestions = []
    
    # Missing must-have skills
    missing_must = analysis_result["missing_skills"]["must_have"]
    if missing_must:
        suggestions.append({
            "category": "Critical Skills",
            "message": f"Add these essential skills to your resume: {', '.join(missing_must)}",
            "priority": "High"
        })
    
    # Missing preferred skills
    missing_pref = analysis_result["missing_skills"]["preferred"]
    if missing_pref:
        suggestions.append({
            "category": "Preferred Skills",
            "message": f"Consider highlighting experience with: {', '.join(missing_pref)}",
            "priority": "Medium"
        })
    
    # Low component scores
    scores = analysis_result["component_scores"]
    
    if scores["skills_match"] < 50:
        suggestions.append({
            "category": "Skills Alignment",
            "message": "Your skills don't strongly align with job requirements. Review the job posting and tailor your resume accordingly.",
            "priority": "High"
        })
        
    if scores["keyword_match"] < 40:
        suggestions.append({
            "category": "Keywords",
            "message": "Your resume is missing important keywords from the job description. Consider using more industry-specific terminology.",
            "priority": "Medium"
        })
        
    if scores["content_similarity"] < 30:
        suggestions.append({
            "category": "Content Relevance",
            "message": "The overall content of your resume doesn't closely match the job description. Consider rewriting to better align with the role.",
            "priority": "Medium"
        })
        
    if scores["experience_match"] < 50:
        suggestions.append({
            "category": "Experience",
            "message": "Your experience level may not meet the job requirements. Highlight relevant projects or roles that demonstrate equivalent experience.",
            "priority": "High"
        })
        
    if scores["education_match"] < 50:
        suggestions.append({
            "category": "Education",
            "message": "Your education may not meet the job requirements. Consider highlighting relevant coursework or certifications.",
            "priority": "Medium"
        })
    
    # General suggestions if doing well but could improve
    if not suggestions and analysis_result["score"] < 85:
        suggestions.append({
            "category": "Resume Format",
            "message": "Consider using a more ATS-friendly format with clear section headers and bullet points.",
            "priority": "Low"
        })
        suggestions.append({
            "category": "Quantify Achievements",
            "message": "Add measurable achievements and results to strengthen your resume.",
            "priority": "Medium"
        })
    
    # If very low score
    if analysis_result["score"] < 40:
        suggestions.append({
            "category": "Overall Match",
            "message": "This role may not be a good match for your current resume. Consider applying to roles that better align with your experience or making significant updates.",
            "priority": "High"
        })
    
    return suggestions