# Gym-Pose-Detector-AutoSwitch

Multi-exercise pose detection engine with real-time rep counting and PostgreSQL session logging for computer vision.

# Real-Time Multi-Exercise Gym Pose Detector & Database Logging System

An end-to-end Computer Vision project. The system performs real-time human pose estimation, multi-exercise recognition with automated state preservation, Finite State Machine (FSM) repetition counting, and persistent session logging into a PostgreSQL database.

---

## Key Features

- **Multi-Exercise Auto-Switching Engine:** Dynamically switches state between **Bicep Curls**, **Squats**, **Pushups**, and **Idle** modes using spatial landmark thresholds.
- **State Preservation:** Keeps active rep counts stored when switching between exercises without resetting session progress.
- **Geometric Vector Mathematics:** Joint angle estimation using 3-point planar vector projections with 2D arctangent normalization ($0^\circ \text{ to } 180^\circ$).
- **Relational Database Integration:** Auto-saves workout summaries and individual arm/leg repetition counts to a local PostgreSQL instance via `psycopg2`.
- **Head-Up Display (HUD):** Dynamic real-time visual feedback rendered using OpenCV overlays.

---

## System Architecture & Computer Vision Pipeline

1. **Frame Acquisition & Color Space Transformation:** RGB frame extraction from webcam stream (`cv2.VideoCapture`).
2. **Landmark Localization:** Extraction of 33 normalized 3D keypoints using MediaPipe Pose engine ($x, y, z \in [0.0, 1.0]$).
3. **Planar Angle Calculation:**
   Using three joints $A(x_1, y_1)$, $B(x_2, y_2)$ (vertex), and $C(x_3, y_3)$:
   $$\theta = \left\vert \text{arctan2}(y_C - y_B, x_C - x_B) - \text{arctan2}(y_A - y_B, x_A - x_B) \right\vert \times \frac{180}{\pi}$$
   If $\theta > 180^\circ$, then $\theta = 360^\circ - \theta$.
4. **Finite State Machine (FSM) Repetition Counting:**
   - **Bicep Curl:** Extension ($>150^\circ$) $\rightarrow$ Flexion ($<30^\circ$).
   - **Squats:** Standing ($>160^\circ$) $\rightarrow$ Full Squat ($<90^\circ$).
   - **Pushups:** Plank ($>150^\circ$) $\rightarrow$ Low Pushup ($<90^\circ$) with horizontal shoulder posture constraint ($y_{\text{shoulder}} > 0.5$).
5. **Database Persistence:** Triggered on session termination (`q` key press) to write relational records into PostgreSQL (`workout_logs` table).

---

## Database Schema (PostgreSQL)
```sql
CREATE TABLE IF NOT EXISTS workout_logs (
    id SERIAL PRIMARY KEY,
    exercise_type VARCHAR(50) NOT NULL,
    left_arm_reps INT DEFAULT 0,
    right_arm_reps INT DEFAULT 0,
    squat_reps INT DEFAULT 0,
    pushup_reps INT DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

## Installation & Setup
Prerequisites
Python 3.9+

PostgreSQL Server running locally (e.g., via Postgres.app on macOS)

## Quick Start
Clone the repository:
git clone [https://github.com/minahiliftikhar14/Gym-Pose-Detector-AutoSwitch.git](https://github.com/minahiliftikhar14/Gym-Pose-Detector-AutoSwitch.git)
cd Gym-Pose-Detector-AutoSwitch
## Install dependencies:
pip install -r requirements.txt
## Initialize Database Schema:
Run the SQL commands provided in schema.sql inside your PostgreSQL GUI client (e.g., TablePlus).
Run Application:
python main.py
## Technology Stack
Language: Python 3
Computer Vision & Pose Estimation: OpenCV, MediaPipe
Mathematics & Computation: NumPy (Trigonometry & Vector Math)
Database Architecture: PostgreSQL, psycopg2-binary
Database GUI Client: TablePlus
