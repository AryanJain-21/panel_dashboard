"""
File: gadapi.py

Description: The primary API for interacting with the gad dataset.
"""

import pandas as pd
import sankey as sk
from collections import Counter

class NetflixAPI:

    netflix = None  # DataFrame

    def load_net(self, filename):
        """Loads the Netflix dataset from a CSV file."""
        self.netflix = pd.read_csv(filename)
        print(self.netflix)

    def get_years(self):
        """
        Fetches unique release years from the dataset.

        :return: Sorted list of unique release years.
        """
        years = self.netflix['release_year'].unique()
        return sorted(years)

    def extract_local_network(self, year, min_rating, selected_genres=None, selected_age_certifications=None):

        """
        Extracts a local network of movies based on a specific year, 
        filtering by minimum IMDb rating, genres, and age certifications.

        :param year: The release year to filter by.
        :param min_rating: Minimum rating threshold for movies to be included.
        :param selected_genres: List of genres to filter by (optional).
     :param selected_age_certifications: List of age certifications to filter by (optional).
       :return: A filtered DataFrame of movies for the specified year and rating.
      """
     # Focus on a particular set of columns
        netflix_data = self.netflix[['title', 'type', 'imdb_score', 'release_year', 'genres', 'age_certification']]

        # Filter by minimum rating
        netflix_data = netflix_data[netflix_data.imdb_score >= min_rating]

        # Filter to include only movies that are associated with the specified release year
        netflix_data = netflix_data[netflix_data.release_year == year]

    # Filter by genres if specified
        if selected_genres:
            netflix_data = netflix_data[netflix_data['genres'].isin(selected_genres)]

    # Filter by age certifications if specified
        if selected_age_certifications:
            netflix_data = netflix_data[netflix_data['age_certification'].isin(selected_age_certifications)]

        return netflix_data.reset_index(drop=True)

    def get_movie_details(self, title):
        """
        Fetch details of a specific movie based on its title.

        :param title: The title of the movie to fetch details for.
        :return: A pandas Series containing the movie details.
        """
        movie_details = self.netflix[self.netflix['title'] == title]
        if not movie_details.empty:
            return movie_details.squeeze()  # Return as a Series
        else:
            return None  # Return None if the movie is not found


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
