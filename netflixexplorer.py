import panel as pn
from netflixapi import NetflixAPI  # Assuming you renamed the API for Netflix
import sankey as sk
import pandas as pd  # Ensure pandas is imported for DataFrame manipulation

# Load JavaScript dependencies and configure Panel (required)
pn.extension()  # Set your desired theme, removing the toggle

# Initialize API
api = NetflixAPI()
api.load_net('titles.csv')

# Widget Declarations

# Autocomplete Input for movie titles
autocomplete = pn.widgets.AutocompleteInput(
    name="Media Title",
    value='',
    placeholder='Type media title...',
    options=list(api.netflix['title'].unique())  # Use unique titles for suggestions
)

# Dropdown for selecting release year
years = pn.widgets.Select(name="Year", options=api.get_years(), value=2000)

# Slider for controlling the minimum rating
min_rating = pn.widgets.FloatSlider(name="Min Rating", start=0.0, end=10.0, step=0.1, value=5.0)

# Checkboxes for filtering by type
only_movies = pn.widgets.Checkbox(name='Only Movies', value=False)
only_tv = pn.widgets.Checkbox(name='Only TV Shows', value=False)

# Multi-Select for genres (for plotting)
unique_genres = []

# Loop through the genres in the Netflix data
for x in api.netflix['genres']:
    # Split genres by comma, strip whitespace, and remove unwanted characters
    genres = [genre.strip() for genre in x.split(',')]
    cleaned_genres = [genre.replace('[', '').replace(']', '').replace("'", "").strip() for genre in genres]
    
    # Append cleaned genres to the list while ensuring uniqueness
    for y in cleaned_genres:
        if y not in unique_genres:  # Only add if it's not already in the list
            unique_genres.append(y)

# Print or use the unique genres
#rint(unique_genres)  # This will print genres without quotes or brackets
unique_genres.sort() 

genre_options = unique_genres  # Assuming genres are in list format
genre_selector_plot = pn.widgets.MultiSelect(
    name='Show Media with Specific Genres',
    options=genre_options,
    value=[]  # Default selected genres (can be empty to show all)
)

# Plotting Widgets for Sankey Diagram
sankey_width = pn.widgets.IntSlider(name="Sankey Width", start=250, end=2000, step=250, value=1500)
sankey_height = pn.widgets.IntSlider(name="Sankey Height", start=200, end=2500, step=100, value=800)

# Callback Functions

# Function to get movie details from the autocomplete input
def show_movie_details(title):
    movie_info = api.get_movie_details(title)
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
            height=300,
            width=500  # Set the desired height here (in pixels)
        )
        return details
    else:
        return pn.pane.Markdown("Media not found.")

# Function to get the movie catalog based on year, minimum rating, and type
def get_catalog(release_year, min_rating, only_movies, only_tv):
    global local
    local = api.extract_local_network(release_year, min_rating)
    
    # Filter by type
    if only_movies and not only_tv:
        local = local[local['type'] == 'MOVIE']
    elif only_tv and not only_movies:
        local = local[local['type'] == 'SHOW']
    
    table = pn.widgets.Tabulator(local, selectable=False, width=1500, height=800)
    return table

# Function to create the Sankey diagram
def get_plot(years, min_rating, sankey_width, sankey_height, only_movies, only_tv, selected_genres):
    # Update local based on filters for the Sankey plot
    filtered_local = local.copy()
    
    # Apply filtering by type if applicable
    if only_movies and not only_tv:
        filtered_local = filtered_local[filtered_local['type'] == 'MOVIE']
    elif only_tv and not only_movies:
        filtered_local = filtered_local[filtered_local['type'] == 'SHOW']
    
    # Ensure genres are in a list format and then expand the genres
    filtered_local['genres'] = filtered_local['genres'].apply(lambda x: x.split(', ') if isinstance(x, str) else x)
    # Clean up genre names
    filtered_local['genres'] = filtered_local['genres'].apply(lambda genres: [genre.strip("[]'") for genre in genres])
    
    # Filter by selected genres
    if selected_genres:
        filtered_local = filtered_local[filtered_local['genres'].apply(lambda g: any(genre in g for genre in selected_genres))]

    genre_expanded = filtered_local.explode('genres')

    # Create the Sankey plot with unique titles and genres
    fig = sk.make_sankey(genre_expanded, "title", "genres", width=sankey_width, height=sankey_height)
    return fig

# Callback Bindings
movie_details_output = pn.bind(show_movie_details, autocomplete)
movie_catalog = pn.bind(get_catalog, years, min_rating, only_movies, only_tv)
sankey_plot = pn.bind(get_plot, years, min_rating, sankey_width, sankey_height, only_movies, only_tv, genre_selector_plot)  # Pass selected genres here

# Load the image from the internet
image_url = "https://i.pinimg.com/736x/f6/97/4e/f6974e017d3f6196c4cbe284ee3eaf4e.jpg"
image = pn.pane.Image(image_url, height=450,width=300)  # Adjust the width as needed

# Dashboard Widget Containers ("Cards")
card_width = 560

search_card = pn.Card(
    pn.Column(
        autocomplete,
        years,
        min_rating,
        only_movies,
        only_tv,
    ),
    title="Search", width=card_width, collapsed=False
)

# Create a separate card for plotting dimensions
plotting_card = pn.Card(
    pn.Column(
        sankey_width,
        sankey_height,
        genre_selector_plot  # Added the genre selector to the plotting card
    ),
    title="Plot", width=card_width, collapsed=False
)

# Updated catalog_card to include the new layout with added spacing
catalog_card = pn.Card(
    pn.Column(
        movie_details_output,  # Movie details output above the table
        movie_catalog           # Movie catalog table below
    ),
    title="Media Catalog", width=card_width, height=800, collapsed=False  # Added height
)

# Layout with the image added below the search and plot cards
layout = pn.template.FastListTemplate(
    title="Netflix Movie Explorer",
    sidebar=[
        search_card,
        plotting_card,
        image  # Add the image here
    ],
    main=[
        pn.Tabs(
            ("Search Movie Catalog", catalog_card),
            ("Genre Network", sankey_plot),  # Only in the main area
            active=0  # Which tab is active by default?
        )
    ],
    header_background='#a93226'
).servable()

layout.show()