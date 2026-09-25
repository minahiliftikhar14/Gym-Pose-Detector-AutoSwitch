import cv2
import numpy as np
import psycopg2
import mediapipe as mp


# --- DATABASE SAVE FUNCTION ---
def save_workout_to_db(l_reps, r_reps, s_reps, p_reps):
    try:
        conn = psycopg2.connect(
            dbname="minahiliftikhar",
            user="minahiliftikhar",
            host="localhost",
            port="5432",
        )
        cursor = conn.cursor()

        # Decide primary exercise performed
        ex_type = "Mixed Session"
        if l_reps > 0 or r_reps > 0:
            ex_type = "Bicep Curls"
        elif s_reps > 0:
            ex_type = "Squats"
        elif p_reps > 0:
            ex_type = "Pushups"

        insert_query = """
        INSERT INTO workout_logs (exercise_type, left_arm_reps, right_arm_reps, squat_reps, pushup_reps)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(
            insert_query, (ex_type, l_reps, r_reps, s_reps, p_reps)
        )
        conn.commit()
        print("Workout session successfully saved to PostgreSQL database!")

        cursor.close()
        conn.close()
    except Exception as e:
        print("Failed to save workout to database:", e)


# Angle calculation function
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
        a[1] - b[1], a[0] - b[0]
    )
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Bicep Curl Counters & States
l_counter = 0
l_stage = None
r_counter = 0
r_stage = None

# Squat Counter & State
squat_counter = 0
squat_stage = None

# Pushup Counter & State
pushup_counter = 0
pushup_stage = None

# Mode Tracker: "IDLE", "BICEP_CURL", "SQUAT", "PUSHUP"
active_mode = "IDLE"

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        landmarks = results.pose_landmarks.landmark

        # --- LANDMARK COORDINATES ---
        # Left Arm
        l_shoulder = [
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y,
        ]
        l_elbow = [
            landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y,
        ]
        l_wrist = [
            landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y,
        ]

        # Right Arm
        r_shoulder = [
            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y,
        ]
        r_elbow = [
            landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y,
        ]
        r_wrist = [
            landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y,
        ]

        # Right Leg Joints (Squat)
        r_hip = [
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y,
        ]
        r_knee = [
            landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y,
        ]
        r_ankle = [
            landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y,
        ]

        # Left Leg Joints (Squat)
        l_hip = [
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y,
        ]
        l_knee = [
            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y,
        ]
        l_ankle = [
            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y,
        ]

        # --- ANGLES CALCULATION ---
        left_arm_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        avg_arm_angle = (left_arm_angle + right_arm_angle) / 2

        # Both Knees Angles & Average Knee Angle Calculation
        right_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        left_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        knee_angle = (right_knee_angle + left_knee_angle) / 2

        # Shoulder Level (Body Horizontal/Vertical Detection)
        avg_shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2

        # --- DYNAMIC MODE SWITCHING LOGIC ---
        if avg_shoulder_y > 0.5 and (
            left_arm_angle < 120 and right_arm_angle < 120
        ):
            active_mode = "PUSHUP"
        elif knee_angle < 120:
            active_mode = "SQUAT"
        elif left_arm_angle < 100 or right_arm_angle < 100:
            active_mode = "BICEP_CURL"
        elif (
            knee_angle > 155 and left_arm_angle > 140 and right_arm_angle > 140
        ):
            active_mode = "IDLE"

        # --- LOGIC & DASHBOARD DISPLAY BASED ON ACTIVE MODE ---

        # CASE 1: BICEP CURL ACTIVE
        if active_mode == "BICEP_CURL":
            if left_arm_angle > 150:
                l_stage = "down"
            if left_arm_angle < 30 and l_stage == "down":
                l_stage = "up"
                l_counter += 1

            if right_arm_angle > 150:
                r_stage = "down"
            if right_arm_angle < 30 and r_stage == "down":
                r_stage = "up"
                r_counter += 1

            cv2.rectangle(image, (0, 0), (640, 75), (245, 117, 16), -1)
            cv2.putText(
                image,
                f'LEFT ARM: {l_counter} Reps ({l_stage if l_stage else "-"}) | {int(left_arm_angle)} deg',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                f'RIGHT ARM: {r_counter} Reps ({r_stage if r_stage else "-"}) | {int(right_arm_angle)} deg',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            if squat_counter > 0 or pushup_counter > 0:
                cv2.rectangle(image, (420, 10), (630, 65), (50, 50, 50), -1)
                cv2.putText(
                    image,
                    f"STORED: SQUATS {squat_counter} | PUSHUPS {pushup_counter}",
                    (430, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        # CASE 2: SQUAT ACTIVE
        elif active_mode == "SQUAT":
            if knee_angle > 160:
                squat_stage = "up"
            if knee_angle < 90 and squat_stage == "up":
                squat_stage = "down"
                squat_counter += 1

            cv2.rectangle(image, (0, 0), (640, 75), (16, 117, 245), -1)
            cv2.putText(
                image,
                f'SQUATS: {squat_counter} Reps | State: {squat_stage.upper() if squat_stage else "-"}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                f'Knee Angles - L: {int(left_knee_angle)} deg | R: {int(right_knee_angle)} deg | Avg: {int(knee_angle)} deg',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            if l_counter > 0 or r_counter > 0 or pushup_counter > 0:
                cv2.rectangle(image, (410, 10), (630, 65), (50, 50, 50), -1)
                cv2.putText(
                    image,
                    f"CURLS (L:{l_counter}/R:{r_counter}) | PUSHUPS: {pushup_counter}",
                    (420, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        # CASE 3: PUSHUP ACTIVE
        elif active_mode == "PUSHUP":
            if avg_arm_angle > 150:
                pushup_stage = "up"
            if avg_arm_angle < 90 and pushup_stage == "up":
                pushup_stage = "down"
                pushup_counter += 1

            cv2.rectangle(image, (0, 0), (640, 75), (147, 20, 255), -1)
            cv2.putText(
                image,
                f'PUSHUPS: {pushup_counter} Reps | State: {pushup_stage.upper() if pushup_stage else "-"}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                f'Arm Angles - L: {int(left_arm_angle)} deg | R: {int(right_arm_angle)} deg | Avg: {int(avg_arm_angle)} deg',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            if l_counter > 0 or r_counter > 0 or squat_counter > 0:
                cv2.rectangle(image, (410, 10), (630, 65), (50, 50, 50), -1)
                cv2.putText(
                    image,
                    f"CURLS (L:{l_counter}/R:{r_counter}) | SQUATS: {squat_counter}",
                    (420, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        # CASE 4: IDLE STATE
        else:
            if (
                l_counter > 0
                or r_counter > 0
                or squat_counter > 0
                or pushup_counter > 0
            ):
                cv2.rectangle(image, (10, 10), (380, 50), (0, 0, 0), -1)
                cv2.putText(
                    image,
                    f"Curls (L:{l_counter}/R:{r_counter}) | Squats: {squat_counter} | Pushups: {pushup_counter}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

    except Exception as e:
        pass

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
        )

    cv2.imshow("Gym Pose Detector - Smart Auto-Switch Engine", image)

    if cv2.waitKey(10) & 0xFF == ord("q"):
        # Auto-save to PostgreSQL on Quit if any reps were done
        if (
            l_counter > 0
            or r_counter > 0
            or squat_counter > 0
            or pushup_counter > 0
        ):
            save_workout_to_db(
                l_counter, r_counter, squat_counter, pushup_counter
            )
        break

cap.release()
cv2.destroyAllWindows()