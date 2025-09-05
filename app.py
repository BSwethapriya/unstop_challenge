import streamlit as st
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Support Assistant", layout="wide")

# ---------- Utility functions ----------
filter_terms = r"(support|query|request|help)"

issue_map = [
    ("login_issue", r"(unable to log in|cannot log in|login|log into)"),
    ("password_reset", r"(reset my password|reset link|password)"),
    ("billing_error", r"(billing error|charged twice|refund)"),
    ("downtime", r"(servers are down|system.*inaccessible|downtime|completely inaccessible)"),
    ("integration_api", r"(integration|api|crm)"),
    ("pricing", r"(pricing tier|pricing|cost)"),
    ("account_verification", r"(verification|verify my account|verification email)"),
    ("subscription", r"(subscription)"),
    ("general_query", r"(general query)"),
]

negative_words = [
    "unable", "cannot", "doesn't", "doesnt", "error", "charged twice", "down", "inaccessible",
    "urgent", "critical", "immediately", "blocked", "cannot access", "frustrated", "issue", "problem"
]
positive_words = ["thank you", "appreciate", "great", "good", "thanks"]

urgent_keywords = [
    "urgent", "immediate", "immediately", "critical", "cannot access", "blocked",
    "servers are down", "completely inaccessible", "charged twice", "reset link doesn", "reset link doesn’t", "reset link doesn't"
]

email_regex = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
phone_regex = r"(\+?\d[\d\-\s]{7,}\d)"


def try_parse_date(s):
    for fmt in ["%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(str(s), fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.NaT


def classify_issue(text: str) -> str:
    t = (text or "").lower()
    for label, pattern in issue_map:
        if re.search(pattern, t):
            return label
    return "other"


def detect_sentiment(text: str) -> str:
    t = (text or "").lower()
    neg = any(w in t for w in negative_words)
    pos = any(w in t for w in positive_words)
    if neg and not pos:
        return "Negative"
    if pos and not neg:
        return "Positive"
    if pos and neg:
        return "Mixed"
    return "Neutral"


def compute_priority(text: str) -> str:
    t = (text or "").lower()
    score = sum(int(w in t) for w in urgent_keywords)
    if "Negative" in detect_sentiment(t):
        score += 1
    return "Urgent" if score >= 1 else "Not urgent"


def extract_contacts(text):
    t = text or ""
    emails = re.findall(email_regex, t)
    phones = re.findall(phone_regex, t)
    emails_s = ", ".join(sorted(set(emails))) or None
    phones_s = ", ".join(sorted({p.strip() for p in phones})) or None
    return emails_s, phones_s


def response_template(row: pd.Series) -> str:
    sender = row.get("sender", "")
    name = sender.split("@")[0].split(".")[0].title() if isinstance(sender, str) else "there"
    is_urgent = row.get("priority") == "Urgent"
    senti = row.get("sentiment", "Neutral")

    opening = f"Hi {name},"
    empathy = ""
    if is_urgent or senti in ["Negative", "Mixed"]:
        empathy = " I’m sorry for the trouble you’re facing—we understand how disruptive this can be and we’re on it."

    it = row.get("issue_type")
    if it == "login_issue":
        summary = "From your message, it looks like you’re unable to access your account. Please confirm your email/username."
    elif it == "password_reset":
        summary = "You mentioned password reset issues. We’ll verify the reset token validity and email deliverability."
    elif it == "billing_error":
        summary = "You flagged a billing concern. We’ll audit your last invoice and payment events."
    elif it == "downtime":
        summary = "You reported a service outage. We’re checking system health and incident logs."
    elif it == "integration_api":
        summary = "Regarding API/CRM integration, we support standard OAuth and webhook flows."
    elif it == "pricing":
        summary = "You asked about pricing tiers. I’ll send a breakdown of plans and features."
    elif it == "account_verification":
        summary = "You’re facing account verification issues. We’ll re-trigger the verification email."
    elif it == "subscription":
        summary = "On subscription queries, happy to help with plan changes, renewals, or cancellations."
    elif it == "general_query":
        summary = "Thanks for your general query. Could you share a bit more context?"
    else:
        summary = "Thanks for reaching out. Could you share more detail so I can assist quickly?"

    sla = "We’ve prioritized your case and will update you shortly." if is_urgent else "We’ll review and get back to you soon."
    closing = "Best regards,\nSupport Team"

    body = (
        f"{opening}\n\n"
        f"Thanks for writing in.{empathy}\n\n"
        f"{summary}\n\n"
        f"{sla}\n\n"
        f"{closing}"
    )
    return body


# ---------- Load data ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("enriched_emails.csv")
        if "sent_dt" in df.columns:
            df["sent_dt"] = pd.to_datetime(df["sent_dt"], errors="coerce")
        return df
    except Exception:
        pass

    try:
        df = pd.read_csv("68b1acd44f393_Sample_Support_Emails_Dataset (1).csv")
    except Exception:
        st.error("Please upload the CSV using the sidebar.")
        return pd.DataFrame()

    df["sent_dt"] = df["sent_date"].apply(try_parse_date)
    df["eligible"] = df["subject"].str.lower().str.contains(filter_terms, regex=True, na=False)
    df["issue_type"] = df.apply(lambda r: classify_issue(f"{r['subject']} {r['body']}"), axis=1)
    df["sentiment"] = df.apply(lambda r: detect_sentiment(f"{r['subject']} {r['body']}"), axis=1)
    df["priority"] = df.apply(lambda r: compute_priority(f"{r['subject']} {r['body']}"), axis=1)
    df["priority_score"] = df["priority"].map({"Urgent": 1, "Not urgent": 2})
    emails_phones = df["body"].apply(extract_contacts)
    df["contacts_email_in_body"] = [c[0] for c in emails_phones]
    df["contacts_phone_in_body"] = [c[1] for c in emails_phones]
    df["draft_response"] = df.apply(response_template, axis=1)
    return df


with st.sidebar:
    st.title("Controls")
    uploaded = st.file_uploader("Upload support emails CSV", type=["csv"])
    df = None
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        df["sent_dt"] = df["sent_date"].apply(try_parse_date)
        df["eligible"] = df["subject"].str.lower().str.contains(filter_terms, regex=True, na=False)
        df["issue_type"] = df.apply(lambda r: classify_issue(f"{r['subject']} {r['body']}"), axis=1)
        df["sentiment"] = df.apply(lambda r: detect_sentiment(f"{r['subject']} {r['body']}"), axis=1)
        df["priority"] = df.apply(lambda r: compute_priority(f"{r['subject']} {r['body']}"), axis=1)
        df["priority_score"] = df["priority"].map({"Urgent": 1, "Not urgent": 2})
        emails_phones = df["body"].apply(extract_contacts)
        df["contacts_email_in_body"] = [c[0] for c in emails_phones]
        df["contacts_phone_in_body"] = [c[1] for c in emails_phones]
        df["draft_response"] = df.apply(response_template, axis=1)
    else:
        df = load_data()

    st.markdown("---")
    sentiments = ["All"] + sorted(df["sentiment"].dropna().unique().tolist()) if not df.empty else ["All"]
    sentiment_filter = st.selectbox("Sentiment", sentiments)

    priorities = ["All"] + sorted(df["priority"].dropna().unique().tolist()) if not df.empty else ["All"]
    priority_filter = st.selectbox("Priority", priorities)

    issues = ["All"] + sorted(df["issue_type"].dropna().unique().tolist()) if not df.empty else ["All"]
    issue_filter = st.selectbox("Issue Type", issues)

    search = st.text_input("Search (subject/body)")


st.title("AI-Powered Communication Assistant")

if df is None or df.empty:
    st.info("Upload a CSV to get started.")
    st.stop()

mask = pd.Series([True] * len(df))
if sentiment_filter != "All":
    mask &= (df["sentiment"] == sentiment_filter)
if priority_filter != "All":
    mask &= (df["priority"] == priority_filter)
if issue_filter != "All":
    mask &= (df["issue_type"] == issue_filter)
if search:
    s = search.lower()
    mask &= (df["subject"].str.lower().str.contains(s) | df["body"].str.lower().str.contains(s))

view = df[mask].copy()
view = view.sort_values(by=["eligible", "priority_score", "sent_dt"], ascending=[False, True, True])

# --------- Analytics ---------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total emails", len(df))
col2.metric("Eligible (by subject)", int(df["eligible"].sum()))
last_24h = df[df["sent_dt"] >= (pd.Timestamp.now() - pd.Timedelta(hours=24))]
col3.metric("Last 24h", len(last_24h))
col4.metric("Urgent", int((df["priority"] == "Urgent").sum()))

st.markdown("---")

# --------- Charts with safe checks ---------
colA, colB, colC = st.columns(3)

with colA:
    st.subheader("Issue Types")
    counts = view["issue_type"].value_counts()
    if not counts.empty:
        fig, ax = plt.subplots()
        counts.plot(kind="bar", ax=ax, rot=30)
        ax.set_xlabel("Type")
        ax.set_ylabel("Count")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No such combinations exist for Issue Types")

with colB:
    st.subheader("Sentiment")
    counts = view["sentiment"].value_counts()
    if not counts.empty:
        fig, ax = plt.subplots()
        counts.plot(kind="bar", ax=ax, rot=0)
        ax.set_xlabel("Sentiment")
        ax.set_ylabel("Count")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No such combinations exist for Sentiment")

with colC:
    st.subheader("Priority")
    counts = view["priority"].value_counts()
    if not counts.empty:
        fig, ax = plt.subplots()
        counts.plot(kind="bar", ax=ax, rot=0)
        ax.set_xlabel("Priority")
        ax.set_ylabel("Count")
        st.pyplot(fig)
    else:
        st.warning("⚠️ No such combinations exist for Priority")

st.markdown("---")

# --------- Table ---------
st.subheader("Filtered Support Emails")
if not view.empty:
    st.dataframe(view[["sender", "subject", "issue_type", "sentiment", "priority", "sent_dt"]], use_container_width=True)
else:
    st.warning("⚠️ No such combinations exist for the current filter selection.")

# --------- Email detail + AI response editor ---------
st.subheader("Process Email")
if not view.empty:
    idx = st.selectbox(
        "Select an email to draft a response:",
        view.index.tolist(),
        format_func=lambda i: f"{view.loc[i,'sender']} — {view.loc[i,'subject']}"
    )
    row = view.loc[idx]
    st.write("**Body:**")
    st.write(row["body"])

    st.write("**Extracted details:**")
    c1, c2, c3 = st.columns(3)
    c1.write(f"Issue: `{row['issue_type']}`")
    c2.write(f"Sentiment: `{row['sentiment']}`")
    c3.write(f"Priority: `{row['priority']}`")

    st.write("**Contacts in body:**")
    st.write(row.get("contacts_email_in_body") or "—")
    st.write(row.get("contacts_phone_in_body") or "—")

    draft = row.get("draft_response") or response_template(row)
    edited = st.text_area("AI-generated draft (editable before sending)", draft, height=300)

    colx, coly = st.columns([1, 1])
    if colx.button("Copy to clipboard (browser)"):
        st.info("Use your browser's copy shortcut inside the text area.")
    if coly.button("Mark as resolved"):
        st.success("Marked as resolved (simulation)")
else:
    st.warning("⚠️ No such combinations exist for the current filter selection.")

st.markdown("---")
st.caption("Demo app — rule-based classification + templated drafts. Replace with your LLM + RAG pipeline in production.")

