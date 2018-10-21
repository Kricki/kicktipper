# -*- coding: utf-8 -*-
import numpy as np

import sqlite3

from . import tools


class Team:
    """    Represents a Team
    """
    no_of_teams = 0

    ''' Constructor'''
    def __init__(self, name=''):
        """ Constructor for Team object

        :param string name: Team's name
        :return: Team object

        """

        self._name = name
        self._scored_goals = 0
        self._offense_strength = 0
        self._defense_strength = 0

        Team.no_of_teams += 1

        self._index = Team.no_of_teams

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def scored_goals(self):
        return self._scored_goals

    @scored_goals.setter
    def scored_goals(self, value):
        self._scored_goals = value

    @property
    def offense_strength(self):
        return self._offense_strength

    @offense_strength.setter
    def offense_strength(self, value):
        self._offense_strength = value

    @property
    def defense_strength(self):
        return self._defense_strength

    @defense_strength.setter
    def defense_strength(self, value):
        self._defense_strength = value

    @property
    def index(self):
        return self._index

    def __del__(self):
        """ Desctructor of Team object
        """
        Team.no_of_teams -= 1

    def compute_offense_strength_from_scored_goals(self, home_team_advantage, mu):
        self.offense_strength = (self.scored_goals - 17*home_team_advantage)/(mu*17)


class Liga:
    """ Liga is a container for Team objects
    """
    # TODO: Change to pandas Dataframe

    no_of_teams = 0

    def __init__(self, name):
        """Constructor

        """
        self.name = name
        self.team_dict = {}

    def __del__(self):
        """Destructor

        """
        del self.team_dict

    def add_team(self, team):
        """Add Team to Liga.

        :param team: Team object
        """

        # add team object to member variable "team_dict" (that is a dictionary (pairs key:value=team object:team index))
        self.team_dict.update({team : team.index})
        self.no_of_teams += 1

    def get_team_object_from_index(self, index):
        """ Returns the team object with the given index.

        :param int index: Team index
        :return: Team object. None, if no team with <index> is found.
        """

        for team in self.team_dict:
            if index == team.index:
                return team

        return None

    def get_index_from_team_name(self, team_name):
        """ Returns the index of the passed team name.

        :param string team_name: Name of the team
        :return: int index of team. None if team is not found in Liga.
        """

        for team in self.team_dict:
            if team.name == team_name:
                return team.index

        return None

    def get_team_object_from_team_name(self, team_name, exact_match=True):
        """ Returns team object of the passed team name.

        :param string team_name: Name of the team to find
        :param bool exact_match: If True (default) the team_name has to match the name of a corresponding team object
         exactly. If False, the object with the closest name to team_name is returned.
        :return: Team object. None if team_name is not found in Liga.
        """

        for team in self.team_dict:
            if team.name == team_name:
                return team

        if exact_match:
            return None
        else:
            teamobject, p = self.find_team_object_with_similar_name(team_name)
            return teamobject

        #if team_name in self.team_dict:
        #    teamobject = self.team_dict[team_name]
        #    return teamobject
        #elif exact_match:
        #    return None
        #else:
        #    teamobject, p = self.find_team_object_with_similar_name(team_name)
        #    #print(team_name + " / " + teamobject.name + " / " + str(p))
        #    return teamobject

    def find_team_object_with_similar_name(self, team_name):
        """ Returns the team object with the name closest to team_name.

        The method searches through all team objects in the Liga object

        :param string team_name: Name of the team to find.
        :return: Team object with exact or similar name
        """
        p = -1
        p_max = -1
        closest_name = None
        for team in self.team_dict:
            p = tools.similar(team_name, team.name)
            if p > p_max:
                closest_name = team.name
                p_max = p

        # return self.team_dict[closest_name], p_max
        return self.get_team_object_from_team_name(closest_name, exact_match=True), p_max

    def create_db_table(self, name=None):
        """ Creates a new table in a database for storage of the team parameters.

        The table has the following format (each row stores parameters for one team):
          * 1st col: team index
          * 2nd col: team name
          * 3rd col: scored goals
          * 4th col: offense strength (automatically computed from scored goals)
          * 5th col: defense strength

        Table is only created if database does not already exist.

        :param string name: Name of the database. Filename will be <name>.sqlite. Default name is the name of the Liga object.
        """
        if not name:
            name = self.name

        sql_connection = sqlite3.connect(name + '.sqlite')
        sql_cursor = sql_connection.cursor()
        sql_cursor.execute('''CREATE TABLE IF NOT EXISTS {} (team_index INTEGER PRIMARY KEY, team_name TEXT UNIQUE,
                            scored_goals INT, offense_strength FLOAT, defense_strength FLOAT)'''.format(name))
        sql_connection.commit()
        sql_connection.close()

    def update_db(self, name=None):
        """ Updates the content of the database.

        Writes content of the Liga object to the database with name <name>.

        :param string name: Name of the database. Filename will be <name>.sqlite. Default name is the name of the Liga object.
        """
        if not name:
            name = self.name

        sql_connection = sqlite3.connect(name + '.sqlite')
        sql_cursor = sql_connection.cursor()

        for team in self.team_dict:
            index = team.index
            tname = team.name
            goals = team.scored_goals
            offense = team.offense_strength
            defense = team.defense_strength

            sql_cursor.execute('INSERT OR REPLACE INTO {} VALUES (?,?,?,?,?)'.format(name),
                               (index, tname, goals, offense, defense))

        sql_connection.commit()
        sql_connection.close()

    def read_db(self, name=None):
        """ Reads the content from the database.

        The content populates the Liga, i.e. team objects are added to the current Liga instance.

        :param string name: Name of the database. Filename will be <name>.sqlite.
            Default name is the name of the Liga object.
        :return: content of the database as a tuple
        """

        if not name:
            name = self.name

        sql_connection = sqlite3.connect(name + '.sqlite')
        sql_cursor = sql_connection.cursor()

        sql_cursor.execute('SELECT * FROM {}'.format(name))
        data = sql_cursor.fetchall()

        sql_connection.close()

        # add teams to Liga, according to database content.
        for kk in range(len(data)):
            team = Team(data[kk][1])
            #team.index = data[kk][0]
            team.scored_goals = data[kk][2]
            team.offense_strength = data[kk][3]
            team.defense_strength = data[kk][4]
            self.add_team(team)
            #print(team)

        return data


class ScoreCalculator:
    """ Methods to generate match scores.

    Attributes
    ----------
    mu : float
        Expectation value for the total number of scored goals for the match
    home_team_advantage : float
        Factor to account for the advantage of the home team (extra goals scored by the home team)
    team1 : Team
        Home team
    team2 : Team
        Away team
    """

    def __init__(self):
        self.mu = 2.5
        self.home_team_advantage = 0
        self.team1 = Team()
        self.team2 = Team()

    def expected_score(self):
        """ Calculates "expected score" for a match from individual team strengths.

        The calculation takes into account the teams offense strength, defense strength and the home team advantage.

        Returns
        -------
        int, int
            Expected score of team1 and team2
        """ 
        score1 = self.mu/2*self.team1.offense_strength - self.team2.defense_strength + self.home_team_advantage
        score2 = self.mu/2*self.team2.offense_strength - self.team1.defense_strength

        d = score1-score2

        score1 = round(score1, 0)
        score2 = round(score2, 0)

        if score1 == score2:  # check if the draw ist justified...
            if d > 0.5:  # team1 is much better
                score1 += 1
            if d < -0.5:  # team2 is much better
                score2 += 1

        return int(score1), int(score2)

    def random_score(self, draw_allowed=True):
        """ Generates random score, where the individual team score is drawn from a Poissonian distribution.

        Parameters
        ----------
        draw_allowed : bool, optional
            Indicates if a draw is a legal result. Default: True

        Returns
        -------
        int, int
            Expected score of team1 and team2
        """

        result_ok = False
        score1, score2 = 0, 0
        while not result_ok:
            score1 = np.random.poisson(self.mu/2)
            score2 = np.random.poisson(self.mu/2)
            if draw_allowed:
                result_ok = True
            else:
                if score1 != score2:
                    result_ok = True

        return score1, score2

    @staticmethod
    def probability_from_odd(rawodd, overround):
        """ Compute outcome probability from bookmakers odds



        See: Palomino et al. "Information salience, investor sentiment, and stock returns:
         The case of British soccer betting." Journal of Corporate Finance 15.3 (2009): 368-387.

        Parameters
        ----------
        rawodd : float
            The "raw" quoted bookmakers odd for the outcome of a specific event (e.g. win of team 1)

        overround : float
            Overround
            The raw quoted bookmakers odds are no “honest” odds but are the payout amounts for successful bets which
            has two important implications: (1) They still contain the stake, i.e., the payment for placing the bet
            (2) More importantly, the bookmakers odds contain a profit margin, the so-called “overround”, which
            means that the “true” underlying odds are actually larger.

            The overround must be choosen such that the sum of all probabilities for associated events sums to 1.
            E.g. win, draw, loss are three associataed events which probabilites must sum to 1.

        Returns
        -------
        float
            Probability (between 0 and 1) of the events outcome

        """
        # delta = 1.1 for bwin
        odd = (rawodd-1)*overround
        return 1-odd/(1+odd)



def defineTeams(home_team_advantage, mu):
    teamArray = []

    teamArray.append(Team("Borussia Dortmund"))
    teamArray[0].scored_goals = 80
    teamArray[0].defense_strength = 0.3

    teamArray.append(Team("Bayern Muenchen"))
    teamArray[1].scored_goals = 90
    teamArray[1].defense_strength = 0.5

    teamArray.append(Team("Schalke 04"))
    teamArray[2].scored_goals = 60
    teamArray[2].defense_strength = 0.2

    teamArray.append(Team("Bayer Leverkusen"))
    teamArray[3].scored_goals = 65
    teamArray[3].defense_strength = 0

    teamArray.append(Team("VfL Wolfsburg"))
    teamArray[4].scored_goals = 70
    teamArray[4].defense_strength = 0.3

    teamArray.append(Team("Borussia Moenchengladbach"))
    teamArray[5].scored_goals = 60
    teamArray[5].defense_strength = 0.1

    teamArray.append(Team("FSV Mainz 05"))
    teamArray[6].scored_goals = 50
    teamArray[6].defense_strength = 0

    teamArray.append(Team("FC Augsburg"))
    teamArray[7].scored_goals = 40
    teamArray[7].defense_strength = -0.3

    teamArray.append(Team("TSG Hoppenheim"))
    teamArray[8].scored_goals = 50
    teamArray[8].defense_strength = -0.1

    teamArray.append(Team("Hannover 96"))
    teamArray[9].scored_goals = 39
    teamArray[9].defense_strength = -0.4

    teamArray.append(Team("Hertha BSC Berlin"))
    teamArray[10].scored_goals = 50
    teamArray[10].defense_strength = 0

    teamArray.append(Team("Werder Bremen"))
    teamArray[11].scored_goals = 45
    teamArray[11].defense_strength = -0.2

    teamArray.append(Team("Eintracht Frankfurt"))
    teamArray[12].scored_goals = 45
    teamArray[12].defense_strength = -0.2

    teamArray.append(Team("VfB Stuttgart"))
    teamArray[13].scored_goals = 50
    teamArray[13].defense_strength = -0.3

    teamArray.append(Team("Hamburger SV"))
    teamArray[14].scored_goals = 50
    teamArray[14].defense_strength = -0.2

    teamArray.append(Team("FC Koeln"))
    teamArray[15].scored_goals = 55
    teamArray[15].defense_strength = 0.1

    teamArray.append(Team("FC Ingolstadt"))
    teamArray[16].scored_goals = 45
    teamArray[16].defense_strength = -0.2

    teamArray.append(Team("SV Darmstadt"))
    teamArray[17].scored_goals = 45
    teamArray[17].defense_strength = -0.3

    for k in range(18):
        teamArray[k].compute_offense_strength_from_scored_goals(home_team_advantage, mu)

    return teamArray
