"""
File: sankey.py
Author: Aryan Jain

Description: a wrapper library for plotly sankey visualizations

"""

import pandas as pd
import plotly.graph_objs as go

pd.set_option('future.no_silent_downcasting', True)

def _df_stacking(df, col_x, col_y, args, values):
    """
    Take a dataframe and create a stacked dataframe

    df - Dataframe
    col_x - src column
    col_y - targ column
    args - Tuple of columns (*args given to make_sankey)
    vals - values from val column

    returns - stacked dataframe
    """

    # The columns passed through src and targ stored in a list
    cols = [col_x, col_y]

    # Appending the additional columns to the same list
    for col in args:
        cols.append(col)

    # Getting the stacked list (code from class)
    stacked = list(zip(cols, cols[1:]))

    lst = []

    # Making seperate dataframes per column groupings
    for dfs in stacked:

        # Using the .copy() function to bypass warnings, goes through each grouping and makes a dataframe with those two
        # as columns, changing their names to src and targ
        s_df = df[[dfs[0], dfs[1]]].copy()

        s_df.columns = ['src', 'targ']

        # To add the values later
        s_df.loc[:, 'vals'] = None

        lst.append(s_df)

    # for the values, going through the original dataframe and aggregating the values
    for index, row in df.iterrows():

        value = values.loc[index]

        for objs in lst:

            objs.loc[index, 'vals'] = value

    # Concating the values to the proper rows, and adding them up by using the groupby/sum function
    stacked_df = pd.concat(lst, axis = 0)
    stacked_df = stacked_df.groupby(['src', 'targ'], as_index=False)['vals'].sum()

    return stacked_df


def _code_mapping(df, src, targ):
    """
    Map labels in src and targ columns to integers

    df - Dataframe
    src - src column
    targ - targ column

    returns - Encoded Dataframe with Labels for sankey
    """

    # Get the distinct labels

    df[src] = df[src].astype(str)
    df[targ] = df[targ].astype(str)
    labels = sorted(list(set(list(df[src]) + list(df[targ]))))

    codes = range(len(labels))
    # Create a label->code mapping
    lc_map = dict(zip(labels, codes))
    # Substitute codes for labels in the dataframe

    df = df.replace({src: lc_map, targ: lc_map})

    return df, labels

def make_sankey(df, src, targ, *args, vals=None, **kwargs):
    """
    Create a Sankey figure

    df - Dataframe
    src - Source node column
    targ - Target node column
    vals - Link values (thickness)
    """


    if vals:
        values = df[vals]
    else:
        # to avoid error in _df_stacking
        df['values'] = 1
        values = df['values']


    if args:

        df = _df_stacking(df, src, targ, args, values)
        src = 'src'
        targ = 'targ'
        values = df['vals']

    df, labels = _code_mapping(df, src, targ)

    link = {'source': df[src], 'target': df[targ], 'value': values}

    thickness = kwargs.get('thickness', 50)
    pad = kwargs.get('pad', 50)

    node = {'label': labels, 'thickness': thickness, 'pad': pad}

    sk = go.Sankey(link=link, node=node)
    fig = go.Figure(sk)
    fig.show()



def main():

    # From class
    # bio = pd.read_csv('bio.csv')
    # make_sankey(bio, 'cancer', 'gene', vals ='evidence', pad=100)
    pass

if __name__ == '__main__':
    main()
