# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk

import tkadd

__author__ = 'Kricki (https://github.com/Kricki)'


class MainWidgets(ttk.Frame):
    """Class for creating the main widgets:
    - Team selectors
    - Results
    - Selector for drawing type

    """
    def __init__(self, master=None, team_array=None):
        ttk.Frame.__init__(self, master)

        '''
        Create selectors for the teams
        '''
        self.team_array = team_array
        self.team_tuple = ()
        for k in range(18):
            self.team_tuple = self.team_tuple + (self.team_array[k].name,)

        self.v_team_list = []
        self.combo_TeamList = []
        self.v_results_list = []
        self.entry_results_list = []
        for kk in range(18):
            # create comboboxes for the teams
            self.v_team_list.append(tk.StringVar())
            (self.v_team_list[kk]).set(self.team_tuple[kk])
            self.combo_TeamList.append(ttk.Combobox(self, textvariable=self.v_team_list[kk], state='readonly'))
            self.combo_TeamList[kk]['values'] = self.team_tuple
            # ??? http://www.tkdocs.com/tutorial/widgets.html
            # self.cb_TeamList[kk].bind('<<ComboboxSelected>>', self.cb_TeamList[kk].selection_clear)

            # create labels for the results
            self.v_results_list.append(tk.StringVar())
            (self.v_results_list[kk]).set("0")
            self.entry_results_list.append(ttk.Entry(self, width=2, justify=tk.CENTER, textvariable=self.v_results_list[kk]))

        # create and place Comboboxes for Teams. Place labels for results.
        for kk in range(9):
            self.combo_TeamList[2*kk].grid(row=kk, column=0, sticky="EW")
            self.combo_TeamList[2*kk+1].grid(row=kk, column=1, sticky="EW")
            self.entry_results_list[2*kk].grid(row=kk, column=2)
            ttk.Label(self, text=":").grid(row=kk, column=3)
            self.entry_results_list[2*kk+1].grid(row=kk, column=4)

        # RadioButtons as selector for the score generator
        self.v_score_generator = tk.StringVar()
        self.v_score_generator.set('xS')
        self.rb_score_generator = [None]*2
        self.rb_score_generator[0] = ttk.Radiobutton(self, text='xS', variable=self.v_score_generator, value='xS')
        self.rb_score_generator[1] = ttk.Radiobutton(self, text='Random', variable=self.v_score_generator, value='Random')

        self.rb_score_generator[0].grid(row=13, column=0, sticky = 'EW')
        self.rb_score_generator[1].grid(row=14, column=0, sticky = 'EW')

        # "Go" button
        self.btn_go = ttk.Button(self, text='Go!')
        self.btn_go.grid(row=15, column=0)

        # "Fetch" button
        self.btn_fetch = ttk.Button(self, text='Fetch')
        self.btn_fetch.grid(row=13, column=1)

        # "Submit" button
        self.btn_submit = ttk.Button(self, text='Submit')
        self.btn_submit.grid(row=14, column=1)

        # Status bar
        ttk.Separator(master, orient=tk.HORIZONTAL).grid(row=15, columnspan=10, sticky='EW')
        self.v_statusbar = tk.StringVar()
        self.label_statusbar = ttk.Label(self, textvariable=self.v_statusbar)
        self.label_statusbar.grid(row=17, column=0, columnspan=2, sticky='W')


class FileMenu(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)

        self.menubar = tk.Menu(self)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Settings...")
        self.filemenu.add_command(label="Teams...")
        self.filemenu.add_command(label="Info...")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Quit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.connectionmenu = tk.Menu(self.menubar, tearoff=0)
        self.connectionmenu.add_command(label="Login...")
        self.connectionmenu.add_command(label="Logout")
        self.menubar.add_cascade(label="Connection", menu=self.connectionmenu)

        self.master.config(menu=self.menubar)


class MiscWidgets(ttk.Frame):
    """ Class for creating misc widgets

    """
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.v_test = tk.StringVar

        self.cb_testlist = []
        self.cb_testlist.append(ttk.Combobox(self, textvariable=self.v_test, state='readonly'))
        self.cb_testlist.append(ttk.Combobox(self, textvariable=self.v_test, state='readonly'))

        for kk in range(2):
            self.cb_testlist[kk]['values'] = ('Borussia Dortmund', 'Werder Bremen')

        for kk in range(2):
            self.cb_testlist[kk].grid(column=kk, row=kk)

        ttk.Label(self, text="Hi").grid(column=0, row=2)


class MainView(ttk.Frame):
    def __init__(self, master=None, team_array=None):
        """ Create GUI
        """
        ttk.Frame.__init__(self, master)

        self.file_menu = FileMenu(master)
        self.main_widgets = MainWidgets(master, team_array)

        self.main_widgets.grid()


class LoginDialog(tkadd.Dialog):
    """ The login dialog

    """
    def __init__(self, master):
        self._entry_group = None
        self._entry_username = None
        self._entry_password = None

        self.group = None
        self.username = None
        self.password = None

        super().__init__(master, "Login")

    def body(self, master):
        self._entry_group = ttk.Entry(master)
        self._entry_username = ttk.Entry(master)
        self._entry_password = ttk.Entry(master, show="*")

        self._entry_group.insert(0, str(self.group))
        self._entry_username.insert(0, str(self.username))

        ttk.Label(master, text="Group:").grid(row=0)
        ttk.Label(master, text="Username:").grid(row=1)
        ttk.Label(master, text="Password:").grid(row=2)

        self._entry_group.grid(row=0, column=1)
        self._entry_username.grid(row=1, column=1)
        self._entry_password.grid(row=2, column=1)

        return self._entry_group  # initial focus

    def apply(self):
        self.group = self._entry_group.get()
        self.username = self._entry_username.get()
        self.password = self._entry_password.get()


class SettingsDialog(tkadd.Dialog):
    """ The settings dialog

    """
    def __init__(self, master):
        self._entry_mu = None
        self._entry_home_team_advantage = None

        self.mu = None
        self.home_team_advantage = None

        super().__init__(master, "Settings")

    def body(self, master):
        self._entry_mu = ttk.Entry(master)
        self._entry_home_team_advantage = ttk.Entry(master)

        self._entry_mu.insert(0, str(self.mu))
        self._entry_home_team_advantage.insert(0, str(self.home_team_advantage))

        ttk.Label(master, text="Expectation Value:").grid(row=0)
        ttk.Label(master, text="Home Team Advantage:").grid(row=1)

        self._entry_mu.grid(row=0, column=1)
        self._entry_home_team_advantage.grid(row=1, column=1)

        return self._entry_mu  # initial focus

    def apply(self):
        self.mu = self._entry_mu.get()
        self.home_team_advantage = self._entry_home_team_advantage.get()


class TeamSettingsDialog(tkadd.Dialog):
    """ The dialog for the team settings

    """
    def __init__(self, master):
        self._entry_team_names = [""]*18
        self._entry_scored_goals = [0]*18
        self._entry_defense_strengths = [0]*18

        self.team_names = [""]*18
        self.scored_goals = [0]*18
        self.defense_strengths = [0]*18

        super().__init__(master, "Team Settings")

    def body(self, master):
        ttk.Label(master, text="Team").grid(row=0, column=1)
        ttk.Label(master, text="Scored Goals").grid(row=0, column=2)
        ttk.Label(master, text="Defense Strength").grid(row=0, column=3)

        for kk in range(18):
            ttk.Label(master, text=str(kk+1)).grid(row=kk+1, column=0)

            self._entry_team_names[kk] = ttk.Entry(master, width=28)
            self._entry_team_names[kk].insert(0, str(self.team_names[kk]))
            self._entry_team_names[kk].grid(row=kk+1, column=1)

            self._entry_scored_goals[kk] = ttk.Entry(master, width=12)
            self._entry_scored_goals[kk].insert(0, str(self.scored_goals[kk]))
            self._entry_scored_goals[kk].grid(row=kk+1, column=2)

            self._entry_defense_strengths[kk] = ttk.Entry(master, width=12)
            self._entry_defense_strengths[kk].insert(0, str(self.defense_strengths[kk]))
            self._entry_defense_strengths[kk].grid(row=kk+1, column=3)

        return self._entry_team_names[0] # initial focus

    def apply(self):
        for kk in range(18):
            self.team_names[kk] = self._entry_team_names[kk].get()
            self.scored_goals[kk] = self._entry_scored_goals[kk].get()
            self.defense_strengths[kk] = self._entry_defense_strengths[kk].get()

