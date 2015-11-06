# -*- coding: utf-8 -*-
__author__ = 'kricki'

import tkinter as tk
from tkinter import messagebox as tkmessagebox
import configparser

import tipper
import gui

VERSION = 0.1


class Model:
    def __init__(self):
        self.liga = tipper.Liga("Bundesliga")
        self.team_array = [None]*18
        self.home_team_advantage = 0
        self.mu = 0
        self.group = ""
        self.username = ""
        self.scores = [[0]*2 for _ in range(9)]  # stores the match scores

    def update_teams(self):
        #self.team_array = tipper.defineTeams(self.home_team_advantage, self.mu)
        self.liga.create_db_table()
        self.liga.read_db()

        for kk in range(18):
            #self.team_array.append(self.liga.get_team_object_from_index(kk+1))
            self.team_array[kk] = self.liga.get_team_object_from_index(kk+1)
            #self.liga.add_team(self.team_array[kk])

    def update_db(self):
        self.liga.update_db()


class Controller:
    def __init__(self, master=None):
        self._master = master
        self.model = Model()
        self.score_calculator = tipper.ScoreCalculator()

        self.kicktipp_api = tipper.KicktippAPI("")  # Constructur will again be called in "login"

        # Initialize the model
        self.read_config()
        self.model.update_teams()

        # Initialize the view
        self.main_view = gui.MainView(master, self.model.team_array)
        self.main_view.main_widgets.btn_go.config(command=self.generate_score)
        self.main_view.main_widgets.btn_fetch.config(command=self.fetch_games)
        self.main_view.main_widgets.btn_submit.config(command=self.submit_scores)
        self.main_view.file_menu.filemenu.entryconfig(0, command=self.show_config)
        self.main_view.file_menu.filemenu.entryconfig(1, command=self.show_team_settings)
        self.main_view.file_menu.filemenu.entryconfig(2, command=self.show_info)
        self.main_view.file_menu.connectionmenu.entryconfig(0, command=self.login)
        self.main_view.file_menu.connectionmenu.entryconfig(1, command=self.logout)

        self.set_statusbar("Offline")

    def read_config(self):
        """ Read config file and update internal variables
        """
        print("Read config... ")
        config = configparser.ConfigParser()
        config.read('config.ini')
        config.sections()

        main_config = config['main']
        self.model.mu = float(main_config['ExpectationValue'])
        self.model.home_team_advantage = float(main_config['HomeTeamAdvantage'])
        login_config = config['login']
        self.model.group = login_config['group']
        self.model.username = login_config['username']

        print("Done.")

    def write_config(self):
        """ Write internal variables to config file
        """
        print("Write config...")
        config = configparser.ConfigParser()
        config['main'] = {}
        config['main']['ExpectationValue'] = str(self.model.mu)
        config['main']['HomeTeamAdvantage'] = str(self.model.home_team_advantage)

        config['login'] = {}
        config['login']['group'] = str(self.model.group)
        config['login']['username'] = str(self.model.username)

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        print("Done.")

    def show_config(self):
        """ Display the settings dialog.

        If the user presses "OK", the new settings are updated (config file and internal variables).
        """
        self.read_config()
        settings_dialog = gui.SettingsDialog(self._master)
        settings_dialog.mu = self.model.mu
        settings_dialog.home_team_advantage = self.model.home_team_advantage
        settings_dialog.show(self._master)

        if not settings_dialog.canceled:
            self.model.mu = float(settings_dialog.mu)
            self.model.home_team_advantage = float(settings_dialog.home_team_advantage)
            self.write_config()

    def show_team_settings(self):
        """ Display the team settings dialog.

        If the user presses "OK", the new settings are updated (internal variables).
        """
        team_settings_dialog = gui.TeamSettingsDialog(self._master)

        # populate the dialog
        for kk in range(18):
            team = self.model.liga.get_team_object_from_index(kk+1)
            team_settings_dialog.team_names[kk] = team.name
            team_settings_dialog.scored_goals[kk] = team.scored_goals
            team_settings_dialog.defense_strengths[kk] = team.defense_strength

        team_settings_dialog.show(self._master)

        if not team_settings_dialog.canceled:
            for team, team_index in self.model.liga.team_dict.items():  # iterate over all team objects in liga
                team.name = team_settings_dialog.team_names[team_index-1]
                team.scored_goals = int(team_settings_dialog.scored_goals[team_index-1])
                team.defense_strength = float(team_settings_dialog.defense_strengths[team_index-1])
                team.compute_offense_strength_from_scored_goals(self.model.home_team_advantage, self.model.mu)
            self.model.update_db()

    def generate_score(self):
        if(self.main_view.main_widgets.v_score_generator.get()=="xS"):
            for kk in range(9):
                team_name1 = self.main_view.main_widgets.v_team_list[2*kk].get()
                team_name2 = self.main_view.main_widgets.v_team_list[2*kk+1].get()
                team1 = self.model.liga.get_team_object_from_team_name(team_name1, exact_match=False)
                team2 = self.model.liga.get_team_object_from_team_name(team_name2, exact_match=False)

                score1, score2 = self.score_calculator.expected_score(self.model.mu, self.model.home_team_advantage, team1, team2)
                self.main_view.main_widgets.v_results_list[2*kk].set(score1)
                self.main_view.main_widgets.v_results_list[2*kk+1].set(score2)

                self.update_scores()

        elif(self.main_view.main_widgets.v_score_generator.get()=="Random"):
            for kk in range(9):
                score1, score2 = self.score_calculator.random_score(self.model.mu)
                self.main_view.main_widgets.v_results_list[2*kk].set(score1)
                self.main_view.main_widgets.v_results_list[2*kk+1].set(score2)

                self.update_scores()

    def show_info(self):
        """ Display the info screen
        """
        tkmessagebox.showinfo("Info", "Kicktipper v"+str(VERSION))

    def login(self):
        login_dialog = gui.LoginDialog(self._master)
        login_dialog.group = self.model.group
        login_dialog.username = self.model.username
        login_dialog.show(self._master)

        if not login_dialog.canceled:
            print("Logging in... ")
            self.model.group = login_dialog.group
            self.model.username = login_dialog.username
            self.write_config()
            self.kicktipp_api = tipper.KicktippAPI(login_dialog.group)
            login_status = self.kicktipp_api.login(login_dialog.username, login_dialog.password)

            if login_status == 0:
                print("Login succesful")
                self.set_statusbar("Logged in as " + self.model.username + " in " + self.model.group)
            else:
                print("Login failed")

    def logout(self):
        print("Logging out... ")
        try:
            self.kicktipp_api.logout()
            print("Done.")
            self.set_statusbar("Offline")
        except AttributeError:
            print("Not possible.")

    def fetch_games(self):
        print("Fetching match day... ")
        games = self.kicktipp_api.fetch_games()
        if games is not None:
            for kk in range(len(games)):
                self.main_view.main_widgets.v_team_list[2*kk].set(games[kk][0])
                self.main_view.main_widgets.v_team_list[2*kk+1].set(games[kk][1])
        print("Done.")

    def submit_scores(self):
        print("Submit scores... ")
        self.kicktipp_api.submit_scores(self.model.scores)
        print("Done.")

    def update_scores(self):
        for kk in range(9):
            self.model.scores[kk][0] = self.main_view.main_widgets.v_results_list[2*kk].get()
            self.model.scores[kk][1] = self.main_view.main_widgets.v_results_list[2*kk+1].get()

    def set_statusbar(self, text):
        """ Sets the text displayed in the status bar

        :param string text: The text to be displayed.
        """
        self.main_view.main_widgets.v_statusbar.set(text)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Kicktipper')
    root.option_add('*tearOff', False) # see: http://www.tkdocs.com/tutorial/menus.html (for Menubar)

    app = Controller(root)
    root.mainloop()