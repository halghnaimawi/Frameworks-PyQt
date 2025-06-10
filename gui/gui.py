import csv
import logging
import sqlite3
import sys
from datetime import datetime

import matplotlib.pyplot as plt
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QTextCharFormat, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMessageBox,
                             QLineEdit, QTableWidget, QTableWidgetItem, QDateEdit, QFileDialog)
from PyQt6.uic import loadUi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from config import DB_PATH
from design_pattern.repository.repository import ProjectManagementRepository


class ProjectManagementGUI(QMainWindow):
    """
    A PyQt6-based GUI class for managing project-related data (Tasks, Milestones, Persons).
    Provides a user interface with tables, dialogs, and a Gantt chart for CRUD operations and data visualization.
    """

    def __init__(self):
        """
        Initialize the main window, set up the repository, and configure the UI.

        Sets the window title, size, and initializes the database repository and logger.
        """
        super().__init__()
        self.setWindowTitle("Project Management System")  # Set the window title
        self.setGeometry(100, 100, 1000, 600)  # Set window position and size
        self.repository = ProjectManagementRepository(DB_PATH)  # Initialize repository with database path
        self.logger = logging.getLogger(__name__)  # Configure logger
        self.init_ui()  # Set up UI components
        self.load_initial_window()  # Load initial window content

    def init_ui(self):
        """
        Set up the UI by loading the main window layout and connecting signals to slots.

        Loads the UI from a .ui file and connects buttons and input fields to their respective methods.
        Initializes tables and the Gantt chart.
        """
        loadUi("gui/main_window.ui", self)  # Load UI from file
        # Connect main bar
        self.searchBox.textChanged.connect(self.search_active_tab)  # Connect search box to filter active tab
        # Connect tasks tab actions
        self.tasksAddButton.clicked.connect(self.open_create_task_dialog)  # Add task button
        self.tasksUpdateButton.clicked.connect(self.open_update_task_dialog)  # Update task button
        self.tasksDeleteButton.clicked.connect(self.delete_task)  # Delete task button
        self.tasksExportButton.clicked.connect(self.export_tasks_to_csv)  # Export tasks button
        self.tasksFilterBox.textChanged.connect(self.filter_tasks)  # Task filter input
        # Connect milestones tab actions
        self.milestonesAddButton.clicked.connect(self.open_create_milestone_dialog)  # Add milestone button
        self.milestonesUpdateButton.clicked.connect(self.open_update_milestone_dialog)  # Update milestone button
        self.milestonesDeleteButton.clicked.connect(self.delete_milestone)  # Delete milestone button
        self.milestonesFilterBox.textChanged.connect(self.filter_milestones)  # Milestone filter input
        # Connect people tab actions
        self.peopleAddButton.clicked.connect(self.open_create_person_dialog)  # Add person button
        self.peopleUpdateButton.clicked.connect(self.open_update_person_dialog)  # Update person button
        self.peopleDeleteButton.clicked.connect(self.delete_person)  # Delete person button
        self.peopleFilterBox.textChanged.connect(self.filter_people)  # Person filter input
        self.milestonesCalendar.clicked.connect(self.show_milestone_details)
        # Initialize tables
        self.setup_tables()  # Configure table widgets
        # Initialize Gantt chart
        self.setup_gantt_chart()  # Set up Gantt chart visualization

    def setup_tables(self):
        """
        Configure the structure and properties of the Tasks, Milestones, and People tables.

        Sets column counts, headers, and selection behavior for each table.
        """
        # Tasks table
        self.tasksTable.setColumnCount(7)  # Set 7 columns for task data
        self.tasksTable.setHorizontalHeaderLabels(
            ["ID", "Title", "Status", "Priority", "Start Date", "Due Date", "Assigned Person"])  # Set column headers
        self.tasksTable.setColumnHidden(0, True)  # Hide ID column
        self.tasksTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Select entire rows
        self.tasksTable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)  # Allow single row selection
        self.tasksTable.horizontalHeader().setStretchLastSection(True)  # Stretch last column to fill space
        # Milestones table
        self.milestonesTable.setColumnCount(2)  # Set 2 columns for milestone data
        self.milestonesTable.setHorizontalHeaderLabels(["ID", "Name"])  # Set column headers
        self.milestonesTable.setColumnHidden(0, True)  # Hide ID column
        self.milestonesTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Select entire rows
        self.milestonesTable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)  # Allow single row selection
        self.milestonesTable.horizontalHeader().setStretchLastSection(True)  # Stretch last column to fill space
        # People table
        self.peopleTable.setColumnCount(4)  # Set 4 columns for person data
        self.peopleTable.setHorizontalHeaderLabels(["ID", "Name", "Email", "Role"])  # Set column headers
        self.peopleTable.setColumnHidden(0, True)  # Hide ID column
        self.peopleTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Select entire rows
        self.peopleTable.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)  # Allow single row selection
        self.peopleTable.horizontalHeader().setStretchLastSection(True)  # Stretch last column to fill space

    def setup_gantt_chart(self):
        """
        Initialize the matplotlib-based Gantt chart canvas and add it to the UI layout.
        """
        # Create matplotlib figure and canvas
        self.figure, self.ax = plt.subplots(figsize=(8, 4))  # Create figure with specified size
        self.canvas = FigureCanvas(self.figure)  # Create canvas for rendering the chart
        # Add canvas to the existing ganttChartLayout
        self.ganttChartLayout.addWidget(self.canvas)  # Add canvas to UI layout
        self.figure.tight_layout()  # Adjust layout to fit
        self.refresh_gantt_chart()  # Populate the chart with initial data

    def refresh_gantt_chart(self):
        """
        Refresh the Gantt chart with the latest task data.

        Displays tasks as horizontal bars based on start and due dates. Shows a message if no tasks are available.

        Raises:
            sqlite3.Error: If a database error occurs.
            Exception: For other unexpected errors.
        """
        try:
            self.ax.clear()  # Clear previous chart content
            tasks = self.repository.get_all_tasks()  # Fetch all tasks
            if not tasks:
                # Display message if no tasks are available
                self.ax.text(0.5, 0.5, "No tasks available", horizontalalignment='center', verticalalignment='center',
                             transform=self.ax.transAxes)
                self.ax.set_axis_off()  # Hide axes
                self.canvas.draw()  # Redraw canvas
                self.logger.info("No tasks to display in Gantt chart")
                return

            y_positions = range(len(tasks))  # Y positions for tasks
            for i, task in enumerate(tasks):
                try:
                    start_date = datetime.strptime(task.start_date, '%Y-%m-%d')  # Parse start date
                    due_date = datetime.strptime(task.due_date, '%Y-%m-%d')  # Parse due date
                    duration = (due_date - start_date).days  # Calculate task duration
                    # Plot task as a horizontal bar
                    self.ax.barh(i, duration, left=start_date, height=0.4, align='center', color='#3498db')
                    # Add task title next to bar
                    self.ax.text(start_date, i, task.title, va='center', ha='left', color='black', fontsize=8)
                except ValueError as ve:
                    self.logger.error(f"Invalid date format for task {task.title}: {ve}")
                    continue
            self.ax.set_yticks(y_positions)  # Set y-axis ticks
            self.ax.set_yticklabels([task.title for task in tasks])  # Set y-axis labels
            self.ax.set_xlabel('Date')  # Set x-axis label
            self.ax.set_ylabel('Tasks')  # Set y-axis label
            self.ax.set_title('Gantt Chart')  # Set chart title
            self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)  # Add grid
            self.figure.autofmt_xdate()  # Rotate date labels
            self.figure.tight_layout()  # Adjust layout
            self.canvas.draw()  # Redraw canvas
            self.logger.info("Refreshed Gantt chart")
        except (sqlite3.Error, Exception) as e:
            self.logger.error(f"Error refreshing Gantt chart: {e}")
            self.show_error(f"Error refreshing Gantt chart: {e}")

    def load_initial_window(self):
        """
        Load the initial state of the main window.

        Shows the content tabs and refreshes all tables.

        Raises:
            sqlite3.Error: If a database error occurs during loading.
        """
        try:
            self.contentTabs.setVisible(True)  # Show content tabs
            self.refresh_all_tabs()  # Refresh all tables
            self.logger.info(f"Loaded Tasks")
        except sqlite3.Error as e:
            self.show_error(f"Error loading tasks: {e}")

    def refresh_all_tabs(self):
        """
        Refresh all tables (Tasks, Milestones, People) and the Gantt chart.
        """
        self.refresh_tasks_table()  # Refresh tasks table
        self.refresh_milestones_table()  # Refresh milestones table
        self.refresh_people_table()  # Refresh people table
        self.refresh_gantt_chart()  # Refresh Gantt chart

    def refresh_tasks_table(self, filter_text=""):
        """
        Refresh the tasks table with the latest data, optionally filtered by title.

        Args:
            filter_text (str): Text to filter tasks by title (default: "").

        Raises:
            sqlite3.Error: If a database error occurs.
            LookupError: If a person lookup fails.
        """
        try:
            self.tasksTable.setRowCount(0)  # Clear existing rows
            tasks = self.repository.get_all_tasks()  # Fetch all tasks
            for task in tasks:
                person = self.repository.get_person(task.person_id)  # Get assigned person
                if filter_text.lower() not in task.title.lower():  # Apply filter
                    continue
                row = self.tasksTable.rowCount()
                self.tasksTable.insertRow(row)  # Add new row
                # Populate table with task data
                self.tasksTable.setItem(row, 0, QTableWidgetItem(str(task.id)))
                self.tasksTable.setItem(row, 1, QTableWidgetItem(task.title))
                self.tasksTable.setItem(row, 2, QTableWidgetItem(task.status))
                self.tasksTable.setItem(row, 3, QTableWidgetItem(task.priority))
                self.tasksTable.setItem(row, 4, QTableWidgetItem(task.start_date))
                self.tasksTable.setItem(row, 5, QTableWidgetItem(task.due_date))
                self.tasksTable.setItem(row, 6, QTableWidgetItem(person.name))
            self.logger.info(f"Refreshed tasks table")
        except (sqlite3.Error, LookupError) as e:
            self.show_error(f"Error refreshing tasks: {e}")

    def refresh_milestones_table(self, filter_text=""):
        """
        Refresh the milestones table with the latest data, optionally filtered by name.

        Args:
            filter_text (str): Text to filter milestones by name (default: "").

        Raises:
            sqlite3.Error: If a database error occurs.
            LookupError: If a milestone lookup fails.
        """
        try:
            self.milestonesTable.setRowCount(0)  # Clear existing rows
            milestones = self.repository.get_all_milestones()  # Fetch all milestones
            for milestone in milestones:
                if filter_text.lower() not in milestone.name.lower():  # Apply filter
                    continue
                row = self.milestonesTable.rowCount()
                self.milestonesTable.insertRow(row)  # Add new row
                # Populate table with milestone data
                self.milestonesTable.setItem(row, 0, QTableWidgetItem(str(milestone.id)))
                self.milestonesTable.setItem(row, 1, QTableWidgetItem(milestone.name))
            self.refresh_milestones_calendar(filter_text)
            self.logger.info(f"Refreshed milestones table")
        except (sqlite3.Error, LookupError) as e:
            self.show_error(f"Error refreshing milestones: {e}")

    def refresh_people_table(self, filter_text=""):
        """
        Refresh the people table with the latest data, optionally filtered by name.

        Args:
            filter_text (str): Text to filter persons by name (default: "").

        Raises:
            sqlite3.Error: If a database error occurs.
            LookupError: If a person lookup fails.
        """
        try:
            self.peopleTable.setRowCount(0)  # Clear existing rows
            people = self.repository.get_all_persons()  # Fetch all persons
            for person in people:
                if filter_text.lower() not in person.name.lower():  # Apply filter
                    continue
                row = self.peopleTable.rowCount()
                self.peopleTable.insertRow(row)  # Add new row
                # Populate table with person data
                self.peopleTable.setItem(row, 0, QTableWidgetItem(str(person.id)))
                self.peopleTable.setItem(row, 1, QTableWidgetItem(person.name))
                self.peopleTable.setItem(row, 2, QTableWidgetItem(person.email))
                self.peopleTable.setItem(row, 3, QTableWidgetItem(person.role))
            self.logger.info(f"Refreshed people table")
        except (sqlite3.Error, LookupError) as e:
            self.show_error(f"Error refreshing people: {e}")

    def show_people(self):
        """
        Display the people tab and refresh its table.
        """
        self.refresh_people_table()  # Refresh people table
        self.contentTabs.setCurrentWidget(self.peopleTab)  # Switch to people tab
        self.logger.info("Clicked People menu item")

    def search_active_tab(self, text):
        """
        Filter the active tab's table based on the search text.

        Args:
            text (str): Search text to filter the active tab's content.
        """
        current_tab = self.contentTabs.currentWidget()  # Get current tab
        if current_tab == self.tasksTab:
            self.filter_tasks(text)  # Filter tasks
        elif current_tab == self.milestonesTab:
            self.filter_milestones(text)  # Filter milestones
        elif current_tab == self.peopleTab:
            self.filter_people(text)  # Filter people

    def filter_tasks(self, text):
        """
        Filter the tasks table based on the provided text.

        Args:
            text (str): Text to filter tasks by title.
        """
        self.refresh_tasks_table(text)  # Refresh tasks table with filter

    def filter_milestones(self, text):
        """
        Filter the milestones table based on the provided text.

        Args:
            text (str): Text to filter milestones by name.
        """
        self.refresh_milestones_table(text)  # Refresh milestones table with filter

    def filter_people(self, text):
        """
        Filter the people table based on the provided text.

        Args:
            text (str): Text to filter persons by name.
        """
        self.refresh_people_table(text)  # Refresh people table with filter

    def open_create_task_dialog(self):
        """
        Open a dialog to create a new task.

        Collects task details and adds the task to the database.

        Raises:
            ValueError: If required fields are missing.
            sqlite3.Error: If a database error occurs.
            LookupError: If a referenced person or milestone is invalid.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Task")
        layout = QFormLayout(dialog)

        # Create input fields
        title_input = QLineEdit()
        description_input = QLineEdit()
        status_input = QComboBox()
        status_input.addItems(["ToDo", "InProgress", "Done"])  # Add status options
        priority_input = QComboBox()
        priority_input.addItems(["High", "Medium", "Low"])  # Add priority options
        start_date_input = QDateEdit()
        start_date_input.setCalendarPopup(True)
        start_date_input.setDisplayFormat("yyyy-MM-dd")  # Set date format
        start_date_input.setDate(QDate.currentDate())  # Default to current date
        due_date_input = QDateEdit()
        due_date_input.setCalendarPopup(True)
        due_date_input.setDisplayFormat("yyyy-MM-dd")  # Set date format
        due_date_input.setDate(QDate.currentDate())  # Default to current date
        person_id_input = QComboBox()
        people = self.repository.get_all_persons()  # Fetch all persons
        for person in people:
            person_id_input.addItem(f"{person.id}: {person.name}", person.id)  # Add person options
        milestone_id_input = QComboBox()
        milestone_id_input.addItem("None", None)  # Add None option for milestone
        milestones = self.repository.get_all_milestones()  # Fetch all milestones
        for milestone in milestones:
            milestone_id_input.addItem(f"{milestone.id}: {milestone.name}", milestone.id)  # Add milestone options

        # Add fields to layout
        layout.addRow("Title:", title_input)
        layout.addRow("Description:", description_input)
        layout.addRow("Status:", status_input)
        layout.addRow("Priority:", priority_input)
        layout.addRow("Start Date:", start_date_input)
        layout.addRow("Due Date:", due_date_input)
        layout.addRow("Assigned Person:", person_id_input)
        layout.addRow("Milestone (Optional):", milestone_id_input)

        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            try:
                # Retrieve input values
                title = title_input.text()
                description = description_input.text()
                status = status_input.currentText()
                priority = priority_input.currentText()
                start_date = start_date_input.date().toString("yyyy-MM-dd")
                due_date = due_date_input.date().toString("yyyy-MM-dd")
                person_id = person_id_input.currentData()
                milestone_id = milestone_id_input.currentData()

                # Validate required fields
                if not (title and status and priority and start_date and due_date and person_id):
                    raise ValueError("Title, Status, Priority, Start Date, Due Date, and Assigned Person are required")

                # Add task to database
                self.repository.add_task(
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    start_date=start_date,
                    due_date=due_date,
                    person_id=int(person_id),
                    milestone_id=milestone_id
                )
                self.refresh_tasks_table()  # Refresh tasks table
                self.refresh_gantt_chart()  # Refresh Gantt chart
                self.logger.info(f"Created task: {title}")
            except (ValueError, sqlite3.Error, LookupError) as e:
                self.show_error(f"Error creating task: {e}")

    def open_update_task_dialog(self):
        """
        Open a dialog to update an existing task.

        Loads the selected task's data into input fields and updates the task in the database.

        Raises:
            ValueError: If required fields are missing.
            sqlite3.Error: If a database error occurs.
            LookupError: If the task or referenced entities are invalid.
        """
        selected = self.tasksTable.selectedItems()
        if not selected:
            self.show_error("Please select a task to update.")
            return
        task_id = int(self.tasksTable.item(selected[0].row(), 0).text())
        try:
            task = self.repository.get_task(task_id)  # Fetch task by ID
            dialog = QDialog(self)
            dialog.setWindowTitle("Update Task")
            layout = QFormLayout(dialog)

            # Create input fields with current task data
            title_input = QLineEdit(task.title)
            description_input = QLineEdit(task.description)
            status_input = QComboBox()
            status_input.addItems(["ToDo", "InProgress", "Done"])
            status_input.setCurrentText(task.status)  # Set current status
            priority_input = QComboBox()
            priority_input.addItems(["High", "Medium", "Low"])
            priority_input.setCurrentText(task.priority)  # Set current priority
            start_date_input = QDateEdit()
            start_date_input.setCalendarPopup(True)
            start_date_input.setDisplayFormat("yyyy-MM-dd")
            start_date_input.setDate(QDate.fromString(task.start_date, "yyyy-MM-dd"))  # Set current start date
            due_date_input = QDateEdit()
            due_date_input.setCalendarPopup(True)
            due_date_input.setDisplayFormat("yyyy-MM-dd")
            due_date_input.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))  # Set current due date
            person_id_input = QComboBox()
            people = self.repository.get_all_persons()
            for person in people:
                person_id_input.addItem(f"{person.id}: {person.name}", person.id)
            person_id_input.setCurrentText(f"{task.person_id}: {self.repository.get_person(task.person_id).name}")  # Set current person
            milestone_id_input = QComboBox()
            milestone_id_input.addItem("None", None)
            milestones = self.repository.get_all_milestones()
            for milestone in milestones:
                milestone_id_input.addItem(f"{milestone.id}: {milestone.name}", milestone.id)
            if task.milestone_id:
                milestone_id_input.setCurrentText(
                    f"{task.milestone_id}: {self.repository.get_milestone(task.milestone_id).name}")  # Set current milestone

            # Add fields to layout
            layout.addRow("Title:", title_input)
            layout.addRow("Description:", description_input)
            layout.addRow("Status:", status_input)
            layout.addRow("Priority:", priority_input)
            layout.addRow("Start Date:", start_date_input)
            layout.addRow("Due Date:", due_date_input)
            layout.addRow("Assigned Person:", person_id_input)
            layout.addRow("Milestone (Optional):", milestone_id_input)

            # Add OK/Cancel buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)

            if dialog.exec():
                # Retrieve input values
                title = title_input.text()
                description = description_input.text()
                status = status_input.currentText()
                priority = priority_input.currentText()
                start_date = start_date_input.date().toString("yyyy-MM-dd")
                due_date = due_date_input.date().toString("yyyy-MM-dd")
                person_id = person_id_input.currentData()
                milestone_id = milestone_id_input.currentData()

                # Validate required fields
                if not (title and status and priority and start_date and due_date and person_id):
                    raise ValueError("Title, Status, Priority, Start Date, Due Date, and Assigned Person are required")

                # Update task in database
                self.repository.update_task(
                    task_id=task_id,
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    start_date=start_date,
                    due_date=due_date,
                    person_id=int(person_id),
                    milestone_id=milestone_id
                )
                self.refresh_tasks_table()  # Refresh tasks table
                self.refresh_gantt_chart()  # Refresh Gantt chart
                self.refresh_milestones_calendar()  # Refresh milestones calendar to update highlights
                self.logger.info(f"Updated task ID: {task_id}")
        except (ValueError, sqlite3.Error, LookupError) as e:
            self.show_error(f"Error updating task: {e}")

    def delete_task(self):
        """
        Delete the selected task from the database.

        Raises:
            sqlite3.Error: If a database error occurs.
        """
        selected = self.tasksTable.selectedItems()
        if not selected:
            self.show_error("Please select a task to delete.")
            return
        task_id = int(self.tasksTable.item(selected[0].row(), 0).text())
        try:
            self.repository.delete_task(task_id)  # Delete task
            self.refresh_tasks_table()  # Refresh tasks table
            self.refresh_gantt_chart()  # Refresh Gantt chart
            self.logger.info(f"Deleted task ID: {task_id}")
        except sqlite3.Error as e:
            self.show_error(f"Error deleting task: {e}")

    def export_tasks_to_csv(self):
        """
        Export all tasks to a CSV file.

        Opens a file dialog to select the output file and writes task data to it.

        Raises:
            sqlite3.Error: If a database error occurs.
            IOError: If a file operation error occurs.
        """
        try:
            # Show file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV",
                "tasks_export.csv",
                "CSV Files (*.csv);;All Files (*)"
            )

            # If user cancels the dialog
            if not file_path:
                return

            tasks = self.repository.get_all_tasks()  # Fetch all tasks
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write CSV header
                writer.writerow(
                    ["ID", "Title", "Description", "Status", "Priority", "Start Date", "Due Date", "Assigned Person",
                     "Milestone"])
                for task in tasks:
                    person = self.repository.get_person(task.person_id)  # Get assigned person
                    # Get milestone name or "None"
                    milestone_name = self.repository.get_milestone(
                        task.milestone_id).name if task.milestone_id else "None"
                    # Write task data to CSV
                    writer.writerow([
                        task.id,
                        task.title,
                        task.description,
                        task.status,
                        task.priority,
                        task.start_date,
                        task.due_date,
                        person.name,
                        milestone_name
                    ])

            self.logger.info(f"Exported tasks to {file_path}")
            QMessageBox.information(self, "Success", f"Tasks exported to:\n{file_path}")
        except (sqlite3.Error, IOError) as e:
            self.show_error(f"Error exporting tasks: {e}")

    def open_create_milestone_dialog(self):
        """
        Open a dialog to create a new milestone.

        Collects milestone name and adds it to the database.

        Raises:
            ValueError: If the name is missing.
            sqlite3.Error: If a database error occurs.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Milestone")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()

        layout.addRow("Name:", name_input)

        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            try:
                name = name_input.text()
                if not name:
                    raise ValueError("Name is required")
                self.repository.add_milestone(name)  # Add milestone to database
                self.refresh_milestones_table()  # Refresh milestones table
                self.logger.info(f"Created milestone: {name}")
            except (ValueError, sqlite3.Error) as e:
                self.show_error(f"Error creating milestone: {e}")

    def open_update_milestone_dialog(self):
        """
        Open a dialog to update an existing milestone.

        Loads the selected milestone's data and updates it in the database.

        Raises:
            ValueError: If the name is missing.
            sqlite3.Error: If a database error occurs.
            LookupError: If the milestone is invalid.
        """
        selected = self.milestonesTable.selectedItems()
        if not selected:
            self.show_error("Please select a milestone to update.")
            return
        milestone_id = int(self.milestonesTable.item(selected[0].row(), 0).text())
        try:
            milestone = self.repository.get_milestone(milestone_id)  # Fetch milestone by ID
            dialog = QDialog(self)
            dialog.setWindowTitle("Update Milestone")
            layout = QFormLayout(dialog)

            name_input = QLineEdit(milestone.name)

            layout.addRow("Name:", name_input)

            # Add OK/Cancel buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)

            if dialog.exec():
                name = name_input.text()
                if not name:
                    raise ValueError("Name is required")
                self.repository.update_milestone(milestone_id, name=name)  # Update milestone
                self.refresh_milestones_table()  # Refresh milestones table
                self.logger.info(f"Updated milestone ID: {milestone_id}")
        except (ValueError, sqlite3.Error, LookupError) as e:
            self.show_error(f"Error updating milestone: {e}")

    def delete_milestone(self):
        """
        Delete the selected milestone from the database.

        Raises:
            sqlite3.Error: If a database error occurs.
        """
        selected = self.milestonesTable.selectedItems()
        if not selected:
            self.show_error("Please select a milestone to delete.")
            return
        milestone_id = int(self.milestonesTable.item(selected[0].row(), 0).text())
        try:
            self.repository.delete_milestone(milestone_id)  # Delete milestone
            self.refresh_milestones_table()  # Refresh milestones table
            self.logger.info(f"Deleted milestone ID: {milestone_id}")
        except sqlite3.Error as e:
            self.show_error(f"Error deleting milestone: {e}")

    def open_create_person_dialog(self):
        """
        Open a dialog to create a new person.

        Collects person details and adds them to the database.

        Raises:
            ValueError: If required fields are missing.
            sqlite3.Error: If a database error occurs.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Person")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        email_input = QLineEdit()
        role_input = QLineEdit()
        role_input.setPlaceholderText("e.g., Developer, Manager")  # Set placeholder for role

        # Add fields to layout
        layout.addRow("Name:", name_input)
        layout.addRow("Email:", email_input)
        layout.addRow("Role:", role_input)

        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            try:
                name = name_input.text()
                email = email_input.text()
                role = role_input.text()
                if not (name and email):
                    raise ValueError("Name and Email are required")
                self.repository.add_person(name, email, role)  # Add person to database
                self.refresh_people_table()  # Refresh people table
                self.logger.info(f"Created person: {name}")
            except (ValueError, sqlite3.Error) as e:
                self.show_error(f"Error creating person: {e}")

    def open_update_person_dialog(self):
        """
        Open a dialog to update an existing person.

        Loads the selected person's data and updates it in the database.

        Raises:
            ValueError: If required fields are missing.
            sqlite3.Error: If a database error occurs.
            LookupError: If the person is invalid.
        """
        selected = self.peopleTable.selectedItems()
        if not selected:
            self.show_error("Please select a person to update.")
            return
        person_id = int(self.peopleTable.item(selected[0].row(), 0).text())
        try:
            person = self.repository.get_person(person_id)  # Fetch person by ID
            dialog = QDialog(self)
            dialog.setWindowTitle("Update Person")
            layout = QFormLayout(dialog)

            name_input = QLineEdit(person.name)
            email_input = QLineEdit(person.email)
            role_input = QLineEdit(person.role if hasattr(person, 'role') else "")  # Handle optional role
            role_input.setPlaceholderText("e.g., Developer, Manager")  # Set placeholder for role

            # Add fields to layout
            layout.addRow("Name:", name_input)
            layout.addRow("Email:", email_input)
            layout.addRow("Role:", role_input)

            # Add OK/Cancel buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)

            if dialog.exec():
                name = name_input.text()
                email = email_input.text()
                role = role_input.text()
                if not (name and email):
                    raise ValueError("Name and Email are required")
                self.repository.update_person(person_id, name, email, role)  # Update person
                self.refresh_people_table()  # Refresh people table
                self.logger.info(f"Updated person ID: {person_id}")
        except (ValueError, sqlite3.Error, LookupError) as e:
            self.show_error(f"Error updating person: {e}")

    def delete_person(self):
        """
        Delete the selected person from the database.

        Raises:
            sqlite3.Error: If a database error occurs.
        """
        selected = self.peopleTable.selectedItems()
        if not selected:
            self.show_error("Please select a person to delete.")
            return
        person_id = int(self.peopleTable.item(selected[0].row(), 0).text())
        try:
            self.repository.delete_person(person_id)  # Delete person
            self.refresh_people_table()  # Refresh people table
            self.logger.info(f"Deleted person ID: {person_id}")
        except sqlite3.Error as e:
            self.show_error(f"Error deleting person: {e}")

    def show_error(self, message):
        """
        Display an error message in a dialog and log it.

        Args:
            message (str): Error message to display.
        """
        self.logger.error(message)
        QMessageBox.critical(self, "Error", str(message))  # Show error dialog

    def refresh_milestones_calendar(self, filter_text=""):
        """
        Refresh the milestones calendar with the latest data, optionally filtered by name.

        Highlights dates with milestones and adds tooltips with milestone names.

        Args:
            filter_text (str): Text to filter milestones by name (default: "").

        Raises:
            sqlite3.Error: If a database error occurs.
            LookupError: If a milestone lookup fails.
        """
        try:
            # Clear existing formats by applying a default QTextCharFormat
            default_format = QTextCharFormat()
            self.milestonesCalendar.setDateTextFormat(QDate(), default_format)

            tasks = self.repository.get_all_tasks()
            date_formats = {}
            for task in tasks:
                if task.milestone_id:
                    milestone = self.repository.get_milestone(task.milestone_id)
                    if filter_text.lower() not in milestone.name.lower():
                        continue
                    start_date = QDate.fromString(task.start_date, "yyyy-MM-dd")
                    due_date = QDate.fromString(task.due_date, "yyyy-MM-dd")
                    current_date = start_date
                    while current_date <= due_date:
                        format = QTextCharFormat()
                        format.setBackground(QColor("#3498db"))
                        format.setForeground(QColor("#ffffff"))
                        format.setToolTip(f"Milestone: {milestone.name}\nTask: {task.title}")
                        date_formats[current_date] = format
                        current_date = current_date.addDays(1)

            # Apply formats to calendar
            for date, format in date_formats.items():
                self.milestonesCalendar.setDateTextFormat(date, format)

            self.logger.info("Refreshed milestones calendar")
        except (sqlite3.Error, LookupError) as e:
            self.show_error(f"Error refreshing milestones calendar: {e}")
    def show_milestone_details(self, date):
        """
        Display details of milestones associated with the selected date in a dialog.

        Args:
            date (QDate): The date selected in the milestonesCalendar.

        Raises:
            sqlite3.Error: If a database error occurs.
            LookupError: If a milestone lookup fails.
        """
        try:
            selected_date = date.toString("yyyy-MM-dd")
            tasks = self.repository.get_all_tasks()
            milestones_on_date = []

            # Find tasks with milestones that fall on the selected date
            for task in tasks:
                if task.milestone_id:
                    task_start = QDate.fromString(task.start_date, "yyyy-MM-dd")
                    task_due = QDate.fromString(task.due_date, "yyyy-MM-dd")
                    if task_start <= date <= task_due:
                        milestone = self.repository.get_milestone(task.milestone_id)
                        milestones_on_date.append((milestone.name, task.title))

            if not milestones_on_date:
                QMessageBox.information(self, "Milestone Details", f"No milestones on {selected_date}")
                return

            # Format milestone details
            details = f"Milestones on {selected_date}:\n\n"
            for milestone_name, task_title in milestones_on_date:
                details += f"Milestone: {milestone_name}\nAssociated Task: {task_title}\n\n"

            # Show details in a dialog
            QMessageBox.information(self, "Milestone Details", details)
            self.logger.info(f"Displayed milestone details for date: {selected_date}")
        except (sqlite3.Error, LookupError) as e:
            self.show_error(f"Error displaying milestone details: {e}")


def run_gui():
    """
    Launch the Project Management GUI application.

    Initializes the QApplication, creates the main window, and starts the event loop.
    """
    app = QApplication(sys.argv)  # Create application instance
    window = ProjectManagementGUI()  # Create main window
    window.show()  # Show the window
    sys.exit(app.exec())  # Start event loop and exit with application status



