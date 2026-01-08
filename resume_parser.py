# enhanced_resume_parser.py

import fitz  # PyMuPDF
import re
import spacy
from spacy.matcher import PhraseMatcher
import pandas as pd
from dateutil import parser
from collections import Counter

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Extended skills database with categories
SKILLS_DB = {
    'programming_languages': ['python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'perl', 'scala'],
    'web_dev': ['html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'express', 'django', 'flask', 'spring boot', 'asp.net', 'jquery', 'bootstrap', 'tailwind'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'firebase', 'redis', 'oracle', 'cassandra', 'dynamodb', 'sqlite'],
    'cloud': ['aws', 'azure', 'google cloud', 'heroku', 'digitalocean', 'kubernetes', 'docker', 'terraform', 'cloudformation'],
    'data_science': ['machine learning', 'deep learning', 'nlp', 'data analysis', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'tableau', 'power bi'],
    'devops': ['git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'travis ci', 'circle ci', 'ansible', 'puppet', 'chef'],
    'soft_skills': ['communication', 'teamwork', 'leadership', 'problem-solving', 'time management', 'critical thinking', 'adaptability', 'creativity']
}

# Flatten skills for easier checking
ALL_SKILLS = [skill for category in SKILLS_DB.values() for skill in category]

# Education degrees
DEGREES = ['bachelor', 'master', 'phd', 'doctorate', 'bs', 'ms', 'ba', 'mba', 'associate', 'diploma']

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_sections(text):
    """Extract different sections from resume text."""
    text_lower = text.lower()
    
    # Find potential section headers
    education_start = find_section_start(text_lower, ["education", "academic background", "academic qualifications"])
    experience_start = find_section_start(text_lower, ["experience", "work experience", "professional experience", "employment"])
    skills_start = find_section_start(text_lower, ["skills", "technical skills", "core competencies", "expertise"])
    projects_start = find_section_start(text_lower, ["projects", "personal projects", "academic projects"])
    
    # Determine section ends by finding the next section start
    all_starts = sorted([pos for pos in [education_start, experience_start, skills_start, projects_start] if pos > -1])
    
    # Create sections dictionary
    sections = {}
    
    for i, section_name in enumerate([s for s, pos in zip(["education", "experience", "skills", "projects"], 
                                    [education_start, experience_start, skills_start, projects_start]) if pos > -1]):
        start = all_starts[i]
        end = all_starts[i+1] if i+1 < len(all_starts) else len(text_lower)
        sections[section_name] = text[start:end]
    
    return sections

def find_section_start(text, possible_headers):
    """Find the starting position of a section given possible header names."""
    positions = []
    for header in possible_headers:
        # Look for the header followed by a newline or colon
        matches = re.finditer(r'{}[ \t]*(?::|$|\n)'.format(re.escape(header)), text, re.IGNORECASE)
        for match in matches:
            positions.append(match.start())
    
    return min(positions) if positions else -1

def extract_email(text):
    """Extract email address from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None

def extract_phone(text):
    """Extract phone number from text."""
    phone_pattern = r'(?:\+?\d{1,2}\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    return phones[0] if phones else None

def extract_skills(text):
    """Extract skills using NLP and pattern matching."""
    doc = nlp(text.lower())
    
    # Create phrase matcher
    matcher = PhraseMatcher(nlp.vocab)
    
    # Add skill patterns to matcher
    patterns = [nlp(skill) for skill in ALL_SKILLS]
    matcher.add("SKILLS", None, *patterns)
    
    # Find matches
    matches = matcher(doc)
    skills_found = set()
    
    for match_id, start, end in matches:
        span = doc[start:end]
        skills_found.add(span.text)
    
    # Also check for skills directly
    for skill in ALL_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
            skills_found.add(skill)
    
    # Categorize skills
    categorized_skills = {}
    for category, skills in SKILLS_DB.items():
        category_skills = [skill for skill in skills_found if skill in skills]
        if category_skills:
            categorized_skills[category] = category_skills
    
    return {
        "all_skills": list(skills_found),
        "categorized": categorized_skills
    }

def extract_education(text):
    """Extract education information from text."""
    sections = extract_sections(text)
    education_section = sections.get('education', text)  # Use full text if section not found
    
    education_entries = []
    
    # Look for degrees
    degree_pattern = r'(?:' + '|'.join(DEGREES) + r')["\']?s?\s*(?:degree\s*|of\s*|in\s*)?(?:science|arts|engineering|business|education|fine arts|law|medicine|nursing|technology|administration)?'
    degrees = re.finditer(degree_pattern, education_section.lower())
    
    # Extract university names
    university_pattern = r'(?:university|college|institute|school) of [a-z ]+'
    universities = re.finditer(university_pattern, education_section.lower())
    
    # Extract dates
    date_pattern = r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,? \d{4}|(?:19|20)\d{2})'
    dates = re.findall(date_pattern, education_section, re.IGNORECASE)
    
    # Simple parsing for now - future versions could match degrees with universities and dates
    education_info = {
        "degrees": [match.group(0) for match in degrees],
        "institutions": [match.group(0) for match in universities],
        "dates": dates[:4]  # Limit to avoid irrelevant dates
    }
    
    return education_info

def extract_experience(text):
    """Extract work experience from text."""
    sections = extract_sections(text)
    experience_section = sections.get('experience', '')  # Empty if section not found
    
    if not experience_section:
        return {"positions": [], "companies": [], "duration": 0}
    
    # Parse job titles - common titles followed by optional "level" words
    job_titles_pattern = r'\b(?:software|senior|junior|lead|principal|staff|data|product|project|program|web|full[\s-]?stack|front[\s-]?end|back[\s-]?end)? ?(?:engineer|developer|scientist|analyst|manager|director|administrator|designer|architect|consultant)\b'
    job_titles = re.findall(job_titles_pattern, experience_section, re.IGNORECASE)
    
    # Parse company names - this is a simplified approach
    company_pattern = r'(?:at|with|for) ([A-Z][A-Za-z0-9\'\-\.\&]+(?: [A-Z][A-Za-z0-9\'\-\.\&]+)*)'
    companies = re.findall(company_pattern, experience_section)
    
    # Parse dates for experience duration
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,? \d{4}|(?:19|20)\d{2})'
    dates = re.findall(date_pattern, experience_section, re.IGNORECASE)
    
    try:
        # Try to calculate total experience
        total_exp_years = 0
        if len(dates) >= 2:
            date_pairs = [(dates[i], dates[i+1]) for i in range(0, len(dates)-1, 2)]
            for start_date, end_date in date_pairs:
                try:
                    # Handle "Present" or current dates
                    if "present" in end_date.lower():
                        import datetime
                        end_date = datetime.datetime.now().strftime("%b %Y")
                    
                    start = parser.parse(start_date)
                    end = parser.parse(end_date)
                    total_exp_years += (end - start).days / 365.25
                except:
                    pass
    except:
        total_exp_years = 0
    
    return {
        "positions": job_titles[:5],  # Limit to top 5
        "companies": companies[:5],
        "duration": round(total_exp_years, 1) if total_exp_years > 0 else None
    }

def extract_resume_data(resume_file):
    """Main function to extract all resume data."""
    text = extract_text_from_pdf(resume_file)
    
    # Personal information
    email = extract_email(text)
    phone = extract_phone(text)
    
    # Skills
    skills_data = extract_skills(text)
    
    # Education
    education_data = extract_education(text)
    
    # Experience
    experience_data = extract_experience(text)
    
    # Get the raw sections
    sections = extract_sections(text)
    
    return {
        "text": text,
        "email": email,
        "phone": phone,
        "skills": skills_data["all_skills"],
        "categorized_skills": skills_data["categorized"],
        "education": education_data,
        "experience": experience_data,
        "sections": sections
    }