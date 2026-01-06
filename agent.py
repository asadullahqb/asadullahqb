import os
import sys
import requests
import html
from duckduckgo_search import DDGS
from github import Github, Auth
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_NAME = "asadullahqb/asadullahqb"

def scrape_content(url):
    """Scrapes text content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit to 1500 chars per site to save tokens
        return text[:1500]
    except Exception as e:
        print(f"⚠️ Failed to scrape {url}: {e}")
        return ""

def synthesize_skills(search_results):
    """Synthesizes top skills using Kimi K2 Thinking (via Hugging Face)."""
    if not HF_TOKEN:
        print("⚠️ HF_TOKEN not found. Skipping synthesis.")
        return None

    print("🦁 Reading content from top results...")
    
    combined_content = ""
    for i, r in enumerate(search_results[:5]): # Only top 5
        url = r.get('href')
        title = r.get('title')
        print(f"   Reading: {title}")
        content = scrape_content(url)
        if content:
            combined_content += f"\n\nSource {i+1} ({title}):\n{content}\n"

    if not combined_content:
        return "🦁 Could not read any content to synthesize."

    print("🦁 Synthesizing with Kimi K2 Thinking (HF Inference)...")
    
    try:
        # Using Hugging Face InferenceClient
        # Model: moonshotai/Kimi-K2-Thinking (Assuming it's available on Inference API or similar)
        # Note: If this specific model is not available on free inference, we might need to fallback or user needs Pro
        
        client = InferenceClient(
            model="moonshotai/Kimi-K2-Thinking", 
            token=HF_TOKEN
        )
        
        prompt = f"""
        You are an expert Data Science Career Advisor. Analyze the following text about 2026 market trends.
        
        Identify the top 5 MOST critical skills mentioned.
        For each skill, provide a brief 1-sentence explanation.
        
        Format the output exactly as an HTML list suitable for a Telegram message:
        <b>🦁 Weekly Market Recon 🦁</b>
        
        <b>1. Skill Name</b>: Explanation.
        <b>2. Skill Name</b>: Explanation.
        ...
        
        Text Content:
        {combined_content}
        """

        # Using chat completion if available, otherwise text generation
        # Kimi K2 is a chat/reasoning model, so chat_completion is preferred
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Increase max_tokens for reasoning + output
        response = client.chat_completion(
            messages=messages, 
            max_tokens=2048,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Kimi Synthesis Failed (HF): {e}")
        return None

def search_trends():
    """Searches for the latest Data Science skills."""
    print("🦁 Hunting for latest skills...")
    query = f"top data science skills {datetime.now().year}"
    
    try:
        results = DDGS().text(query, max_results=20, region='us-en')
        if not results:
            return "🦁 No trends found this week."

        # Filter results
        filtered_results = []
        blocklist = ["dictionary", "meaning", "definition", "translate", "traducir", "cambridge", "top |"]
        
        for r in results:
            title = r.get('title', '')
            title_lower = title.lower()
            
            # 1. Blocklist check
            if any(b in title_lower for b in blocklist):
                continue
                
            # 2. ASCII check (allow some non-ascii like em-dash, but mostly ascii)
            ascii_count = sum(1 for c in title if ord(c) < 128)
            if len(title) > 0 and (ascii_count / len(title)) < 0.8:
                continue
            
            # 3. Relevance check
            relevance_keywords = ["data", "science", "ai", "machine learning", "analytics", "skill", "trend", "demand", "tech", "python", "statistics"]
            if not any(k in title_lower for k in relevance_keywords):
                continue
                
            filtered_results.append(r)
            if len(filtered_results) >= 5:
                break

        if not filtered_results:
             return "🦁 No relevant trends found this week (filtered all results)."

        # Try Synthesis first
        synthesis = synthesize_skills(filtered_results)
        if synthesis:
            return synthesis

        # Fallback to link list if synthesis fails or no key
        summary = "<b>🦁 Weekly Market Recon (Link Only) 🦁</b>\n\n"
        for i, r in enumerate(filtered_results, 1):
            clean_title = html.escape(r.get('title', 'No Title'))
            link = r.get('href', '#')
            summary += f"{i}. <a href='{link}'>{clean_title}</a>\n"
        return summary

    except Exception as e:
        print(f"Error searching: {e}")
        return f"🦁 Could not fetch trends this week. Error: {e}"

def send_telegram(message, manual_link=None, dry_run=False):
    """Sends the digest to Telegram."""
    if dry_run:
        print("\n[DRY RUN] Telegram Message Preview:")
        print("-" * 30)
        print(f"Chat ID: {TELEGRAM_CHAT_ID}")
        print(f"Message:\n{message}")
        if manual_link:
             print(f"Button: [Update Profile] -> {manual_link}")
        print("-" * 30)
        return

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
                    "text": "Update Profile",
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
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")
    
    mode = "weekly"
    if args:
        mode = args[0]
    
    print(f"Running in {mode} mode (Dry Run: {dry_run})")
    trends = search_trends()
    
    if mode in ["notify", "weekly"]:
        manual_trigger_link = f"https://github.com/{REPO_NAME}/actions/workflows/update_profile.yml"
        send_telegram(trends, manual_trigger_link, dry_run=dry_run)
        
    elif mode == "update":
        if not dry_run:
            update_readme(trends)
        else:
            print("[DRY RUN] Skipping README update.")
        send_telegram(f"✅ Quarterly Profile Update Complete!\n\nData used:\n{trends}", dry_run=dry_run)

if __name__ == "__main__":
    main()
