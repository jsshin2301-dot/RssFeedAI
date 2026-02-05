import json
import os
import base64
import feedparser
import pandas as pd
from github import Github, InputGitTreeElement
import google.generativeai as genai
from datetime import datetime, timedelta
import streamlit as st

class GithubDB:
    def __init__(self, token, repo_name):
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)
    
    def load_json(self, file_path):
        try:
            content = self.repo.get_contents(file_path)
            decoded_content = base64.b64decode(content.content).decode("utf-8")
            return json.loads(decoded_content)
        except Exception as e:
            # Fallback to local file if GitHub fails
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as local_e:
                    st.error(f"Error loading local file {file_path}: {local_e}")
                    return {}
            st.error(f"Error loading {file_path} from GitHub and local: {e}")
            return {}

    def save_json(self, file_path, data, commit_message):
        # Always save locally first to ensure data persistence
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as local_e:
            st.error(f"Error saving local file {file_path}: {local_e}")
        
        # Try to save to GitHub
        try:
            try:
                content = self.repo.get_contents(file_path)
                sha = content.sha
                self.repo.update_file(file_path, commit_message, json.dumps(data, ensure_ascii=False, indent=4), sha)
            except:
                self.repo.create_file(file_path, commit_message, json.dumps(data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            # If GitHub fails, we rely on local save (which already happened)
            # st.warning(f"Failed to sync with GitHub: {e}")
            return False

def fetch_rss_feeds(feed_urls, days=3):
    articles = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Handle different date formats or missing dates
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed'):
                 published = datetime(*entry.updated_parsed[:6])
            
            if published and published > cutoff_date:
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": published.strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": getattr(entry, 'summary', '')
                })
    return articles

def generate_ai_report(api_key, articles):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    if not articles:
        return "최근 3일간의 IT 뉴스가 없습니다."
    
    # Chunking input to avoid token limits if necessary, but for this spec we assume it fits or simple truncation
    # Create a simple text representation of articles
    news_text = ""
    for i, art in enumerate(articles[:50]): # Limit to 50 articles to be safe
        news_text += f"{i+1}. Title: {art['title']}\nLink: {art['link']}\nSummary: {art['summary'][:200]}\n\n"
        
    prompt = f"""
    당신은 전문 IT 뉴스 큐레이터입니다. 아래 제공된 최근 IT 뉴스 기사들을 분석하여 1장 분량의 데일리 뉴스 리포트를 작성해주세요.
    
    [지침]
    1. 기사들을 유사한 주제끼리 그룹화하세요 (예: AI/ML, 반도체, 모바일, 비즈니스 등).
    2. 각 주제별로 핵심 내용을 3문장 이내로 요약하세요.
    3. 각 요약 항목 끝에는 반드시 관련 기사의 제목과 [Link](URL)를 포함하여 출처를 명시하세요.
    4. 전체적인 어조는 전문적이고 통찰력 있게 유지하세요.
    5. 가독성 좋은 Markdown 형식으로 작성하세요.
    
    [뉴스 데이터]
    {news_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류 발생: {e}"

def update_visitor_stats(db):
    stats = db.load_json("data/stats.json")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize if empty
    if "total_views" not in stats:
        stats["total_views"] = 0
    if "daily_visitors" not in stats:
        stats["daily_visitors"] = {}
        
    stats["total_views"] += 1
    stats["daily_visitors"][today] = stats["daily_visitors"].get(today, 0) + 1
    
    # Save quietly (optimistic locking issue might occur in high traffic but okay for prototype)
    # Note: To avoid excessive commits on every page load in dev, we might want to skip or batch, 
    # but requirement says "Update stats". We will do it.
    # However, saving on EVERY refresh might be too slow/rate-limited for GitHub API on Streamlit Cloud.
    # For now, implemented as requested.
    db.save_json("data/stats.json", stats, f"Update stats for {today}")
    return stats
