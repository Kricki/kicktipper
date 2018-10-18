import mechanicalsoup
import re
import pandas as pd


class KicktippAPI:
    """ API for communication with kicktipp.de website

    Attributes
    ----------
    name : str
        Name of the kicktipp group

    members : pandas.DataFrame
        DataFrame containing registered member of the kicktipp group
    """

    def __init__(self, name):
        """

        Parameters
        ----------
        name : str
            Name of the kicktipp group
        """
        self._name = self.name = name
        self.members = pd.DataFrame(columns=['name', 'id'])

        self._url = "https://www.kicktipp.de/" + self._name + "/"
        self._url_login = self._url + "profil/login"
        self._url_logout = self._url + "profil/logout"
        self._url_tippabgabe = self._url + "tippabgabe"

        self._browser = mechanicalsoup.StatefulBrowser(soup_config={'features': 'html5lib'})

    @property
    def name(self):
        """str: Name of the kicktipp group"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self._url = "https://www.kicktipp.de/" + self._name + "/"
        self._url_login = self._url + "profil/login"
        self._url_logout = self._url + "profil/logout"
        self._url_tippabgabe = self._url + "tippabgabe"

    def _browser_open(self, url):
        """ Open URL.

        The object self.browser is updated.

        Parameters
        ----------
        url : str
            URL of target website

        Returns
        -------
        bool
            True if opening was successful, False otherwise.

        """
        self._browser.open(url)
        if self._browser.get_url() == url:
            return True
        else:
            return False

    def login(self, username, password):
        """ Logs into the kicktipp website in the current group.

        Parameters
        ----------
        username : str
        password : str

        Returns
        -------
        bool
            True if login was successful, False otherwise.

        """
        self._browser.open(self._url_login)

        # Select the signup form
        self._browser.select_form('form[action="/' + self._name + '/profil/loginaction"]')

        # Fill it out and submit
        self._browser['kennung'] = username
        self._browser['passwort'] = password
        self._browser.submit_selected()

        if self._browser.get_url() == self._url:  # redirection to group page successful?
            return True
        else:
            return False

    def logout(self):
        """ Logs out from current account.

        Returns
        -------
        bool
            True if logout was successful, False otherwise

        """
        return self._browser_open(self._url_logout)

    def fetch_games_old(self):
        """ Fetches the upcoming matchday from the Kicktipp website.

        The user must be logged in.

        :return: 9x2 matrix (9 rows, 2 columns), each row containing the name of the teams for one match
                None is returned, if fetching was not successful.
        """
        #TODO: Obselete, can be deleted. (replaced by read_games)
        if self._browser_open(self._url_tippabgabe):
            soup = self._browser.get_current_page() # get BeautifulSoup object from mechanicalsoup browser
            data = soup.find_all('td', {'class': 'nw'})

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


    def read_games(self, matchday=None):
        """ Reads data of a matchday from the kicktipp website

        Parameters
        ----------
        matchday : int, optional
            Number of matchday to be read. If None (default), the upcoming matchday is read.

        Returns
        -------
        pandas.DataFrame
            Dataframe containing the games, points and odds

        """
        if matchday is None:
            url = self._url_tippabgabe
        else:
            url = self._url_tippabgabe + '?&spieltagIndex=' + str(matchday)
        if self._browser_open(url):
            soup = self._browser.get_current_page()
            data = soup.find_all('td', {'class': 'nw'})

            teams = []
            points = []
            odds = []

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
                        points.append(quoten_temp)
                        quoten_temp = []
                    if wettquoten_temp:
                        odds.append(wettquoten_temp)
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
                points.append(quoten_temp)
            if wettquoten_temp:
                odds.append(wettquoten_temp)

            # Transpose the nested lists
            # see https://stackoverflow.com/questions/6473679/transpose-list-of-lists
            teams = list(map(list, zip(*teams)))
            points = list(map(list, zip(*points)))
            odds = list(map(list, zip(*odds)))

            # Create pands DataFrame
            n_games = len(teams[0])  # no of games = no of rows
            col_names = ['team1', 'team2', 'points_win1', 'points_draw', 'points_win2',
                         'odds_win1', 'odds_draw', 'odds_win2']
            df = pd.DataFrame(columns=col_names)

            df['team1'] = teams[0]
            df['team2'] = teams[1]
            if len(points) == 3:
                if len(points[0]) == len(points[1]) == len(points[2]) == n_games:
                    df['points_win1'] = points[0]
                    df['points_draw'] = points[1]
                    df['points_win2'] = points[2]
            if len(odds) == 3:
                if len(odds[0]) == len(odds[1]) == len(odds[2]) == n_games:
                    df['odds_win1'] = odds[0]
                    df['odds_draw'] = odds[1]
                    df['odds_win2'] = odds[2]

            return df
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
        #TODO: Obsolete (replaced by read_games).
        if matchday is None:
            url = self._url_tippabgabe
        else:
            url = self._url_tippabgabe + '?&spieltagIndex=' + str(matchday)
        if self._browser_open(url):
            soup = self._browser.get_current_page()
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

    def read_predictions(self, member, matchday):
        """ Reads predictions from a member for a specific matchday

        Parameters
        ----------
        member : str or int
            Name or ID of member (see self.members)
        matchday : int
            Matchday to be read

        Returns
        -------
        pandas.DataFrame
            Dataframe containing the predictions
        """
        if type(member) is str:  # assume the member name is passed => convert to ID
            member_id = self.members[self.members['name'] == member]['id'].item()
        else:
            member_id = member
        url = self._url + 'tippuebersicht/tipper?spieltagIndex=' + str(matchday) + '&rankingTeilnehmerId=' \
              + str(member_id)
        if self._browser_open(url):
            soup = self._browser.get_current_page()
            data = soup.find_all('td', {"class": 'nw'})

            tipps = pd.DataFrame(columns=['team1', 'team2', 'tipp1', 'tipp2', 'tipp_string'])

            team1 = []
            team2 = []
            tipp1 = []
            tipp2 = []
            tipp_string = []

            team_names_read = 0
            for el in data:
                if el.string is not None:
                    if re.match('^[a-zA-ZäöüÄÖÜß_\-\s]+$',
                                el.string):  # a team name (including Umlauts, hyphen and whitespace)
                        if team_names_read == 2:
                            tipp1.append(None)
                            tipp2.append(None)
                            tipp_string.append(None)
                            team_names_read = 0
                        if team_names_read == 0:
                            team1.append(el.string)
                            team_names_read = 1
                        elif team_names_read == 1:
                            team2.append(el.string)
                            team_names_read = 2
                    elif re.match('[0-9]:[0-9]', el.string):  # a score
                        tipp1.append(int(el.string.split(':')[0]))
                        tipp2.append(int(el.string.split(':')[1]))
                        tipp_string.append(str(el.string))
                        team_names_read = 0
            if team_names_read == 2:
                tipp1.append(None)
                tipp2.append(None)
                tipp_string.append(None)

            tipps['team1'] = team1
            tipps['team2'] = team2
            tipps['tipp1'] = tipp1
            tipps['tipp2'] = tipp2
            tipps['tipp_string'] = tipp_string

            return tipps

    def read_members(self):
        """ Reads the members and corresponding IDs and stores it in the pandas.DataFrame self.members

        Returns
        -------
        pandas.DataFrame
            Dataframe containing the members names and IDs
        """
        url = self._url + 'gesamtuebersicht'
        if self._browser_open(url):
            soup = self._browser.get_current_page()
            data = soup.find_all('td', {"class": 'name'})

            names = []
            for el in data:
                names.append(str(el.string))

            data = soup.find_all('tr', {"class": 'teilnehmer'})  # "TeilnehmerID"
            ids = []
            for el in data:
                ids.append(int(el.attrs['data-teilnehmer-id']))

            self.members['name'] = names
            self.members['id'] = ids

            return self.members

    def submit_predictions(self, scores):
        """ Uploads the matchday predictions to the kicktipp website

        The user must be logged in.

        Parameters
        ----------
        scores : 2-d array with 2 columns
            Containing the predicted scores

        """
        # TODO: Test new mechanicalsoup implementation
        if self._browser_open(self._url_tippabgabe):
            tipp_form = self._browser.select_form(nr=0)

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
                    tipp_form[element] = scores[match_number+9-n_matches][0]
                elif "gastTipp" in element:
                    tipp_form[element] = scores[match_number+9-n_matches][1]
                    match_number += 1

            self._browser.submit_selected()
