# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk


class Dialog(tk.Toplevel):
    """ A Dialog
    Adapted from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm

    Example usage:

    class MyDialog(Dialog):

        def body(self, master):

            ttk.Label(master, text="First:").grid(row=0)
            ttk.Label(master, text="Second:").grid(row=1)

            self.e1 = ttk.Entry(master)
            self.e2 = ttk.Entry(master)

            self.e1.grid(row=0, column=1)
            self.e2.grid(row=1, column=1)
            return self.e1 # initial focus

        def apply(self):
            first = int(self.e1.get())
            second = int(self.e2.get())
            print(first, second) # or something
    """

    def __init__(self, parent, title=None):
        #pass
        self.mytitle = title
        #self.title = title
        self.result = None
        self.canceled = False

    def show(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)

        if self.mytitle:
            self.title(self.mytitle)

        self.parent = parent

        body = ttk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)



    #
    # construction hooks

    def body(self, master):
        """ create dialog body.  return widget that should have initial focus. this method should be overridden.

        """
        pass

    def buttonbox(self):
        """ Add standard button box (OK, Cancel). Override if you don't want the standard buttons

        """

        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics (ok, cancel)
    def ok(self, event=None):
        """ Semantics for the OK Button

        """

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.parent.focus_set()
        self.destroy()

    def cancel(self, event=None):
        """ Semantics for the Cancel Button

        """

        self.canceled = True
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        """ Is called before the dialog is removed after OK has been pressed. This method should be overridden.

        Usage: if we carry out some potentially lengthy processing in the apply method,
        it would be very confusing if the dialog wasn’t removed before we finished.
        """

        return 1 # override

    def apply(self):
        """ Is called when "OK" is pressed (see def ok). This method should be overridden.

        """
        pass # override
