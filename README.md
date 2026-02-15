<div align="center">

# 🤖 Reddit Scraper

<img src="./images/logo.png" alt="Project Logo" width="420"/>

**Modular Reddit data collection framework**  
Scrape subreddits, posts, and users into clean structured JSON.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Data](https://img.shields.io/badge/Output-JSON-green)
![Database](https://img.shields.io/badge/MongoDB-supported-47A248?logo=mongodb&logoColor=white)
![License](https://img.shields.io/github/license/glowfi/reddit-scraper)

</div>

---

## ✨ Overview

A modular Reddit scraping pipeline designed for **data collection, analytics, and research workflows**.

The project gathers structured data about:

- 📚 **Subreddits**
- 📝 **Posts**
- 👤 **Users**

and exports everything as **clean JSON datasets** ready for:

- databases
- machine learning pipelines
- analytics
- data exploration

No manual scraping steps required.

---

## 🚀 Features

- Modular scraper architecture
- Structured JSON output
- Automated scraping workflow
- MongoDB import helpers
- Large dataset handling utilities
- Environment-based configuration

### Collects

| Entity     | Data                        |
| ---------- | --------------------------- |
| Subreddits | metadata & statistics       |
| Posts      | content, scores, engagement |
| Users      | profile & activity info     |

---

## 🧠 How It Works

```

run.py
│
├── subreddits.py
├── posts.py
└── users.py
↓
JSON datasets
↓
(optional) MongoDB import

```

Each scraper is independent and reusable.

---

## 📦 Installation

### 1️⃣ Clone & setup environment

```bash
git clone https://github.com/glowfi/reddit-scraper
cd reddit-scraper

python -m venv env
source env/bin/activate      # Linux / macOS
# env\Scripts\activate       # Windows

pip install -r requirements.txt
```

---

### 2️⃣ Configure API credentials

Edit `env-sample` and rename it:

```
.env
```

```env
username=<RedditUsername>
password=<RedditPassword>
client_id=<ClientID>
client_secret=<ClientSecret>

TOTAL_SUBREDDITS_PER_TOPICS=6
SUBREDDIT_SORT_FILTER="hot"
POSTS_PER_SUBREDDIT=10
POSTS_SORT_FILTER="new"
```

Create Reddit API credentials here:

👉 [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

---

### 3️⃣ Run scraper

```bash
python run.py
```

Pipeline execution:

1. Scrape subreddits
2. Scrape posts
3. Scrape users
4. Export JSON datasets
5. Optional dataset splitting

---

## 📊 Output Examples

> JSON files are large (16–25MB). Download instead of viewing in browser.

### Subreddit Document

![Subreddit example](./images/subreddits.png)

Sample:
[https://files.catbox.moe/r7a7um.json](https://files.catbox.moe/r7a7um.json)

---

### Post Document

![Post example](./images/posts.png)

Sample:
[https://files.catbox.moe/5cf2xw.json](https://files.catbox.moe/5cf2xw.json)

---

### User Document

![User example](./images/users.png)

Sample:
[https://files.catbox.moe/yp506n.json](https://files.catbox.moe/yp506n.json)

---

## 🗂️ Project Structure

```
reddit-scraper/
├── subreddits.py
├── posts.py
├── users.py
├── run.py
├── utils/
│   ├── split.py
│   └── import_data_to_mongodb.sh
└── output/
```

---

## 🧩 Utilities

| Tool                        | Purpose                         |
| --------------------------- | ------------------------------- |
| `run.py`                    | Executes full scraping pipeline |
| `utils/split.py`            | Splits large JSON datasets      |
| `import_data_to_mongodb.sh` | Bulk imports into MongoDB       |

---

## 🗄️ MongoDB Import

After scraping:

```bash
./utils/import_data_to_mongodb.sh
```

Ensure MongoDB is running beforehand.

---

## ⚠️ Notes

- Reddit API rate limits apply
- Scraping speed depends on network/API limits
- Designed for research & data workflows
- Respect Reddit API terms of service

---

## 🤝 Contributing

Contributions, improvements, and issue reports are welcome.

Small focused PRs are preferred.

---

## 📄 License

GPL-3.0
