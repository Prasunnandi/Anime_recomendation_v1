import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import random

load_dotenv()

MAL_CLIENT_ID = os.getenv('MAL_CLIENT_ID')

def get_anime_details(anime_name):
    """Fetch anime details from MyAnimeList API"""
    if not MAL_CLIENT_ID:
        return None
        
    try:
        url = f"https://api.myanimelist.net/v2/anime?q={anime_name}&limit=1"
        headers = {'X-MAL-CLIENT-ID': MAL_CLIENT_ID}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('data'):
            return None
            
        anime_id = data['data'][0]['node']['id']
        
        # Get anime details
        detail_url = f"https://api.myanimelist.net/v2/anime/{anime_id}?fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics"
        detail_response = requests.get(detail_url, headers=headers)
        detail_response.raise_for_status()
        
        anime_data = detail_response.json()
        
        # Get recommendations
        rec_url = f"https://api.myanimelist.net/v2/anime/{anime_id}/recommendations?limit=5"
        rec_response = requests.get(rec_url, headers=headers)
        
        recommendations = []
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            recommendations = [{
                'title': item['node']['title'],
                'image_url': item['node']['main_picture']['medium']
            } for item in rec_data['data']]
        
        return {
            'title': anime_data.get('title', ''),
            'image_url': anime_data.get('main_picture', {}).get('medium', ''),
            'score': anime_data.get('mean', 0),
            'type': anime_data.get('media_type', 'Unknown'),
            'episodes': anime_data.get('num_episodes', 0),
            'recommendations': recommendations
        }
    except Exception as e:
        print(f"Error fetching anime details from MAL: {e}")
        return None

def get_anime_image(anime_name):
    """Fallback method to get anime image from web search"""
    try:
        search_url = f"https://www.google.com/search?tbm=isch&q={anime_name}+anime+cover"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')
        
        if len(images) > 1:  # Skip the first image which is usually a Google logo
            return images[1]['src']
        return None
    except:
        return None