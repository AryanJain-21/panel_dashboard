"""
File: gadapi.py

Description: The primary API for interacting with the gad dataset.
"""

import pandas as pd
import sankey as sk
from collections import Counter

class NetflixAPI:

    netflix = None # dataframe

    def load_net(self, filename):

        self.netflix = pd.read_csv(filename)
        print(self.netflix)

    
    def get_years(self):
        """
        Fetch data from the MongoDB collection, optionally filtered by a field and value.
        
        :param filter_field: Field to filter on (e.g., 'release_year')
        :param filter_value: Value to filter by (e.g., 2000)
        :return: pandas DataFrame of fetched data
        """
        # .phenotype and ['phenotype'] serve the same function
        years = self.netflix['release_year'].unique()

        return sorted(years)
    
    def extract_local_network(self, year, min_rating):
        """
        Extracts a local network of movies based on a specific title, 
        filtering by minimum rating and optionally excluding singular movie associations.

        :param title: The title of the movie to focus on.
        :param min_rating: Minimum rating threshold for movies to be included.
        :param singular: If True, include only singular associations; if False, exclude them.
        :return: A filtered DataFrame of movies associated with the specified title.
        """
    
        # Focus on a particular set of columns
        netflix_data = self.netflix[['title', 'imdb_score', 'release_year']]

        # Filter by minimum rating
        netflix_data = netflix_data[netflix_data.imdb_score >= min_rating]

        # Filter to include only movies that are associated with the target movie's release year
        if not netflix_data.empty:
            netflix_data = netflix_data[netflix_data.release_year == year]


        return netflix_data.reset_index(drop=True)



def main():

    netapi = NetflixAPI()
    netapi.load_net('titles.csv')

    # For debugging purposes, seeing what the function returns
    phen = netapi.get_years()
    for p in phen:
        print(p)

    # How many phenotypes are we getting
    print(len(phen))


if __name__ == '__main__':

    main()