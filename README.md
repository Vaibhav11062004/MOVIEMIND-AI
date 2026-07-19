# 🍿 MovieMind AI — Premium Movie Explorer

A gorgeous, feature-rich cinematic movie discovery dashboard built with **Streamlit** and powered by the **TMDB API**. 

Drawing design inspiration from **Netflix**, **IMDb**, and **Apple TV**, this dashboard features an elegant dark glassmorphism user interface, dynamic recommendations, provider availability maps, and seamless movie search.

---

## ✨ Features

*   **🎬 Cinematic Billboard Hero:** Wide featured backdrop banners at the top of the dashboard displaying trending titles, detailed ratings, and overview summaries.
*   **💎 Premium Glassmorphism UI:** Frosted-glass navigation tabs in the sidebar, glowing indicators, responsive grid cards, and smooth hover micro-animations.
*   **🔍 State-Managed Recent Searches:** Interactive, clickable recent searches history that re-populates search text fields safely without crashes.
*   **🛠️ Fault-Tolerant Fallbacks:** Missing or broken movie poster URLs automatically fall back to high-resolution cinema-theater graphic displays.
*   **⚡ ISP Connection Bypass:** Built-in routing redirects TMDB requests to `api.tmdb.org` to bypass region-specific DNS and deep packet inspection blocks.
*   **📺 Watch Providers & Trailers:** Real-time lookup of regional streaming providers (Netflix, Prime, Apple TV, etc.) and direct Youtube video trailers.

---

## 🛠️ Tech Stack

*   **Frontend & Logic:** [Python](https://www.python.org/) & [Streamlit](https://streamlit.io/)
*   **Styles & Overrides:** Vanilla CSS (`assets/style.css`)
*   **API Connection:** [The Movie Database (TMDB) API v3](https://developer.themoviedb.org/docs)
*   **Environment Manager:** Dotenv (`python-dotenv`)

---

## 🚀 Getting Started

Follow these step-by-step instructions to run the application locally on Windows:

### 1. Prerequisites
Ensure you have **Python 3.10+** installed. You can check your version in PowerShell:
```powershell
python --version
```

### 2. Configure Environment Variables
1. Sign up for a free account at [themoviedb.org](https://www.themoviedb.org/).
2. Navigate to your Account **Settings** > **API** and request a developer API Key.
3. In the root directory of this project, create a file named `.env`:
    ```env
    TMDB_API_KEY="your_actual_tmdb_api_key_here"
    ```

### 3. Create a Virtual Environment & Run
In your project directory, execute the following commands in PowerShell:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the Streamlit application
streamlit run app.py
```

The application will launch and open in your default browser at `http://localhost:8501`.

---

## 📁 Project Structure

```text
├── assets/
│   └── style.css            # Premium dark glassmorphism CSS overrides
├── app.py                   # Core Streamlit app containing UI and pages logic
├── .env                     # Private environment configurations (API key)
├── .gitignore               # Excludes virtual environments (venv/) & credentials
├── requirements.txt         # Required Python packages
├── README.md                # Project documentation (this file)
└── test_script.py           # Quick CLI database query verification tool
```

---

## 🛡️ License

This project is open-source and available under the [MIT License](LICENSE).
