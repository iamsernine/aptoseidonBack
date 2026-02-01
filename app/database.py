import sqlite3
import json
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aptoseidon.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Analysis results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        job_id TEXT PRIMARY KEY,
        project_url TEXT,
        project_type TEXT,
        wallet_address TEXT,
        report_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Reputation/Ratings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reputation (
        job_id TEXT PRIMARY KEY,
        up_votes INTEGER DEFAULT 0,
        down_votes INTEGER DEFAULT 0,
        FOREIGN KEY (job_id) REFERENCES analyses (job_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def save_analysis(job_id: str, project_url: str, project_type: str, wallet_address: str, report: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO analyses (job_id, project_url, project_type, wallet_address, report_json)
    VALUES (?, ?, ?, ?, ?)
    ''', (job_id, project_url, project_type, wallet_address, json.dumps(report)))
    
    # Initialize reputation for new job
    cursor.execute('INSERT OR IGNORE INTO reputation (job_id) VALUES (?)', (job_id,))
    
    conn.commit()
    conn.close()

def get_analysis_by_url(project_url: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses WHERE project_url = ? ORDER BY created_at DESC LIMIT 1', (project_url,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "job_id": row["job_id"],
            "report": json.loads(row["report_json"])
        }
    return None

def update_rating(job_id: str, rating: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if rating == "up":
        cursor.execute('UPDATE reputation SET up_votes = up_votes + 1 WHERE job_id = ?', (job_id,))
    elif rating == "down":
        cursor.execute('UPDATE reputation SET down_votes = down_votes + 1 WHERE job_id = ?', (job_id,))
    
    conn.commit()
    conn.close()

def get_rating(job_id: str) -> Dict[str, int]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT up_votes, down_votes FROM reputation WHERE job_id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"up": row["up_votes"], "down": row["down_votes"]}
    return {"up": 0, "down": 0}
