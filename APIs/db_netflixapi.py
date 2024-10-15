import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import sankey as sk  # Ensure this is the correct import for your Sankey implementation

# Define the db_NetflixAPI class
class db_NetflixAPI:
    
    def __init__(self, db_name='netflix_movies', collection_name='movies', connection_string=None):
        """Initialize the MongoDB connection and set the database and collection."""
        if connection_string is None:
            connection_string = 'mongodb://mongoadmin:password@localhost:27017/'  # Use environment variables in production
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.data = self.fetch_data()  # Fetch all data on initialization
        self.data = self.convert_objectid_to_string(self.data)

    def fetch_data(self, filter_field=None, filter_value=None):
        """Fetch data from the MongoDB collection, optionally filtered by a field and value."""
        query = {filter_field: filter_value} if filter_field and filter_value else {}
        data = list(self.collection.find(query))
        df = pd.DataFrame(data)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df

    def convert_objectid_to_string(self, df):
        """Convert ObjectId fields in a DataFrame to strings."""
        for column in df.select_dtypes(include=[object]):
            if df[column].apply(lambda x: isinstance(x, ObjectId)).any():
                df[column] = df[column].astype(str)
        return df

    def get_years(self):
        """Fetches unique release years from the dataset."""
        return sorted(self.data['release_year'].unique())
    
    def clean_genre(self, genre):
        """Cleans up the genre string."""
        if isinstance(genre, str):
            return genre.replace('[', '').replace(']', '').replace("'", "").strip()
        return genre 

    def get_unique_genres(self):
        """Fetch unique genres, applying the clean_genre method."""
        genre_list = []
        for genres in self.data['genres']:
            if isinstance(genres, list):
                cleaned_genres = [self.clean_genre(genre) for genre in genres]
                genre_list.extend(cleaned_genres)
            else:
                cleaned_genres = [self.clean_genre(genre) for genre in genres.split(',')]
                genre_list.extend(cleaned_genres)
        
        # Return unique genres
        return sorted(set(genre_list))

    def extract_local_network(self, release_year, min_rating, only_movies, only_tv, selected_genres=None):
        """Extracts a local network of movies/shows based on filters."""
        if selected_genres is None:
            selected_genres = [] 

        local_network = self.data.copy()

        # Filtering based on release year
        local_network = local_network[local_network['release_year'] == release_year]

        # Filtering based on minimum rating
        local_network = local_network[local_network['imdb_score'] >= min_rating]

        # Applying movie and TV show filters
        if only_movies:
            local_network = local_network[local_network['type'] == 'MOVIE']
        if only_tv:
            local_network = local_network[local_network['type'] == 'SHOW']

        # Filtering by selected genres
        if selected_genres:
            local_network = local_network[local_network['genres'].apply(lambda x: any(genre in x for genre in selected_genres))]

        columns_to_display = ['title', 'type', 'imdb_score', 'release_year', 'genres', 'age_certification', 'runtime', 'seasons']
        existing_columns = [col for col in columns_to_display if col in local_network.columns]
        local_network = local_network.reset_index(drop=True)[existing_columns]

        return local_network

    def get_movie_details(self, title):
        """Fetches details of a specific movie based on its title."""
        movie_details = self.data[self.data['title'] == title]
        return movie_details.squeeze() if not movie_details.empty else None

    def create_sankey_plot(self, data, sankey_width=1500, sankey_height=800):
        """Creates a Sankey diagram based on the provided data."""
        def clean_genre(genre):
            if isinstance(genre, str):
                return genre.replace('[', '').replace(']', '').replace("'", "").strip()
            return genre 

        data['genres'] = data['genres'].apply(lambda x: [clean_genre(genre) for genre in x.split(',')] if isinstance(x, str) else [])
        genre_expanded = data.explode('genres').dropna(subset=['genres'])
        sankey_data = genre_expanded[['title', 'genres']].rename(columns={'title': 'src', 'genres': 'targ'})

        # Ensure the data types are consistent
        sankey_data['src'] = sankey_data['src'].astype(str)
        sankey_data['targ'] = sankey_data['targ'].astype(str)

        fig = sk.make_sankey(
            df=sankey_data,
            src='src',
            targ='targ',
            width=sankey_width,
            height=sankey_height
        )
        return fig
