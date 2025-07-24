import os
import requests

def test_tmdb_api():
    """Test TMDB API to get movies with specific watch providers"""
    key = os.getenv("TMDB_API_KEY")
    
    if not key:
        print("❌ TMDB_API_KEY environment variable not found!")
        print("Please set your TMDB API key:")
        print("export TMDB_API_KEY='your_api_key_here'")
        return
    
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/discover/movie",
            params={
                "with_watch_providers": "337|15", 
                "watch_region": "US", 
                "api_key": key
            }
        )
        
        if r.status_code == 200:
            data = r.json()
            print("✅ API call successful!")
            print(f"Found {data.get('total_results', 0)} movies")
            print("\nFirst few results:")
            for movie in data.get('results', [])[:5]:
                print(f"- {movie.get('title', 'Unknown')} ({movie.get('release_date', 'Unknown year')})")
        else:
            print(f"❌ API call failed with status code: {r.status_code}")
            print(f"Response: {r.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    test_tmdb_api() 