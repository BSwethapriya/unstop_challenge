📧 AI-Powered Communication Assistant

This project is a Streamlit-based dashboard that helps modern organizations manage customer support emails intelligently.

It retrieves emails from a dataset (CSV for demo), filters and categorizes them, prioritizes urgent cases, performs sentiment analysis, and generates AI-powered draft responses.

🚀 Features

Email Retrieval & Filtering

Filters support-related emails (support, query, help, request).

Displays sender, subject, body, and date.

Categorization & Prioritization

Detects issue types (login issue, password reset, billing error, downtime, integration, etc.).

Sentiment analysis: Positive / Negative / Neutral.

Prioritization: Urgent / Not urgent (based on keywords).

Context-Aware Auto Responses

Generates professional, empathetic draft replies.

Custom response templates for each issue type.

Editable response box in the dashboard.

Information Extraction

Extracts emails and phone numbers from email body.

Displays structured metadata for support agents.

Dashboard / UI

Built with Streamlit.

Interactive charts for Issue Types, Sentiment, and Priority.

Filters by sentiment, priority, issue type, and search.

Metrics: total emails, eligible emails, urgent cases, and last 24h stats.

📂 Project Structure
unstop_challenge/
│
├── app.py             
├── requirements.txt    
├── README.md           
├── 68b1acd44f393_Sample_Support_Emails_Dataset.csv  
├── output screens.png      

🛠️ Installation & Setup
1. Clone the repo
git clone https://github.com/BSwethapriya/unstop_challenge.git
cd unstop_challenge

2. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux

3. Install dependencies
pip install -r requirements.txt

4. Run the app
streamlit run app.py


Then open your browser at 👉 http://localhost:8501

📊 Demo Workflow

Upload the provided CSV of support emails (or connect to IMAP/Gmail APIs).

Dashboard shows:

Filtered emails list

Charts for Issue Type, Sentiment, Priority

Metrics (total, urgent, 24h)

Select an email → see extracted details → get AI-generated draft response.

Review/edit → mark resolved.

🖼️ Output Screen

Here’s an example of the dashboard in action:

⚡ Tech Stack

Frontend/Dashboard: Streamlit

Backend Processing: Python (pandas, regex, datetime)

Visualization: Matplotlib

Data: CSV dataset of support emails

🌟 Future Enhancements

Integrate with Gmail/Outlook APIs for real-time email retrieval.

Use advanced NLP models (BERT/GPT) for sentiment & classification.

Deploy to Streamlit Cloud or Hugging Face Spaces.

Add multi-agent workflow (escalations, SLA tracking).

👩‍💻 Author

Bomma Swetha Priya
Hackathon Project: AI-Powered Communication Assistant
