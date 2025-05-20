# Kahaniya - Django Blogging Platform 📝

Kahaniya is a Django-powered blog website focused on storytelling. It allows authors to write and publish stories, and lets readers comment, like, and follow their favorite creators.

## 🌐 Live Demo

🚧 Not deployed yet — coming soon!

---

## ✨ Features

- User authentication via Django Allauth
- Author dashboard with profile image and bio
- Blog post creation, editing, and detail view
- Comment system with nested replies
- Like system using Django ContentType
- Follow system to connect readers with authors
- Public reader profiles with activity tabs

---

## 🛠️ Installation

Clone and run the project locally:

```bash
 # 1. Clone the repo
 git clone https://github.com/yourusername/blogger.git
 cd blogger
    
# 2. Create and activate a virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
    
 # 3. Install dependencies
pip install -r requirements.txt
    
 # 4. Run migrations
python manage.py migrate
    
# 5. Run the development server
python manage.py runserver    
