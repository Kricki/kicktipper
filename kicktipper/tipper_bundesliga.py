import pandas as pd
from typing import Union
from datetime import datetime
import os

from . import kicktipp_api
from . import fivethirtyeight
from . import predictor
from . import tools


class TipperBundesliga:
    def __init__(self, kicktipp_group):
        self._datapath = '../data'

        self.kicktipp_group = kicktipp_group
        self.kicktipp_username = None
        self.kicktipp_password = None

        self._kicktipp_api = kicktipp_api.KicktippAPI(self.kicktipp_group)
        self._fte = fivethirtyeight.FiveThirtyEight()
        self._pred = predictor.MatchPredictor()

        self.leaguetable = self.leaguetable_read()
        self.projected_scores = self.projected_scores_read()

    def find_similar_teamname(self, teamname):
        p = [tools.similar(teamname, team) for team in self.leaguetable['team']]
        idx = p.index(max(p))
        return self.leaguetable.iloc[idx]['team']

    def align_team_names_in_df(self, df):
        dfc = df.copy()
        for i, row in dfc.iterrows():
            name = self.find_similar_teamname(row['team1'])
            dfc.at[i, 'team1'] = name
            name = self.find_similar_teamname(row['team2'])
            dfc.at[i, 'team2'] = name
        return dfc

    def leaguetable_read(self, filename='Bundesliga.csv'):
        filename = os.path.join(self._datapath, filename)
        return pd.read_csv(filename)

    def login(self):
        self._kicktipp_api.login(self.kicktipp_username, self.kicktipp_password)

    def logout(self):
        self._kicktipp_api.logout()

    def projected_scores_read(self, update=False, align_team_names=True):
        fte = fivethirtyeight.FiveThirtyEight()
        fte.read_data(update=update)
        fte.data = fte.data[fte.data['date'] >= '2019-08-15']
        df = fte.data.loc[:, ('team1', 'team2', 'proj_score1', 'proj_score2')]

        if align_team_names:
            df = self.align_team_names_in_df(df)
        return df

    def kicktipp_matches_read(self, matchday=None, align_team_names=True):
        df = self._kicktipp_api.read_games(matchday)
        if align_team_names:
            df = self.align_team_names_in_df(df)
        return df

    def projected_scores_for_match(self, team1, team2):
        match = self.projected_scores[(self.projected_scores['team1'] == team1)
                                      & (self.projected_scores['team2'] == team2)]
        ps1 = match['proj_score1'].values[0]
        ps2 = match['proj_score2'].values[0]

        return ps1, ps2

    def projected_scores_for_matchday(self, matchday=None):
        df_matchday = self.kicktipp_matches_read(matchday=matchday)
        proj_score1 = []
        proj_score2 = []
        for _, row in df_matchday.iterrows():
            ps1, ps2 = self.projected_scores_for_match(row['team1'], row['team2'])
            proj_score1.append(ps1)
            proj_score2.append(ps2)

        df_ps = pd.DataFrame(
            {'team1': df_matchday['team1'], 'team2': df_matchday['team2'],
             'proj_score1': proj_score1, 'proj_score2': proj_score2})

        return df_ps

    def predicted_scores_for_matchday(self, matchday=None):
        df_ps = self.projected_scores_for_matchday(matchday=matchday)

        pred_score1 = []
        pred_score2 = []
        prob1 = []
        prob2 = []
        prob_draw = []

        for _, row in df_ps.iterrows():
            self._pred.l1 = row['proj_score1']
            self._pred.l2 = row['proj_score2']
            pred_score1.append(self._pred.predicted_score[0][0])
            pred_score2.append(self._pred.predicted_score[0][1])
            prob1.append(self._pred.probs_tendency[0])
            prob2.append(self._pred.probs_tendency[1])
            prob_draw.append(self._pred.probs_tendency[2])

        df_ps['pred_score1'] = pred_score1
        df_ps['pred_score2'] = pred_score2
        df_ps['prob1'] = prob1
        df_ps['prob2'] = prob2
        df_ps['prob_draw'] = prob_draw
        return df_ps

    def predict_and_submit_scores_for_matchday(self, matchday: Union[int, list] = None):
        """
        Predict scores for a matchday and submit these scores the Kicktipp website.

        Parameters
        ----------
        matchday : int or list
            Defining the matchday to predict and submit. Can be a list of integers, then the procedure is performed for
            all matchdays from the list.
        """
        if isinstance(matchday, int):
            matchday = [matchday]  # matchday is not a list, so convert it to one
        for md in matchday:
            df_pred_scores = self.predicted_scores_for_matchday(matchday=md)
            scores = [df_pred_scores['pred_score1'].tolist(), df_pred_scores['pred_score2'].tolist()]
            scores = list(map(list, zip(*scores)))  # transpose list of lists
            # see https://stackoverflow.com/questions/6473679/transpose-list-of-lists/6473727
            self._kicktipp_api.submit_predictions(scores=scores, matchday=md)

    def store_data_for_matchday_to_file(self, filename=None, overwrite=False):
        df = self.kicktipp_matches_read()
        df_proj_score = self.projected_scores_for_matchday()
        df_pred_score = self.predicted_scores_for_matchday()
        df = df.drop('date', 1)
        df['proj_score1'] = df_proj_score['proj_score1']
        df['proj_score2'] = df_proj_score['proj_score2']
        df['pred_score1'] = df_pred_score['pred_score1']
        df['pred_score2'] = df_pred_score['pred_score2']
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['timestamp'] = [dt]*len(df.index)

        if filename is None:
            md = df['matchday'][0]
            filename = os.path.join(self._datapath, 'matchday' + str(md) + '.csv')
        else:
            filename = os.path.join(self._datapath, filename)

        if not overwrite and os.path.isfile(filename):
            return
        else:
            df.to_csv(filename, index=False)
