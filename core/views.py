from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserProfileForm
from .models import UserProfile, Project
from .utils import extract_text_from_pdf, match_projects, fetch_real_time_jobs, fetch_open_source_projects, get_courses,extract_skills

# Login View
def user_login(request):
    """
    Handles user login.
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('create_profile')  # Redirect to create-profile after login
        else:
            return render(request, 'core/login.html', {'error': 'Invalid username or password'})
    return render(request, 'core/login.html')

# Create Profile View
@login_required
def create_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        is_update = True
    except UserProfile.DoesNotExist:
        user_profile = None
        is_update = False

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user

            # Debugging: Print form data
            print("Form Data:", form.cleaned_data)

            # Extract skills from resume if uploaded
            if 'resume' in request.FILES:
                print("Resume uploaded:", request.FILES['resume'].name)  # Debugging
                resume_text = extract_text_from_pdf(request.FILES['resume'])
                print("Resume Text:", resume_text)  # Debugging
                skills = extract_skills(resume_text)
                print("Skills Extracted from Resume:", skills)  # Debugging
                profile.skills = ", ".join(skills)
            else:
                print("No resume uploaded. Extracting skills from form.")  # Debugging
                skills = extract_skills(form.cleaned_data.get('skills', ''))
                print("Skills Extracted from Form:", skills)  # Debugging
                profile.skills = ", ".join(skills)

            # Debugging: Print final skills being saved
            print("Final Skills Being Saved:", profile.skills)

            profile.save()
            print("Profile saved successfully.")  # Debugging
            return redirect('dashboard')
        else:
            print("Form is not valid:", form.errors)  # Debugging
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'core/create_profile.html', {
        'form': form,
        'is_update': is_update,
    })

# Dashboard View
@login_required
def dashboard(request):
    """
    Displays the user dashboard with matched projects, jobs, and courses.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    print("User Skills for Open-Source Projects:", user_profile.skills)  # Debugging
    
    projects = Project.objects.all()
    real_time_jobs = fetch_real_time_jobs(user_profile.skills)
    open_source_projects = fetch_open_source_projects(user_profile.skills)
    courses = get_courses(user_profile.skills)
    
    return render(request, 'core/dashboard.html', {
        'projects': projects,
        'jobs': real_time_jobs,
        'open_source_projects': open_source_projects,
        'courses': courses,
    })