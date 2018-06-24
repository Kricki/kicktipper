# -*- coding: utf-8 -*-
import numpy
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
import re  # RegExp
import sqlite3

import tools


__author__ = 'Kricki (https://github.com/Kricki)'
__version__ = "0.1.4"


class Team:
    """    Representes a Team
    """
    no_of_teams = 0

    ''' Constructor'''
    def __init__(self, name):
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
    """ Functions to generate match scores.

    """

    @staticmethod
    def expected_score(mu, home_team_advantage, team1, team2):
        """ Calculates "expected score" for the match between team1 and team2

        :param double mu: expectation value for the number of scored goals for the match
        :param double home_team_advantage: Factor to account for the advantage of the home team
        :param Team team1: Home team
        :param Team team2: Away team
        :return: int score for team 1 and score for team2
        """
        score1 = mu/2*team1.offense_strength - team2.defense_strength + home_team_advantage
        score2 = mu/2*team2.offense_strength - team1.defense_strength

        d = score1-score2

        score1 = round(score1, 0)
        score2 = round(score2, 0)

        if score1 == score2:  # check if the draw ist justified...
            if d > 0.5:  # team1 is much better
                score1 += 1
            if d < -0.5:  # team2 is much better
                score2 += 1

        return int(score1), int(score2)

    @staticmethod
    def random_score(mu, draw_allowed=True):
        """ Generates random score, where the individual team score is drawn from a Poissonian distribution
        :param double mu: the expectation value for the number of scored goals for the match. I.e. mu/2 is the
            expectation value for the number of goals scored per team.
        :param bool draw_allowed: A draw is a legal result. Default: True

        :return: int score for team 1 and score for team2

        """

        result_ok = False

        while not result_ok:
            score1 = numpy.random.poisson(mu/2)
            score2 = numpy.random.poisson(mu/2)
            if draw_allowed:
                result_ok = True
            else:
                if score1 != score2:
                    result_ok = True

        return score1, score2


class KicktippAPI:
    """ API for communication with kicktipp.de website

    Uses robobrowser library

    """

    def __init__(self, name):
        self._name = name
        self._url = "https://www.kicktipp.de/" + self._name + "/"
        self._url_login = self._url + "profil/login"
        self._url_logout = self._url + "profil/logout"
        self._url_tippabgabe = self.url + "tippabgabe"

        self._browser = RoboBrowser()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self._url = "https://www.kicktipp.de/" + self._name + "/"
        self._url_login = self._url + "profil/login"
        self._url_logout = self._url + "profil/logout"
        self._url_tippabgabe = self.url + "tippabgabe"

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def url_login(self):
        return self._url_login

    @url_login.setter
    def url_login(self, value):
        self._url_login = value

    @property
    def url_logout(self):
        return self._url_logout

    @url_logout.setter
    def url_logout(self, value):
        self._url_logout = value

    @property
    def url_tippabgabe(self):
        return self._url_tippabgabe

    @url_tippabgabe.setter
    def url_tippabgabe(self, value):
        self._url_tippabgabe = value

    @property
    def browser(self):
        return self._browser

    def login(self, username, password):
        """ Logs into the kicktipp website in the current group.

        :param string username: Username
        :param string password: Password
        :return: int 0 if login succesful, -1 if not.
        """
        self.browser.open(self._url_login)

        # Get the signup form
        signup_form = self.browser.get_form(id='loginFormular')

        # Fill it out
        signup_form['kennung'].value = username
        signup_form['passwort'].value = password

        # Submit the form
        self._browser.submit_form(signup_form)

        # print(self.browser.state.response.history)
        if self.browser.url == self.url:
            return 0
        else:
            return -1

    def logout(self):
        self.browser.open(self.url_logout)
        if self.browser.url == self.url_logout:
            print("Logout successful")
        else:
            print("Logout failed")

    def fetch_games(self):
        """ Fetches the upcoming matchday from the Kicktipp website.

        The user must be logged in.

        :return: 9x2 matrix (9 rows, 2 columns), each row containing the name of the teams for one match
                None is returned, if fetching was not successful.
        """
        self.browser.open(self.url_tippabgabe)
        if self.browser.url == self.url_tippabgabe: # redirection successful?
            soup = BeautifulSoup(self.browser.response.content, "html.parser") # get BeautifulSoup object from RoboBrowser
            data = soup.find_all('td', class_='nw')

            teams = []
            for element in data:
                if element.string is not None:  # not another id tag (element is not a string)
                    if not re.match('^[0-9]{2}\.', element.string):  # not a date. RegExp: First two symbols are digits, followed by dot.
                        if not re.match('[0-9]:[0-9]', element.string):  # not a score (e.g. '2:1')
                            if not re.match('[0-9]\.[0-9]', element.string):  # not a betting odd (e.g. "1.85")
                                teams.append(element.string)

            games = [[None]*2 for _ in range(9)]

            for kk in range(9):
                games[kk][0] = teams[2*kk]
                games[kk][1] = teams[2*kk+1]

            return games
        else:
            return None

    def fetch_games_world_cup(self, matchday=None):
        """Fetches the matchday from the Kicktipp website. Version for world cups.

        The user must be logged in.

        Parameters
        ----------
        matchday : int
            Specifies the matchday to be fetched. If None (default) the upcoming matchday is fetched.

        Returns
        -------
        list of teams, list of quoten, list of wettquoten

        """

        """ Fetches the matchday from the Kicktipp website.

        The user must be logged in.

        :return: list of teams, list of quoten, list of wettquoten
        """
        if matchday is None:
            url = self.url_tippabgabe
        else:
            url = self.url_tippabgabe + '?&spieltagIndex=' + str(matchday)
        self.browser.open(url)
        if self.browser.url == url:  # redirection successful?
            soup = BeautifulSoup(self.browser.response.content,
                                 "html.parser")  # get BeautifulSoup object from RoboBrowser
            data = soup.find_all('td', {'class': 'nw'})

            teams = []
            quoten = []
            wettquoten = []

            teams_temp = []
            quoten_temp = []
            wettquoten_temp = []
            for element in data:
                class_name = None
                if len(element.attrs['class']) > 1:
                    if element.attrs['class'][1] == 'kicktipp-time':
                        class_name = 'kicktipp-time'
                    elif element.attrs['class'][0] == 'kicktipp-wettquote':
                        class_name = 'kicktipp-wettquote'

                if class_name == 'kicktipp-time':  # a date => new row (new match)
                    if teams_temp:
                        teams.append(teams_temp)
                        teams_temp = []
                    if quoten_temp:
                        quoten.append(quoten_temp)
                        quoten_temp = []
                    if wettquoten_temp:
                        wettquoten.append(wettquoten_temp)
                        wettquoten_temp = []
                elif class_name == 'kicktipp-wettquote':  # wettquote
                    wettquoten_temp.append(float(element.string.replace(',', '.')))
                elif class_name is None:
                    if re.match('[0-9]{2} - [0-9]{2} - [0-9]{2}', element.string):  # quoten (Punkte)
                        quoten_temp = re.findall(r'\d+', element.string)
                        quoten_temp = [int(_) for _ in quoten_temp]
                    elif not re.match('[0-9]:[0-9]', element.string):  # not a score (e.g. '2:1')
                        # it is a team name
                        teams_temp.append(element.string)

            if teams_temp:
                teams.append(teams_temp)
            if quoten_temp:
                quoten.append(quoten_temp)
            if wettquoten_temp:
                wettquoten.append(wettquoten_temp)

            return teams, quoten, wettquoten
        else:
            return None

    def submit_scores(self, scores):
        """ Uploads the matchday scores to the kicktipp website

        The user must be logged in.

        :param scores: 9x2 matrix contatining the scores (see model)
        """
        self.browser.open(self.url_tippabgabe)
        form = self.browser.get_forms()
        tipp_form = form[0]

        # count number of matches that are not played yet
        n_matches = 0
        for element in tipp_form.keys():
            if "heimTipp" in element:
                n_matches += 1

        # "match_number+9-n_matches": matches that are already played are ignored
        # e.g. if you submit your scores on saturday, the score from the friday's match will be ignored.
        match_number = 0
        for element in tipp_form.keys():
            if "heimTipp" in element:
                tipp_form[element].value = scores[match_number+9-n_matches][0]
            elif "gastTipp" in element:
                tipp_form[element].value = scores[match_number+9-n_matches][1]
                match_number += 1

        self.browser.submit_form(tipp_form)


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
