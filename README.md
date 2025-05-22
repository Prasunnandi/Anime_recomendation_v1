
# 🎌 Anime Recommendation System


The **Anime Recommender System** is a web application that suggests anime titles based on user input and preferences. It uses a hybrid filtering approach combining **content-based filtering**, **collaborative filtering**, and **popularity-based ranking** to provide personalized and accurate anime suggestions.


Users can:
- Search for anime recommendations by name or genre.
- Filter recommendations by anime types (TV, Movie, OVA, etc.).
- Browse popular anime by type with pagination.
- View detailed project information and team member profiles.

This system aims to enhance the anime discovery experience for fans and newcomers alike.

## 📌 Features

- 🔍 **Content-Based Recommendations** using TF-IDF and Cosine Similarity.
- 🌟 **Popularity-Based Suggestions** based on normalized ratings and member counts.
- 🧠 **Hybrid Filtering** combining personalization and trending shows.
- 📊 **Type-based Filtering** for popular anime (TV, Movie, OVA).
- 💻 **Flask Web Application** with a clean, user-friendly UI.

---

## 📁 Project Directory Structure

```
anime-recommender/
├── app.py
├── templates/
│ ├── index.html
│ ├── recommendations.html
│ └── popular.html
├── static/
│ ├── css/
│ │ └── style.css
│ └── js/
│ └── script.js
├── data/
│ └── anime_data.csv
├── models/
│ └── collaborative_model.pkl
├── requirements.txt
├── Procfile
├── runtime.txt
└── README.md
```

> ℹ️ **The full project description and motivation can be found in** `templates/description.html`. It includes:
> - Purpose & scope
> - Dataset details
> - Algorithmic steps
> - Comparisons with other approaches
> - Advantages of the hybrid model
> - Future improvement scope

---
## Installation & Setup

### Prerequisites

- Python 3.7 or above  
- pip (Python package installer)  
- Git  

### Steps

1. Clone the repository:
   ```bash
   [git clone https://github.com/Prasunnandi/Anime_recomendation_2025.git]
   cd Anime_recomendation_2025

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

4. Run the Flask app:
   ```bash
   flask run
