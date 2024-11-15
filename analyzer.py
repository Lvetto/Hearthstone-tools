from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QApplication, QMainWindow,
    QLabel, QHBoxLayout, QHeaderView, QFileDialog, QSplitter
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QPixmap, QAction
from PySide6.QtCore import Qt
import sys
import re
import os
from datetime import datetime
from bisect import bisect_right
from itertools import groupby

from parser_lib import Parser

class Packet:
    def __init__(self, timestamp, ptype, content):
        self.timestamp = timestamp
        self.ptype = ptype
        self.content = content
    
    def print_contents(self):
        # Generate more readable strings from the packet data

        command = self.content[0]
        out_str = command#f"Command '{command}' not implemented!"

        if (command == "CREATE_GAME"):
            pass
            #out_str = f"{command}"
        
        elif (command == "FULL_ENTITY"):
            type = self.content[1]
            inline_tags_list = self.content[2]
            other_tags_list = self.content[3]

            command_type = f"{command}: {type}\t"
            inline_tags = "\n".join([f"{i[0]}={i[1]}" for i in inline_tags_list])

            pairs = list(zip(other_tags_list[::2], other_tags_list[1::2]))
            pairs = [(i[0][1], i[1][1]) for i in pairs]

            other_tags = "\n".join([f"{i[0]} = {i[1]}" for i in pairs])

            out_str = f"{command_type}\n{"-"*20}\n{inline_tags}\n{"-"*20}\n{other_tags}"
        
        elif (command == "TAG_CHANGE"):
            entity_info = self.content[1][:-2]
            changed_tags_list = self.content[1][-2:]

            command_type = f"{command}"
            entity = "\n".join([f"{i[0]}={i[1]}" for i in entity_info])
            changed_tags = f"{changed_tags_list[0][1]} = {changed_tags_list[1][1]}"

            out_str = f"{command_type}\n{"-"*20}\n{entity}\n{"-"*20}\n{changed_tags}"
        
        elif (command == "BLOCK_START") or (command == "BLOCK_END"):
            out_str = f"{command}"

        return out_str


def create_packet_objs(text):
    r"""out = []
    for line in lines:
        # remove extra whitespaces
        line = line.strip()

        try:
            # recognise different parts of the packet
            timestamp = re.findall(r"\b\d{1,2}:\d{2}:\d{2}\.\d{1,7}\b", line)[0]    # timestamp is a bunch of numbers with colons, we can just use a regex
            ptype = re.findall(r'\s+([A-Za-z0-9]+)\.([A-Za-z0-9]+)\(\)\s+', line)[0]    # a more complex regex, but same thing
            ptype = ".".join(ptype) # and we then need to join the various parts
            content = line.split("-")[1:]   # the content comes after a - symbol
            content = " ".join(content) # and also needs to be joined in case there are more -s in the string

            # make the packet object and append it to the output list
            p = Packet(timestamp, ptype, content)
            out.append(p)

        # IndexErrors are caught as they usually are related to invalid packets, so we should be able to safely skip them
        except IndexError:
            pass"""

    parser = Parser()
    packet_data = parser.parse_str(text).as_list()

    out = []

    for packet in packet_data:
        p = Packet(packet[1], packet[2], packet[3:])
        out.append(p)


    return out

def convert_ts(ts):
    return datetime.strptime(ts[:-1], '%H:%M:%S.%f').time()

def search_timeslot(target, available_timestamps):
    # Binary search using bisect
    index = bisect_right(available_timestamps, target)

    # Check if the result is valid, otherwise return -1
    if index < len(available_timestamps):
        return index
    else:
        return -1

def group_timestamps(timestamps, slots):
    t = groupby(timestamps, lambda x: search_timeslot(x, slots))
    return t

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set initial size for the window
        self.resize(1000, 600)

        # Set window title
        self.setWindowTitle("Visualizzatore Log e Screenshot")

        # Create a widget to be used as a container for ui elements and add it in the middle of the screen
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a splitter
        splitter = QSplitter(Qt.Horizontal)

        # Log widget
        self.packets = []
        self.log_widget = LogWidget(self.packets)
        self.log_widget.parent_window = self
        splitter.addWidget(self.log_widget)

        # Image display area
        self.image_label = QLabel("Select a package to view the image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: white;")
        splitter.addWidget(self.image_label)

        # Set the splitter as the central widget's layout
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        central_widget.setLayout(layout)

        # Connect the selection event
        #self.log_widget.list_widget.itemClicked.connect(self.on_package_selected)

        # Initialize screenshot folder (optional default)
        self.screenshot_folder = ""

        # Create a menu bar
        menu_bar = self.menuBar()

        # Add 'File' menu
        file_menu = menu_bar.addMenu('File')

        # 'Open Log File' action
        open_log_action = QAction('Open Log File', self)
        open_log_action.triggered.connect(self.open_log_file)
        file_menu.addAction(open_log_action)

        # 'Select Screenshot Folder' action
        select_folder_action = QAction('Select Screenshot Folder', self)
        select_folder_action.triggered.connect(self.select_screenshot_folder)
        file_menu.addAction(select_folder_action)

        # must be initialized to avoid a crash when opening a log file before a screenshot folder
        self.available_times = []

    def on_packet_selected(self, selected_time):        
        if (self.screenshot_folder and self.available_timestamps):
            i = search_timeslot(selected_time, self.available_times)

            self.pixmap = QPixmap(f"{self.screenshot_folder}/{self.available_timestamps[i]}")

            self.scaled_pixmap = self.pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
            )
            self.image_label.setPixmap(self.scaled_pixmap)

    def open_log_file(self):
        # Open a file dialog to select the log file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Log File",
            "",
            "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            # Parse the log file and update the package list
            self.parse_log_file(file_path)
            self.log_widget.update_packets(self.packets)
    
    def parse_log_file(self, filepath):
        with open(filepath, "r") as file:
            #lines = file.readlines()
            text = file.read()
        packets = create_packet_objs(text)
        self.packets = packets

    def select_screenshot_folder(self):
        # Open a dialog to select the screenshot folder
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Screenshot Folder",
            ""
        )
        if folder_path:
            self.screenshot_folder = folder_path
            self.available_timestamps = os.listdir(self.screenshot_folder)
            self.available_timestamps = sorted(self.available_timestamps)
            self.available_times = [datetime.strptime(ts.split(".")[0][11:], '%Y-%m-%d_%H-%M-%S').time() for ts in self.available_timestamps]
            if (self.packets != []):
                self.log_widget.update_packets(self.packets)

class LogWidget(QWidget):
    def __init__(self, packets=None):
        super().__init__()

        # Set background color
        self.setStyleSheet("background-color: white;")

        # Initialize and set central layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a QTableView
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Create a QStandardItemModel with 3 columns: Timestamp, Type, Content
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Timestamp', 'Type', 'Content'])
        self.table_view.setModel(self.model)

        # Set relative widths for columns (e.g., Timestamp: 1, Type: 1, Content: 3)
        header = self.table_view.horizontalHeader()

        # First two columns can be manually resized, the last stretches to fill the space
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        header.resizeSection(0, 150)  # Set Timestamp column to 150 pixels
        header.resizeSection(1, 200)  # Set Type column to 200 pixels



        #header.setSectionResizeMode(QHeaderView.Stretch)

        # Connect selection signal
        self.table_view.selectionModel().currentRowChanged.connect(self.on_row_selected)
        #selection_model = self.table_view.selectionModel()
        #selection_model.selectionChanged.connect(self.on_selection_changed)

        if packets:
            self.update_packets(packets)

    def update_packets(self, packets):
        # Clear existing data
        self.model.removeRows(0, self.model.rowCount())

        # if timeslots are available, keep track of a few variables for the highlighting process
        if (len(self.parent_window.available_times) > 0):
            cols = [(100, 100, 100, 100), (200, 200, 200, 100)]
            ci = 0
            cts = search_timeslot(convert_ts(packets[0].timestamp), self.parent_window.available_times)

        for packet in packets:
            # Create items for each column
            timestamp_item = QStandardItem(packet.timestamp)
            type_item = QStandardItem(packet.ptype)
            content_item = QStandardItem(packet.print_contents())

            # Set text colors
            timestamp_item.setForeground(QColor('green'))
            type_item.setForeground(QColor('blue'))
            content_item.setForeground(QColor('black'))

            # Disable editing for each item
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
            timestamp_item.setFlags(flags)
            type_item.setFlags(flags)
            content_item.setFlags(flags)

            # if timeslots are available, do the highlighting
            if (len(self.parent_window.available_times) > 0):
                ts = search_timeslot(convert_ts(packet.timestamp), self.parent_window.available_times)

                if (ts != cts):
                    ci += 1
                    ci %= 2
                    cts = ts
        
                timestamp_item.setBackground(QColor(*cols[ci]))
                type_item.setBackground(QColor(*cols[ci]))
                content_item.setBackground(QColor(*cols[ci]))

            # Add items to the model
            self.model.appendRow([timestamp_item, type_item, content_item])

        # Allow wordrapping and adjust horizontal size to match
        self.table_view.setWordWrap(True)
        self.table_view.resizeRowsToContents()

    def on_row_selected(self, index):
        # Get the selected packet
        row = index.row()
        if (row < 0):
            return
        packet = self.get_packet_from_row(row)
        if packet and (packet.timestamp != ""):
            selected_time = datetime.strptime(packet.timestamp[:-1], '%H:%M:%S.%f').time()
            self.parent_window.on_packet_selected(selected_time)

    def get_packet_from_row(self, row):
        # Retrieve packet data from the model
        try:
            timestamp = self.model.item(row, 0).text()
            packet_type = self.model.item(row, 1).text()
            content = self.model.item(row, 2).text()
            return Packet(timestamp, packet_type, content)
        except AttributeError:
            return Packet("", "", "")


# run the application if the code is ran as main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
