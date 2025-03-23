import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from pdfminer.high_level import extract_text
from io import BytesIO
import logging

# Initialize the logger
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

def extract_skills(text):
    if not text:
        logger.info("No text provided for skill extraction.")  # Log info message
        return []
    
    skill_keywords = [
        "python", "django", "machine learning", "javascript", "react", 
        "java", "sql", "html", "css", "data analysis", "flask", 
        "node.js", "angular", "vue.js", "docker", "kubernetes", 
        "aws", "azure", "git", "rest api", "graphql", "mongodb", 
        "postgresql", "linux", "bash", "pandas", "numpy", "tensorflow", 
        "pytorch", "scikit-learn", "big data", "spark", "hadoop"
    ]
    
    doc = nlp(text.lower())
    skills = []
    
    logger.debug(f"Tokens in Text: {[token.text for token in doc]}")  # Log debug message
    
    for token in doc:
        if token.text in skill_keywords:
            skills.append(token.text)
    
    logger.debug(f"Extracted Skills: {skills}")  # Log debug message
    return skills

def extract_text_from_pdf(pdf_file):
    """
    Extracts text from a PDF file.
    Handles both file paths and InMemoryUploadedFile objects.
    """
    try:
        if hasattr(pdf_file, 'read'):  # Check if it's a file-like object
            pdf_content = pdf_file.read()
            pdf_stream = BytesIO(pdf_content)
            text = extract_text(pdf_stream)
        else:
            text = extract_text(pdf_file)
        
        logger.info("Successfully extracted text from PDF.")  # Log info message
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")  # Log error message
        return None

def match_projects(user_skills, projects):
    vectorizer = TfidfVectorizer()
    skill_matrix = vectorizer.fit_transform([user_skills] + [p.required_skills for p in projects])
    similarities = cosine_similarity(skill_matrix[0:1], skill_matrix[1:])
    matched_indices = similarities.argsort()[0][::-1]
    return [projects[i] for i in matched_indices]

def fetch_real_time_jobs(skills, location='us'):
    ADZUNA_API_ID = '146640b5'
    ADZUNA_API_KEY = 'ab9bf9bfd9a702edb7b063759d631313'
    base_url = 'https://api.adzuna.com/v1/api/jobs'
    endpoint = f'{base_url}/{location}/search/1'
    params = {
        'app_id': ADZUNA_API_ID,
        'app_key': ADZUNA_API_KEY,
        'what': skills,  # Job title or skills
        'sort_by': 'relevance',  # Sort by relevance
        'results_per_page': 10,  # Number of jobs to fetch
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def fetch_open_source_projects(skills):
    if not skills:
        logger.info("No skills provided for GitHub API query.")  # Log info message
        return []
    
    query = '+'.join(skills.split(','))
    url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc'
    
    logger.debug(f"GitHub API URL: {url}")  # Log debug message
    
    headers = {'Authorization': 'token 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'}
    response = requests.get(url, headers=headers)
    
    logger.debug(f"GitHub API Response: {response.json()}")  # Log debug message
    
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        logger.error(f"GitHub API Error: {response.text}")  # Log error message
        return []

def get_courses(skill):
    """
    Fetch courses from Coursera API based on a skill.
    """
    try:
        url = "https://api.coursera.org/api/courses.v1"
        params = {
            'q': skill,
            'fields': 'name,description',
            'limit': 5  # Limit the number of results
        }
        logger.debug(f"Fetching courses from Coursera API for skill: {skill}")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json().get('elements', [])
            if not data:
                logger.warning(f"No courses found for skill: {skill}")
                return [{"name": "No courses found", "description": "Try a different skill or check back later."}]
            return data
        else:
            logger.error(f"Failed to fetch courses from Coursera API. Status code: {response.status_code}, Response: {response.text}")
            return [{"name": "Error fetching courses", "description": "Please try again later."}]
    except Exception as e:
        logger.error(f"Error fetching courses from Coursera API: {e}")
        return [{"name": "Error fetching courses", "description": "Please try again later."}]