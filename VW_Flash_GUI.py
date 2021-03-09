import glob
import wx
import os.path as path
import logging
from datetime import datetime

from lib import simos_uds
from lib import simos_flash_utils
from lib import constants

# Get an instance of logger, which we'll pull from the config file
logger = logging.getLogger("VWFlash")

try:
    currentPath = path.dirname(path.abspath(__file__))
except NameError:  # We are the main py2exe script, not a module
    currentPath = path.dirname(path.abspath(sys.argv[0]))

logging.config.fileConfig(path.join(currentPath, "logging.conf"))

logger.info("Starting VW_Flash.py")


def read_from_file(infile=None):
    f = open(infile, "rb")
    return f.read()


class FlashPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create a drop down menu
        flash_actions = ["Calibration only", "Full flash"]
        self.action_choice = wx.Choice(self, choices=flash_actions)
        self.action_choice.SetSelection(0)

        # Create a button for choosing the folder
        self.folder_button = wx.Button(self, label="Open Folder")
        self.folder_button.Bind(wx.EVT_BUTTON, self.GetParent().on_open_folder)

        middle_sizer.Add(self.action_choice, 0, wx.EXPAND | wx.ALL, 5)
        middle_sizer.Add(self.folder_button, 0, wx.ALL | wx.RIGHT, 5)

        self.progress_bar = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)

        self.row_obj_dict = {}

        self.list_ctrl = wx.ListCtrl(
            self, size=(-1, 250), style=wx.LC_REPORT | wx.BORDER_SUNKEN
        )
        self.list_ctrl.InsertColumn(0, "Filename", width=400)
        self.list_ctrl.InsertColumn(1, "Modify time", width=100)

        self.feedback_text = wx.TextCtrl(
            self, size=(-1, 300), style=wx.TE_READONLY | wx.TE_LEFT | wx.TE_MULTILINE
        )

        edit_button = wx.Button(self, label="Flash")
        edit_button.Bind(wx.EVT_BUTTON, self.on_flash)

        get_info_button = wx.Button(self, label="Get Ecu Info")
        get_info_button.Bind(wx.EVT_BUTTON, self.on_get_info)

        bottom_sizer.Add(get_info_button, 0, wx.ALL | wx.CENTER, 5)
        bottom_sizer.Add(edit_button, 0, wx.ALL | wx.CENTER, 5)

        main_sizer.Add(self.feedback_text, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(middle_sizer)
        main_sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.progress_bar, 0, wx.EXPAND, 5)
        main_sizer.Add(bottom_sizer)
        self.SetSizer(main_sizer)

    def on_get_info(self, event):
        ecu_info = simos_uds.read_ecu_data(
            interface="J2534", callback=self.update_callback
        )

        [
            self.feedback_text.AppendText(did + " : " + ecu_info[did] + "\n")
            for did in ecu_info
        ]

    # def on_folder_choice(self, event):
    #    ecu_info = simos_uds.read_ecu_data(
    #        interface="J2534", callback=self.update_callback
    #    )

    #    [
    #        self.feedback_text.AppendText(did + " : " + ecu_info[did] + "\n")
    #        for did in ecu_info
    #    ]

    def on_flash(self, event):
        selected_file = self.list_ctrl.GetFirstSelected()

        if selected_file == -1:
            print("Select a file to flash")
        else:
            self.blocks_infile = {}
            self.blocks_infile[self.row_obj_dict[selected_file]] = {
                "blocknum": 5,
                "binary_data": read_from_file(self.row_obj_dict[selected_file]),
            }

            self.flash_bin()

    def update_bin_listing(self, folder_path):
        self.current_folder_path = folder_path
        self.list_ctrl.ClearAll()

        self.list_ctrl.InsertColumn(0, "Filename", width=500)
        self.list_ctrl.InsertColumn(1, "Modify Time", width=140)

        bins = glob.glob(folder_path + "/*.bin")
        bins.sort(key=path.getmtime, reverse=True)

        bin_objects = []
        index = 0
        for bin_file in bins:
            self.list_ctrl.InsertItem(index, path.basename(bin_file))
            self.list_ctrl.SetItem(
                index,
                1,
                str(
                    datetime.fromtimestamp(path.getmtime(bin_file)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ),
            )

            bin_objects.append(bin_file)
            self.row_obj_dict[index] = bin_file
            index += 1

    def update_callback(self, flasher_step, flasher_status, flasher_progress):
        self.GetParent().statusbar.SetStatusText(flasher_step)
        self.progress_bar.SetValue(float(flasher_progress))
        self.feedback_text.AppendText(flasher_status + "\n")

    def flash_bin(self):

        ecu_info = simos_uds.read_ecu_data(
            interface="J2534", callback=self.update_callback
        )

        [
            self.feedback_text.AppendText(did + " : " + ecu_info[did] + "\n")
            for did in ecu_info
        ]

        for filename in self.blocks_infile:
            logger.info(
                "Executing flash_bin with the following blocks:\n"
                + "\n".join(
                    [
                        " : ".join(
                            [
                                filename,
                                str(self.blocks_infile[filename]["blocknum"]),
                                constants.int_to_block_name[
                                    self.blocks_infile[filename]["blocknum"]
                                ],
                                str(
                                    self.blocks_infile[filename]["binary_data"][
                                        constants.software_version_location[
                                            self.blocks_infile[filename]["blocknum"]
                                        ][0] : constants.software_version_location[
                                            self.blocks_infile[filename]["blocknum"]
                                        ][
                                            1
                                        ]
                                    ].decode()
                                ),
                                str(
                                    self.blocks_infile[filename]["binary_data"][
                                        constants.box_code_location[
                                            self.blocks_infile[filename]["blocknum"]
                                        ][0] : constants.box_code_location[
                                            self.blocks_infile[filename]["blocknum"]
                                        ][
                                            1
                                        ]
                                    ].decode()
                                ),
                            ]
                        )
                        for filename in self.blocks_infile
                    ]
                )
            )

        for filename in self.blocks_infile:
            fileBoxCode = str(
                self.blocks_infile[filename]["binary_data"][
                    constants.box_code_location[
                        self.blocks_infile[filename]["blocknum"]
                    ][0] : constants.box_code_location[
                        self.blocks_infile[filename]["blocknum"]
                    ][
                        1
                    ]
                ].decode()
            )

            if ecu_info["VW Spare Part Number"].strip() != fileBoxCode:
                self.feedback_text.AppendText(
                    "Attempting to flash a file that doesn't match box codes, exiting!: "
                    + ecu_info["VW Spare Part Number"]
                    + " != "
                    + fileBoxCode
                    + "\n"
                )
            else:

                simos_flash_utils.flash_bin(
                    self.blocks_infile, self.update_callback, interface="J2534"
                )


class VW_Flash_Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="VW_Flash GUI", size=(640, 750))
        self.create_menu()
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText("Choose a bin file directory")
        self.panel = FlashPanel(self)
        self.Show()

    def create_menu(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        open_folder_menu_item = file_menu.Append(
            wx.ID_ANY, "Open Folder", "Open a folder with bins"
        )
        menu_bar.Append(file_menu, "&File")
        self.Bind(
            event=wx.EVT_MENU,
            handler=self.on_open_folder,
            source=open_folder_menu_item,
        )
        self.SetMenuBar(menu_bar)

    def on_open_folder(self, event):
        title = "Choose a directory:"
        dlg = wx.DirDialog(self, title, style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.panel.update_bin_listing(dlg.GetPath())
        dlg.Destroy()


if __name__ == "__main__":
    app = wx.App(False)
    frame = VW_Flash_Frame()
    app.MainLoop()