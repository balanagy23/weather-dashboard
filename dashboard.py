import streamlit as st
import requests
import plotly.express as px
import datetime
import pandas as pd

API_KEY = st.secrets["openweather"]["api_key"]

BEAUFORT_SCALE = [
    (0, 0.3, "Teljes szélcsend"),
    (0.3, 1.5, "Gyenge"),
    (1.6, 3.3, "Gyenge"),
    (3.4, 5.5, "Mérsékelt"),
    (5.6, 7.9, "Mérsékelt"),
    (8.0, 10.7, "Élénk"),
    (10.8, 13.8, "Erős"),
    (13.9, 17.1, "Erős"),
    (17.2, 20.7, "Viharos"),
    (20.8, 24.4, "Viharos"),
    (24.5, 28.4, "Erősen viharos"),
    (28.5, 32.6, "Szélviharos"),
    (32.7, float("inf"), "Szélviharos")
]

CLOUDINESS_MAP = {
    "clear sky": "Derült égbolt",
    "few clouds": "Gyengén felhős",
    "scattered clouds": "Közepesen felhős",
    "broken clouds": "Erősen felhős",
    "overcast clouds": "Borult"
}

DIRECTIONS = ["É", "ÉK", "K", "DK", "D", "DNY", "NY", "ÉNY"]

def get_beaufort_scale(speed):
    for lower, upper, category in BEAUFORT_SCALE:
        if lower <= speed <= upper:
            return category
    return "Ismeretlen"

def get_wind_direction(degrees):
    index = round(degrees / 45) % 8
    return f"{degrees}° ({DIRECTIONS[index]})"

@st.cache_data(ttl=86400)
def get_weather_data(city: str, endpoint: str) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/{endpoint}?q={city}&appid={API_KEY}&units=metric'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Hiba történt az OpenWeather API elérésekor: {e}")
        return {}

st.set_page_config(page_title="Weather Dashboard", layout="wide")
st.title("Enapló - Weather Map & Data Visualization App")

city = st.text_input("Város neve:", "Budapest").capitalize()
try:
    # Jelenlegi időjárás és előrejelzés lekérése
    current_weather = get_weather_data(city, "weather")
    forecast = get_weather_data(city, "forecast")
    
    wind_speed = current_weather["wind"]["speed"]
    beaufort_category = get_beaufort_scale(wind_speed)
    cloudiness = CLOUDINESS_MAP.get(current_weather["weather"][0]["description"], "Ismeretlen")
    wind_direction = get_wind_direction(current_weather["wind"]["deg"])
    
    # Jelenlegi időjárás mutatók
    st.subheader(f"Jelenlegi időjárás {city} városban")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hőmérséklet (°C)", current_weather["main"]["temp"])
    with col2:
        st.metric("Páratartalom (%)", current_weather["main"]["humidity"])
    with col3:
        st.metric("Szélsebesség (m/s)", wind_speed)
    
    # Egyéb időjárási adatok
    st.subheader("További időjárási adatok")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Légnyomás (hPa)", current_weather["main"]["pressure"])
    with col5:
        st.metric("Szélirány", wind_direction)
    with col6:
        st.metric("Égkép", cloudiness)
    
    # Térkép megjelenítés
    lat = current_weather["coord"]["lat"]
    lon = current_weather["coord"]["lon"]
    city_location = pd.DataFrame({'latitude': [lat], 'longitude': [lon]})
    st.subheader(f"Időjárási térkép {city} városban")
    st.map(city_location)
    
    # Előrejelzési adatok feldolgozása
    df_forecast = pd.DataFrame(forecast["list"])
    df_forecast["Dátum"] = df_forecast["dt"].apply(lambda x: datetime.datetime.fromtimestamp(x))
    df_forecast["Óra"] = df_forecast["Dátum"].dt.hour
    
    # Délelőtti és délutáni hőmérséklet számítása
    df_forecast["Délelőtti hőmérséklet"] = df_forecast[df_forecast["Óra"].between(6, 12)]["main"].apply(lambda x: x["temp"]).mean()
    df_forecast["Délutáni hőmérséklet"] = df_forecast[df_forecast["Óra"].between(12, 18)]["main"].apply(lambda x: x["temp"]).mean()
    
    st.subheader(f"Hőmérsékleti átlagok {city} városban")
    col7, col8 = st.columns(2)
    with col7:
        st.metric("Délelőtti átlaghőmérséklet (°C)", df_forecast["Délelőtti hőmérséklet"].iloc[0])
    with col8:
        st.metric("Délutáni átlaghőmérséklet (°C)", df_forecast["Délutáni hőmérséklet"].iloc[0])
    
except requests.exceptions.RequestException as e:
    st.error(f"Hiba történt az adatok lekérésekor: {e}")
