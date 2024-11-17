import panel as pn
from db_netflixapi import db_NetflixAPI


pn.extension()

# Initialize API pulling from database
api = db_NetflixAPI()

# Widget Declarations

# Autocomplete Input for movie titles
autocomplete = pn.widgets.AutocompleteInput(
    name="Media Title",
    value='',
    placeholder='Type media title...',
    options=list(api.data['title'].unique()) 
)

# Dropdown for selecting release year
years = pn.widgets.Select(name="Year", options=api.get_years(), value=2008)

# Slider for controlling the minimum rating
min_rating = pn.widgets.FloatSlider(name="Min Rating", start=0.0, end=10.0, step=0.1, value=5.0)

# Checkboxes for filtering by type
only_movies = pn.widgets.Checkbox(name='Movies', value=True)
only_tv = pn.widgets.Checkbox(name='TV Shows', value=True)

# Multi-Select for genres (plotting specific)
genre_selector_plot = pn.widgets.MultiSelect(
    name='Show Media with Specific Genres',
    options=api.get_unique_genres(),
    value=[],
    height=200
)

# Plotting Widgets for Sankey Diagram
sankey_width = pn.widgets.IntSlider(name="Sankey Width", start=250, end=2000, step=250, value=1500)
sankey_height = pn.widgets.IntSlider(name="Sankey Height", start=200, end=2500, step=100, value=800)

# Function to get movie details from the autocomplete input
def show_movie_details(title):
    movie_info = api.get_media_details(title)
    if movie_info is not None:
        details = pn.pane.Markdown(
            f"### Title: {movie_info['title']}  \n"
            f"**Release Year:** {movie_info['release_year']}  \n"
            f"**Type of Media:** {movie_info['type']}  \n"
            f"**IMDb Score:** {movie_info['imdb_score']}  \n"
            f"**Genres:** {movie_info['genres']}  \n"
            f"**Age Certification:** {movie_info['age_certification']}  \n"
            f"**Runtime:** {movie_info['runtime']} minutes  \n"
            f"**Description:** {movie_info['description']}",
            width=500
        )
        return details
    else:
        return pn.pane.Markdown("Media not found.")

# Function to get the movie catalog based on year and minimum rating
def get_catalog(release_year, min_rating, only_movies, only_tv):
    local = api.extract_local_network(release_year, min_rating, only_movies, only_tv)
    table = pn.widgets.Tabulator(local, selectable=False, width=1500, height=800)
    return table

# Function to create the Sankey diagram
def get_plot(years, min_rating, sankey_width, sankey_height, only_movies, only_tv, selected_genres):
    filtered_local = api.extract_local_network(years, min_rating, only_movies, only_tv)
    fig = api.create_sankey_plot(filtered_local, sankey_width, sankey_height, selected_genres)
    return fig


# Callback Bindings
movie_details_output = pn.bind(show_movie_details, autocomplete)
movie_catalog = pn.bind(get_catalog, years, min_rating, only_movies, only_tv)
sankey_plot = pn.bind(get_plot, years, min_rating, sankey_width, sankey_height, only_movies, only_tv, genre_selector_plot)

# Netflix Logo
image_url = "https://i.pinimg.com/736x/f6/97/4e/f6974e017d3f6196c4cbe284ee3eaf4e.jpg"
image = pn.pane.Image(image_url, height=350, width=295)

# Layout and cards

card_width = 560

search_card = pn.Card(
    pn.Column(
        autocomplete,
    ),
    title="Search", width=card_width, collapsed=False
)

filter_card = pn.Card(
    pn.Column(
        years,
        min_rating,
        only_movies,
        only_tv,
    ),
    title="Filter", width=card_width, collapsed=False
)

plotting_card = pn.Card(
    pn.Column(
        sankey_width,
        sankey_height,
        genre_selector_plot
    ),
    title="Plot", width=card_width, collapsed=False
)

catalog_card = pn.Card(
    pn.Column(
        movie_details_output,  
        movie_catalog          
    ),
    title="Media Catalog", width=card_width, height=800, collapsed=False
)

layout = pn.template.FastListTemplate(
    title="Movies and TV Shows listings in the U.S. on Netflix (July, 2022)",
    sidebar=[
        search_card,
        filter_card,
        plotting_card,
        image
    ],
    main=[
        pn.Tabs(
            ("Search Movie Catalog", catalog_card),
            ("Genre Network", sankey_plot)
        )
    ],
    header_background='#a93226'
)

layout.show(port=2121)
