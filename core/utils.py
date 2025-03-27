import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from pdfminer.high_level import extract_text
from io import BytesIO
import logging
from decouple import config  
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the current file's directory
CSV_FILE_PATH = os.path.join(BASE_DIR, "data", "Online_Courses.csv")  # Join path correctly

df = pd.read_csv(CSV_FILE_PATH)


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

    # Ensure skills is a list (preventing query errors)
    if isinstance(skills, str):
        skills_list = skills.split(",")  
    else:
        skills_list = skills

    query = "+".join(skills_list)  # Convert list to GitHub search query
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"

    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        logger.error(f"GitHub API Error: {response.text}")
        return []

def get_courses(skill):
    """
    Fetches the top 5 relevant courses from the CSV file based on the skill.
    """
    try:
        # Load CSV file
        df = pd.read_csv("core/data/Online_Courses.csv")  # Ensure the correct file path
        

        # Ensure the CSV file has the correct column names
        required_columns = {'Title', 'URL', 'Short Intro', 'Created by'}  
        if not required_columns.issubset(df.columns):
            raise ValueError(f"CSV file is missing required columns. Found: {df.columns.tolist()}")

        # Convert all text to lowercase for better matching
        df['Title'] = df['Title'].astype(str).str.lower()
        df['Short Intro'] = df['Short Intro'].astype(str).str.lower()

        # Filter courses containing the skill in their title or short intro
        skill_lower = skill.lower()
        filtered_courses = df[
            df['Title'].str.contains(skill_lower, na=False) | 
            df['Short Intro'].str.contains(skill_lower, na=False)
        ]

        # Get the top 5 results
        top_courses = filtered_courses.head(5).copy()
        top_courses['Know More'] = top_courses['URL'].apply(lambda url: f"[Know More]({url})")

        # Rename columns for output formatting
        # Ensure correct key in `get_courses()`
        top_courses = filtered_courses[['Title', 'Created by', 'Short Intro', 'URL']].rename(
            columns={'Title': 'name', 'Created by': 'created_by', 'Short Intro': 'description', 'URL': 'know_more'}
        ).to_dict(orient='records')


        return top_courses

    except Exception as e:
        print(f"Error reading courses CSV file: {e}")
        return []
def get_courses(skills):
    """
    Fetches the top 5 most relevant courses from the CSV file based on skill similarity.
    Uses TF-IDF and cosine similarity for better matching.
    """
    try:
        # Load CSV file
        df = pd.read_csv(CSV_FILE_PATH)  

        # Ensure required columns exist
        required_columns = {'Title', 'Short Intro', 'URL', 'Created by'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"CSV file is missing required columns. Found: {df.columns.tolist()}")

        # Convert all text to lowercase for better matching
        df['Full Text'] = (df['Title'] + " " + df['Short Intro']).astype(str).str.lower()

        # Convert skills to a single query string
        skills_text = " ".join(skills).lower()

        # TF-IDF Vectorization
        vectorizer = TfidfVectorizer()
        course_vectors = vectorizer.fit_transform(df['Full Text'])
        skill_vector = vectorizer.transform([skills_text])

        # Compute Cosine Similarity
        similarities = cosine_similarity(skill_vector, course_vectors).flatten()
        
        # Get top 5 relevant courses
        top_indices = similarities.argsort()[-5:][::-1]
        top_courses = df.iloc[top_indices].copy()

        # Prepare output format
        top_courses['Know More'] = top_courses['URL'].apply(lambda url: f"[Know More]({url})")
        top_courses = top_courses[['Title', 'Created by', 'Short Intro', 'URL']].rename(
            columns={'Title': 'name', 'Created by': 'created_by', 'Short Intro': 'description', 'URL': 'know_more'}
        ).to_dict(orient='records')

        return top_courses

    except Exception as e:
        print(f"Error reading courses CSV file: {e}")
        return []

def recommend_courses_from_resume(pdf_file):
    resume_text = extract_text_from_pdf(pdf_file)
    if not resume_text:
        logger.error("Failed to extract text from the uploaded resume.")
        return []

    extracted_skills = list(set(extract_skills(resume_text)))
    if not extracted_skills:
        logger.info("No relevant skills found in the resume.")
        return []

    print(f"Extracted skills: {extracted_skills}")  # Debugging print

    # Fetch courses for all extracted skills in one call
    recommended_courses = get_courses(extracted_skills)

    return recommended_courses
