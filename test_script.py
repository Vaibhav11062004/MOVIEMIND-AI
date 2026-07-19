from app import fetch_data
movie_id = 27205 # Inception
data = fetch_data(f"/movie/{movie_id}", {"append_to_response": "watch/providers"})
print(data.get("watch/providers", {}).get("results", {}).get("US", {}))
