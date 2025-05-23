import pandas as pd
import numpy as np
import requests
import time
import os
from tqdm import tqdm

# Create data directory if not exists
os.makedirs("data", exist_ok=True)

# Load datasets (assuming files are already downloaded)
try:
    anime_df = pd.read_csv('data/anime.csv')
    rating_df = pd.read_csv('data/rating.csv')
except FileNotFoundError:
    print("Please download the datasets from Kaggle and place them in the data folder")
    print("Anime dataset: https://www.kaggle.com/CooperUnion/anime-recommendations-database")
    print("Rating dataset: https://www.kaggle.com/CooperUnion/anime-recommendations-database")
    exit()

# --- Data Preprocessing ---

def clean_anime_data(df):
    # Rename columns for consistency
    df = df.rename(columns={'name': 'title', 'rating': 'avg_rating'})

    # Handle missing values
    df['genre'] = df['genre'].fillna('Unknown')
    df['type'] = df['type'].fillna('Unknown')
    df['episodes'] = df['episodes'].replace('Unknown', np.nan)

    # Convert to numeric
    df['episodes'] = pd.to_numeric(df['episodes'], errors='coerce')
    df['avg_rating'] = pd.to_numeric(df['avg_rating'], errors='coerce')

    # Fill numeric missing values
    df['avg_rating'] = df['avg_rating'].fillna(df['avg_rating'].median())
    df['members'] = df['members'].fillna(df['members'].median())
    df['episodes'] = df['episodes'].fillna(df['episodes'].median())

    return df

def clean_rating_data(df):
    # Replace -1 (unknown rating) with NaN
    df['rating'] = df['rating'].replace(-1, np.nan)
    return df

anime_df = clean_anime_data(anime_df)
rating_df = clean_rating_data(rating_df)

# --- Update anime_df with missing anime info from rating.csv ---

existing_ids = set(anime_df['anime_id'].tolist())
max_id = max(existing_ids)
print(f"Currently {len(existing_ids)} anime in dataset. Max anime_id = {max_id}")

def fetch_anime_info(anime_id):
    url = f'https://api.jikan.moe/v4/anime/{anime_id}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()['data']
            return {
                'anime_id': anime_id,
                'title': data['title'],
                'genre': ', '.join([g['name'] for g in data['genres']]) if data['genres'] else 'Unknown',
                'type': data['type'] or 'Unknown',
                'episodes': data['episodes'],
                'avg_rating': data['score'],
                'members': data['members'],
                'aired': data['aired']['from']
            }
        else:
            return None
    except Exception:
        return None

rating_anime_ids = set(rating_df['anime_id'].unique())
missing_anime_ids = rating_anime_ids - existing_ids
print(f"Found {len(missing_anime_ids)} missing anime IDs from rating.csv")

new_anime_data = []
for anime_id in tqdm(sorted(missing_anime_ids), desc="Fetching missing anime"):
    info = fetch_anime_info(anime_id)
    if info:
        new_anime_data.append(info)
    time.sleep(0.5)  # avoid rate limiting

# Update aired and avg_rating for existing anime
print("Updating aired and avg_rating for existing anime...")
updated_data = []
for anime_id in tqdm(anime_df['anime_id'], desc="Updating existing anime"):
    info = fetch_anime_info(anime_id)
    if info:
        updated_data.append(info)
    else:
        row = anime_df[anime_df['anime_id'] == anime_id].iloc[0].to_dict()
        row['aired'] = None
        updated_data.append(row)
    time.sleep(0.5)

updated_df = pd.DataFrame(updated_data)

if new_anime_data:
    new_df = pd.DataFrame(new_anime_data)
    updated_df = pd.concat([updated_df, new_df], ignore_index=True)

# Clean updated_df to fill missing values like before
updated_df = clean_anime_data(updated_df)

# --- Fetch Adult and NSFW-leaning themed anime from Jikan ---

existing_ids = set(updated_df['anime_id'])

# Genres: hentai(12), ecchi(9)
adult_genres = [9, 12]

# Themes NSFW-leaning: Adult Cast(49), Harem(34), Gag Humor(50), Gore(51), Sexual Content(64)
nsfw_themes = [34, 49, 50, 51, 64]

def fetch_anime_by_genre_or_theme(id_list, limit=500):
    all_anime = []
    for genre_or_theme_id in id_list:
        page = 1
        while True:
            url = f"https://api.jikan.moe/v4/anime?genres={genre_or_theme_id}&limit=25&page={page}"
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    break
                data = response.json()['data']
                if not data:
                    break
                for item in data:
                    anime_id = item['mal_id']
                    if anime_id in existing_ids:
                        continue
                    anime_info = {
                        'anime_id': anime_id,
                        'title': item['title'],
                        'genre': ', '.join([g['name'] for g in item['genres']]) if item['genres'] else 'Unknown',
                        'type': item['type'] or 'Unknown',
                        'episodes': item['episodes'],
                        'avg_rating': item['score'],
                        'members': item['members'],
                        'aired': item['aired']['from'] if item['aired'] else None
                    }
                    all_anime.append(anime_info)
                page += 1
                time.sleep(0.5)
                if len(all_anime) >= limit:
                    break
            except Exception as e:
                print(f"Error fetching genre/theme {genre_or_theme_id} page {page}: {e}")
                break
    return all_anime

print("Fetching adult anime (Hentai and Ecchi)...")
adult_data = fetch_anime_by_genre_or_theme(adult_genres, limit=250)

print("Fetching NSFW-leaning themed anime (Adult Cast, Harem, Gag Humor, Gore, Sexual Content)...")
nsfw_data = fetch_anime_by_genre_or_theme(nsfw_themes, limit=250)

# Combine and deduplicate
combined_adult_nsfw = adult_data + nsfw_data
if combined_adult_nsfw:
    adult_nsfw_df = pd.DataFrame(combined_adult_nsfw)
    full_df = pd.concat([updated_df, adult_nsfw_df], ignore_index=True).drop_duplicates(subset='anime_id')
    full_df = clean_anime_data(full_df)
else:
    full_df = updated_df

# --- Save cleaned datasets ---
full_df.to_csv('data/cleaned_anime.csv', index=False)
rating_df.to_csv('data/cleaned_rating.csv', index=False)

print(f"Cleaned anime dataset saved with {len(full_df)} entries at 'data/cleaned_anime.csv'.")
print(f"Cleaned rating dataset saved at 'data/cleaned_rating.csv'.")

# You can continue with your EDA and feature engineering on 'full_df' and 'rating_df'.