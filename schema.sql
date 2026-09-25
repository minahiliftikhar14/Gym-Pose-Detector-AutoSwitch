CREATE TABLE IF NOT EXISTS workout_logs (
    id SERIAL PRIMARY KEY,
    exercise_type VARCHAR(50) NOT NULL,
    left_arm_reps INT DEFAULT 0,
    right_arm_reps INT DEFAULT 0,
    squat_reps INT DEFAULT 0,
    pushup_reps INT DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
