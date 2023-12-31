import time
from keras.models import load_model
from mtcnn import MTCNN
from my_utils import alignment_procedure
import tensorflow as tf
import ArcFace
import cv2
import numpy as np
import pandas as pd
import pickle
import csv
import os
import datetime
from PIL import Image, ImageTk
import threading

recognition_active = False

# Define the base folder path where program-specific folders will be created
base_folder = 'Attendance_records'

# Define a list of program names
program_names = ["RDS", "REI", "RWS", "RSD"]

# Initialize sets to store recognized student IDs for each program
recognized_ids = {program: set() for program in program_names}

# Initialize a dictionary to store the CSV file paths for each program
csv_file_paths = {program: '' for program in program_names}

# Function to generate the CSV file name with today's date
def get_csv_file_name():
    today_date = datetime.date.today()
    date_str = today_date.strftime("%d_%m_%Y")
    return f'attendanceList-{date_str}.csv'

def initialize_program_folders():
    student_database_path = 'student_database_test.csv'
    try:
        df_students = pd.read_csv(student_database_path, header=None)
        df_students.columns = ['No', 'Name', 'Student ID', 'Programme', 'Group', 'Year/Sem']
        df_students['Group'] = df_students['Group'].fillna(0).astype(int)
    except FileNotFoundError:
        print("Student database file not found.")
        return

    for program in program_names:
        program_folder = os.path.join(base_folder, program)
        os.makedirs(program_folder, exist_ok=True)
        csv_file_name = get_csv_file_name()
        csv_file_path = os.path.join(program_folder, csv_file_name)
        csv_file_paths[program] = csv_file_path

        # Check if the CSV file exists and is not empty
        if os.path.isfile(csv_file_path) and os.stat(csv_file_path).st_size != 0:
            try:
                existing_df = pd.read_csv(csv_file_path)
                if not existing_df.empty:
                    recognized_ids[program] = set(existing_df['Student ID'][existing_df['Status'] == 'Present'])
            except pd.errors.EmptyDataError:
                # Handle empty CSV file
                print(f"CSV file for {program} is empty, initializing with default values.")
                df_program_students = df_students[df_students['Programme'] == program].copy()
                df_program_students['Current Time'] = ''
                df_program_students['Status'] = 'Absent'
                df_program_students.to_csv(csv_file_path, index=False, header=True)
        else:
            # File does not exist or is empty, create new from database
            df_program_students = df_students[df_students['Programme'] == program].copy()
            df_program_students['Current Time'] = ''
            df_program_students['Status'] = 'Absent'
            df_program_students.to_csv(csv_file_path, index=False, header=True)

def recognize_attendance(feed_label, stop_event):
    source = "0"  # Path to Video or webcam
    path_saved_model = 'models/model.h5'  # Path to saved .h5 model
    threshold = 0.80  # Min prediction confidence (0<conf<1)

    # Liveness Model
    liveness_model_path = 'models/liveness.model'
    label_encoder_path = 'models/le.pickle'

    if source.isnumeric():
        source = int(source)

    # Load saved FaceRecognition Model
    face_rec_model = load_model(path_saved_model, compile=True)

    # Load MTCNN
    detector = MTCNN()

    # Load ArcFace Model
    arcface_model = ArcFace.loadModel()
    target_size = arcface_model.layers[0].input_shape[0][1:3]

    # Liveness Model
    liveness_model = tf.keras.models.load_model(liveness_model_path)
    label_encoder = pickle.loads(open(label_encoder_path, "rb").read())

    cap = cv2.VideoCapture(0)

    start_time = None
    face_detected_time = None

    while True:
        if stop_event.is_set():
            cap.release()
            break

        ret, img = cap.read()
        if not ret:
            break

        detections = detector.detect_faces(img)
        if len(detections) > 0:
            for detect in detections:

                bbox = detect['box']
                xmin, ymin, xmax, ymax = int(bbox[0]), int(bbox[1]), \
                    int(bbox[2] + bbox[0]), int(bbox[3] + bbox[1])

                # Liveness
                img_roi = img[ymin:ymax, xmin:xmax]
                face_resize = cv2.resize(img_roi, (32, 32))
                face_norm = face_resize.astype("float") / 255.0
                face_array = tf.keras.preprocessing.image.img_to_array(face_norm)
                face_prepro = np.expand_dims(face_array, axis=0)
                preds_liveness = liveness_model.predict(face_prepro)[0]
                decision = np.argmax(preds_liveness)

                if decision == 0:
                    # Show Decision
                    cv2.rectangle(
                        img, (xmin, ymin), (xmax, ymax),
                        (0, 0, 255), 2
                    )
                    cv2.putText(
                        img, 'Liveness: Fake',
                        (xmin, ymin - 10), cv2.FONT_HERSHEY_PLAIN,
                        2, (0, 0, 255), 2
                    )

                    # Reset the timer if a face is detected as fake
                    face_detected_time = None

                else:
                    # Real
                    right_eye = detect['keypoints']['right_eye']
                    left_eye = detect['keypoints']['left_eye']

                    norm_img_roi = alignment_procedure(img, left_eye, right_eye, bbox)
                    img_resize = cv2.resize(norm_img_roi, target_size)
                    img_pixels = tf.keras.preprocessing.image.img_to_array(img_resize)
                    img_pixels = np.expand_dims(img_pixels, axis=0)
                    img_norm = img_pixels / 255  # normalize input in [0, 1]
                    img_embedding = arcface_model.predict(img_norm)[0]

                    data = pd.DataFrame([img_embedding], columns=np.arange(512))

                    predict = face_rec_model.predict(data)[0]
                    if max(predict) > threshold:
                        class_id = predict.argmax()
                        pose_class = label_encoder.classes_[class_id]
                        color = (0 ,255, 0)

                    else:
                        pose_class = 'Unknown Person'
                        color = (0, 0, 255)

                    # Show Result
                    cv2.rectangle(
                        img, (xmin, ymin), (xmax, ymax),
                        color, 2
                    )
                    cv2.putText(
                        img, f'{pose_class}',
                        (xmin, ymin - 10), cv2.FONT_HERSHEY_PLAIN,
                        2, (255, 0, 255), 2
                    )

                    # Check if it's time to display the attendance message
                    if start_time is None:
                        start_time = time.time()
                    elif time.time() - start_time >= 3:
                        # Check if a face has been continuously detected for 5 seconds
                        if face_detected_time is None:
                            face_detected_time = time.time()
                        elif time.time() - face_detected_time >= 3:

                            # Split the student information into individual details
                            name, student_id, programme, tutorial_group, year_and_sem = pose_class.split('_')

                            # Get the CSV file path for this program
                            csv_path = csv_file_paths[programme]

                            if student_id not in recognized_ids[programme]:
                                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                recognized_ids[programme].add(student_id)

                                # Update the CSV file
                                csv_path = csv_file_paths[programme]
                                df = pd.read_csv(csv_path)
                                df.loc[df['Student ID'] == student_id, ['Status', 'Current Time']] = ['Present',
                                                                                                      current_time]
                                df.to_csv(csv_path, index=False)

                                cv2.putText(img, "Attendance was taken!", (10, 40), cv2.FONT_HERSHEY_PLAIN, 2,
                                            (0, 255, 0), 2)
                            else:
                                cv2.putText(img, "Attendance is existing!", (10, 40), cv2.FONT_HERSHEY_PLAIN, 2,
                                            (255, 0, 0), 2)

        else:
            print('[INFO] Eyes Not Detected!!')

            # Reset the timer if no face is detected
            start_time = None
            face_detected_time = None

        cv_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)
        feed_label.config(image=tk_image)
        feed_label.image = tk_image

    # cap.release()
    cv2.destroyAllWindows()

    print('[INFO] Inference on Videostream is Ended...')

# Initialize program-specific folders and recognized_ids sets
initialize_program_folders()

