import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from utils import get_anime_details, get_anime_image
import pickle
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load data
anime_df = pd.read_csv('data/anime.csv')
ratings_df = pd.read_csv('data/ratings.csv')

# Preprocess data
anime_df = anime_df.dropna(subset=['genre', 'type', 'episodes'])
anime_df['episodes'] = anime_df['episodes'].replace('Unknown', 0).astype(int)
anime_df['genre'] = anime_df['genre'].fillna('')
anime_df['type'] = anime_df['type'].fillna('')

# Create content features
anime_df['content'] = anime_df['genre'] + ' ' + anime_df['type'] + ' ' + anime_df['episodes'].astype(str)

# Vectorize content
vectorizer = CountVectorizer()
content_matrix = vectorizer.fit_transform(anime_df['content'])

# Compute content similarity
content_similarity = cosine_similarity(content_matrix)

# Load or create collaborative filtering model
model_path = 'models/recommendation_model.pkl'
if os.path.exists(model_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
else:
    # Create a pivot table for collaborative filtering
    user_anime_matrix = ratings_df.pivot_table(index='user_id', columns='anime_id', values='rating')
    user_anime_matrix = user_anime_matrix.fillna(0)
    
    # Compute cosine similarity between anime
    anime_similarity = cosine_similarity(user_anime_matrix.T)
    model = {'user_anime_matrix': user_anime_matrix, 'anime_similarity': anime_similarity}
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

@app.route('/')
def home():
    popular_anime = anime_df.sort_values('members', ascending=False).head(10)
    return render_template('index.html', popular_anime=popular_anime.to_dict('records'))

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        anime_name = request.form['anime_name']
        
        # Find anime in dataset
        anime_match = anime_df[anime_df['name'].str.contains(anime_name, case=False, na=False)]
        
        if len(anime_match) == 0:
            # Try to get from MAL API if not found in dataset
            try:
                mal_data = get_anime_details(anime_name)
                if mal_data:
                    recommendations = []
                    for item in mal_data.get('recommendations', [])[:5]:
                        rec_details = get_anime_details(item['title'])
                        if rec_details:
                            recommendations.append({
                                'name': rec_details['title'],
                                'image_url': rec_details['image_url'],
                                'score': rec_details['score'],
                                'type': rec_details['type'],
                                'episodes': rec_details['episodes'],
                                'source': 'MAL API'
                            })
                    return render_template('recommend.html', 
                                        input_anime=anime_name,
                                        recommendations=recommendations,
                                        source='MyAnimeList API')
            except Exception as e:
                print(f"Error fetching from MAL API: {e}")
            
            return render_template('recommend.html', 
                                input_anime=anime_name,
                                message="Anime not found in our database or MAL API.")
        
        # Get recommendations from our model
        anime_id = anime_match.iloc[0]['anime_id']
        
        # Content-based filtering
        idx = anime_df[anime_df['anime_id'] == anime_id].index[0]
        content_scores = list(enumerate(content_similarity[idx]))
        content_scores = sorted(content_scores, key=lambda x: x[1], reverse=True)[1:6]
        content_indices = [i[0] for i in content_scores]
        content_recs = anime_df.iloc[content_indices]
        
        # Collaborative filtering
        try:
            anime_idx = model['user_anime_matrix'].columns.get_loc(anime_id)
            collab_scores = list(enumerate(model['anime_similarity'][anime_idx]))
            collab_scores = sorted(collab_scores, key=lambda x: x[1], reverse=True)[1:6]
            collab_indices = [i[0] for i in collab_scores]
            collab_recs = anime_df[anime_df['anime_id'].isin(model['user_anime_matrix'].columns[collab_indices])]
            
            # Combine recommendations
            combined_recs = pd.concat([content_recs, collab_recs]).drop_duplicates().head(5)
        except:
            combined_recs = content_recs.head(5)
        
        # Get additional details and images
        recommendations = []
        for _, row in combined_recs.iterrows():
            try:
                mal_data = get_anime_details(row['name'])
                image_url = mal_data['image_url'] if mal_data else get_anime_image(row['name'])
            except:
                image_url = get_anime_image(row['name'])
            
            recommendations.append({
                'name': row['name'],
                'image_url': image_url,
                'score': row['score'],
                'type': row['type'],
                'episodes': row['episodes'],
                'source': 'Our Recommendation Engine'
            })
        
        return render_template('recommend.html', 
                            input_anime=anime_match.iloc[0]['name'],
                            recommendations=recommendations,
                            source='Our Recommendation Engine')
    
    return render_template('recommend.html')

@app.route('/team')
def team():
    team_members = [
        {'name': 'Your Name', 'role': 'Project Lead', 'bio': 'Responsible for overall project development and deployment.'},
        {'name': 'Member 2', 'role': 'ML Engineer', 'bio': 'Developed the recommendation algorithms.'},
        {'name': 'Member 3', 'role': 'Frontend Developer', 'bio': 'Designed and implemented the user interface.'},
        {'name': 'Member 4', 'role': 'Data Engineer', 'bio': 'Processed and cleaned the anime datasets.'}
    ]
    return render_template('team.html', team_members=team_members)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)