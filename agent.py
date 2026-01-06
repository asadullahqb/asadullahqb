import os
import sys
import requests
from github import Github
from collections import Counter
from datetime import datetime, timedelta

# Configuration
REPO_NAME = "asadullahqb/asadullahqb"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_trending_skills():
    """
    Fetches trending topics/languages from GitHub repositories related to Data Science.
    """
    print("Fetching trending skills...")
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set. Using fallback skills.")
        return ["Python", "Transformers", "LLM", "PyTorch", "Data Science"]

    g = Github(GITHUB_TOKEN)
    
    # Search for data science repos created this year
    current_year = datetime.now().year
    date_since = f"{current_year}-01-01"
    query = f"topic:data-science created:>{date_since} sort:stars-desc"
    
    try:
        repos = g.search_repositories(query=query)
        skills = []
        
        # Analyze top 20 repos
        for i, repo in enumerate(repos):
            if i >= 20: break
            if repo.language:
                skills.append(repo.language)
            skills.extend(repo.get_topics())
            
        # Clean and count
        # Filter out common non-skill topics
        ignore = {'data-science', 'machine-learning', 'deep-learning', 'artificial-intelligence', 'hacktoberfest', 'project'}
        cleaned_skills = [s for s in skills if s.lower() not in ignore]
        
        counter = Counter(cleaned_skills)
        top_5 = counter.most_common(5)
        return [skill[0] for skill in top_5]
        
    except Exception as e:
        print(f"Error fetching skills: {e}")
        return ["Python", "PyTorch", "Transformers", "LLM", "Pandas"] # Fallback

def send_telegram_digest(skills):
    """
    Sends a message to Telegram with the trending skills.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return

    message = f"🦁 **Lion Agent Weekly Digest**\n\n🔥 **Trending Data Science Skills:**\n"
    for i, skill in enumerate(skills, 1):
        message += f"{i}. {skill}\n"
    
    message += "\nStay ahead of the curve! 🚀"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def update_readme(skills):
    """
    Updates the README.md file with the top skills.
    """
    if not GITHUB_TOKEN:
        print("GitHub token missing.")
        return

    g = Github(GITHUB_TOKEN)
    try:
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents("README.md")
        content_decoded = contents.decoded_content.decode("utf-8")
        
        start_marker = "<!-- SKILLS_START -->"
        end_marker = "<!-- SKILLS_END -->"
        
        if start_marker in content_decoded and end_marker in content_decoded:
            start_index = content_decoded.find(start_marker) + len(start_marker)
            end_index = content_decoded.find(end_marker)
            
            new_skills_section = "\n"
            for skill in skills:
                new_skills_section += f"- {skill}\n"
            
            new_content = (
                content_decoded[:start_index] + 
                new_skills_section + 
                content_decoded[end_index:]
            )
            
            if new_content != content_decoded:
                repo.update_file(
                    contents.path,
                    "🦁 Lion Agent: Updated Skills Section",
                    new_content,
                    contents.sha
                )
                print("README.md updated successfully.")
                send_telegram_notification("README.md updated with new trending skills!")
            else:
                print("No changes needed for README.md.")
        else:
            print("Markers not found in README.md. Please add <!-- SKILLS_START --> and <!-- SKILLS_END -->.")
            send_telegram_notification("Lion Agent Warning: README markers not found.")
            
    except Exception as e:
        print(f"Failed to update README: {e}")

def send_telegram_notification(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py [weekly|update]")
        sys.exit(1)
        
    mode = sys.argv[1]
    trending_skills = get_trending_skills()
    
    if mode == "weekly":
        send_telegram_digest(trending_skills)
    elif mode == "update":
        update_readme(trending_skills)
    else:
        print(f"Unknown mode: {mode}")
