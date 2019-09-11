import mechanicalsoup
import re
import pandas as pd
import warnings
import getpass


class KicktippAPI:
    """ API for communication with kicktipp.de website

    Attributes
    ----------
    name : str
        Name of the kicktipp group
    members : pandas.DataFrame
        DataFrame containing registered members of the kicktipp group
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

    @staticmethod
    def read_username_from_user_input():
        return input('Username: ')

    @staticmethod
    def read_password_from_user_input():
        return getpass.getpass('Password: ')

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

    def login(self, username=None, password=None):
        """ Logs into the kicktipp website in the current group.

        Parameters
        ----------
        username : str
            Username, optional. If not given, the user is prompted to type the username.
        password : str
            Password, optional. If not given, the user is prompted to type the password.
        Returns
        -------
        bool
            True if login was successful, False otherwise.

        """
        if username is None:
            username = self.read_username_from_user_input()
        if password is None:
            password = self.read_password_from_user_input()

        # TODO: implement timeout
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
            dates = []

            teams_temp = []
            quoten_temp = []
            wettquoten_temp = []
            dates_temp = []
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
                    if dates_temp:
                        dates.append(dates_temp)

                    date = element.text
                    if date:
                        dates_temp = date
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
            if dates_temp:
                dates.append(dates_temp)

            # Transpose the nested lists
            # see https://stackoverflow.com/questions/6473679/transpose-list-of-lists
            teams = list(map(list, zip(*teams)))
            points = list(map(list, zip(*points)))
            odds = list(map(list, zip(*odds)))

            # Read matchday number
            text = soup.find_all('div', {'class': 'prevnextTitle'})[0].get_text()
            r = re.findall(r'\d+\. Spieltag', text)
            md_no = None
            if r:
                md_no = int(re.findall(r'\d+', r[0])[0])

            # consistency check
            if matchday is not None:
                if md_no != matchday:
                    warnings.warn('Parsed matchday from website does not match the requested value.', UserWarning)

            # Create pandas DataFrame
            n_games = len(teams[0])  # no of games = no of rows
            md_no_col = [md_no]*n_games
            col_names = ['matchday', 'date', 'team1', 'team2',
                         'points_win1', 'points_draw', 'points_win2',
                         'odds_win1', 'odds_draw', 'odds_win2']
            df = pd.DataFrame(columns=col_names)

            df['matchday'] = md_no_col
            df['date'] = dates
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
            data = soup.find_all('td', {'class': 'nw'})

            tipps = pd.DataFrame(columns=['team1', 'team2', 'tipp1', 'tipp2'])

            team1 = []
            team2 = []
            tipp1 = []
            tipp2 = []

            team_names_read = 0
            for el in data:
                if el.string is not None:
                    if len(el.find_all()) > 0:
                        # the element has subtags => This is probably a strangely formatted score ("Ergebnis")
                        # which we will ignore
                        pass
                    elif re.match('^[a-zA-Z0-9ZäöüÄÖÜß._\-\s]+$', el.string):
                        # a team name (including Umlauts, numbers (e.g. "Mainz 05"), period (e.g. "1. FC Köln")
                        # hyphen and whitespace)
                        if team_names_read == 2:
                            tipp1.append(None)
                            tipp2.append(None)
                            team_names_read = 0
                        if team_names_read == 0:
                            team1.append(el.string)
                            team_names_read = 1
                        elif team_names_read == 1:
                            team2.append(el.string)
                            team_names_read = 2
                    elif re.match('[0-9]:[0-9]', el.string):  # a score
                        tipp_score = self._parse_score(el.string)
                        tipp1.append(tipp_score[0])
                        tipp2.append(tipp_score[1])
                        team_names_read = 0
            if team_names_read == 2:
                tipp1.append(None)
                tipp2.append(None)

            tipps['team1'] = team1
            tipps['team2'] = team2
            tipps['tipp1'] = tipp1
            tipps['tipp2'] = tipp2

            return tipps

    def read_members(self):
        """ Reads the members and corresponding IDs and stores it in the pandas.DataFrame self.members

        Returns
        -------
        pandas.DataFrame
            Dataframe containing the member's names and IDs
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

    def submit_predictions(self, scores, matchday=None, n_matches=9):
        """ Uploads the matchday predictions to the kicktipp website

        The user must be logged in.

        Parameters
        ----------
        scores : 2-d array with 2 columns
            Containing the predicted scores
        matchday : int, optional
            Number of matchday to be read. If None (default), the upcoming matchday is read.
        n_matches : int
            Number of matches per matchday, defaults to 9

        """
        if matchday is None:
            url = self._url_tippabgabe
        else:
            url = self._url_tippabgabe + '?&spieltagIndex=' + str(matchday)

        if self._browser_open(url):
            tipp_form = self._browser.select_form('form[id="tippabgabeForm"]')
            soup = self._browser.get_current_page()

            # Get the names of the individual forms
            # The forms have the name "spieltippForms[ID].heimTipp" and "spieltippForms[ID].gastTipp", where ID
            # is an integer specifying the individual form.
            # Get these IDs from the form:
            form_ids = []
            for tag in soup.find_all('td', {'class':'kicktipp-tippabgabe'}): # iterate over tags in form
                id_ = int(re.findall(r'\d+', tag.find_all()[0]['name'])[0])
                form_ids.append(id_)
                # Example for tag.find_all()[0]['name']: "spieltippForms[697554851].tippAbgegeben"

            n_not_played = len(form_ids)  # number of matches of this matchday not played yet

            # iteration starts at "n_matches-n_not_played": matches that are already played are ignored
            # e.g. if you submit your scores on saturday, the score from the friday's match will be ignored.
            for idx, score in enumerate(scores[n_matches-n_not_played:]):
                form_name = 'spieltippForms[' + str(form_ids[idx]) + ']'
                tipp_form[form_name + '.heimTipp'] = score[0]
                tipp_form[form_name + '.gastTipp'] = score[1]

            self._browser.submit_selected()

    def _parse_score(self, element) -> list:
        """ Generic method to parse a score.

        The method tries to pick the appropriate method according to the passed datatype of element

        Parameters
        ----------
        element : {str, bs4.element.Tag}
            Element to be parsed

        Returns
        -------
        list
            List with two values: score of the two teams, e.g. [3, 2]
        """
        if isinstance(element, str):
            score = self._score_from_str(element)  # type: list
        else:
            score = self._score_from_tag(element)  # type: list

        return score

    @staticmethod
    def _score_from_str(score_str) -> list:
        """ Parses score from a string

        Parameters
        ----------
        score_str : str
            String containing the score in the format "3:2"

        Returns
        -------
        list
            List with two values: score of the two teams, e.g. [3, 2]
        """
        score_team1 = int(score_str.split(':')[0])
        score_team2 = int(score_str.split(':')[1])

        return [score_team1, score_team2]

    @staticmethod
    def _score_from_tag(tag) -> list:
        """ Parses score from a beautiful soup tag

        As the kicktipp website seems to regularly change their tag syntax, this function might be adapted in the
        future.
        This works for the 2019/20 season.

        Parameters
        ----------
        tag : bs4.element.Tag

        Returns
        -------
        list
            List with two values: score of the two teams, e.g. [3, 2]
        """

        '''
        The passed tag is in the following form:
        <td class="nw"><span class ="kicktipp-ergebnis"><span class="kicktipp-abschnitt kicktipp-abpfiff"> 
        <span class="kicktipp-heim">3</span><span class="kicktipp-tortrenner" >:</span>
        <span class ="kicktipp-gast">2</span></span></span></td>
        
        The score is hidden in "kicktipp-heim" (3) and "kicktipp-gast (2).
        '''
        score_team1 = int(tag.find_all('span', {'class': 'kicktipp-heim'})[0].string)
        score_team2 = int(tag.find_all('span', {'class': 'kicktipp-gast'})[0].string)

        return [score_team1, score_team2]

