import streamlit as st
import pandas as pd
import numpy as np
import requests

#---------------------------------------------------------------------------------------
#API Keys
OMDB_KEY = "cb5009c1"
WATCHMODE_KEY = "vpjbwCNB0iIQFveYzpjZgL8QBP0GIuHGPLob9sQl"

#---------------------------------------------------------------------------------------
#Initialize session state
if "results" not in st.session_state:
    st.session_state.results = []

if "selected_imdb" not in st.session_state:
    st.session_state.selected_imdb = []

#---------------------------------------------------------------------------------------
#Page set-up
info_box = st.empty()
st.set_page_config(layout="wide",
                   page_title="Movie Night",
                   page_icon="🎥",
                   initial_sidebar_state="expanded",)

st.title("🎬 Movie Night 🍿")
st.header("Can't decide what to watch? Search for movies and shows here, or let us pick a random one!")

#---------------------------------------------------------------------------------------
#Sidebar
st.sidebar.text("Enter part of the movie or show title in the search box."
                " Then, select the one you want from the results in the drop down menu.")
movie_search = st.sidebar.text_input("Enter Movie or Show Title:")
type_select = st.sidebar.radio("Select Media Type",
                               ["Movie", "Series"])
stream_check = st.sidebar.checkbox("Check for streaming availability")

if stream_check:
    select_region = st.sidebar.selectbox("Select Region", [
                                         "United States",
                                         "Canada",
                                         "Great Britain"])
    if select_region == "United States":
        stream_region = str ("US")
    if select_region == "Canada":
        stream_region = str ("CA")
    if select_region == "Great Britain":
        stream_region = str ("GB")

search_button = st.sidebar.button("Search")
st.sidebar.divider()
random_button = st.sidebar.button("Random Movie Suggestion")

#---------------------------------------------------------------------------------------
#Random movie search
info_box = st.sidebar.empty()
if random_button:
    info_box.info(f"Searching for random movie!")
    random_url = "https://random-movie-api2.p.rapidapi.com/api/random-movie"
    random_headers = {
        "x-rapidapi-key": "68b868734bmsh3c0c2e03f788434p161689jsn441b7f5ba733",
	    "x-rapidapi-host": "random-movie-api2.p.rapidapi.com"
    }
    random_response = requests.get(random_url, headers = random_headers).json()
    random_title = random_response.get("movie", None)

    info_box.empty()

    if random_title:
        st.sidebar.text(f"Try: {random_title}")

    else:
        st.sidebar.warning("No movie title found.")

#---------------------------------------------------------------------------------------
#Text search
info_box = st.empty()
if search_button:
    if not movie_search:
        st.error("Please enter a movie or show title.")
        st.session_state.results = []
    else:
        if type_select == "Movie":
            info_box.info(f"Searching for movie: {movie_search}")
        if type_select == "Series":
            info_box.info(f"Searching for series: {movie_search}")

        #OMBd API: Movie and show search results
        search_url = f"https://www.omdbapi.com/?apikey={OMDB_KEY}&s={movie_search}&type={type_select}"
        search_data = requests.get(search_url).json()

        info_box.empty()

        if search_data.get("Response") == "False":

            st.error("No results found, try another title.")
            st.session_state.results = []
        else:
            st.success("Search successful!")
            st.session_state.results = search_data.get("Search", [])
            #Reset selection
            st.session_state.selected_imdb = None

#---------------------------------------------------------------------------------------
#Dropdown list of search results
if st.session_state.results:
    titles_list = [f"{m['Title']} ({m['Year']})" for m in st.session_state.results]

    #User chooses from the dropdown list
    selected_title = st.selectbox("Choose your movie or show", titles_list)

    #IMDb ID value for selected title
    selected_index = titles_list.index(selected_title)
    imdb_id = st.session_state.results[selected_index]["imdbID"]

    st.session_state.selected_imdb = imdb_id

#---------------------------------------------------------------------------------------
#Details for selected title
if st.session_state.selected_imdb:
    imdb_id = st.session_state.selected_imdb

    #Full details
    detail_url = f"https://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_KEY}"
    detail_data = requests.get(detail_url).json()

    if detail_data.get("Response") == "False":
        st.error("Error loading movie/show details, try again later.")
    else:
        st.success("Details loaded successfully!")

        #Layout design
        col1, col2 = st.columns([1, 2])
        with col1:
            poster_url = detail_data.get("Poster", "")

            if poster_url and poster_url != "N/A":
                st.image(poster_url)
            else:
                st.warning("📷 No poster available.")

        with col2:
            st.header(detail_data["Title"])
            st.write(f"**Year:** {detail_data['Year']}")
            st.write(f"**Genre:** {detail_data['Genre']}")
            st.write(f"**Runtime:** {detail_data['Runtime']}")
            st.write(f"**Director:** {detail_data['Director']}")
            st.write(f"**Plot:** {detail_data['Plot']}")

        # ---------------------------------------------------------------------------------------
        #Movie Trailer Integration from API KinoCheck
        with st.expander("🎬 Watch the Trailer Here"):

            try:
                trailer_url = f"https://api.kinocheck.com/movies?imdb_id={imdb_id}&types=trailer&language=en"

                response = requests.get(trailer_url)

                if response.status_code != 200:
                    st.warning("No trailer information available at this time, try again later.")
                else:
                    data = response.json()

                    #Extract and combine trailers to one list
                    main_trailer = data.get("trailer")
                    videos = data.get("videos", [])
                    all_trailers = []

                    if main_trailer and main_trailer.get("youtube_video_id"):
                        all_trailers.append({
                            "title": main_trailer["title"],
                            "youtube_id": main_trailer["youtube_video_id"],
                            "views": main_trailer.get("views", 0)
                        })

                    for v in videos:
                        if v.get("youtube_video_id"):
                            all_trailers.append({
                                "title": v["title"],
                                "youtube_id": v["youtube_video_id"],
                                "views": v.get("views", 0)
                            })

                    #Remove duplicate trailers and convert back to list
                    unique = {}
                    for t in all_trailers:
                        if t["title"] not in unique:
                            unique[t["title"]] = t

                    all_trailers = list(unique.values())

                    #If no trailers found
                    if len(all_trailers) == 0:
                        st.warning("No trailers found for this title from our provider.")
                    else:
                        #Sort by number of views
                        all_trailers = sorted(all_trailers, key=lambda x: x["views"], reverse=True)

                        #Show as dropdown menu
                        trailer_titles = [t["title"] for t in all_trailers]

                        selected_title = st.selectbox("Select Trailer:", trailer_titles)

                        selected_trailer = next(t for t in all_trailers if t["title"] == selected_title)

                        youtube_id = selected_trailer["youtube_id"]

                        st.video(f"https://www.youtube.com/watch?v={youtube_id}")

            except:
                st.error(f"Error loading trailer")

        # ---------------------------------------------------------------------------------------
        #Ratings Table and Bar Graph
        if "Ratings" in detail_data:
            with st.expander("📊 Ratings Information"):
                ratings_df = pd.DataFrame(detail_data["Ratings"])
                st.dataframe(ratings_df)

                #Bar graph setup
                try:
                    chart_df = ratings_df.copy()

                    #Convert ratings to be the same format for bar graph
                    def convert_rating(val):
                        if isinstance(val, str):
                            val = val.strip()

                            #Percentages
                            if val.endswith("%"):
                                return float(val[:-1])

                            #Fractions
                            if "/" in val:
                                num, denom = val.split("/")
                                num, denom = float(num), float(denom)
                                return (num / denom) * 100

                        return None

                    chart_df["Numeric"] = (chart_df["Value"].apply(convert_rating))

                    chart_df = chart_df.set_index("Source")

                    st.bar_chart(chart_df["Numeric"],y_label="Rating Value", x_label="Rating Source")
                except:
                    st.warning("No ratings were found for this title.")

        # ---------------------------------------------------------------------------------------
        #Streaming services availability information from Watchmode API
        if stream_check:
            with st.expander("📺 Streaming availability"):

                #Convert IMDb ID to Watchmode ID
                watchmode_url = (f"https://api.watchmode.com/v1/search/?apiKey={WATCHMODE_KEY}"
                                 f"&search_field=imdb_id&search_value={imdb_id}")
                watchmode_search = requests.get(watchmode_url).json()

                if watchmode_search.get("title_results"):
                    watchmode_id = watchmode_search["title_results"][0]["id"]

                    #Obtain streaming sources
                    source_url = (f"https://api.watchmode.com/v1/title/{watchmode_id}/sources/?apiKey={WATCHMODE_KEY}")
                    sources = requests.get(source_url).json()

                    #Obtain providers list for logos
                    providers_url = (f"https://api.watchmode.com/v1/sources/?apiKey={WATCHMODE_KEY}")
                    providers = requests.get(providers_url).json()
                    providers_df = pd.DataFrame(providers)[["id", "name", "logo_100px"]]

                    if sources:
                        df = pd.DataFrame(sources)
                        df = df[df["region"] == stream_region]
                        df = df[["source_id", "type", "web_url"]]

                        #Merge streaming sources with providers for logos
                        df = df.merge(providers_df, left_on="source_id", right_on="id", how="left")

                        if not df.empty:
                            #Remove duplicate streaming services
                            df = df.drop_duplicates(subset="name")

                            for _, row in df.iterrows():
                                col1, col2, col3 = st.columns([1 ,2, 2])

                                with col1:
                                    if row.get("logo_100px"):
                                        st.image(row["logo_100px"], width=60)
                                    else:
                                        st.write("No logo found")

                                with col2:
                                    st.write(f"**{row['name']}**")

                                with col3:
                                    if row.get("web_url"):
                                        st.markdown(f"[Watch Here]({row['web_url']}")
                                    else:
                                        st.write("N/A")
                    else:
                        st.warning("No streaming options found for this title.")
                else:
                    st.warning("No streaming options found for this title.")