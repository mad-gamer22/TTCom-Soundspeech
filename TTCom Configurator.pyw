import wx
import os
import configparser

class ServerConfigApp(wx.Frame):
    def __init__(self, parent, title):
        super(ServerConfigApp, self).__init__(parent, title=title, size=(600, 400))

        # Define the configuration file
        self.config_file = 'ttcom.conf'
        self.config = configparser.ConfigParser()

        self.panel = wx.Panel(self)
        self.server_list = wx.ListCtrl(self.panel, style=wx.LC_REPORT)
        self.server_list.InsertColumn(0, 'Server Shortname', width=400)

        add_btn = wx.Button(self.panel, label='Add Server')
        edit_btn = wx.Button(self.panel, label='Edit Server')
        remove_btn = wx.Button(self.panel, label='Remove Server')

        add_btn.Bind(wx.EVT_BUTTON, self.add_server)
        edit_btn.Bind(wx.EVT_BUTTON, self.edit_server)
        remove_btn.Bind(wx.EVT_BUTTON, self.remove_server)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(add_btn, 0, wx.ALL, 5)
        btn_sizer.Add(edit_btn, 0, wx.ALL, 5)
        btn_sizer.Add(remove_btn, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.server_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        self.panel.SetSizer(main_sizer)
        self.Centre()

        # Check if the config file exists and handle accordingly
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                self.load_servers()
                self.Show()  # Show the main window only if config file exists
            except configparser.Error:
                wx.MessageBox("Error reading the configuration file.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            # File doesn't exist, open the add server window directly and close if cancelled
            self.initial_add_server()

    def load_servers(self):
        self.server_list.DeleteAllItems()
        for section in self.config.sections():
            if section.startswith('server ') and section != 'server defaults':
                shortname = section.split(' ', 1)[1]
                self.server_list.InsertItem(self.server_list.GetItemCount(), shortname)

    def initial_add_server(self):
        # Hide the main window since it's not initialized with data
        self.Hide()
        dlg = ServerFrame(self, "Add Server", initial=True)
        dlg.Show()

    def add_server(self, event):
        dlg = ServerFrame(self, "Add Server")
        dlg.Bind(wx.EVT_CLOSE, self.on_server_frame_close)
        self.Hide()  # Hide the main window
        dlg.Show()

    def edit_server(self, event):
        selected = self.server_list.GetFirstSelected()
        if selected >= 0:
            shortname = self.server_list.GetItemText(selected, 0)
            section = f'server {shortname}'
            current_details = {
                'host': self.config.get(section, 'host', fallback=''),
                'tcpport': self.config.get(section, 'tcpport', fallback=''),
                'username': self.config.get(section, 'username', fallback=''),
                'password': self.config.get(section, 'password', fallback=''),
                'channel': self.config.get(section, 'channel', fallback=''),
            }
            dlg = ServerFrame(self, "Edit Server", current_details, shortname)
            dlg.Bind(wx.EVT_CLOSE, self.on_server_frame_close)
            self.Hide()  # Hide the main window
            dlg.Show()

    def remove_server(self, event):
        selected = self.server_list.GetFirstSelected()
        if selected >= 0:
            shortname = self.server_list.GetItemText(selected, 0)
            section = f'server {shortname}'
            self.config.remove_section(section)
            self.save_changes()
            self.load_servers()

    def save_changes(self):
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        except IOError:
            wx.MessageBox("Could not save the configuration file.", "Error", wx.OK | wx.ICON_ERROR)

    def on_server_frame_close(self, event):
        self.Show()  # Show the main window again
        self.load_servers()
        self.server_list.SetFocus()
        event.GetEventObject().Destroy()

class ServerFrame(wx.Frame):
    def __init__(self, parent, title, current_details=None, shortname=None, initial=False):
        super(ServerFrame, self).__init__(parent, title=title, size=(400, 350))

        self.parent = parent
        self.initial = initial
        self.shortname_value = shortname
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Input fields
        self.shortname = self.create_input_row("Server Shortname", shortname if shortname else "")
        self.host = self.create_input_row("Host", current_details.get('host') if current_details else "")
        self.tcpport = self.create_input_row("TCP Port", current_details.get('tcpport') if current_details else "")
        self.username = self.create_input_row("Username", current_details.get('username') if current_details else "")
        self.password = self.create_input_row("Password", current_details.get('password') if current_details else "")
        self.channel = self.create_input_row("Channel", current_details.get('channel') if current_details else "")

        # OK and Cancel buttons
        btn_panel = wx.Panel(self.panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(btn_panel, label='OK')
        cancel_btn = wx.Button(btn_panel, label='Cancel')
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        btn_panel.SetSizer(btn_sizer)
        self.sizer.Add(btn_panel, 0, wx.ALIGN_CENTER)

        self.panel.SetSizer(self.sizer)
        self.Layout()

        # Set initial focus to the first text control
        self.shortname.SetFocus()

    def create_input_row(self, label, value=""):
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(self.panel, label=label, size=(100, -1))
        txt = wx.TextCtrl(self.panel, value=value, size=(250, -1))
        row_sizer.Add(lbl, 0, wx.ALL, 5)
        row_sizer.Add(txt, 1, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(row_sizer, 0, wx.EXPAND)
        return txt

    def on_ok(self, event):
        new_shortname = self.shortname.GetValue().strip()
        new_details = {
            'host': self.host.GetValue().strip(),
            'tcpport': self.tcpport.GetValue().strip(),
            'username': self.username.GetValue().strip(),
            'password': self.password.GetValue().strip(),
            'channel': self.channel.GetValue().strip(),
        }

        if all(new_details.values()) and new_shortname:
            section = f'server {new_shortname}'
            # Add new server or edit existing one:
            if section not in self.parent.config:
                self.parent.config.add_section(section)

            for key, value in new_details.items():
                self.parent.config.set(section, key, value)

            self.parent.save_changes()  # Save immediately after adding/editing
        else:
            wx.MessageBox("All fields must be filled out.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self.Close()

    def on_cancel(self, event):
        if self.initial:
            wx.Exit()  # Exit the application if the initial server addition is cancelled
        else:
            self.Close()

if __name__ == '__main__':
    app = wx.App(False)
    frame = ServerConfigApp(None, "Server Configuration")
    app.MainLoop()