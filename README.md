🤖 CONVERSA

A hackathon project to enhance CONVERSA by integrating a suite of intelligent chatbots.  
These bots automate repetitive tasks, improve collaboration, and maintain better data hygiene inside Talk rooms.  

---

🚩 Problem Statement
Nextcloud Talk is a powerful collaboration tool, but it lacks automation for routine tasks such as answering FAQs, reminding users of file expiries, boosting team morale, and cleaning up stale content.  
This project solves that gap by building **bots that integrate seamlessly with Nextcloud APIs**.

---

💡 Our Solution
We designed **four bots** that integrate with the **Nextcloud Talk Bot Framework** and **Files API**:

A. FAQ Bot
A chatbot that answers frequently asked questions using a **markdown knowledge base**.  
- Parses markdown (`# Question`, `## Variants`, `### Answer`)  
- Responds to queries  
- Fuzzy matching for variants  
- **Bonus**: Admins can update FAQs directly from Admin Panel  

---

B. File Expiry Reminder Bot
Automatically reminds users when shared files are about to expire.  
- Scans shares using **Nextcloud Files API**  
- Posts reminders in Talk rooms linked to the file or user  
- **Bonus**: Supports customizable schedules (e.g., 7 days / 1 day before expiry)  

---

C. Quote-of-the-Day Bot
Keeps teams engaged with daily motivational or fun quotes.  
- Posts scheduled quotes in a Talk room  
- Quotes from local files or external APIs  
- **Bonus**: Users can add quotes via 'add quote' function  

---

D. Clean-up Bot
Helps maintain a tidy workspace by flagging stale content.  
- Detects inactive rooms, old pinned messages, stale files  
- Posts weekly cleanup reports in Talk  
- **Bonus**: Users can run cleanup with commands like 

---

🛠️ Tech Stack
- Frontend: HTML, CSS, JavaScript

Backend: Python

Framework: Django

Voice Input (STT): Web Speech API (SpeechRecognition)

Voice Output (TTS): Web Speech API (SpeechSynthesis)

APIs: WeatherStack API, Date & Time APIs

Database: SQLite (FAQs, Query Logs)

Nextcloud Integration (React-based):

Frontend: React + TailwindCSS / ShadCN (for UI components)

Framework: Nextcloud App Framework (via APIs)

Backend Integration: Nextcloud Talk API, Nextcloud Dashboard Widget API, Nextcloud Files API

Authentication & Security: OAuth / API key management (for external apps)

Real-Time Features: WebSockets / Server-Sent Events for live chat & notifications

Extras: Chart libraries (Recharts, D3.js) for analytics widgets

---

⚙️ Installation (Demo Setup)

1. Clone the repository:
   '''bash
   git clone (https://github.com/Nisarg0403/AI-Assistant)'''


---

SCREENSHOTS

![Homepage](static/images/Homepage.png)
![Admin Panel](static/images/Admin_panel.png)
![Manage FAQs](static/images/Manage_faqs.png)

---

🔮 Future Improvements

* Web-based admin dashboard for bot configuration
* Multi-language support for FAQ & Quotes
* AI-powered natural language FAQ responses
* Integration with third-party APIs (quotes, compliance tools)

---

👥 Team

Built with ❤️ during \प्रज्ञा - National Level Open Source Online Hackathon by **\Trouble Shooters**.

---


