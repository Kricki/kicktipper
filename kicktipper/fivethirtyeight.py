import pandas as pd
import urllib.request
import ntpath
import os


class FiveThirtyEight:
    def __init__(self):
        self.data = pd.DataFrame()
        self.url = 'https://projects.fivethirtyeight.com/soccer-api/club/spi_matches.csv'
        # see: https://github.com/fivethirtyeight/data/tree/master/soccer-spi

        self._save_dir = '../data'

    def read_data(self, filename=None, update=False):
        if filename is None:
            filename = os.path.join(self._save_dir, 'spi_matches.csv')

        if update or not os.path.isfile(filename):
            self.download_data()

        data = pd.read_csv(filename)
        data = data[data['league_id'] == 1845]  # Keep only Bundesliga matches
        data = data[data['date'] >= '2019-08-01']  # Keep only matches from 2019/20 season
        data['team1'] = data['team1'].str.replace('FC Cologne', '1. FC Köln')
        data['team2'] = data['team2'].str.replace('FC Cologne', '1. FC Köln')
        data = data.reset_index()
        self.data = data

    def download_data(self, url=None, save_dir=None):
        """ Downloads a data file

        Parameters
        ----------
        url : str
            URL to the datafile
        save_dir : str
            Filepath to storage location (directory)

        """
        if url is None:
            url = self.url
        if save_dir is None:
            save_dir = self._save_dir

        if not os.path.isdir(save_dir):  # create directory if it does not exist
            os.makedirs(save_dir)

        filename = os.path.join(save_dir, ntpath.basename(url))
        urllib.request.urlretrieve(url, filename)

