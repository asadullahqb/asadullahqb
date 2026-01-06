import os
import sys
import requests
import html
from duckduckgo_search import DDGS
from github import Github, Auth
from datetime import datetime

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "asadullahqb/asadullahqb"

def search_trends():
    """Searches for the latest Data Science skills."""
    print("🦁 Hunting for latest skills...")
    query = f"Top data scientist skills trends {datetime.now().year} market demand"
    
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "🦁 No trends found this week."

        # using HTML format for safety against random special characters in titles
        summary = "<b>🦁 Weekly Market Recon 🦁</b>\n\n"
        for i, r in enumerate(results, 1):
            # Clean title to prevent HTML breakage using html.escape
            clean_title = html.escape(r.get('title', 'No Title'))
            link = r.get('href', '#')
            summary += f"{i}. <a href='{link}'>{clean_title}</a>\n"
        return summary
    except Exception as e:
        print(f"Error searching: {e}")
        return f"🦁 Could not fetch trends this week. Error: {e}"

def send_telegram(message, manual_link=None):
    """Sends the digest to Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram token or Chat ID missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML", # Switched to HTML for stability
        "disable_web_page_preview": True # Keeps chat clean
    }

    if manual_link:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {
                    "text": "🚀 Force Update Profile Now",
                    "url": manual_link
                }
            ]]
        }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Telegram message sent.")
    except Exception as e:
        print(f"❌ Failed to send Telegram: {e}")
        # Print response text to see exact error if it fails again
        try:
            print(f"Server response: {response.text}")
        except:
            pass

def update_readme(skills_text):
    """Updates the README (Quarterly Action)."""
    if not GITHUB_TOKEN:
        print("GitHub token missing.")
        return

    # FIXED: The Deprecation Warning
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents("README.md")
        content_decoded = contents.decoded_content.decode("utf-8")
        
        start_marker = "<!-- SKILLS_START -->"
        end_marker = "<!-- SKILLS_END -->"
        
        if start_marker in content_decoded and end_marker in content_decoded:
            start_index = content_decoded.find(start_marker) + len(start_marker)
            end_index = content_decoded.find(end_marker)
            
            # Since skills_text is now an HTML summary, we might want to strip HTML or format it differently for Markdown
            # For now, let's just inject it as is. GitHub README supports HTML.
            
            new_content = (
                content_decoded[:start_index] + 
                "\n" + skills_text + "\n" +
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
            else:
                print("No changes needed for README.md.")
        else:
            print("Markers not found in README.md.")
            
    except Exception as e:
        print(f"Failed to update README: {e}")

def main():
    # flexible argument handling
    mode = "weekly"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    print(f"Running in {mode} mode")
    trends = search_trends()
    
    if mode in ["notify", "weekly"]:
        manual_trigger_link = f"https://github.com/{REPO_NAME}/actions/workflows/lion_agent.yml"
        send_telegram(trends, manual_trigger_link)
        
    elif mode == "update":
        update_readme(trends)
        send_telegram(f"✅ Quarterly Profile Update Complete!\n\nData used:\n{trends}")

if __name__ == "__main__":
    main()
