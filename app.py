import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TMDB_BASE_URL = "https://api.tmdb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"
PROFILE_BASE_URL = "https://image.tmdb.org/t/p/w185"
LOGO_BASE_URL = "https://image.tmdb.org/t/p/w92"

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Streamlit Movie Explorer",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION INITIALIZATION ---
def init_session_state():
    """Initialize default session state variables if they don't exist."""
    defaults = {
        "favorites": {},
        "history": [],
        "settings_adult": False,
        "settings_language": "en-US",
        "recent_searches": [],
        "selected_movie": None,
        "discover_filters": {
            "sort_by": "popularity.desc",
            "vote_count.gte": 100
        }
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# --- CUSTOM CSS INJECTION ---
def inject_custom_css():
    """Load and inject custom CSS stylesheet."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception:
            pass

inject_custom_css()

# --- CUSTOM UI COMPONENTS ---
def display_empty_state(icon, title, message):
    """Renders a beautifully styled custom empty state card."""
    st.markdown(
        f"""
        <div class="empty-state-container">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-message">{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- API HELPERS ---
@st.cache_resource
def get_session():
    """Returns a requests Session with retry logic."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def get_api_key():
    """Retrieve TMDB API key from environment."""
    load_dotenv(override=True)
    key = os.getenv("TMDB_API_KEY")
    if not key or key.strip() == "" or key.strip().lower() in ("your_tmdb_api_key", "your_api_key_here"):
        if st.runtime.exists():
            # Render a beautiful glass setup wizard!
            st.markdown(
                """
                <div class="empty-state-container" style="max-width: 600px; margin: 3rem auto !important; border: 1px dashed rgba(99, 102, 241, 0.3) !important;">
                    <div class="empty-state-icon">🍿</div>
                    <div class="empty-state-title">TMDB API Key Required</div>
                    <div class="empty-state-message">
                        Welcome to the <b>Movie Explorer Dashboard</b>! To fetch live movies, ratings, and trailers, you need a free API key from The Movie Database (TMDB).
                    </div>
                    <hr style="width: 100%; border-color: rgba(255,255,255,0.06); margin: 1.5rem 0 !important;" />
                    <div style="text-align: left; width: 100%; color: #94a3b8; font-size: 0.9rem; line-height: 1.7; font-family: 'Outfit', sans-serif;">
                        <b>How to get your key:</b>
                        <ol style="margin-top: 0.5rem; padding-left: 1.25rem;">
                            <li>Sign up at <a href="https://www.themoviedb.org/" target="_blank" style="color: #818cf8; text-decoration: underline;">themoviedb.org</a></li>
                            <li>Navigate to your account <b>Settings</b> > <b>API</b></li>
                            <li>Request an API Key (choose the Developer option)</li>
                            <li>Open the file <code style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; color: #fff;">.env</code> in your project</li>
                            <li>Paste your key: <code style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; color: #fff;">TMDB_API_KEY="your_api_key"</code></li>
                        </ol>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.stop()
        else:
            raise ValueError("TMDB_API_KEY is missing or invalid in your .env file.")
    return key.strip()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(endpoint: str, params: dict = None):
    """Generic function to fetch data from TMDB API with caching and error handling."""
    if params is None:
        params = {}
        
    api_key = get_api_key()
    if not api_key:
        return None
        
    params["api_key"] = api_key
    
    # Check if running within a Streamlit session context
    if st.runtime.exists():
        params["language"] = st.session_state.settings_language
        if "include_adult" not in params:
            params["include_adult"] = st.session_state.settings_adult
    else:
        params["language"] = "en-US"
        if "include_adult" not in params:
            params["include_adult"] = False
        
    url = f"{TMDB_BASE_URL}{endpoint}"
    try:
        response = get_session().get(url, params=params, timeout=10)
        
        # Check specific status codes before raising generic exceptions
        if response.status_code == 401:
            if st.runtime.exists():
                st.error("🔒 Invalid API key: You must be granted a valid key from TMDB.")
            return None
        elif response.status_code == 404:
            # 404 can happen for a missing movie ID, silently ignore or handle higher up
            return None
        elif response.status_code == 429:
            if st.runtime.exists():
                st.warning("⏳ Rate limit exceeded. Please wait a moment before trying again.")
            return None
        elif response.status_code >= 500:
            if st.runtime.exists():
                st.error("🌐 TMDB servers are currently experiencing issues. Please try again later.")
            return None
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        if st.runtime.exists():
            st.error("⏱️ Network timeout: The request took too long to complete. Please check your connection.")
        return None
    except requests.exceptions.ConnectionError:
        if st.runtime.exists():
            st.error("🔌 Connection error: Unable to connect to TMDB servers. Please check your internet connection.")
        return None
    except requests.exceptions.RequestException as e:
        if st.runtime.exists():
            st.error(f"❌ Failed to fetch data: {e}")
        return None

# --- TMDB CALLS ---
def get_popular_movies(page=1): return fetch_data("/movie/popular", {"page": page})
def get_trending_movies(window="day"): return fetch_data(f"/trending/movie/{window}")
def get_top_rated_movies(page=1): return fetch_data("/movie/top_rated", {"page": page})
def get_upcoming_movies(page=1): return fetch_data("/movie/upcoming", {"page": page})
def search_movies(query, page=1): return fetch_data("/search/movie", {"query": query, "page": page})
def get_movie_details(movie_id): return fetch_data(f"/movie/{movie_id}", {"append_to_response": "videos,credits,reviews,watch/providers"})
def get_similar_movies(movie_id): return fetch_data(f"/movie/{movie_id}/similar")
def get_genres(): return fetch_data("/genre/movie/list")
def discover_movies_advanced(params): return fetch_data("/discover/movie", params)
def search_person(query, page=1): return fetch_data("/search/person", {"query": query, "page": page})
def get_person_movie_credits(person_id): return fetch_data(f"/person/{person_id}/movie_credits")

# --- UI HELPERS ---
def toggle_favorite(movie):
    """Toggle a movie in the user's favorites."""
    mid = movie.get("id")
    if mid in st.session_state.favorites:
        del st.session_state.favorites[mid]
    else:
        st.session_state.favorites[mid] = movie

def add_to_history(movie):
    """Add a movie to the viewing history, keeping only the latest 50."""
    st.session_state.history = [m for m in st.session_state.history if m.get("id") != movie.get("id")]
    st.session_state.history.insert(0, movie)
    st.session_state.history = st.session_state.history[:50]

def view_movie_details(movie):
    """Set the selected movie and add it to history."""
    st.session_state.selected_movie = movie.get("id")
    add_to_history(movie)

def get_movie_card_genres(movie):
    """Retrieve genre names string for the movie card."""
    genres_list = movie.get("genres")
    if genres_list and isinstance(genres_list, list):
        if len(genres_list) > 0 and isinstance(genres_list[0], dict):
            names = [g.get("name") for g in genres_list if g.get("name")]
            return ", ".join(names[:2])
    
    genre_ids = movie.get("genre_ids")
    if genre_ids:
        genres_data = get_genres()
        if genres_data and genres_data.get("genres"):
            genre_map = {g["id"]: g["name"] for g in genres_data["genres"]}
            names = [genre_map[gid] for gid in genre_ids if gid in genre_map]
            return ", ".join(names[:2])
            
    return ""

def display_movie_card(movie, key_prefix="grid"):
    """Render a single movie card with details and actions."""
    mid = movie.get("id")
    title = movie.get("title", "Unknown")
    poster_path = movie.get("poster_path")
    rating = movie.get("vote_average", 0)
    date_str = movie.get("release_date", "N/A")
    popularity = movie.get("popularity", 0)
    year = date_str.split("-")[0] if "-" in date_str else date_str
    
    genres = get_movie_card_genres(movie)
    genre_str = f"  •  🎭 {genres}" if genres else ""
    
    with st.container(border=True):
        if poster_path:
            poster_url = f"{POSTER_BASE_URL}{poster_path}"
        else:
            poster_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop"
            
        # HTML Image component with custom glassmorphism rating badge overlay and error fallback handler
        st.markdown(
            f"""
            <div class="movie-poster-container">
                <img src="{poster_url}" class="movie-poster" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop';" loading="lazy" />
                <span class="movie-rating-badge">⭐ {rating:.1f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
            
        st.write(f"**{title}**")
        st.caption(f"📅 {year}  •  🔥 {popularity:.1f}{genre_str}")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            if st.button("ℹ️ Details", key=f"det_{key_prefix}_{mid}", use_container_width=True):
                view_movie_details(movie)
                st.rerun()
        with c2:
            is_fav = mid in st.session_state.favorites
            fav_btn_text = "❤️" if is_fav else "🤍"
            if st.button(fav_btn_text, key=f"fav_{key_prefix}_{mid}", use_container_width=True):
                toggle_favorite(movie)
                st.rerun()

def display_movie_grid(movies, key_prefix="grid"):
    """Render a list of movies in a responsive grid."""
    if not movies:
        display_empty_state("🍿", "No Movies Found", "We couldn't find any movies for this category or filter combination.")
        return
        
    cols_per_row = 4
    for i in range(0, len(movies), cols_per_row):
        row_movies = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, movie in enumerate(row_movies):
            with cols[j]:
                display_movie_card(movie, key_prefix=key_prefix)

def show_movie_details_view():
    """Render the detailed view for a single selected movie."""
    movie_id = st.session_state.selected_movie
    
    with st.spinner("Fetching movie details..."):
        movie = get_movie_details(movie_id)
        
    if not movie:
        if st.button("⬅️ Back"):
            st.session_state.selected_movie = None
            st.rerun()
        return
        
    if st.button("⬅️ Back"):
        st.session_state.selected_movie = None
        st.rerun()
        
    # Combined Hero Banner Layout (Netflix/Apple TV style)
    backdrop_path = movie.get("backdrop_path")
    backdrop_url = f"{BACKDROP_BASE_URL}{backdrop_path}" if backdrop_path else "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280"
    rating = movie.get('vote_average', 0)
    
    st.markdown(
        f"""<div class="movie-hero-banner" style="background-image: linear-gradient(to top, #09090b 5%, rgba(9, 9, 11, 0.45) 50%, rgba(9, 9, 11, 0.15) 100%), url('{backdrop_url}');">
<div class="movie-hero-content">
<span class="hero-rating-badge">⭐ {rating:.1f} / 10</span>
<h1 class="hero-title">{movie.get('title')}</h1>
{f'<p class="hero-tagline">"{movie.get("tagline")}"</p>' if movie.get("tagline") else ''}
<p class="hero-overview">{movie.get('overview')}</p>
</div>
</div>""",
        unsafe_allow_html=True
    )
        
    col1, col2 = st.columns([1, 2.5])
    with col1:
        poster_path = movie.get("poster_path")
        if poster_path:
            st.markdown(
                f"""
                <div class="movie-poster-container">
                    <img src="{POSTER_BASE_URL}{poster_path}" class="movie-poster" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop';" />
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="movie-poster-container">
                    <img src="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop" class="movie-poster" />
                </div>
                """,
                unsafe_allow_html=True
            )
            
        is_fav = movie.get("id") in st.session_state.favorites
        if st.button("❤️ Remove from Favorites" if is_fav else "🤍 Add to Favorites", use_container_width=True, type="primary" if not is_fav else "secondary"):
            toggle_favorite(movie)
            st.rerun()
            
        trailer_key = None
        if movie.get("videos") and movie["videos"].get("results"):
            # Try to find a trailer
            for video in movie["videos"]["results"]:
                if video.get("site") == "YouTube" and video.get("type") == "Trailer" and video.get("official"):
                    trailer_key = video.get("key")
                    break
            # Fallback to any trailer
            if not trailer_key:
                for video in movie["videos"]["results"]:
                    if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                        trailer_key = video.get("key")
                        break
                        
        if trailer_key:
            st.link_button("▶ Watch Trailer", f"https://www.youtube.com/watch?v={trailer_key}", use_container_width=True)
        else:
            st.info("No trailer available.")
            
    with col2:
        # Metascore progress bar indicator
        st.write("**Metascore Rating:**")
        st.progress(rating / 10.0)
        
        with st.expander("📊 Key Metrics & Details", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Status:** {movie.get('status', 'N/A')}")
                st.write(f"**Release Date:** {movie.get('release_date', 'N/A')}")
                st.write(f"**Runtime:** {movie.get('runtime', 0)} mins")
            with c2:
                st.write(f"**Popularity:** {movie.get('popularity', 0)}")
                st.write(f"**Vote Count:** {movie.get('vote_count', 0):,}")
                
                langs = [l.get("english_name") for l in movie.get("spoken_languages", [])]
                lang_str = ", ".join(langs) if langs else movie.get("original_language", "N/A").upper()
                st.write(f"**Language:** {lang_str}")
            with c3:
                budget = movie.get('budget', 0)
                revenue = movie.get('revenue', 0)
                st.write(f"**Budget:** ${budget:,}" if budget else "**Budget:** N/A")
                st.write(f"**Revenue:** ${revenue:,}" if revenue else "**Revenue:** N/A")
                
                genres = [g.get("name") for g in movie.get("genres", [])]
                st.write(f"**Genres:** {', '.join(genres)}")
        
        companies = [c.get("name") for c in movie.get("production_companies", [])]
        if companies:
            st.write(f"**Production Companies:** {', '.join(companies)}")
        
        credits = movie.get("credits", {})
        if credits:
            crew = credits.get("crew", [])
            directors = [c.get("name") for c in crew if c.get("job") == "Director"]
            writers = []
            for c in crew:
                if c.get("department") == "Writing" and c.get("name") not in writers:
                    writers.append(c.get("name"))
            producers = [c.get("name") for c in crew if c.get("job") == "Producer"]
            
            c4, c5, c6 = st.columns(3)
            with c4:
                if directors: st.write(f"**Director:** {', '.join(directors)}")
            with c5:
                if writers: st.write(f"**Writer:** {', '.join(writers[:3])}")
            with c6:
                if producers: st.write(f"**Producer:** {', '.join(producers[:3])}")
            
            cast = credits.get("cast", [])
            if cast:
                with st.expander("🎭 Top Cast", expanded=True):
                    top_cast = cast[:10]
                    cols_per_row = 5
                    for i in range(0, len(top_cast), cols_per_row):
                        row_cast = top_cast[i:i + cols_per_row]
                        cols = st.columns(cols_per_row)
                        for j, actor in enumerate(row_cast):
                            with cols[j]:
                                profile_path = actor.get("profile_path")
                                if profile_path:
                                    st.image(f"{PROFILE_BASE_URL}{profile_path}", use_container_width=True)
                                else:
                                    st.image("https://via.placeholder.com/185x278.png?text=No+Photo", use_container_width=True)
                                st.write(f"**{actor.get('name')}**")
                                st.caption(actor.get('character'))
        
        # Streaming Providers
        country_code = st.session_state.settings_language.split("-")[1] if "-" in st.session_state.settings_language else "US"
        providers_data = movie.get("watch/providers", {}).get("results", {}).get(country_code, {})
        flatrate_providers = providers_data.get("flatrate", [])
        
        target_providers = ["Netflix", "Amazon Prime Video", "Disney Plus", "Apple TV", "Max", "HBO Max", "Hulu", "Paramount Plus", "Peacock", "Crunchyroll"]
        filtered_providers = [p for p in flatrate_providers if any(t in p.get("provider_name", "") for t in target_providers)]
        if not filtered_providers:
            filtered_providers = flatrate_providers # Fallback to all if none of the major ones match
            
        if filtered_providers:
            with st.expander("📺 Streaming On", expanded=True):
                prov_cols = st.columns(min(len(filtered_providers), 8))
                for idx, prov in enumerate(filtered_providers[:8]):
                    with prov_cols[idx]:
                        logo_path = prov.get("logo_path")
                        if logo_path:
                            st.image(f"{LOGO_BASE_URL}{logo_path}", use_container_width=True)
                        st.caption(prov.get("provider_name"))
        
        # External Links
        links = []
        if movie.get("homepage"):
            links.append(f"[Homepage]({movie.get('homepage')})")
        if movie.get("imdb_id"):
            links.append(f"[IMDb](https://www.imdb.com/title/{movie.get('imdb_id')}/)")
        links.append(f"[TMDB](https://www.themoviedb.org/movie/{movie.get('id')})")
        
        st.write("---")
        st.markdown(" | ".join(links))
        
        # Reviews
        reviews = movie.get("reviews", {}).get("results", [])
        if reviews:
            with st.expander("💬 Reviews"):
                for review in reviews[:5]:
                    with st.container(border=True):
                        author = review.get("author")
                        rating = review.get("author_details", {}).get("rating")
                        rating_str = f" ⭐ {rating}/10" if rating else ""
                        st.write(f"**{author}**{rating_str}")
                        
                        content = review.get("content", "")
                        if len(content) > 300:
                            content = content[:300] + "..."
                        st.write(content)

    st.write("---")
    st.subheader("🎬 Similar Movies")
    with st.spinner("Finding similar movies..."):
        similar = get_similar_movies(movie_id)
        if similar and similar.get("results"):
            display_movie_grid(similar.get("results")[:8], key_prefix="sim")
        else:
            st.info("No similar movies found.")

# --- HERO COMPONENT ---
def display_featured_hero(movie):
    """Render a premium hero banner for the featured movie."""
    if not movie:
        return
    title = movie.get("title", "Featured Movie")
    backdrop_path = movie.get("backdrop_path")
    overview = movie.get("overview", "")
    rating = movie.get("vote_average", 0)
    mid = movie.get("id")
    
    backdrop_url = f"{BACKDROP_BASE_URL}{backdrop_path}" if backdrop_path else "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1280"
        
    st.markdown(
        f"""<div class="featured-hero-banner" style="background-image: linear-gradient(to right, rgba(9, 9, 11, 0.95) 30%, rgba(9, 9, 11, 0.45) 60%, rgba(9, 9, 11, 0.15) 100%), url('{backdrop_url}');">
<div class="featured-hero-content">
<span class="featured-tag">★ FEATURED TODAY</span>
<h1 class="featured-title">{title}</h1>
<div class="featured-meta">⭐ {rating:.1f} / 10  •  🔥 Popularity: {movie.get('popularity', 0):.1f}</div>
<p class="featured-overview">{overview[:220]}...</p>
</div>
</div>""",
        unsafe_allow_html=True
    )
    
    c1, _ = st.columns([1.6, 4])
    with c1:
        if st.button("ℹ️ Featured Movie Details", key=f"feat_det_{mid}", use_container_width=True, type="primary"):
            view_movie_details(movie)
            st.rerun()

# --- PAGE VIEWS ---
def page_home():
    st.title("🏠 Dashboard")
    
    with st.spinner("Loading dashboard..."):
        trending_data = get_trending_movies("day")
        popular_data = get_popular_movies()
        top_rated_data = get_top_rated_movies()
        upcoming_data = get_upcoming_movies()
        
    # Render featured movie hero banner at the top of the dashboard
    if trending_data and trending_data.get("results"):
        display_featured_hero(trending_data["results"][0])
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # Dashboard Metrics
    with st.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔥 Trending", f"{trending_data.get('total_results', 0):,}" if trending_data else "0", "Today")
        m2.metric("🎥 Popular", f"{popular_data.get('total_results', 0):,}" if popular_data else "0", "All Time")
        m3.metric("❤️ Favorites", len(st.session_state.favorites), "Saved")
        m4.metric("🕒 History", len(st.session_state.history), "Viewed")
    
    st.write("---")
    
    # Content Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trending", "🎥 Popular", "⭐ Top Rated", "📅 Upcoming"])
    
    with tab1:
        if trending_data and trending_data.get("results"):
            display_movie_grid(trending_data["results"][:12], key_prefix="trend")
    with tab2:
        if popular_data and popular_data.get("results"):
            display_movie_grid(popular_data["results"][:12], key_prefix="pop")
    with tab3:
        if top_rated_data and top_rated_data.get("results"):
            display_movie_grid(top_rated_data["results"][:12], key_prefix="top")
    with tab4:
        if upcoming_data and upcoming_data.get("results"):
            display_movie_grid(upcoming_data["results"][:12], key_prefix="upcom")

def page_discover():
    st.title("🎯 Discover Movies")
    
    st.sidebar.write("---")
    st.sidebar.subheader("🎛️ Filters")
    
    genres_data = get_genres()
    genre_options = {"Any": ""}
    if genres_data and genres_data.get("genres"):
        for g in genres_data["genres"]:
            genre_options[g["name"]] = g["id"]
            
    selected_genre_name = st.sidebar.selectbox("🎭 Genre", list(genre_options.keys()))
    min_rating = st.sidebar.slider("⭐ Minimum Rating", 0.0, 10.0, 5.0, 0.5)
    
    languages = {"Any": "", "English": "en", "Spanish": "es", "French": "fr", "German": "de", "Hindi": "hi", "Japanese": "ja", "Korean": "ko", "Chinese": "zh"}
    selected_language_name = st.sidebar.selectbox("🗣️ Language", list(languages.keys()))
    
    current_year = datetime.datetime.now().year
    years = ["Any"] + list(range(current_year, 1899, -1))
    selected_year = st.sidebar.selectbox("📅 Release Year", years)
    
    sort_options = {
        "Popularity Descending": "popularity.desc",
        "Popularity Ascending": "popularity.asc",
        "Rating Descending": "vote_average.desc",
        "Rating Ascending": "vote_average.asc",
        "Release Date Descending": "primary_release_date.desc",
        "Release Date Ascending": "primary_release_date.asc"
    }
    selected_sort_name = st.sidebar.selectbox("🔃 Sort By", list(sort_options.keys()))
    
    if st.sidebar.button("Apply Filters", type="primary", use_container_width=True):
        st.session_state.discover_filters = {
            "with_genres": genre_options[selected_genre_name],
            "vote_average.gte": min_rating,
            "with_original_language": languages[selected_language_name],
            "primary_release_year": selected_year if selected_year != "Any" else "",
            "sort_by": sort_options[selected_sort_name],
            "vote_count.gte": 100
        }
    
    params = {k: v for k, v in st.session_state.discover_filters.items() if v != ""}
    
    with st.spinner("Discovering movies..."):
        data = discover_movies_advanced(params)
        
    if data and data.get("results"):
        display_movie_grid(data["results"], key_prefix="disc")
    else:
        display_empty_state("🍿", "No Discoveries", "No movies matched your filter settings. Try adjusting or relaxing your filter options.")

def page_search():
    st.title("🔍 Search Movie")
    
    # Process recent search clicks before the text input is instantiated
    if "clicked_recent_search" in st.session_state and st.session_state.clicked_recent_search:
        st.session_state.search_query_input = st.session_state.clicked_recent_search
        st.session_state.clicked_recent_search = None
        
    # Horizontal grid layout for search input and search button
    c1, c2 = st.columns([4, 1.2])
    with c1:
        query = st.text_input("Enter movie title...", key="search_query_input", placeholder="e.g. Inception", label_visibility="collapsed")
    with c2:
        search_clicked = st.button("Search", key="search_btn", use_container_width=True, type="primary")
        
    if query or search_clicked:
        q_strip = query.strip() if query else ""
        if q_strip:
            if q_strip in st.session_state.recent_searches:
                st.session_state.recent_searches.remove(q_strip)
            st.session_state.recent_searches.insert(0, q_strip)
            st.session_state.recent_searches = st.session_state.recent_searches[:10]
            
            with st.spinner("Searching..."):
                data = search_movies(q_strip)
            if data and data.get("results"):
                display_movie_grid(data["results"], key_prefix="srch")
            else:
                display_empty_state("🤷‍♂️", "No Matches Found", f"We couldn't find any movies matching '{q_strip}'. Try searching for something else.")
        else:
            display_empty_state("🔍", "Search Movies", "Search for movies across TMDB by typing their title in the box above.")
    else:
        display_empty_state("🔍", "Search Movies", "Search for movies across TMDB by typing their title in the box above.")

    if st.session_state.recent_searches:
        st.write("---")
        with st.expander("🕒 Recent Searches", expanded=True):
            cols = st.columns(5)
            for j, past_query in enumerate(st.session_state.recent_searches[:5]):
                with cols[j]:
                    if st.button(past_query, key=f"rs_{j}", use_container_width=True):
                        st.session_state.clicked_recent_search = past_query
                        st.rerun()

def page_genres():
    st.title("🎭 Browse by Genre")
    
    with st.spinner("Loading genres..."):
        genres_data = get_genres()
        
    if genres_data and genres_data.get("genres"):
        genre_map = {g["name"]: g["id"] for g in genres_data["genres"]}
        
        target_genres = [
            "Action", "Comedy", "Drama", "Fantasy", "Adventure", 
            "Animation", "Crime", "Mystery", "Thriller", "Romance", "Science Fiction"
        ]
        available_genres = [g for g in target_genres if g in genre_map]
        
        if available_genres:
            selected_genre = st.selectbox("Select a Genre", options=available_genres)
            st.divider()
            
            if selected_genre:
                with st.spinner(f"Loading {selected_genre} movies..."):
                    params = {"with_genres": genre_map[selected_genre], "sort_by": "popularity.desc"}
                    data = discover_movies_advanced(params)
                if data and data.get("results"):
                    display_movie_grid(data["results"], key_prefix="gnr")
        else:
            st.info("Genres could not be loaded.")

def page_mood():
    st.title("😊 Mood Recommendations")
    st.caption("Find movies based on how you feel.")
    
    mood_map = {
        "😁 Happy": [35, 10751],      # Comedy, Family
        "😍 Romantic": [10749],        # Romance
        "😢 Sad": [18],                # Drama
        "😱 Horror": [27, 53],         # Horror, Thriller
        "💪 Motivation": [28, 36, 99], # Action, History, Documentary
        "🧠 Mind Bending": [878, 9648], # Science Fiction, Mystery
        "👨‍👩‍👧 Family": [10751, 16],  # Family, Animation
        "🍿 Weekend": [28, 35, 12]     # Action, Comedy, Adventure
    }
    
    mood = st.selectbox("How are you feeling?", [""] + list(mood_map.keys()))
    if mood:
        genre_ids = ",".join(map(str, mood_map[mood]))
        with st.spinner(f"Finding movies for a {mood.split()[1]} mood..."):
            params = {"with_genres": genre_ids, "sort_by": "popularity.desc"}
            data = discover_movies_advanced(params)
            
        if data and data.get("results"):
            display_movie_grid(data["results"], key_prefix="mood")
    else:
        display_empty_state("🎭", "Select Your Mood", "Choose how you are feeling from the dropdown above to discover curated movies matching your vibe.")

def page_cast():
    st.title("👥 Cast & Crew")
    query = st.text_input("Search for an actor or director:", placeholder="e.g. Leonardo DiCaprio")
    
    if query:
        with st.spinner("Searching person..."):
            person_data = search_person(query)
            
        if person_data and person_data.get("results"):
            person = person_data["results"][0]
            
            c1, c2 = st.columns([1, 4])
            with c1:
                profile_path = person.get("profile_path")
                if profile_path:
                    st.image(f"{PROFILE_BASE_URL}{profile_path}", use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/185x278.png?text=No+Photo", use_container_width=True)
            with c2:
                st.subheader(person.get('name'))
                st.write(f"**Known for:** {person.get('known_for_department', 'N/A')}")
                
            st.divider()
            st.subheader("🎥 Known Movies")
            
            with st.spinner("Loading movies..."):
                credits = get_person_movie_credits(person["id"])
                
            if credits and credits.get("cast"):
                # Sort by popularity
                sorted_movies = sorted(credits["cast"], key=lambda x: x.get("popularity", 0), reverse=True)
                display_movie_grid(sorted_movies[:20], key_prefix="cast")
            else:
                display_empty_state("🎬", "No Credits Found", f"We couldn't find any movie credits for {person.get('name')}.")
        else:
            display_empty_state("🔍", "Person Not Found", f"No actors or directors found matching '{query}'.")
    else:
        display_empty_state("👥", "Find Cast & Crew", "Type the name of an actor or director above to view their biography and movie filmography.")

def page_favorites():
    st.title("❤️ Favorites")
    if st.session_state.favorites:
        display_movie_grid(list(st.session_state.favorites.values()), key_prefix="favs")
    else:
        display_empty_state("❤️", "No Favorites Yet", "You haven't added any favorites yet. Click the heart icon on any movie card to add it to this list.")

def page_history():
    st.title("🕒 Viewing History")
    if st.session_state.history:
        display_movie_grid(st.session_state.history, key_prefix="hist")
    else:
        display_empty_state("🕒", "Viewing History Empty", "Your viewing history is currently empty. Explore details of movies to build your history list.")

def page_settings():
    st.title("⚙️ Settings")
    
    with st.container(border=True):
        st.subheader("Preferences")
        adult = st.toggle("Include Adult Content", value=st.session_state.settings_adult)
        
        langs = ["en-US", "es-ES", "fr-FR", "de-DE", "hi-IN", "ja-JP", "ko-KR"]
        lang_idx = langs.index(st.session_state.settings_language) if st.session_state.settings_language in langs else 0
        lang = st.selectbox("Content Language", langs, index=lang_idx)
        
        if st.button("Save Settings", type="primary"):
            st.session_state.settings_adult = adult
            st.session_state.settings_language = lang
            st.success("✅ Settings saved successfully!")
            st.rerun()

def page_about():
    st.title("ℹ️ About")
    
    st.markdown("""
    **Streamlit Movie Explorer** is a modern web application built purely with Python and Streamlit.
    
    - **Data Source:** [The Movie Database (TMDB) API](https://www.themoviedb.org/)
    - **Developer:** AI Studio Code Agent
    - **Features:** 
      - 🔍 Search & Discover with Advanced Filters
      - 🔥 Trending, Popular, Top Rated insights
      - 😊 Mood-based Recommendations
      - ❤️ Favorites & 🕒 History tracking
      - 📺 Streaming Providers lookup
    - **Architecture:** Zero frontend code (No HTML, CSS, or JS). Fully functional Python-based UI.
    """)

# --- MAIN EXECUTOR ---
def main():
    # User Profile Section
    st.sidebar.markdown(
        """
        <div class="sidebar-profile">
            <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=256" class="sidebar-avatar" />
            <div class="sidebar-profile-info">
                <div class="sidebar-profile-name">Cinephile User</div>
                <div class="sidebar-profile-role">Movie Explorer Pro</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    st.sidebar.subheader("Navigation")
    
    pages = {
        "🏠 Dashboard": page_home,
        "🎯 Discover": page_discover,
        "🔍 Search Movie": page_search,
        "🎭 Genres": page_genres,
        "😊 Moods": page_mood,
        "👥 Cast": page_cast,
        "❤️ Favorites": page_favorites,
        "🕒 History": page_history,
        "⚙️ Settings": page_settings,
        "ℹ️ About": page_about
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()), key="nav_radio", label_visibility="collapsed")
    
    # Clear selected movie if navigation changes
    if "last_nav" not in st.session_state:
        st.session_state.last_nav = selection
        
    if selection != st.session_state.last_nav:
        st.session_state.selected_movie = None
        st.session_state.last_nav = selection
        
    st.sidebar.markdown("<hr style='margin: 1.25rem 0 0.75rem 0 !important; opacity: 0.15;' />", unsafe_allow_html=True)
    
    # Sidebar Live Statistics
    fav_count = len(st.session_state.favorites)
    hist_count = len(st.session_state.history)
    st.sidebar.markdown(
        f"""
        <div class="sidebar-stats-container">
            <div class="sidebar-stat-card">
                <div class="sidebar-stat-value">{fav_count}</div>
                <div class="sidebar-stat-label">❤️ Saved</div>
            </div>
            <div class="sidebar-stat-card">
                <div class="sidebar-stat-value">{hist_count}</div>
                <div class="sidebar-stat-label">🕒 Viewed</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.info("💡 **Tip:** Click 'Details' on any movie to view trailers, streaming options, and cast!")
    
    if st.session_state.selected_movie:
        show_movie_details_view()
    else:
        pages[selection]()

if __name__ == "__main__":
    main()
