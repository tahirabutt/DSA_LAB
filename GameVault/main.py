
import sys
import csv
import os
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QTableWidget,
    QTableWidgetItem, QLineEdit, QProgressBar, QHeaderView,
QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


import threading
from scraper import scrape_games

def bubble_sort(values):
    arr = values.copy()
    comparisons = 0
    swaps = 0
    n = len(arr)

    for i in range(n):
        changed = False
        for j in range(0, n - i - 1):
            comparisons += 1
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swaps += 1
                changed = True
        if not changed:
            break

    return arr, comparisons, swaps


def selection_sort(values):
    arr = values.copy()
    comparisons = 0
    swaps = 0

    for i in range(len(arr)):
        minimum = i
        for j in range(i + 1, len(arr)):
            comparisons += 1
            if arr[j] < arr[minimum]:
                minimum = j

        if minimum != i:
            arr[i], arr[minimum] = arr[minimum], arr[i]
            swaps += 1

    return arr, comparisons, swaps


def insertion_sort(values):
    arr = values.copy()
    comparisons = 0
    shifts = 0

    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1

        while j >= 0:
            comparisons += 1
            if arr[j] > key:
                arr[j + 1] = arr[j]
                shifts += 1
                j -= 1
            else:
                break

        arr[j + 1] = key

    return arr, comparisons, shifts


def merge_sort(values):
    comparisons = 0
    moves = 0

    def merge(arr):
        nonlocal comparisons, moves

        if len(arr) <= 1:
            return arr

        middle = len(arr) // 2
        left = merge(arr[:middle])
        right = merge(arr[middle:])

        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            comparisons += 1
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
            moves += 1

        result.extend(left[i:])
        result.extend(right[j:])
        moves += len(left) - i + len(right) - j

        return result

    return merge(values.copy()), comparisons, moves


def quick_sort(values):
    arr = values.copy()
    comparisons = 0
    swaps = 0

    def partition(low, high):
        nonlocal comparisons, swaps
        pivot = arr[high]
        i = low - 1

        for j in range(low, high):
            comparisons += 1
            if arr[j] <= pivot:
                i += 1
                if i != j:
                    arr[i], arr[j] = arr[j], arr[i]
                    swaps += 1

        if i + 1 != high:
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            swaps += 1

        return i + 1

    def sort(low, high):
        if low < high:
            pivot_index = partition(low, high)
            sort(low, pivot_index - 1)
            sort(pivot_index + 1, high)

    sort(0, len(arr) - 1)
    return arr, comparisons, swaps


def heap_sort(values):
    arr = values.copy()
    comparisons = 0
    swaps = 0
    n = len(arr)

    def heapify(size, root):
        nonlocal comparisons, swaps
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2

        if left < size:
            comparisons += 1
            if arr[left] > arr[largest]:
                largest = left

        if right < size:
            comparisons += 1
            if arr[right] > arr[largest]:
                largest = right

        if largest != root:
            arr[root], arr[largest] = arr[largest], arr[root]
            swaps += 1
            heapify(size, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)

    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        swaps += 1
        heapify(end, 0)

    return arr, comparisons, swaps


class ScraperWorker(QThread):
    progress_changed = pyqtSignal(int, int, int)
    status_changed = pyqtSignal(str)
    finished_count = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

    def run(self):
        count = scrape_games(
            progress_callback=self.send_progress,
            status_callback=self.status_changed.emit,
            pause_event=self.pause_event,
            stop_event=self.stop_event
        )
        self.finished_count.emit(count)

    def send_progress(self, current, total, count):
        self.progress_changed.emit(current, total, count)

class GameVault(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GameVault - My Video Game Explorer")
        self.resize(1350, 820)
        self.setMinimumSize(1000, 650)

        self.games = self.load_games()
        print("First 5 games:", self.games[:5]) 
        self.advanced_filter_active = False
        self.advanced_filter_settings = None

        self.setup_ui()
    
    def load_games(self):
        csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "games.csv"
        )

        games = []

        try:
            with open(
                csv_path,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                reader = csv.DictReader(file)

                for row in reader:
                    games.append([
                        row.get("Game Title", "") or "",
                        row.get("Platform", "") or "",
                        str(row.get("Positive Reviews", "") or ""),
                        str(row.get("Negative Reviews", "") or ""),
                        row.get("Publisher", "") or "",
                        row.get("Developer", "") or "",
                        str(row.get("Rating", "") or ""),
                        str(row.get("Price", "") or "")
                    ])

            print(f"Loaded {len(games)} games from games.csv")

        except (OSError, csv.Error) as error:
            print(f"Could not load games.csv: {error}")

        return games


    def setup_ui(self):
        
        # Main background
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # LEFT SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(13)

        logo = QLabel("🎮 GAMEVAULT")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(logo)

        tagline = QLabel("MY VIDEO GAME EXPLORER")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(tagline)

        side_layout.addSpacing(25)

        for name in [
            "🏠  Dashboard",
            "🎮  Game Library",
            "🔎  Search Games",
            "⚡  Sorting Lab",
            "📊  Benchmark Lab",
            "⚙️  Settings"
        ]:
            button = QPushButton(name)
            button.setObjectName("sideButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            side_layout.addWidget(button)

        side_layout.addStretch()

        side_note = QLabel("LEVEL UP YOUR DATA")
        side_note.setObjectName("sideNote")
        side_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(side_note)

        main_layout.addWidget(sidebar)

        # RIGHT CONTENT
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        main_layout.addWidget(content, 1)

        # Header
        header = QHBoxLayout()

        heading_box = QVBoxLayout()

        heading = QLabel("Gaming Dashboard")
        heading.setObjectName("heading")
        heading_box.addWidget(heading)

        subtitle = QLabel(
            "Explore, search and organize your favorite games."
        )
        subtitle.setObjectName("subtitle")
        heading_box.addWidget(subtitle)

        header.addLayout(heading_box)
        header.addStretch()

        project_label = QLabel("✦  PROJECT 01")
        project_label.setObjectName("projectLabel")
        header.addWidget(project_label, alignment=Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(header)

        # STATISTICS CARDS
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        card_data = [
           
("TOTAL GAMES", f"{len(self.games):,}", "🎮", "greenCard"),
            ("PLATFORMS", "12", "🖥️", "cyanCard"),
            ("GENRES", "25+", "⚡", "pinkCard"),
        ]

        for title, value, emoji, style_name in card_data:
            card = QFrame()
            card.setObjectName(style_name)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 14, 18, 14)

            top = QLabel(f"{emoji}  {title}")
            top.setObjectName("cardTitle")

            number = QLabel(value)
            number.setObjectName("cardNumber")

            card_layout.addWidget(top)
            card_layout.addWidget(number)

            cards_layout.addWidget(card)

        content_layout.addLayout(cards_layout)

        # SCRAPING PANEL
        scrape_panel = QFrame()
        scrape_panel.setObjectName("panel")

        scrape_layout = QVBoxLayout(scrape_panel)
        scrape_layout.setContentsMargins(16, 14, 16, 14)
        scrape_layout.setSpacing(10)

        scrape_heading = QLabel("⚡  DATA COLLECTION")
        scrape_heading.setObjectName("sectionHeading")
        scrape_layout.addWidget(scrape_heading)

        scrape_description = QLabel(
            "Control the game-data collection process"
        )
        scrape_description.setObjectName("subtitle")
        scrape_layout.addWidget(scrape_description)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        
        control_buttons = [
            ("▶  START SCRAPING", "startButton"),
            ("Ⅱ  PAUSE", "pauseButton"),
            ("↻  RESUME", "resumeButton"),
            ("■  STOP", "stopButton"),
        ]

        self.start_button = None
        self.pause_button = None
        self.resume_button = None
        self.stop_button = None

        for text, style_name in control_buttons:
            button = QPushButton(text)
            button.setObjectName(style_name)
            button.setMinimumHeight(38)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            if style_name == "startButton":
                self.start_button = button
                button.clicked.connect(self.start_scraping)
            elif style_name == "pauseButton":
                self.pause_button = button
                button.clicked.connect(self.pause_scraping)
            elif style_name == "resumeButton":
                self.resume_button = button
                button.clicked.connect(self.resume_scraping)
            elif style_name == "stopButton":
                self.stop_button = button
                button.clicked.connect(self.stop_scraping)

            controls.addWidget(button)

        scrape_layout.addLayout(controls)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p% completed")
        self.progress.setMinimumHeight(19)
        scrape_layout.addWidget(self.progress)

        content_layout.addWidget(scrape_panel)

        # SEARCH PANEL
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "🔎  Search by title, platform, genre, publisher..."
        )
        self.search_input.setMinimumHeight(42)
        self.search_input.textChanged.connect(self.filter_games)

        search_layout.addWidget(self.search_input, 1)

        self.search_column = QComboBox()
        self.search_column.addItems([
            "All Columns",
            "Game Title",
            "Platform",
            "Positive Reviews",
            "Negative Reviews",
            "Publisher",
            "Developer",
            "Rating",
            "Price"
        ])
        self.search_column.setMinimumHeight(42)
        search_layout.addWidget(self.search_column)

        self.search_mode = QComboBox()
        self.search_mode.addItems([
            "Contains",
            "Starts With",
            "Ends With",
            "Exact Match"
        ])
        self.search_mode.setMinimumHeight(42)
        search_layout.addWidget(self.search_mode)
        self.search_column.currentIndexChanged.connect(
            lambda: self.filter_games(self.search_input.text())
)
        self.search_mode.currentIndexChanged.connect(    
            lambda: self.filter_games(self.search_input.text())
)
        search_button = QPushButton("SEARCH")
        search_button.setObjectName("searchButton")
        search_button.setMinimumHeight(42)
        search_button.clicked.connect(
            lambda: self.filter_games(self.search_input.text())
        )
        search_layout.addWidget(search_button)

        content_layout.addLayout(search_layout)

        # GAME LIBRARY TABLE
        table_heading = QLabel("🎮  GAME LIBRARY")
        table_heading.setObjectName("sectionHeading")
        content_layout.addWidget(table_heading)


        # SORTING CONTROLS
        sorting_layout = QHBoxLayout()
        sorting_layout.setSpacing(10)

        self.sort_column = QComboBox()
        self.sort_column.addItems([
            "Game Title",
            "Platform",
            "Positive Reviews",
            "Negative Reviews",
            "Publisher",
            "Developer",
            "Rating",
            "Price"
        ])
        self.sort_column.setMinimumHeight(38)
        sorting_layout.addWidget(self.sort_column)

        self.sort_algorithm = QComboBox()
        self.sort_algorithm.addItems([
            "Bubble Sort",
            "Selection Sort",
            "Insertion Sort",
            "Merge Sort",
            "Quick Sort",
            "Heap Sort"
        ])
        self.sort_algorithm.setMinimumHeight(38)
        sorting_layout.addWidget(self.sort_algorithm)

        self.sort_button = QPushButton("SORT")
        
        self.benchmark_button = QPushButton("BENCHMARK ALL")
        self.benchmark_button.setObjectName("searchButton")
        self.benchmark_button.setMinimumHeight(38)
        self.benchmark_button.clicked.connect(self.benchmark_sorts)
        sorting_layout.addWidget(self.benchmark_button)

        self.sort_button.setObjectName("searchButton")
        self.sort_button.setMinimumHeight(38)
        sorting_layout.addWidget(self.sort_button)
        self.sort_button.clicked.connect(self.sort_games)
        content_layout.addLayout(sorting_layout)

           
        # MULTI-LEVEL SORTING CONTROLS
        multi_sort_layout = QHBoxLayout()
        multi_sort_layout.setSpacing(10)

        self.second_sort_column = QComboBox()
        self.second_sort_column.addItems([
            "None",
            "Game Title",
            "Platform",
            "Positive Reviews",
            "Negative Reviews",
            "Publisher",
            "Developer",
            "Rating",
            "Price"
        ])
        self.second_sort_column.setMinimumHeight(38)
        multi_sort_layout.addWidget(self.second_sort_column)

        self.multi_sort_button = QPushButton("MULTI-LEVEL SORT")
        self.multi_sort_button.setObjectName("searchButton")
        self.multi_sort_button.setMinimumHeight(38)
        multi_sort_layout.addWidget(self.multi_sort_button)

        content_layout.addLayout(multi_sort_layout)

        self.multi_sort_button.clicked.connect(
            self.multi_level_sort
        )


        # ADVANCED AND / OR / NOT FILTERS
        advanced_filter_layout = QHBoxLayout()
        advanced_filter_layout.setSpacing(8)

        self.filter_column1 = QComboBox()
        self.filter_column1.addItems([
            "Game Title", "Platform", "Positive Reviews",
            "Negative Reviews", "Publisher", "Developer",
            "Rating", "Price"
        ])
        self.filter_column1.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.filter_column1)

        self.filter_value1 = QLineEdit()
        self.filter_value1.setPlaceholderText("First condition")
        self.filter_value1.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.filter_value1)

        self.filter_logic = QComboBox()
        self.filter_logic.addItems(["AND", "OR", "NOT"])
        self.filter_logic.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.filter_logic)

        self.filter_column2 = QComboBox()
        self.filter_column2.addItems([
            "Game Title", "Platform", "Positive Reviews",
            "Negative Reviews", "Publisher", "Developer",
            "Rating", "Price"
        ])
        self.filter_column2.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.filter_column2)

        self.filter_value2 = QLineEdit()
        self.filter_value2.setPlaceholderText("Second condition")
        self.filter_value2.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.filter_value2)

        self.advanced_filter_button = QPushButton("APPLY FILTER")
        self.advanced_filter_button.setObjectName("searchButton")
        self.advanced_filter_button.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.advanced_filter_button)

        self.clear_advanced_filter_button = QPushButton("CLEAR")
        self.clear_advanced_filter_button.setObjectName("searchButton")
        self.clear_advanced_filter_button.setMinimumHeight(38)
        advanced_filter_layout.addWidget(self.clear_advanced_filter_button)

        content_layout.addLayout(advanced_filter_layout)

        self.advanced_filter_button.clicked.connect(
            self.apply_advanced_filter
        )
        self.clear_advanced_filter_button.clicked.connect(
            self.clear_advanced_filter
        )

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Game Title", "Platform", "Positive Reviews",
            "Negative Reviews", "Publisher", "Developer",
            "Rating", "Price"
        ])

        self.table.setRowCount(len(self.games))
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        for row, game in enumerate(self.games):
            for column, value in enumerate(game):
                item = QTableWidgetItem(value)

                if column in (2, 3, 6):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(row, column, item)

        content_layout.addWidget(self.table, 1)

        # STATUS BAR
        self.status_label = QLabel(
            "●  READY  |  Games loaded from CSV: "
            + str(len(self.games))
        )
        self.status_label.setObjectName("statusLabel")
        content_layout.addWidget(self.status_label)

        self.apply_theme()

    
   
    def filter_games(self, text):
        self.apply_all_filters()

    def apply_all_filters(self):
        query = self.search_input.text().strip().lower()
        selected_column = self.search_column.currentIndex() - 1
        mode = self.search_mode.currentText()

        visible_count = 0

        for row in range(self.table.rowCount()):
            search_match = False

            if not query:
                search_match = True
            else:
                if selected_column == -1:
                    columns_to_check = range(self.table.columnCount())
                else:
                    columns_to_check = [selected_column]

                for column in columns_to_check:
                    item = self.table.item(row, column)
                    value = item.text().strip().lower() if item else ""

                    if mode == "Contains" and query in value:
                        search_match = True
                    elif mode == "Starts With" and value.startswith(query):
                        search_match = True
                    elif mode == "Ends With" and value.endswith(query):
                        search_match = True
                    elif mode == "Exact Match" and value == query:
                        search_match = True

                    if search_match:
                        break

            advanced_match = True

            if self.advanced_filter_active and self.advanced_filter_settings:
                column1, value1, logic, column2, value2 = (
                    self.advanced_filter_settings
                )

                item1 = self.table.item(row, column1)
                item2 = self.table.item(row, column2)

                text1 = item1.text().strip().lower() if item1 else ""
                text2 = item2.text().strip().lower() if item2 else ""

                condition1 = value1 in text1
                condition2 = value2 in text2

                if logic == "AND":
                    advanced_match = condition1 and condition2
                elif logic == "OR":
                    advanced_match = condition1 or condition2
                else:
                    advanced_match = condition1 and not condition2

            show_row = search_match and advanced_match
            self.table.setRowHidden(row, not show_row)

            if show_row:
                visible_count += 1

        self.status_label.setText(
            f"● FILTER RESULTS | {visible_count:,} games found"
        )


  
    def apply_advanced_filter(self):
        column1 = self.filter_column1.currentIndex()
        column2 = self.filter_column2.currentIndex()

        value1 = self.filter_value1.text().strip().lower()
        value2 = self.filter_value2.text().strip().lower()
        logic = self.filter_logic.currentText()

        if not value1 or not value2:
            self.status_label.setText(
                "Please enter both filter conditions."
            )
            return

        self.advanced_filter_settings = (
            column1, value1, logic, column2, value2
        )
        self.advanced_filter_active = True

        self.apply_all_filters()
       
    def clear_advanced_filter(self):
        self.filter_value1.clear()
        self.filter_value2.clear()

        self.advanced_filter_active = False
        self.advanced_filter_settings = None

        self.apply_all_filters()



    def multi_level_sort(self):
        first_column = self.sort_column.currentIndex()
        second_column = self.second_sort_column.currentIndex() - 1

        if second_column == -1:
            self.sort_games()
            return

        if first_column == second_column:
            self.status_label.setText(
                "Please select two different sorting columns."
            )
            return

        rows = []

        for row_index in range(self.table.rowCount()):
            if self.table.isRowHidden(row_index):
                continue

            row_data = []

            for column in range(self.table.columnCount()):
                item = self.table.item(row_index, column)
                row_data.append(item.text() if item else "")

            rows.append(row_data)

        numeric_columns = [2, 3, 6, 7]

        def make_key(value, column):
            if column in numeric_columns:
                try:
                    return float(value.replace(",", "").replace("$", ""))
                except ValueError:
                    return 0.0
            return value.lower()

        rows.sort(
            key=lambda row: (
                make_key(row[first_column], first_column),
                make_key(row[second_column], second_column)
            )
        )

        self.table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            for column, value in enumerate(row_data):
                self.table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(value)
                )

        self.status_label.setText(
            f"Multi-level sorting complete: {len(rows):,} games"
        )

    
    def sort_games(self):
        column = self.sort_column.currentIndex()
        algorithm = self.sort_algorithm.currentText()

        rows = []
        for row in range(self.table.rowCount()):
            values = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                values.append(item.text() if item else "")
            rows.append(values)

        def make_key(row):
            value = row[column].strip()
            if column in (2, 3, 6, 7):
                try:
                    return float(value)
                except ValueError:
                    return -1.0
            return value.lower()

        decorated = [(make_key(row), i, row) for i, row in enumerate(rows)]
        values = decorated
        start_time = time.perf_counter()

        if algorithm == "Bubble Sort":
            sorted_values, comparisons, swaps = bubble_sort(values)
        elif algorithm == "Selection Sort":
            sorted_values, comparisons, swaps = selection_sort(values)
        elif algorithm == "Insertion Sort":
            sorted_values, comparisons, swaps = insertion_sort(values)
        elif algorithm == "Merge Sort":
            sorted_values, comparisons, swaps = merge_sort(values)
        elif algorithm == "Quick Sort":
            sorted_values, comparisons, swaps = quick_sort(values)
        else:
            sorted_values, comparisons, swaps = heap_sort(values)

        elapsed = (time.perf_counter() - start_time) * 1000
        sorted_rows = [entry[2] for entry in sorted_values]

        self.table.setRowCount(len(sorted_rows))
        for row_index, row_data in enumerate(sorted_rows):
            for col_index, value in enumerate(row_data):
                self.table.setItem(
                    row_index, col_index, QTableWidgetItem(value)
                )

        self.status_label.setText(
            f"● Sorted by {self.sort_column.currentText()} | "
            f"{algorithm} | Time: {elapsed:.2f} ms | "
            f"Comparisons: {comparisons:,} | Swaps/Moves: {swaps:,}"
        )

    def benchmark_sorts(self):
        column = self.sort_column.currentIndex()

        rows = []
        for row in range(self.table.rowCount()):
            values = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                values.append(item.text() if item else "")
            rows.append(values)

        def make_key(row):
            value = row[column].strip()
            if column in (2, 3, 6, 7):
                try:
                    return float(value)
                except ValueError:
                    return -1.0
            return value.lower()

        
        sample_rows = rows[:500]
        decorated = [
            (make_key(row), i, row)
            for i, row in enumerate(sample_rows)
        ]


        algorithms = [
            ("Bubble Sort", bubble_sort),
            ("Selection Sort", selection_sort),
            ("Insertion Sort", insertion_sort),
            ("Merge Sort", merge_sort),
            ("Quick Sort", quick_sort),
            ("Heap Sort", heap_sort),
        ]

        results = []

        self.benchmark_button.setEnabled(False)
        self.status_label.setText("● Benchmark running...")

        try:
            for name, function in algorithms:
                data = decorated.copy()
                start = time.perf_counter()
                _, comparisons, moves = function(data)
                elapsed = (time.perf_counter() - start) * 1000

                results.append(
                    (name, elapsed, comparisons, moves)
                )

            
            report = "BENCHMARK RESULTS\n\n"

            details = {
                "Bubble Sort": ("O(n²)", "Stable"),
                "Selection Sort": ("O(n²)", "Unstable"),
                "Insertion Sort": ("O(n²)", "Stable"),
                "Merge Sort": ("O(n log n)", "Stable"),
                "Quick Sort": ("Average O(n log n)", "Unstable"),
                "Heap Sort": ("O(n log n)", "Unstable"),
            }

            report += (
                f"{'Algorithm':<18} {'Time (ms)':<12} "
                f"{'Comparisons':<14} {'Swaps/Moves':<13} "
                f"{'Complexity':<22} Stability\n"
            )
            report += "-" * 100 + "\n"

            for name, elapsed, comparisons, moves in results:
                complexity, stability = details[name]
                report += (
                    f"{name:<18} {elapsed:<12.2f} "
                    f"{comparisons:<14,} {moves:<13,} "
                    f"{complexity:<22} {stability}\n"
                )


            
            from PyQt6.QtWidgets import QDialog, QVBoxLayout

            dialog = QDialog(self)
            dialog.setWindowTitle("GameVault - Sorting Benchmark")
            dialog.resize(950, 350)

            layout = QVBoxLayout(dialog)

            heading = QLabel("SORTING ALGORITHM COMPARISON")
            heading.setStyleSheet(
                "font-size: 18px; font-weight: bold; padding: 8px;"
            )
            layout.addWidget(heading)

            result_table = QTableWidget()
            result_table.setColumnCount(6)
            result_table.setHorizontalHeaderLabels([
                "Algorithm",
                "Time (ms)",
                "Comparisons",
                "Swaps / Moves",
                "Time Complexity",
                "Stability"
            ])

            result_table.setRowCount(len(results))

            details = {
                "Bubble Sort": ("O(n²)", "Stable"),
                "Selection Sort": ("O(n²)", "Unstable"),
                "Insertion Sort": ("O(n²)", "Stable"),
                "Merge Sort": ("O(n log n)", "Stable"),
                "Quick Sort": ("Average O(n log n)", "Unstable"),
                "Heap Sort": ("O(n log n)", "Unstable"),
            }

            for row_index, (name, elapsed, comparisons, moves) in enumerate(results):
                complexity, stability = details[name]

                cells = [
                    name,
                    f"{elapsed:.2f}",
                    f"{comparisons:,}",
                    f"{moves:,}",
                    complexity,
                    stability
                ]

                for col_index, value in enumerate(cells):
                    item = QTableWidgetItem(value)
                    item.setFlags(
                        item.flags()
                        & ~Qt.ItemFlag.ItemIsEditable
                    )
                    result_table.setItem(
                        row_index, col_index, item
                    )

            result_table.setAlternatingRowColors(True)
            result_table.setSortingEnabled(True)
            result_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )

            layout.addWidget(result_table)

            close_button = QPushButton("CLOSE")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.exec()


            self.status_label.setText(
                "● Benchmark completed successfully."
            )

        finally:
            self.benchmark_button.setEnabled(True)

    def start_scraping(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.status_label.setText("●  Scraping is already running.")
            return

        self.worker = ScraperWorker()
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.status_changed.connect(self.update_scrape_status)
        self.worker.finished_count.connect(self.scraping_finished)

        self.progress.setRange(0, 20)
        self.progress.setValue(0)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(True)
        self.stop_button.setEnabled(True)

        self.worker.start()
        self.status_label.setText("●  Scraping started.")

    def pause_scraping(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.pause_event.set()
            self.status_label.setText("●  Scraping paused.")

    def resume_scraping(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.pause_event.clear()
            self.status_label.setText("●  Scraping resumed.")

    def stop_scraping(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop_event.set()
            self.worker.pause_event.clear()
            self.status_label.setText("●  Stopping scraping...")

    def update_progress(self, current, total, count):
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.progress.setFormat(
            f"Page {current}/{total} | {count:,} games collected"
        )

    def update_scrape_status(self, message):
        self.status_label.setText("●  " + message)

    def scraping_finished(self, count):
        self.start_button.setEnabled(True)
        self.progress.setFormat(
            f"Scraping finished | {count:,} games saved"
        )
        self.status_label.setText(
            f"●  SCRAPING COMPLETE | {count:,} games saved"
        )

        self.games = self.load_games()
        self.table.setRowCount(len(self.games))

        for row, game in enumerate(self.games):
            for column, value in enumerate(game):
                item = QTableWidgetItem(value)
                if column in (2, 3, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

        self.status_label.setText(
            f"●  SCRAPING COMPLETE | {len(self.games):,} games loaded"
        )


    def apply_theme(self):
        self.setStyleSheet("""
            QWidget#central {
                background-color: #2949A8;
                color: #FFFFFF;
                font-family: Segoe UI;
                font-size: 12px;
            }

            QFrame#sidebar {
                background-color: #5933A5;
                border: 2px solid #8B5CF6;
                border-radius: 18px;
            }

            QLabel#logo {
                color: #65FFB7;
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#tagline {
                color: #D8C9FF;
                font-size: 9px;
                font-weight: bold;
            }

            QPushButton#sideButton {
                background-color: #6945B8;
                color: white;
                border: 1px solid #8E70D9;
                border-radius: 9px;
                padding: 12px 8px;
                text-align: left;
                font-size: 12px;
            }

            QPushButton#sideButton:hover {
                background-color: #8058DC;
                border: 1px solid #65FFB7;
            }

            QLabel#sideNote {
                color: #65FFB7;
                font-size: 10px;
                font-weight: bold;
            }

            QLabel#heading {
                color: #FFFFFF;
                font-size: 27px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #D8E5FF;
                font-size: 11px;
            }

            QLabel#projectLabel {
                background-color: #FF477E;
                color: white;
                padding: 9px 12px;
                border-radius: 9px;
                font-weight: bold;
            }

            QFrame#greenCard {
                background-color: #147A62;
                border: 2px solid #65FFB7;
                border-radius: 13px;
            }

            QFrame#cyanCard {
                background-color: #126B99;
                border: 2px solid #47DFFF;
                border-radius: 13px;
            }

            QFrame#pinkCard {
                background-color: #963D8A;
                border: 2px solid #FF70D4;
                border-radius: 13px;
            }

            QLabel#cardTitle {
                color: #FFFFFF;
                font-size: 11px;
                font-weight: bold;
            }

            QLabel#cardNumber {
                color: #FFFFFF;
                font-size: 25px;
                font-weight: bold;
            }

            QFrame#panel {
                background-color: #3558B7;
                border: 1px solid #7393EE;
                border-radius: 13px;
            }

            QLabel#sectionHeading {
                color: #65FFB7;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton#startButton {
                background-color: #65FFB7;
                color: #163B49;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton#pauseButton {
                background-color: #925BFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton#resumeButton {
                background-color: #38CFFF;
                color: #173957;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton#stopButton {
                background-color: #FF4848;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton#startButton:hover,
            QPushButton#pauseButton:hover,
            QPushButton#resumeButton:hover,
            QPushButton#stopButton:hover {
                border: 2px solid white;
            }

            QLineEdit {
                background-color: #E7F8FF;
                color: #243B78;
                border: 2px solid #47DFFF;
                border-radius: 9px;
                padding: 10px;
                font-size: 12px;
            }

            QPushButton#searchButton {
                background-color: #FF70D4;
                color: #412052;
                border: none;
                border-radius: 9px;
                padding: 10px 20px;
                font-weight: bold;
            }

            QTableWidget {
                background-color: #EAF3FF;
                alternate-background-color: #D7E7FF;
                color: #20376D;
                border: 2px solid #8B5CF6;
                border-radius: 9px;
                gridline-color: #B7C8F0;
                selection-background-color: #773CE0;
                selection-color: white;
            }

            QHeaderView::section {
                background-color: #773CE0;
                color: white;
                padding: 10px 5px;
                border: 1px solid #9B7AE8;
                font-weight: bold;
            }

            QLabel#statusLabel {
                background-color: #1D367E;
                color: #65FFB7;
                border: 1px solid #4F72D4;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }

            QProgressBar {
                background-color: #DCE8FF;
                color: #20376D;
                border: 1px solid #65FFB7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #65FFB7;
                border-radius: 7px;
            }

            QScrollBar:vertical {
                background-color: #D7E7FF;
                width: 12px;
            }

            QScrollBar::handle:vertical {
                background-color: #773CE0;
                border-radius: 5px;
                min-height: 25px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameVault()
    window.show()
    sys.exit(app.exec())
