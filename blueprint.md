# 🦁 Project Blueprint: The Lion Agent (GitHub Profile Automation)

## 🎯 Objective
Create a hybrid automation system for the user's GitHub profile (`README.md`).
1.  **Weekly (Passive):** Scrape trending Data Scientist skills and send a digest to the user via Telegram every Monday.
2.  **Quarterly/Manual (Active):** Update the `README.md` "Skills" section automatically when triggered.

## 🛠️ Prerequisites (User Action Required)
*Before running the code, the user must provide:*
1.  **Telegram Bot Token:** Obtained from @BotFather.
2.  **Telegram Chat ID:** Obtained from @userinfobot.
3.  **GitHub Secrets:** The user must set `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` in the GitHub Repo Settings -> Secrets -> Actions.

---

## 📂 File Structure
Create the following file structure in the root of the repository:

```text
.
├── .github
│   └── workflows
│       └── lion_agent.yml
├── agent.py
├── requirements.txt
└── blueprint.md