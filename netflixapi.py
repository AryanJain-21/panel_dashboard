import pandas as pd
import sankey as sk

class NetflixAPI:

    def __init__(self):
        self.netflix = None  # DataFrame

    def load_net(self, filename):
        """Loads the Netflix dataset from a CSV file."""
        self.netflix = pd.read_csv(filename)

    def get_years(self):
        """Fetches unique release years from the dataset."""
        years = self.netflix['release_year'].unique()
        return sorted(years)

    def get_unique_genres(self):
        """Returns a sorted list of unique genres in the dataset."""
        unique_genres = set()
        for genres in self.netflix['genres'].dropna():
            genre_list = [genre.strip().replace('[', '').replace(']', '').replace("'", "") for genre in genres.split(',')]
            unique_genres.update(genre_list)
        return sorted(unique_genres)

    def extract_local_network(self, release_year, min_rating, only_movies, only_tv, selected_genres=None):
        # Assuming self.netflix is your main DataFrame
        if selected_genres is None:
            selected_genres = [] 

        local_network = self.netflix.copy()  # Create a copy to avoid SettingWithCopyWarning

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

        # Define columns to display
        columns_to_display = ['title', 'type', 'imdb_score', 'release_year', 'genres', 'age_certification', 'runtime', 'seasons']

        # Ensure the columns exist in the DataFrame before selection
        existing_columns = [col for col in columns_to_display if col in local_network.columns]

        # Reset index and select only existing columns
        local_network = local_network.reset_index(drop=True)[existing_columns]

        return local_network




    def get_movie_details(self, title):
        """Fetches details of a specific movie based on its title."""
        movie_details = self.netflix[self.netflix['title'] == title]
        return movie_details.squeeze() if not movie_details.empty else None

    def create_sankey_plot(self, data, sankey_width=1500, sankey_height=800):
        """
        Creates a Sankey diagram based on the provided data.
        """
        # Step 1: Ensure proper genre separation and clean genres
        def clean_genre(genre):
            if isinstance(genre, str):
                # Remove brackets and single quotes, then strip whitespace
                return genre.replace('[', '').replace(']', '').replace("'", "").strip()
            return genre  # Return as is if not a string

        # Apply the genre cleaning function and create a list of cleaned genres
        data['genres'] = data['genres'].apply(lambda x: [clean_genre(genre) for genre in x.split(',')] if isinstance(x, str) else [])

        # Step 2: Explode the 'genres' column to get each genre in a separate row
        genre_expanded = data.explode('genres').dropna(subset=['genres'])  # Drop rows where 'genres' is NaN

        # Step 3: Create a new DataFrame for the Sankey plot
        sankey_data = genre_expanded[['title', 'genres']].rename(columns={'title': 'src', 'genres': 'targ'})

        # Step 4: Create the Sankey plot using the expanded genre data
        fig = sk.make_sankey(
            df=sankey_data,  # Pass the DataFrame
            src='src',       # Source column name
            targ='targ',     # Target column name
            width=sankey_width,
            height=sankey_height
        )

        return fig


def main():
    netapi = NetflixAPI()
    netapi.load_net('titles.csv')

    # For debugging purposes, see what the function returns
    years = netapi.get_years()
    for year in years:
        print(year)

    # Count of unique release years
    print(len(years))


if __name__ == '__main__':
    main()
