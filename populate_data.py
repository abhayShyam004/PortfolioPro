# Run this script to populate the database with initial data
# python manage.py shell < populate_data.py

from app.models import Profile, SocialLink, Expertise, Experience, Education, Skill, Project, ContactInfo

# Create Profile
profile, created = Profile.objects.get_or_create(pk=1)
if created or not profile.about_text:
    profile.name = "Abhay"
    profile.greeting = "Hi, I am Abhay"
    profile.bio_line1 = "A web designer"
    profile.bio_line2 = "& backend"
    profile.bio_line3 = "developer based"
    profile.bio_line4 = "in India."
    profile.about_text = """I'm Abhay, a BTech student in Computer Science with a focus on software development and system design. I enjoy turning ideas into functional projects and constantly push myself to grow in areas like algorithms, full-stack development, and cloud technologies. Outside academics, I engage in chess and writing, which help me approach challenges with both logic and creativity."""
    profile.cv_link = "https://drive.google.com/uc?export=download&id=17vo7UFsfR4kgWvtU9wY5tuvFcFeHpta6"
    profile.save()
    print("Profile created/updated")

# Create Contact Info
contact, created = ContactInfo.objects.get_or_create(pk=1)
if created or not contact.email:
    contact.email = "abhay315204@gmail.com"
    contact.phone = "+91 9392687414"
    contact.contact_heading = "I love to hear from you. Whether you have a question or just want to chat about design, tech & art — shoot me a message."
    contact.save()
    print("Contact info created/updated")

# Create Social Links
social_data = [
    ('linkedin', 'LinkedIn', 'https://www.linkedin.com/in/abhay-s-60938424a/', 1),
    ('leetcode', 'LeetCode', 'https://leetcode.com/u/abhayArvo', 2),
    ('github', 'GitHub', 'https://github.com/Abhaythecoder', 3),
    ('instagram', 'Instagram', 'https://www.instagram.com/ab_arv/', 4),
]
for platform, display_name, url, order in social_data:
    SocialLink.objects.get_or_create(
        platform=platform,
        defaults={'display_name': display_name, 'url': url, 'order': order}
    )
print("Social links created")

# Create Expertise
expertise_data = [
    ('Full-Stack Development', 1),
    ('Django & REST API', 2),
    ('Front-End Design', 3),
    ('Project Management', 4),
    ('Cloud Deployment', 5),
]
for name, order in expertise_data:
    Expertise.objects.get_or_create(name=name, defaults={'order': order})
print("Expertise created")

# Create Experience
experience_data = [
    {
        'company': 'UL Technology Solutions',
        'position': 'SDE Intern',
        'timeframe': 'December 2024 - March 2025',
        'description': 'During my internship at UL Technology Solutions, I gained hands-on experience in Django and REST API development, building and deploying multiple full-stack web applications. I worked on real-world projects, integrating front-end and back-end systems and managing databases.',
        'order': 1
    },
    {
        'company': 'Ascendia group',
        'position': 'Founder',
        'timeframe': 'May 2025 - present',
        'description': 'I founded Ascendia Group to create and manage innovative software projects, focusing on full-stack development and practical solutions. Leading the group has helped me develop technical expertise, project management skills, and the ability to turn ideas into real-world applications.',
        'order': 2
    },
]
for exp in experience_data:
    Experience.objects.get_or_create(
        company=exp['company'],
        position=exp['position'],
        defaults={'timeframe': exp['timeframe'], 'description': exp['description'], 'order': exp['order']}
    )
print("Experience created")

# Create Education
education_data = [
    {
        'institution': 'VIT Bhopal University',
        'degree': 'Bachelors of Technology in Computer Science',
        'timeframe': 'September 2022',
        'description': 'I am currently pursuing my BTech in Computer Science at VIT Bhopal University, where I am building a strong foundation in programming, algorithms, and software development. Alongside academics, I actively work on projects, enhance my technical skills, and explore innovative solutions to real-world problems.',
        'order': 1
    },
    {
        'institution': 'Kendriya Vidyalaya Tirumalagiri',
        'degree': 'High School',
        'timeframe': 'April 2020',
        'description': 'I completed my high school education at Kendriya Vidyalaya Tirumalagiri, where I focused on building a strong academic foundation while actively participating in extracurricular activities. This period helped me develop discipline, critical thinking, and a passion for learning that continues to drive me today.',
        'order': 2
    },
]
for edu in education_data:
    Education.objects.get_or_create(
        institution=edu['institution'],
        degree=edu['degree'],
        defaults={'timeframe': edu['timeframe'], 'description': edu['description'], 'order': edu['order']}
    )
print("Education created")

# Create Skills (without icons - those need to be uploaded via admin)
skills_data = [
    ('Django', 'backend', 1),
    ('Rest', 'API', 2),
    ('PostgreSQL', 'database', 3),
    ('AWS', 'Cloud', 4),
    ('Github', 'Version control', 5),
    ('MongoDB', 'Database', 6),
    ('Express', 'backend', 7),
    ('React.js', 'frontend', 8),
    ('Node.js', 'backend', 9),
    ('Node-red', 'IOT', 10),
    ('langchain', 'ML', 11),
]
for name, category, order in skills_data:
    Skill.objects.get_or_create(
        name=name,
        defaults={'category': category, 'order': order}
    )
print("Skills created")

# Create Projects (without icons - those need to be uploaded via admin)
projects_data = [
    ('Kapay', 'Ascendia', 'https://ascendiakapi.pythonanywhere.com/', 1),
    ('HomeoCompare', 'Ascendia', 'https://homeocompare.life/', 2),
    ('Snoof', 'Ascendia', 'https://snoof.pythonanywhere.com/', 3),
    ('postIT', 'Ascendia', 'https://github.com/Abhaythecoder/Ascendia', 4),
    ('Go', 'Ascendia', 'https://Ascendiago.onrender.com', 5),
    ('DayLore', 'Ascendia', 'https://github.com/Abhaythecoder/Holiday-Calendar-Website-', 6),
    ('DoLt', 'Ascendia', 'https://github.com/Abhaythecoder/Todo-webpage', 7),
    ('Godrej Furnitures MB', 'Freelance', 'https://godrejmb-3sti.onrender.com/', 8),
]
for title, category, url, order in projects_data:
    Project.objects.get_or_create(
        title=title,
        defaults={'category': category, 'url': url, 'order': order}
    )
print("Projects created")

print("\n✅ Database populated successfully!")
print("You can now access the admin panel at /admin-login/")
print("NOTE: You need to create a superuser to log in.")
print("Run: python manage.py createsuperuser")
