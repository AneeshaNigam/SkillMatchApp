import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from pdfminer.high_level import extract_text
from io import BytesIO
import logging
from decouple import config  

# Initialize the logger
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

# Load API keys from environment variables
ADZUNA_API_ID = config('ADZUNA_API_ID')
ADZUNA_API_KEY = config('ADZUNA_API_KEY')
GITHUB_API_TOKEN = config('GITHUB_API_TOKEN')


def extract_skills(text):
    if not text:
        logger.info("No text provided for skill extraction.")  
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
    skills = [token.text for token in doc if token.text in skill_keywords]
    
    logger.debug(f"Extracted Skills: {skills}")  
    return skills


def extract_text_from_pdf(pdf_file):
    try:
        if hasattr(pdf_file, 'read'):  
            pdf_content = pdf_file.read()
            pdf_stream = BytesIO(pdf_content)
            text = extract_text(pdf_stream)
        else:
            text = extract_text(pdf_file)
        
        logger.info("Successfully extracted text from PDF.")  
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")  
        return None


def match_projects(user_skills, projects):
    vectorizer = TfidfVectorizer()
    skill_matrix = vectorizer.fit_transform([user_skills] + [p.required_skills for p in projects])
    similarities = cosine_similarity(skill_matrix[0:1], skill_matrix[1:])
    matched_indices = similarities.argsort()[0][::-1]
    return [projects[i] for i in matched_indices]


def fetch_real_time_jobs(skills, location='us'):
    base_url = 'https://api.adzuna.com/v1/api/jobs'
    endpoint = f'{base_url}/{location}/search/1'
    params = {
        'app_id': ADZUNA_API_ID,
        'app_key': ADZUNA_API_KEY,
        'what': skills,  
        'sort_by': 'relevance',  
        'results_per_page': 10,  
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []


def fetch_open_source_projects(skills):
    if not skills:
        logger.info("No skills provided for GitHub API query.")  
        return []
    
    query = '+'.join(skills.split(','))
    url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc'
    
    headers = {'Authorization': f'token {GITHUB_API_TOKEN}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        logger.error(f"GitHub API Error: {response.text}")  
        return []


def get_courses(skill):
    """
    Fetches static courses instead of using an API.
    """
    courses = [
        {"name": "Python for Beginners", "description": "Learn Python from scratch.", "url": "#"},
        {"name": "Machine Learning 101", "description": "Introduction to Machine Learning concepts.", "url": "#"},
        {"name": "Full Stack Web Development", "description": "Learn HTML, CSS, JavaScript, and Django.", "url": "#"},
        {"name": "Data Science with Pandas", "description": "Master data manipulation and analysis.", "url": "#"},
        {"name": "React.js for Frontend Development", "description": "Learn React for modern web applications.", "url": "#"},
    ]

    return courses
