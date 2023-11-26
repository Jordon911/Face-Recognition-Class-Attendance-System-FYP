import os
import cv2
import numpy as np

def takeImages(callback, programme, year_and_sem, tutorial_group, name_of_student, student_id_person):
    source = "0"  # RTSP link or webcam-id
    path_to_save = "Data"  # Replace with the path to save dir
    min_confidence = 0.8
    number_of_images = 100

    # Create the folder structure
    student_folder = os.path.join(path_to_save, f"{name_of_student}_{student_id_person}_{programme}_{tutorial_group}_{year_and_sem}")
    os.makedirs(student_folder, exist_ok=True)
    path_to_save = student_folder

    # Load pre-trained model for face detection
    opencv_dnn_model = cv2.dnn.readNetFromCaffe(
        prototxt="models/deploy.prototxt",
        caffeModel="models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
    )

    # Set up webcam source
    if source.isnumeric():
        source = int(source)
    cap = cv2.VideoCapture(source)
    fps = cap.get(cv2.CAP_PROP_FPS)

    count = 0
    img_name = 0

    while True:
        success, img = cap.read()
        if not success:
            print('[INFO] Cam NOT working!!')
            break

        # Save Image at a reduced frame rate to avoid duplicates
        if count % (fps // 5) == 0:
            img_path = os.path.join(path_to_save, f"{img_name}.jpg")
            cv2.imwrite(img_path, img)
            print(f'[INFO] Successfully Saved {img_path}')
            img_name += 1

            # Call the callback with the current frame
            if callback:
                callback(img)

        # Face detection with the pre-trained model
        h, w, _ = img.shape
        blob = cv2.dnn.blobFromImage(img, 1.0, (300, 300), (104.0, 117.0, 123.0), False, False)
        opencv_dnn_model.setInput(blob)
        detections = opencv_dnn_model.forward()

        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > min_confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Draw the face detections on the frame
                cv2.rectangle(img, (startX, startY), (endX, endY), (0, 255, 0), 2)

        # Save Image at a reduced frame rate to avoid duplicates
        if count % (fps // 5) == 0:
            img_path = os.path.join(path_to_save, f"{img_name}.jpg")
            cv2.imwrite(img_path, img)
            print(f'[INFO] Successfully Saved {img_path}')
            img_name += 1

            cv2.putText(img, f'Images Captured: {img_name}/{number_of_images}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


        # Call the callback with the current frame
        if callback:
            callback(img)

        count += 1
        if img_name >= number_of_images:
            print(f"[INFO] Collected {number_of_images} Images")
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()