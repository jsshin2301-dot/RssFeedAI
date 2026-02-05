import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils import GithubDB, fetch_rss_feeds, generate_ai_report, update_visitor_stats

# --- Configuration & Setup ---
st.set_page_config(
    page_title="AI IT Newsroom",
    page_icon="📰",
    layout="wide"
)

# Load Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except FileNotFoundError:
    st.error("Secrets not found. Please configure .streamlit/secrets.toml")
    st.stop()

# Initialize DB
db = GithubDB(GITHUB_TOKEN, REPO_NAME)

# Update Stats on Visit (only once per session ideally, but for now simple increment)
if "stats_updated" not in st.session_state:
    update_visitor_stats(db)
    st.session_state["stats_updated"] = True

# --- Sidebar & Authentication ---
with st.sidebar:
    st.title("📰 AI IT Newsroom")
    
    app_mode = st.radio("Go to", ["Newsroom", "Admin Dashboard"])
    
    st.divider()
    
    if app_mode == "Admin Dashboard":
        password = st.text_input("Admin Password", type="password")
        if password == ADMIN_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Logged in as Admin")
        else:
            st.session_state["authenticated"] = False
            if password:
                st.error("Incorrect password")
    
    st.markdown("---")
    st.caption("Powered by Gemini 1.5 Flash")

# --- Newsroom View (Public) ---
if app_mode == "Newsroom":
    st.header("📢 Daily IT News Report")
    
    news_data = db.load_json("data/news_data.json")
    
    if not news_data:
        st.info("아직 생성된 뉴스 리포트가 없습니다. 관리자 대시보드에서 분석을 실행해주세요.")
    else:
        # Sort dates descending
        available_dates = sorted(news_data.keys(), reverse=True)
        selected_date = st.selectbox("📅 날짜 선택", available_dates)
        
        st.divider()
        
        if selected_date:
            report_content = news_data[selected_date]
            st.markdown(report_content)
        else:
            st.warning("선택 가능한 리포트가 없습니다.")

# --- Admin Dashboard View (Protected) ---
elif app_mode == "Admin Dashboard":
    if not st.session_state.get("authenticated", False):
        st.warning("Please verify your password in the sidebar.")
    else:
        st.header("⚙️ Admin Dashboard")
        
        tab1, tab2, tab3 = st.tabs(["🚀 Run Analysis", "📝 Manage Feeds", "📊 Statistics"])
        
        # Tab 1: Run Analysis
        with tab1:
            st.subheader("Generate New Report")
            st.markdown("최신 RSS 피드를 수집하고 AI 요약을 수행합니다.")
            
            if st.button("Start Analysis"):
                with st.status("Processing...", expanded=True) as status:
                    st.write("📥 Fetching RSS Feeds...")
                    feeds = db.load_json("data/feeds.json")
                    if not feeds:
                        st.error("No feeds configured.")
                        st.stop()
                        
                    articles = fetch_rss_feeds(feeds, days=3)
                    st.write(f"✅ Found {len(articles)} articles from last 3 days.")
                    
                    st.write("🧠 Generating AI Summary (Gemini 1.5 Flash)...")
                    report = generate_ai_report(GEMINI_API_KEY, articles)
                    
                    st.write("💾 Saving to GitHub...")
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    # Reload latest news_data just in case
                    current_news_data = db.load_json("data/news_data.json")
                    current_news_data[today] = report
                    
                    db.save_json("data/news_data.json", current_news_data, f"Add report for {today}")
                    status.update(label="Analysis Completed!", state="complete", expanded=False)
                    
                st.success(f"Report for {today} generated successfully!")
                st.rerun()

        # Tab 2: Manage Feeds
        with tab2:
            st.subheader("RSS Feed List")
            feeds = db.load_json("data/feeds.json")
            
            # Display current feeds with delete button
            if feeds:
                for i, url in enumerate(feeds):
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.text(url)
                    if col2.button("Remove", key=f"del_{i}"):
                        feeds.pop(i)
                        db.save_json("data/feeds.json", feeds, "Remove feed URL")
                        st.rerun()
            else:
                st.info("No feeds added.")
            
            # Add new feed
            st.divider()
            with st.form("add_feed_form"):
                new_feed = st.text_input("Add New RSS URL")
                submitted = st.form_submit_button("Add Feed")
                
                if submitted:
                    if new_feed and new_feed not in feeds:
                        feeds.append(new_feed)
                        db.save_json("data/feeds.json", feeds, "Add feed URL")
                        st.success("Feed added!")
                        st.rerun()
                    elif new_feed in feeds:
                        st.warning("Feed already exists.")
                    elif not new_feed:
                        st.warning("Please enter a URL.")

        # Tab 3: Statistics
        with tab3:
            st.subheader("Visitor Statistics")
            stats = db.load_json("data/stats.json")
            
            col1, col2 = st.columns(2)
            col1.metric("Total Views", stats.get("total_views", 0))
            
            # Daily chart
            daily_data = stats.get("daily_visitors", {})
            if daily_data:
                df = pd.DataFrame(list(daily_data.items()), columns=["Date", "Visitors"])
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")
                st.line_chart(df.set_index("Date"))
            else:
                st.info("Not enough data for chart.")
