import os
import take_imgs
import norm_img
import inference
import threading
import csv
from tkinter import *
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
from tkinter import ttk, Toplevel, Frame, Label, Entry, Checkbutton, Button
from tkinter import messagebox
from tkinter.constants import END
from tkinter.filedialog import asksaveasfilename
import datetime
from tkcalendar import Calendar
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import Toplevel, Label, Button
from take_imgs import takeImages
import datetime


recognition_thread = None
recognition_active = False

FONT_REGULAR = ('Segoe UI', 12)
FONT_BOLD = ('Segoe UI', 12, 'bold')
FONT_HIGHLIGHT = ('Segoe UI', 14, 'bold')
PRIMARY_COLOR = "#008080"
SECONDARY_COLOR = "#2E86C1"
DANGER_COLOR = "#E74C3C"
TEXT_COLOR = "#ffffff"


def center_window(window, width, height):
    # Center the window on the screen
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def create_main_window():
    # Create the main window
    root = Tk()
    root.title("EduFusionX : Attendance System")

    icon_image = PhotoImage(file='logopanel.png')
    root.iconphoto(False, icon_image)

    # Set the color scheme
    root.configure(bg="#B6E1E7")

    # Define the style for the buttons
    style = ttk.Style()
    style.configure('TButton', font=('Segoe UI', 10), borderwidth='4')
    style.map('TButton', foreground=[('active', '!disabled', 'green')], background=[('active', 'black')])

    # Set the color scheme
    primary_color = "#3498db"  # This should be your brand's primary color
    secondary_color = "#2E86C1"  # A slightly different shade for the hover effect
    danger_color = "#E74C3C"  # For the 'Exit' button
    text_color = "#ffffff"  # White text color for better contrast

    # Configure the default style for buttons
    style.configure('TButton', font=('Segoe UI', 12, 'bold'), borderwidth=1, relief='flat', padding=6, background=primary_color, foreground=text_color)
    style.map('TButton',
              foreground=[('pressed', text_color), ('active', text_color)],
              background=[('pressed', '!disabled', secondary_color), ('active', secondary_color)])

    # Define a special style for the 'Recognize Faces' button
    style.configure('Important.TButton', font=('Segoe UI', 14, 'bold'), borderwidth=1, relief='flat', padding=8, background=primary_color, foreground=text_color)
    style.map('Important.TButton',
              foreground=[('pressed', text_color), ('active', text_color)],
              background=[('pressed', '!disabled', secondary_color), ('active', secondary_color)])

    # Define a special style for the exit button
    style.configure('Danger.TButton', font=('Segoe UI', 12, 'bold'), borderwidth=1, relief='flat', padding=6, background=danger_color, foreground=text_color)
    style.map('Danger.TButton',
              foreground=[('pressed', text_color), ('active', text_color)],
              background=[('pressed', '!disabled', danger_color), ('active', danger_color)])

    # Create a 1x2 grid layout
    root.grid_columnconfigure(0, weight=1)  # Left panel (resizable)
    root.grid_columnconfigure(1, weight=1)  # Right panel (resizable)
    root.grid_rowconfigure(0, weight=1)

    # Create the company name and logo on the left side
    company_frame = Frame(root, bg="#B6E1E7")
    company_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)  # Increased the right padding
    company_frame.grid_rowconfigure(0, weight=1)
    company_frame.grid_columnconfigure(0, weight=1)

    # Add your company logo here
    logo = Image.open("company_logo.png")  # Replace 'your_logo.png' with your logo file path
    # Define new width and height
    new_width = 800  # or any size you want
    new_height = 800  # or any size you want
    # Resize the image
    logo = logo.resize((new_width, new_height), Image.LANCZOS)
    logo_image = ImageTk.PhotoImage(logo)
    company_logo_label = Label(company_frame, image=logo_image, bg="#B6E1E7")
    company_logo_label.grid(row=0, column=0, sticky="n")

    # Create the main panel on the right side
    main_frame = Frame(root, bg="#FAF9F6")
    main_frame.grid(row=0, column=1, sticky="nsew", padx=(80, 20), pady=20)  # Decreased the left padding
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    # Set the dimensions for the main window
    main_window_width = 1700
    main_window_height = 800
    center_window(root, main_window_width, main_window_height)  # Center the window on the screen

    def view_attendance():
        root.withdraw()  # Hide the main window
        view_attendance_window = Toplevel(main_frame)
        view_attendance_window.title("View Attendance")
        center_window(view_attendance_window, 1250, 800)
        view_attendance_window.configure(bg="#B6E1E7")

        # Create a frame for selection options
        selection_frame = Frame(view_attendance_window, bg=PRIMARY_COLOR)
        selection_frame.pack(fill='x', pady=20, padx=20)

        def calculate_attendance_rates(csv_file_path):
            df = pd.read_csv(csv_file_path)
            total_students = len(df)
            present_students = len(df[df['Status'] == 'Present'])
            absent_students = total_students - present_students
            present_rate = (present_students / total_students) * 100
            absent_rate = (absent_students / total_students) * 100
            return present_rate, absent_rate

        # Create a frame for statistics
        stats_frame = Frame(view_attendance_window, bg=PRIMARY_COLOR)
        stats_frame.pack(fill='x', pady=10, padx=20)  # Adjust padding as needed

        # Add labels for statistics within the stats_frame
        total_label = Label(stats_frame, text="Total Students: ", bg=PRIMARY_COLOR, fg=TEXT_COLOR, font=FONT_REGULAR)
        total_label.grid(row=0, column=0, padx=10, pady=10)

        present_label = Label(stats_frame, text="Present: ", bg=PRIMARY_COLOR, fg=TEXT_COLOR, font=FONT_REGULAR)
        present_label.grid(row=0, column=1, padx=10, pady=10)

        absent_label = Label(stats_frame, text="Absent: ", bg=PRIMARY_COLOR, fg=TEXT_COLOR, font=FONT_REGULAR)
        absent_label.grid(row=0, column=2, padx=10, pady=10)

        def clear_existing_chart():
            for widget in selection_frame.winfo_children():
                if isinstance(widget, FigureCanvasTkAgg):
                    widget.get_tk_widget().destroy()
            selection_frame.update()  # Update the frame to reflect changes

        def load_attendance_preview():
            # Clear the Treeview
            for item in attendance_tree.get_children():
                attendance_tree.delete(item)

            clear_existing_chart()

            selected_program = program_combobox.get()
            selected_date = cal.selection_get()
            if not selected_program or not selected_date:
                messagebox.showerror("Error", "Please select both a program and a date.")
                return

            formatted_date = selected_date.strftime('%d_%m_%Y')
            csv_file_name = f'attendanceList-{formatted_date}.csv'
            base_folder = 'Attendance_records'
            program_folder = os.path.join(base_folder, selected_program)
            csv_file_path = os.path.join(program_folder, csv_file_name)

            if os.path.isfile(csv_file_path):
                df = pd.read_csv(csv_file_path)

                total_students = len(df)
                present_students = len(df[df['Status'] == 'Present'])
                absent_students = total_students - present_students

                total_label.config(text=f"Total Students: {total_students}")
                present_label.config(text=f"Present: {present_students}")
                absent_label.config(text=f"Absent: {absent_students}")

                # Sort the DataFrame by the 'Status' column
                df.sort_values(by='Status', ascending=False, inplace=True)
                for index, row in df.iterrows():
                    attendance_tree.insert('', 'end', values=list(row))

                present_rate, absent_rate = calculate_attendance_rates(csv_file_path)
                fig, ax = plt.subplots(figsize=(3, 3))

                # Define colors and donut shape
                colors = ['green', 'red']
                wedgeprops = {'width': 0.3}

                ax.pie([present_rate, absent_rate], labels=['Present', 'Absent'], autopct='%1.1f%%',
                       startangle=90, colors=colors, wedgeprops=wedgeprops)
                ax.axis('equal')

                fig.patch.set_facecolor(PRIMARY_COLOR)

                # Embed visualization in the selection frame on the very right
                canvas = FigureCanvasTkAgg(fig, master=selection_frame)
                canvas.draw()
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.configure(highlightthickness=0)
                canvas_widget.grid(row=0, column=3, rowspan=4, padx=10, pady=10, sticky='nesw')
            else:
                # Clear labels and remove visualization if file not found
                total_label.config(text="Total Students: -")
                present_label.config(text="Present: -")
                absent_label.config(text="Absent: -")
                clear_existing_chart()
                messagebox.showinfo("File Not Found", "Attendance file not found for the selected program and date.")

        def download_attendance():
            selected_program = program_combobox.get()
            selected_date = cal.selection_get()

            if not selected_program or not selected_date:
                messagebox.showerror("Error", "Please select both a program and a date.")
                return  # Don't proceed if any field is empty

            formatted_date = selected_date.strftime('%d_%m_%Y')
            csv_file_name = f'attendanceList-{formatted_date}.csv'
            base_folder = 'Attendance_records'
            program_folder = os.path.join(base_folder, selected_program)
            csv_file_path = os.path.join(program_folder, csv_file_name)

            if os.path.isfile(csv_file_path):
                default_filename = f"{selected_program}_{formatted_date}_Attendance.csv"
                save_path = asksaveasfilename(defaultextension=".csv",
                                              filetypes=[("CSV files", "*.csv")],
                                              initialfile=default_filename)
                if save_path:
                    with open(csv_file_path, 'rb') as file, open(save_path, 'wb') as output_file:
                        output_file.write(file.read())
                    messagebox.showinfo("Download Successful", f"Attendance file has been saved to {save_path}")
            else:
                messagebox.showinfo("File Not Found", "Attendance file not found for the selected program and date.")

        def back_to_main_screen():
            view_attendance_window.destroy()
            root.deiconify()

        program_label = Label(selection_frame, text="Select Program:", bg=PRIMARY_COLOR, fg=TEXT_COLOR,
                              font=FONT_REGULAR)
        program_label.grid(row=0, column=0, padx=10, pady=10)
        program_combobox = ttk.Combobox(selection_frame, values=["RDS", "REI", "RWS", "RSD"], state="readonly",
                                        font=FONT_REGULAR)
        program_combobox.grid(row=0, column=1, padx=10, pady=10)

        # Date Selection
        date_label = Label(selection_frame, text="Select Date:", bg=PRIMARY_COLOR, fg=TEXT_COLOR, font=FONT_REGULAR)
        date_label.grid(row=1, column=0, padx=10, pady=10)
        cal = Calendar(selection_frame, selectmode='day', year=datetime.datetime.now().year,
                       month=datetime.datetime.now().month, day=datetime.datetime.now().day, font=FONT_REGULAR)
        cal.grid(row=1, column=1, padx=10, pady=10)

        # Preview and Download Buttons
        preview_button = ttk.Button(selection_frame, text="Preview Attendance", command=load_attendance_preview,
                                    style='TButton')
        preview_button.grid(row=0, column=2, padx=10, pady=10)

        # Treeview Frame for Displaying Attendance
        tree_frame = Frame(view_attendance_window, bg=PRIMARY_COLOR)
        tree_frame.pack(pady=20, padx=20, fill='both', expand=True)

        # Treeview for Attendance
        columns = ('No', 'Name', 'Student ID', 'Programme', 'Group', 'Year/Sem', 'Current Time', 'Status')
        attendance_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for col in columns:
            attendance_tree.heading(col, text=col)
            attendance_tree.column(col, width=120)
        attendance_tree.pack(side='left', fill='both', expand=True)

        # Scrollbar for the Treeview
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=attendance_tree.yview)
        tree_scrollbar.pack(side='right', fill='y')
        attendance_tree.configure(yscrollcommand=tree_scrollbar.set)

        bottom_button_frame = Frame(view_attendance_window, bg="#B6E1E7")
        bottom_button_frame.pack(fill='x', pady=10)
        bottom_button_frame.grid_columnconfigure(0, weight=1)  # Left alignment for centering buttons
        bottom_button_frame.grid_columnconfigure(3, weight=1)  # Right alignment for centering buttons

        # Download Button
        download_button = ttk.Button(bottom_button_frame, text="Download Attendance", command=download_attendance,
                                     style='TButton')
        download_button.grid(row=0, column=1, padx=5, pady=10)

        # Back Button
        back_button = ttk.Button(bottom_button_frame, text="Back", command=back_to_main_screen, style='Danger.TButton')
        back_button.grid(row=0, column=2, padx=5, pady=10)

    def save_student_details(name, student_id, programme, tutorial_group, year_and_sem):
        with open('student_database_test.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([name, student_id, programme, tutorial_group, year_and_sem])

    def update_video_label(frame, video_label):
        # Convert the frame to a format Tkinter can use and display it
        cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)
        video_label.imgtk = tk_image  # Anchor imgtk to prevent garbage collection
        video_label.configure(image=tk_image)

    def start_video_capture(video_label, name, student_id, programme, tutorial_group, year_and_sem):
        def video_stream():
            take_imgs.takeImages(
                lambda frame: root.after(0, update_video_label, frame, video_label),
                name, student_id, programme, tutorial_group, year_and_sem
            )

        threading.Thread(target=video_stream, daemon=True).start()

    # def set_black_screen(video_label):
    #     black_image = np.zeros((480, 640, 3), dtype=np.uint8)  # Create a black image
    #     black_image = Image.fromarray(black_image)
    #     black_image = ImageTk.PhotoImage(image=black_image)
    #     video_label.configure(image=black_image)
    #     video_label.image = black_image  # Keep a reference so it's not garbage collected

    def take_imgs1(name_entry, student_id_entry, programme_entry, tutorial_group_entry, year_sem_entry, error_label, video_label):
        name = name_entry.get()
        student_id = student_id_entry.get()
        programme = programme_entry.get()
        tutorial_group = tutorial_group_entry.get()
        year_and_sem = year_sem_entry.get()

        def capture_images():
            take_imgs.takeImages(
                lambda frame: update_video_label(frame, video_label),
                name, student_id, programme, tutorial_group, year_and_sem
            )
            # Once the images have been captured, set the video label to a black screen
            set_black_screen(video_label)

        if name and student_id and programme and tutorial_group and year_and_sem:
            error_label.config(text="")  # Clear the error message
            save_student_details(name, student_id, programme, tutorial_group, year_and_sem)
            # Start the thread to capture images
            t1 = threading.Thread(target=capture_images, daemon=True)
            t1.start()
        else:
            error_label.config(text="Error: All fields are required!")

    def normalize_img():
        norm_img.normal_img()


    def norm_img1():
        t2 = threading.Thread(target=normalize_img, daemon=True)
        t2.start()

    def rfaces_call():
        inference.recognize_attendance()


    def inference1():
        t4 = threading.Thread(target=rfaces_call, daemon=True)
        t4.start()


    stop_event = threading.Event()

    def start_recognition(webcam_label):
        global recognition_active, recognition_thread
        if not recognition_active:
            recognition_active = True
            stop_event.clear()
            recognition_thread = threading.Thread(target=inference.recognize_attendance,
                                                  args=(webcam_label, stop_event))
            recognition_thread.start()

    def stop_recognition(webcam_label):
        global recognition_active, recognition_thread
        recognition_active = False
        stop_event.set()

        if recognition_thread is not None:
            recognition_thread.join(timeout=5)
            if recognition_thread.is_alive():
                print("Warning: recognition thread did not terminate as expected.")

        # Directly update the webcam label here
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)
        black_image_pil = Image.fromarray(black_image)
        black_image_tk = ImageTk.PhotoImage(image=black_image_pil)
        webcam_label.config(image=black_image_tk)
        webcam_label.image = black_image_tk

        recognition_thread = None

    def update_datetime(datetime_label):
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%A, %Y-%m-%d %H:%M:%S")
        datetime_label.config(text=formatted_datetime)
        datetime_label.after(1000, update_datetime, datetime_label)

    def open_recognition_frame():
        recognition_frame = tk.Toplevel(root)
        recognition_frame.title("Face Recognition")

        # Set the size of the recognition window
        window_width = 1100
        window_height = 580
        screen_width = recognition_frame.winfo_screenwidth()
        screen_height = recognition_frame.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        recognition_frame.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Webcam Frame with Padding
        webcam_frame = tk.Frame(recognition_frame, padx=10, pady=10)
        webcam_frame.grid(row=0, column=0, sticky='ew')

        # Info Frame on the right side of the webcam
        info_frame = tk.Frame(recognition_frame, padx=10, pady=10)
        info_frame.grid(row=0, column=1, rowspan=2, sticky='nsew')

        # Date and Time Label with larger font
        datetime_label = tk.Label(info_frame, text="", font=("Helvetica", 14))  # Increased font size
        datetime_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))  # Increased pady for more space
        update_datetime(datetime_label)  # Initialize datetime update

        # Label and Dropdown for Subject with space in between and larger font
        subject_label = tk.Label(info_frame, text="Subject :", font=("Helvetica", 12))  # Increased font size
        subject_label.grid(row=1, column=0, sticky='w', pady=(10, 0))  # Added pady to create space

        subject_var = tk.StringVar()
        subject_dropdown = ttk.Combobox(info_frame, textvariable=subject_var, state="readonly",
                                        values=["Subject 1", "Subject 2", "Subject 3"])  # Replace with actual values
        subject_dropdown.grid(row=1, column=1, sticky='e', pady=(10, 0))  # Added pady to create space
        subject_dropdown.config(font=("Helvetica", 12))  # Increased font size for dropdown text

        # Label and Dropdown for Programme with space in between and larger font
        programme_label = tk.Label(info_frame, text="Programme :", font=("Helvetica", 12))  # Increased font size
        programme_label.grid(row=2, column=0, sticky='w', pady=(10, 0))  # Added pady to create space

        programme_var = tk.StringVar()
        programme_dropdown = ttk.Combobox(info_frame, textvariable=programme_var, state="readonly",
                                          values=["RDS", "REI",
                                                  "RWS", "RSD"])  # Replace with actual values
        programme_dropdown.grid(row=2, column=1, sticky='e', pady=(10, 0))  # Added pady to create space
        programme_dropdown.config(font=("Helvetica", 12))  # Increased font size for dropdown text

        # Label and Dropdown for Year/Semester with space in between and larger font
        year_sem_label = tk.Label(info_frame, text="Year/Semester :", font=("Helvetica", 12))  # Increased font size
        year_sem_label.grid(row=3, column=0, sticky='w', pady=(10, 0))  # Added pady to create space

        year_sem_var = tk.StringVar()
        year_sem_dropdown = ttk.Combobox(info_frame, textvariable=year_sem_var, state="readonly",
                                         values=["Year 1 Sem 1", "Year 1 Sem 2", "Year 1 Sem 3", "Year 2 Sem 1",
                                                 "Year 2 Sem 2", "Year 2 Sem 3", "Year 3 Sem 1", "Year 3 Sem 2",
                                                 "Year 3 Sem 3"])  # Replace with actual values
        year_sem_dropdown.grid(row=3, column=1, sticky='e', pady=(10, 0))  # Added pady to create space
        year_sem_dropdown.config(font=("Helvetica", 12))  # Increased font size for dropdown text

        # Counter for Supposed to Arrive
        counters_frame = ttk.Frame(info_frame, padding=(10, 5))
        counters_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky='nsew')

        # Supposed to Arrive Counter and Box
        counters_frame = ttk.Frame(info_frame, padding=(10, 5))
        counters_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky='nsew')

        # Supposed to Arrive Counter and Box
        supposed_to_arrive_frame = ttk.LabelFrame(counters_frame, text="Supposed to Arrive", padding=(10, 5))
        supposed_to_arrive_frame.grid(row=0, column=0, padx=(0, 10), sticky='nsew')

        supposed_to_arrive_count = tk.StringVar()
        supposed_to_arrive_count.set("0")  # Initialize with 0, you can update it later
        supposed_to_arrive_count_label = tk.Label(supposed_to_arrive_frame, textvariable=supposed_to_arrive_count,
                                                  font=("Helvetica", 12))
        supposed_to_arrive_count_label.pack()

        # Actual Arrivals Counter and Box
        actual_arrivals_frame = ttk.LabelFrame(counters_frame, text="Actual Arrivals", padding=(10, 5))
        actual_arrivals_frame.grid(row=0, column=1, sticky='nsew')

        actual_arrivals_count = tk.StringVar()
        actual_arrivals_count.set("0")  # Initialize with 0, you can update it later
        actual_arrivals_count_label = tk.Label(actual_arrivals_frame, textvariable=actual_arrivals_count,
                                               font=("Helvetica", 12))
        actual_arrivals_count_label.pack()

        # Set a fixed width for both frames
        supposed_to_arrive_frame.config(width=200)
        actual_arrivals_frame.config(width=200)

        info_frame.grid_rowconfigure(5, weight=1)  # This will allocate space for the new row

        # Create a new frame within info_frame for the additional scroll boxes
        additional_boxes_frame = ttk.Frame(info_frame, padding=(10, 5))
        additional_boxes_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=10, pady=(5, 0))  # Reduced pady

        # Haven't Arrived Scroll Box
        havent_arrived_label_frame = ttk.LabelFrame(additional_boxes_frame, text="Haven't Arrived", padding=(10, 5))
        havent_arrived_label_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=5)
        havent_arrived_label_frame.grid(rowspan=5)  # Span multiple rows to match the info_frame height

        havent_arrived_scroll = ttk.Scrollbar(havent_arrived_label_frame)
        havent_arrived_scroll.pack(side='right', fill='y')

        # Increase the height of the "Haven't Arrived" Listbox
        havent_arrived_listbox = tk.Listbox(havent_arrived_label_frame, yscrollcommand=havent_arrived_scroll.set,
                                            height=10)  # Adjust height as necessary
        havent_arrived_listbox.pack(side='left', fill='both', expand=True)
        havent_arrived_scroll.config(command=havent_arrived_listbox.yview)

        # Late Scroll Box
        late_label_frame = ttk.LabelFrame(additional_boxes_frame, text="Late", padding=(10, 5))
        late_label_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0), pady=5)
        late_label_frame.grid(rowspan=5)  # Reduced pady, changed row to 1 to stack boxes vertically

        late_scroll = ttk.Scrollbar(late_label_frame)
        late_scroll.pack(side='right', fill='y')

        # Increase the height of the "Late" Listbox
        late_listbox = tk.Listbox(late_label_frame, yscrollcommand=late_scroll.set,
                                  height=10)  # Adjust height as necessary
        late_listbox.pack(side='left', fill='both', expand=True)
        late_scroll.config(command=late_listbox.yview)

        # Center the counters_frame horizontally in info_frame
        counters_frame.place(relx=0.5, rely=0.35, anchor='center')

        # Adjust the size of the black image for the initial state
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)
        black_image_pil = Image.fromarray(black_image)
        black_image_tk = ImageTk.PhotoImage(image=black_image_pil)

        # Webcam Label
        webcam_label = tk.Label(webcam_frame, image=black_image_tk)
        webcam_label.image = black_image_tk
        webcam_label.pack(expand=True, fill='both')

        # Button Frame
        button_frame = tk.Frame(recognition_frame)
        button_frame.grid(row=1, column=0, sticky='ew')

        # Buttons
        start_button = ttk.Button(button_frame, text="Start Recognize",
                                  command=lambda: [start_recognition(webcam_label), stop_button.config(state="normal"),
                                                   start_button.config(state="disabled")], style='TButton')
        stop_button = ttk.Button(button_frame, text="Stop Recognize",
                                 command=lambda: [stop_recognition(webcam_label), start_button.config(state="normal"),
                                                  stop_button.config(state="disabled")], style='TButton')
        back_button = ttk.Button(button_frame, text="Back", command=recognition_frame.destroy, style='Danger.TButton')

        # Arrange buttons horizontally with padding
        start_button.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        stop_button.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        back_button.pack(side='left', fill='x', expand=True, padx=5, pady=5)

    def inference1():
        open_recognition_frame()

    def update_gui_with_frame(img, webcam_label):
        cv_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)
        webcam_label.imgtk = tk_image  # Anchor imgtk to prevent garbage collection
        webcam_label.configure(image=tk_image)

    def set_black_screen(webcam_label):
        black_image = Image.new('RGB', (640, 480), (0, 0, 0))
        black_photo = ImageTk.PhotoImage(black_image)
        webcam_label.imgtk = black_photo  # Anchor imgtk to prevent garbage collection
        webcam_label.configure(image=black_photo)
        webcam_label.image = black_photo

    def get_next_sequence_number(file_path):
        try:
            with open(file_path, 'r', newline='') as file:
                # Read the last row and return the next sequence number
                last_row = None
                for last_row in csv.reader(file): pass
                if last_row is not None:
                    return int(last_row[0]) + 1
                else:
                    return 1
        except FileNotFoundError:
            # If the file does not exist, start from 1
            return 1

    def save_to_csv(file_path, programme, year_and_sem, tutorial_group, name_of_student, student_id_person):
        sequence_number = get_next_sequence_number(file_path)
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                [sequence_number, programme, year_and_sem, tutorial_group, name_of_student, student_id_person])

    def handle_take_image(programme, year_and_sem, tutorial_group, name_of_student, student_id_person, webcam_label,
                          error_label):
        # Check if all fields are filled in
        if not (programme and year_and_sem and tutorial_group and name_of_student and student_id_person):
            error_label.config(text="Please fill in all fields before capturing images.")
            return  # Exit the function if any field is empty

        def start_capture():
            # Proceed with capturing the images
            takeImages(lambda img: update_gui_with_frame(img, webcam_label), programme, year_and_sem, tutorial_group,
                       name_of_student, student_id_person)
            set_black_screen(webcam_label)  # Set the webcam view to black after capturing

            file_path = 'student_database_test.csv'
            # Save to CSV
            save_to_csv(file_path, name_of_student, student_id_person, programme, tutorial_group, year_and_sem)

        # Clear any previous error messages
        error_label.config(text="")

        # Run the capture in a separate thread to prevent GUI freezing
        threading.Thread(target=start_capture, daemon=True).start()

    def open_registration_screen():
        root.withdraw()  # Hide the main window
        registration_window = tk.Toplevel(root)
        registration_window.title("Registration")

        main_window_width = 1100  # Adjusted width to accommodate webcam and form side-by-side
        main_window_height = 550
        center_window(registration_window, main_window_width, main_window_height)

        registration_window.resizable(False, False)

        # Grid configuration for layout
        registration_window.grid_rowconfigure(0, weight=1)
        registration_window.grid_columnconfigure([0, 1], weight=1)

        # Webcam label at the top left
        webcam_frame = tk.Frame(registration_window)
        webcam_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10))  # Reduced right padding

        webcam_label = tk.Label(webcam_frame)
        webcam_label.pack(fill='both', expand=True)

        black_image = Image.new('RGB', (640, 480), (0, 0, 0))
        black_photo = ImageTk.PhotoImage(black_image)
        webcam_label.configure(image=black_photo)
        webcam_label.image = black_photo

        # Form frame
        form_frame = tk.Frame(registration_window)
        form_frame.grid(row=0, column=1, sticky="nsew", padx=20)

        # Styling for labels and comboboxes
        label_style = {'font': ('Segoe UI', 10,'bold'), 'background': '#f0f0f0'}
        combobox_style = {'font': ('Segoe UI', 10)}

        # Function to create a label and entry/combobox pair
        def create_form_entry(row, text, widget_type, values=None):
            label = tk.Label(form_frame, text=text + " :", **label_style)
            label.grid(row=row, column=0, sticky="e", padx=10, pady=5)

            if widget_type == 'entry':
                widget = ttk.Entry(form_frame, **combobox_style)
            elif widget_type == 'combobox':
                widget = ttk.Combobox(form_frame, values=values, **combobox_style, state="readonly")
            else:
                raise ValueError("Unsupported widget type")

            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
            return widget

        # Creating form fields
        name_entry = create_form_entry(0, "Name", 'entry')
        student_id_entry = create_form_entry(1, "Student ID", 'entry')
        programme_combobox = create_form_entry(2, "Programme", 'combobox', values=["RDS", "REI", "RWS", "RSD"])
        tutorial_group_combobox = create_form_entry(3, "Tutorial Group", 'combobox',
                                                    values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        year_sem_combobox = create_form_entry(4, "Year and Semester", 'combobox',
                                              values=["Year 1 Sem 1", "Year 1 Sem 2", "Year 1 Sem 3", "Year 2 Sem 1",
                                                      "Year 2 Sem 2", "Year 2 Sem 3", "Year 3 Sem 1", "Year 3 Sem 2",
                                                      "Year 3 Sem 3"])

        # Error label
        error_label = tk.Label(form_frame, text="", fg="red", **label_style)
        error_label.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))

        # Configuring the style for Treeview
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        style.configure("Treeview", font=('Segoe UI', 10), rowheight=25)

        # Treeview Frame
        tree_frame = tk.Frame(form_frame)
        tree_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=(10, 0), pady=(5, 10))

        # Assuming the total width of the treeview is 320 pixels
        total_width = 320  # Adjust this to the actual width of your treeview
        column_width = total_width // 2

        # Create the Treeview widget with a specified height and evenly split column widths
        tree = ttk.Treeview(tree_frame, columns=("one", "two"), show='headings', style="Treeview", height=5)
        tree.column("one", anchor=tk.W, width=column_width)
        tree.column("two", anchor=tk.W, width=column_width)

        tree.heading("one", text="Key", anchor=tk.W)
        tree.heading("two", text="Value", anchor=tk.W)

        # Inserting empty rows into the treeview
        keys = ["Name", "Student ID", "Programme", "Tutorial Group", "Year and Semester"]
        for key in keys:
            tree.insert("", tk.END, values=(key, ""))

        tree.grid(row=0, column=0, sticky='nsew', padx=(10, 0))

        # Add a scrollbar to the treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns', padx=(0, 10))

        tree.configure(yscrollcommand=scrollbar.set)

        def update_tree():
            # Clear the current tree
            for item in tree.get_children():
                tree.delete(item)

            # Insert new data
            data = [
                ("Name", name_entry.get()),
                ("Student ID", student_id_entry.get()),
                ("Programme", programme_combobox.get()),
                ("Tutorial Group", tutorial_group_combobox.get()),
                ("Year and Semester", year_sem_combobox.get()),
            ]
            for key, value in data:
                tree.insert("", tk.END, values=(key, value))

        # Frame for buttons below the webcam
        button_frame = tk.Frame(registration_window)
        # Adjust the row index for the button frame if necessary, it should be right below the form_frame
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))  # Reduce the top padding

        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 12, 'bold'), borderwidth=1, relief='flat', padding=6,
                        background='#3498db', foreground='black')
        style.map('TButton',
                  foreground=[('pressed', 'black'), ('active', 'black')],
                  background=[('pressed', '!disabled', '#2E86C1'), ('active', '#5499C7')])

        # Update the Danger.TButton style to have red text in all states
        style.configure('Danger.TButton', font=('Segoe UI', 12, 'bold'), borderwidth=1, relief='flat', padding=6,
                        background=DANGER_COLOR, foreground='red')  # Foreground set to red
        style.map('Danger.TButton',
                  foreground=[('pressed', 'red'), ('active', 'red'), ('!active', 'red')],
                  background=[('pressed', '!disabled', DANGER_COLOR), ('active', DANGER_COLOR)])

        # Take Image Button
        take_image_button = ttk.Button(
            button_frame,
            text="Take Image",
            command=lambda: handle_take_image(
                programme_combobox.get(),
                year_sem_combobox.get(),
                tutorial_group_combobox.get(),
                name_entry.get(),
                student_id_entry.get(),
                webcam_label,
                error_label  # Pass the error_label to the function
            ),
            style='TButton'
        )
        take_image_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        take_image_button.config(command=lambda: [handle_take_image(
            programme_combobox.get(),
            year_sem_combobox.get(),
            tutorial_group_combobox.get(),
            name_entry.get(),
            student_id_entry.get(),
            webcam_label,
            error_label
        ), update_tree()])

        normalize_button = ttk.Button(
            button_frame,
            text="TRAIN IMAGE",
            command=norm_img1,
            style='TButton'
        )
        normalize_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Back button to go back to the main screen
        back_button = ttk.Button(
            button_frame,
            text="Back",
            command=lambda: [registration_window.destroy(), root.deiconify()],
            style='Danger.TButton'
        )
        back_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

    def check_student_information():
        root.withdraw()  # Hide the main window

        check_window = tk.Toplevel(root)
        check_window.title("Check Student Information")

        # Calculate the screen width and height
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate the position to center the window
        window_width = 1100
        window_height = 650
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set the geometry to center the window
        check_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        check_window.configure(bg="#B6E1E7")  # Set the theme color background for the window

        MODERN_FONT = ("Arial", 12)

        # Search Frame for inputs
        search_frame = Frame(check_window, bg="#B6E1E7")
        search_frame.pack(pady=20, padx=20, fill='x')

        # Optionally, use a LabelFrame to group the checkboxes
        search_group = LabelFrame(search_frame, text=" Search Options ", font=MODERN_FONT, bg="#B6E1E7", fg="black",
                                  padx=10, pady=10)
        search_group.pack(fill='x')

        search_label = Label(search_group, text="Search By :", font=MODERN_FONT, bg="#B6E1E7")
        search_label.grid(row=0, column=0, padx=(0, 20))  # Use grid for better alignment

        # Variables to hold the state of the checkboxes
        search_vars = {
            'Name': tk.BooleanVar(),
            'ID': tk.BooleanVar(),
            'Program': tk.BooleanVar(),
            'Group': tk.BooleanVar(),
            'Year/Sem': tk.BooleanVar()
        }

        # Create a checkbox for each search option
        for i, (text, var) in enumerate(search_vars.items()):
            cb = Checkbutton(search_group, text=text, variable=var, font=MODERN_FONT, bg="#B6E1E7",
                             command=lambda v=var: toggle_entry(v))
            cb.grid(row=0, column=i + 1, sticky='w', padx=10)  # Align checkboxes horizontally

        search_entries = {}  # Dictionary to hold Entry widgets for search criteria

        dropdown_options = {
            'Program': ['RDS', 'REI', 'RWS', 'RSD'],
            'Group': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'],
            'Year/Sem': ["Year 1 Sem 1", "Year 1 Sem 2", "Year 1 Sem 3", "Year 2 Sem 1",
                         "Year 2 Sem 2", "Year 2 Sem 3", "Year 3 Sem 1", "Year 3 Sem 2",
                         "Year 3 Sem 3"]
        }

        def toggle_entry(var):
            criterion = [key for key, value in search_vars.items() if value == var][0]

            if criterion in ['Name', 'ID']:
                placeholder = f"Enter {criterion}"
                if var.get():
                    # Create an Entry widget for typing
                    entry = Entry(search_frame, font=FONT_REGULAR)
                    entry.insert(0, placeholder)
                    entry.bind("<FocusIn>",
                               lambda e: e.widget.delete(0, END) if e.widget.get() == placeholder else None)
                    entry.bind("<FocusOut>", lambda e: e.widget.insert(0, placeholder) if not e.widget.get() else None)
                    entry.pack(side='left', fill='x', expand=True, padx=10)
                    search_entries[criterion] = entry
                else:
                    # Remove the Entry widget if the checkbox is unchecked
                    entry = search_entries.get(criterion)
                    if entry:
                        entry.destroy()
                        search_entries.pop(criterion)
            else:
                if var.get():
                    # Create a Combobox widget for dropdown selection
                    combobox = ttk.Combobox(search_frame, values=dropdown_options[criterion], font=FONT_REGULAR,
                                            state="readonly")
                    combobox.set(f"Select {criterion}")  # Set default placeholder text
                    combobox.pack(side='left', fill='x', expand=True, padx=10)
                    search_entries[criterion] = combobox
                else:
                    # Remove the Combobox if the checkbox is unchecked
                    combobox = search_entries.get(criterion)
                    if combobox:
                        combobox.destroy()
                        search_entries.pop(criterion)

        search_group.grid_columnconfigure(len(search_vars), weight=1)

        search_button = ttk.Button(search_group, text="Search",
                                   command=lambda: search_student_info(search_entries, search_vars))
        search_button.grid(row=0, column=len(search_vars) + 1, padx=(20, 0),
                           sticky='e')  # Place the button in the next empty column

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=30)  # Increase rowheight as needed
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))  # Heading font

        # Treeview for displaying the results
        tree_frame = Frame(check_window)
        tree_frame.pack(pady=20, padx=20, fill='both', expand=True)

        def treeview_sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            l.sort(reverse=reverse)

            # rearrange items in sorted positions
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            # reverse sort next time
            tv.heading(col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))

        # Include 'No.' as the first column for numbering
        tree = ttk.Treeview(tree_frame, columns=('No.', 'Name', 'ID', 'Program', 'Group', 'Year/Sem'), show='headings',
                            selectmode='extended')
        tree.heading('No.', text='No.', command=lambda: treeview_sort_column(tree, 'No.', False))
        tree.column('No.', width=30, anchor='center')

        for col in ('Name', 'ID', 'Program', 'Group', 'Year/Sem'):
            tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree, _col, False))
            tree.column(col, width=100)
        tree.pack(fill='both', expand=True)

        def search_student_info(search_entries, search_vars):

            tree.delete(*tree.get_children())  # Clear the current view

            # Determine selected criteria
            selected_criteria = [key for key, var in search_vars.items() if var.get()]

            # Map column names to their indices
            column_indices = {'Name': 2, 'ID': 3, 'Program': 4, 'Group': 5, 'Year/Sem': 6}

            # Open the CSV file and search
            with open('student_database_test.csv', 'r') as file:
                csv_reader = csv.reader(file)
                index = 1  # Start with index 1 for numbering the rows
                for row in csv_reader:
                    match = True
                    for criterion in selected_criteria:
                        entry = search_entries.get(criterion)
                        if entry:
                            search_terms = [term.strip().lower() for term in entry.get().split(',')]
                            if search_terms and not any(
                                    term in row[column_indices[criterion] - 1].lower() for term in search_terms if
                                    term):
                                match = False
                                break
                    if match:
                        tree.insert('', 'end', values=(index, row[1], row[2], row[3], row[4], row[5]))
                        index += 1

            if not tree.get_children():
                tree.insert('', 'end', values=('No results found', '', '', '', '', ''))

        def edit_student():
            selected_item = tree.selection()
            if selected_item:  # If there is a selection
                selected_item = selected_item[0]  # Grab the selected item in the treeview
                student_id = tree.item(selected_item)['values'][2]  # Student ID is in the third column
                student_name = tree.item(selected_item)['values'][1]  # Student Name is in the second column

                # Open a new window to edit the selected student's information
                edit_window = tk.Toplevel(main_frame)
                edit_window.title("Edit Student Information")

                # Calculate the screen width and height
                screen_width = main_frame.winfo_screenwidth()
                screen_height = main_frame.winfo_screenheight()

                # Calculate the position to center the window
                window_width = 400  # Adjust the width as needed
                window_height = 300  # Adjust the height as needed
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

                # Set the geometry to center the window
                edit_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
                edit_window.configure(bg="#B6E1E7")  # Set the theme color background for the window

                student_info_label = Label(edit_window, text=f"Editing: {student_name} (ID: {student_id})",
                                           font=FONT_BOLD, bg="#B6E1E7")
                student_info_label.pack(pady=(10, 0))

                # Create a dictionary to hold the Entry widgets and the current value for each field
                entry_widgets = {}
                labels = ['Program', 'Group', 'Year/Sem']
                current_values = [tree.item(selected_item)['values'][i + 3] for i in range(3)]

                # Use a frame to contain the form elements for better layout control
                form_frame = Frame(edit_window, bg="#B6E1E7")
                form_frame.pack(fill='both', expand=True, padx=20, pady=20)

                # Create label and entry for each field, and pack them into the form frame
                for i, label in enumerate(labels):
                    Label(form_frame, text=f"{label}:", bg="#B6E1E7", font=FONT_REGULAR).grid(row=i, column=0,
                                                                                              sticky='e', padx=10,
                                                                                              pady=10)
                    # Create a Combobox instead of an Entry
                    combobox = ttk.Combobox(form_frame, values=dropdown_options[label], font=FONT_REGULAR,
                                            state="readonly")
                    combobox.grid(row=i, column=1, sticky='ew', padx=10, pady=10)
                    combobox.set(current_values[i])  # Set the current value
                    entry_widgets[label] = combobox

                # Function to save the edited student information
                def save_edited_student():
                    # Extract the data from the Entry widgets
                    new_data = {label: entry_widgets[label].get() for label in labels}

                    # Check if the new values are different from the old ones
                    if not any(new_data[label] != current_values[i] for i, label in enumerate(labels)):
                        messagebox.showinfo("No changes", "No changes detected.")
                        edit_window.destroy()
                        return

                    # Read all data from the CSV file
                    updated_rows = []
                    with open('student_database_test.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile)
                        for row in reader:
                            if row[2] == student_id:  # Check if the current row is the student's row
                                row[3], row[4], row[5] = new_data['Program'], new_data['Group'], new_data['Year/Sem']
                            updated_rows.append(row)

                    # Write the updated data back to the CSV file
                    with open('student_database_test.csv', 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(updated_rows)

                    # Update the Treeview
                    tree.item(selected_item, values=(
                        tree.item(selected_item)['values'][0],
                        tree.item(selected_item)['values'][1],
                        student_id,
                        new_data['Program'],
                        new_data['Group'],
                        new_data['Year/Sem'],
                    ))

                    # Close the edit window
                    edit_window.destroy()
                    print("CSV and Treeview updated.")

                # Create the Save Changes button
                save_button = ttk.Button(form_frame, text="Save Changes", command=save_edited_student,
                                         style='Red.TButton')
                save_button.grid(row=3, column=0, columnspan=2, pady=10, sticky='e')  # Align to the right (east)
            else:
                messagebox.showwarning("Warning", "Please select an item to edit.")

        # Function to delete student's information
        def delete_student():
            selected_items = tree.selection()  # This will be a tuple of all selected items
            if selected_items:  # If there is at least one selection
                response = messagebox.askyesno("Confirm Delete",
                                               "Are you sure you want to delete the selected students?")
                if response:
                    student_ids = [tree.item(item)['values'][2] for item in
                                   selected_items]  # List of all selected student IDs

                    # Read all data from the CSV file
                    rows = []
                    with open('student_database_test.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile)
                        rows = list(reader)

                    # Filter out the selected students' records
                    rows_to_keep = [row for row in rows if row[2] not in student_ids]

                    # Debugging print statement
                    print(f"Deleting student IDs: {student_ids}")
                    print(f"Rows before deletion: {len(rows)}")
                    print(f"Rows after deletion: {len(rows_to_keep)}")

                    # Write the filtered data back to the CSV file
                    with open('student_database_test.csv', 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(rows_to_keep)

                    # Remove the entries from the Treeview
                    for selected_item in selected_items:
                        tree.delete(selected_item)
            else:
                messagebox.showwarning("Warning", "Please select at least one item to delete.")

        # Function to load the selected student data for editing

        action_frame = Frame(check_window, bg="#B6E1E7")
        action_frame.pack(fill='x', pady=(10, 30))  # Less padding on the bottom

        # Inner frame to contain buttons and center them
        button_container = Frame(action_frame, bg="#B6E1E7")
        button_container.pack()

        style = ttk.Style()
        style.configure('Red.TButton', foreground='red')

        # Function to create a square button
        def create_square_button(parent, text, command, style_name=''):
            # Create a button with the desired text and command
            button = ttk.Button(parent, text=text, command=command, style=style_name)
            button.pack(side='left', padx=10, pady=10)  # Pad the button a bit from its neighbors
            return button

        def back_to_main_screen():
            check_window.destroy()  # Close the check window
            root.deiconify()  # Show the main window again

        # Back button to go back to the main screen
        edit_button = create_square_button(button_container, "Edit", edit_student)
        delete_button = create_square_button(button_container, "Delete", delete_student)
        back_button = create_square_button(button_container, "Back", back_to_main_screen, 'Red.TButton')

        search_student_info(search_entries, search_vars)

    # ---------------main driver ------------------
    # create a tkinter window

    # content_frame = tk.Frame(root)
    # content_frame.grid(row=1, column=0, padx=15, pady=8)

    buttons_frame = Frame(main_frame, bg="#FAF9F6")
    buttons_frame.pack(pady=(30, 0), padx=5)

    # Create buttons with icons
    image_path = 'company_logo.png'
    image = Image.open(image_path)
    recognize_faces_icon = ImageTk.PhotoImage(image)

    style = ttk.Style()
    # Configure the default style for buttons
    style.configure('TButton', font=('Helvetica', 12, 'bold'), borderwidth=1, relief='flat', padding=6,
                    foreground='black', background='#3498db')
    style.map('TButton',
              foreground=[('pressed', 'black'), ('active', 'black')],
              background=[('pressed', '!disabled', '#2E86C1'), ('active', '#5499C7')],
              lightcolor=[('active', '#154360'), ('!active', '#1B4F72')],
              darkcolor=[('active', '#154360'), ('!active', '#1B4F72')])

    # Define a special style for the exit button with different colors
    style.configure('Danger.TButton', font=('Helvetica', 12, 'bold'), borderwidth=1, relief='flat', padding=6,
                    foreground='red', background='darkred')
    style.map('Danger.TButton',
              foreground=[('pressed', 'red'), ('active', 'red')],
              background=[('pressed', '!disabled', 'darkred'), ('active', 'darkred')],
              lightcolor=[('active', '#922B21'), ('!active', '#C0392B')],
              darkcolor=[('active', '#922B21'), ('!active', '#C0392B')])

    # Define a style for the Important button with a green font color and a different background color
    style.configure('Important.TButton', font=('Helvetica', 14, 'bold'),
                    foreground='green', background='#3498db')
    style.map('Important.TButton',
              foreground=[('pressed', 'green'), ('active', 'green')],
              background=[('pressed', '!disabled', '#2980b9'), ('active', '#3498db')],
              lightcolor=[('active', '#2980b9'), ('!active', '#2980b9')],
              darkcolor=[('active', '#2980b9'), ('!active', '#2980b9')])

    # Apply styles to buttons
    icon_size = (30, 30)  # Set the icon size to match the text

    # Resize and load the icons for each button
    registration_icon_image = Image.open('registration.png').resize(icon_size, Image.LANCZOS)
    check_info_icon_image = Image.open('studentinfo.png').resize(icon_size, Image.LANCZOS)
    recognize_faces_icon_image = Image.open('recognize.png').resize(icon_size, Image.LANCZOS)
    view_attendance_icon_image = Image.open('attendance.png').resize(icon_size, Image.LANCZOS)
    exit_icon_image = Image.open('exit.png').resize(icon_size, Image.LANCZOS)

    # Convert them to a format Tkinter can use
    registration_icon = ImageTk.PhotoImage(registration_icon_image)
    check_info_icon = ImageTk.PhotoImage(check_info_icon_image)
    recognize_faces_icon = ImageTk.PhotoImage(recognize_faces_icon_image)
    view_attendance_icon = ImageTk.PhotoImage(view_attendance_icon_image)
    exit_icon = ImageTk.PhotoImage(exit_icon_image)

    # Create a special style for the "Recognize Faces" button
    style.configure('Important.TButton', font=('Helvetica', 14, 'bold'), background='#3498db')

    # Now create the buttons with the icons
    # Modify the padx value to control the spacing between the icon and text
    registration_button = ttk.Button(
        buttons_frame,
        text="REGISTRATION",
        image=registration_icon,
        compound="left",  # Place the icon to the left of the text
        command=open_registration_screen,
        style='TButton',
        padding=(20, 10)  # Add padding to the left side of the text
    )
    registration_button.image = registration_icon

    check_info_button = ttk.Button(
        buttons_frame,
        text="STUDENT DATABASE",
        image=check_info_icon,
        compound="left",  # Place the icon to the left of the text
        command=check_student_information,
        style='TButton',
        padding=(20, 10)  # Add padding to the left side of the text
    )
    check_info_button.image = check_info_icon

    # Make the "Recognize Faces" button larger and more prominent
    recognize_faces_button = ttk.Button(
        buttons_frame,
        text="RECOGNIZE FACES",
        image=recognize_faces_icon,
        compound="left",  # Place the icon to the left of the text
        command=inference1,
        style='Important.TButton',
        padding=(20, 10)  # Add padding to the left side of the text
    )
    recognize_faces_button.image = recognize_faces_icon

    view_attendance_button = ttk.Button(
        buttons_frame,
        text="VIEW ATTENDANCE",
        image=view_attendance_icon,
        compound="left",  # Place the icon to the left of the text
        command=view_attendance,
        style='TButton',
        padding=(20, 10)  # Add padding to the left side of the text
    )
    view_attendance_button.image = view_attendance_icon

    exit_button = ttk.Button(
        buttons_frame,
        text="EXIT",
        image=exit_icon,
        compound="left",  # Place the icon to the left of the text
        command=root.destroy,
        style='Danger.TButton',
        padding=(20, 10)  # Add padding to the left side of the text
    )
    exit_button.image = exit_icon

    button_padding_y = 20  # Adjust the vertical padding to your preference

    # Arrange the buttons with the most important one at the top
    recognize_faces_button.pack(fill='x', pady=button_padding_y, padx=50, anchor='s')
    registration_button.pack(fill='x', pady=button_padding_y, padx=50, anchor='s')
    check_info_button.pack(fill='x', pady=button_padding_y, padx=50, anchor='s')
    view_attendance_button.pack(fill='x', pady=button_padding_y, padx=50, anchor='s')
    exit_button.pack(fill='x', pady=button_padding_y, padx=50, anchor='s')

    # Ensure that the buttons expand to fill the horizontal space
    buttons_frame.pack(pady=(20, 0), side='bottom', fill='x', expand=True)

    root.image = logo_image
    root.mainloop()
    # mainMenu()

create_main_window()