# scanner.py

import pyautogui
import cv2
import numpy as np
import time
import os
from config import AREAS, DEFAULT_IMAGE_FOLDER, SELECTED_IMAGE_FOLDER, START_SCREEN_FOLDER, MATCH_THRESHOLD, MAX_WIDTH, \
    MAX_HEIGHT, START_AREA, START_THRESHOLD, AGENT_ROLES


# Load reference images into memory and resize if necessary
reference_images = {}
# Load default state images
DEFAULT_IMAGES = [f for f in os.listdir(DEFAULT_IMAGE_FOLDER) if f.endswith(('.png', '.jpg', '.jpeg'))]
for agent_image in DEFAULT_IMAGES:
    img = cv2.imread(os.path.join(DEFAULT_IMAGE_FOLDER, agent_image))
    height, width = img.shape[:2]
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        scale = min(MAX_WIDTH / width, MAX_HEIGHT / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    reference_images[agent_image] = img

# Load selected state images
SELECTED_IMAGES = [f for f in os.listdir(SELECTED_IMAGE_FOLDER) if f.endswith(('.png', '.jpg', '.jpeg'))]
for agent_image in SELECTED_IMAGES:
    img = cv2.imread(os.path.join(SELECTED_IMAGE_FOLDER, agent_image))
    height, width = img.shape[:2]
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        scale = min(MAX_WIDTH / width, MAX_HEIGHT / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    reference_images[f"selected_{agent_image}"] = img  # Prefix to distinguish

# Load starting screen reference image
START_IMAGES = [f for f in os.listdir(START_SCREEN_FOLDER) if f.endswith(('.png', '.jpg', '.jpeg'))]
start_reference = None
if START_IMAGES:
    start_img = cv2.imread(os.path.join(START_SCREEN_FOLDER, START_IMAGES[0]))
    height, width = start_img.shape[:2]
    if width > START_AREA[2] or height > START_AREA[3]:
        scale = min(START_AREA[2] / width, START_AREA[3] / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        start_img = cv2.resize(start_img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    start_reference = start_img


def capture_screen_area(x, y, width, height, full_screen=None):
    """Capture a specific area of the screen or crop from a full screen capture."""
    if full_screen is None:
        screenshot = pyautogui.screenshot()
        full_screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return full_screen[y:y + height, x:x + width]


def compare_images(screen_area, reference_img):
    """Compare two images using template matching."""
    result = cv2.matchTemplate(screen_area, reference_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val


# Initialize global dictionaries if not already set
if 'detection_times' not in globals():
    detection_times = {i: None for i in range(1, 6)}  # Initial selection time
if 'confirmation_times' not in globals():
    confirmation_times = {i: None for i in range(1, 6)}  # Confirmation time
if 'last_detected_agents' not in globals():
    last_detected_agents = {i: None for i in range(1, 6)}  # Last detected agent
if 'locked_agents' not in globals():
    locked_agents = {i: None for i in range(1, 6)}  # Locked (confirmed) agents
if 'last_update_times' not in globals():
    last_update_times = {i: 0 for i in range(1, 6)}  # Last update time for debounce
if 'start_screen_confirmed' not in globals():
    start_screen_confirmed = False  # Flag to stop further starting screen checks


def scan_and_identify_agents(start_time=None):
    """Scan the five areas and identify agents by comparing to reference images, tracking selection and confirmation times.
    Returns None if starting screen not detected initially, otherwise returns agent results."""
    global detection_times, confirmation_times, last_detected_agents, locked_agents, last_update_times, start_screen_confirmed

    # Initialize function-specific attributes if not set
    if not hasattr(scan_and_identify_agents, 'captured_start_screen_area'):
        scan_and_identify_agents.captured_start_screen_area = None
    if not hasattr(scan_and_identify_agents, 'start_score'):
        scan_and_identify_agents.start_score = 0.0

    # Capture full screen once
    full_screen = pyautogui.screenshot()
    full_screen = cv2.cvtColor(np.array(full_screen), cv2.COLOR_RGB2BGR)

    # Check starting screen only if not already confirmed
    if not start_screen_confirmed and start_reference is not None:
        start_screen_area = capture_screen_area(*START_AREA, full_screen=full_screen)
        start_score = compare_images(start_screen_area, start_reference)
        scan_and_identify_agents.start_score = start_score  # Store the confidence score
        scan_and_identify_agents.captured_start_screen_area = start_screen_area  # Store the captured area
        if start_score < START_THRESHOLD:
            return None  # Do not proceed if starting screen not detected
        else:
            start_screen_confirmed = True  # Set flag to stop further checks

    # Proceed with agent scanning only if start_time is set and starting screen was initially detected
    if start_time is None:
        return None

    agent_results = []
    current_time = time.perf_counter()

    for i, (x, y, width, height) in enumerate(AREAS):
        screen_area = capture_screen_area(x, y, width, height, full_screen=full_screen)

        best_match = None
        best_score = 0

        # Compare with both default and selected state images
        for agent_name, ref_img in reference_images.items():
            score = compare_images(screen_area, ref_img)
            if score > best_score and score >= MATCH_THRESHOLD:
                best_score = score
                best_match = agent_name

        # Adjust agent name to remove 'selected_' prefix and '.png' extension
        display_name = best_match.replace("selected_", "").replace(".png", "").lower() if best_match else "Unknown"

        # Calculate selection and confirmation times
        selection_time = detection_times[i + 1] - start_time if detection_times[i + 1] is not None else None
        confirmation_time = confirmation_times[i + 1] - start_time if confirmation_times[i + 1] is not None else None

        if locked_agents[i + 1] is not None:
            # If locked, use the locked agent and times, ignoring new matches
            display_name = locked_agents[i + 1].replace("selected_", "").replace(".png", "")
            selection_time = detection_times[i + 1] - start_time if detection_times[i + 1] is not None else None
            confirmation_time = confirmation_times[i + 1] - start_time if confirmation_times[
                                                                              i + 1] is not None else None
        elif best_match:
            if "selected_" in best_match:  # Selected state
                if last_detected_agents[i + 1] != best_match:  # Update only if agent changes
                    # Debounce: Update only if 1 second has passed since last update
                    if current_time - last_update_times[i + 1] >= 1.0:
                        detection_times[i + 1] = current_time
                        selection_time = detection_times[i + 1] - start_time
                        last_detected_agents[i + 1] = best_match  # Update last detected agent
                        last_update_times[i + 1] = current_time
            elif "selected_" not in best_match:  # Confirmed state
                if detection_times[i + 1] is None:  # No selection time yet
                    detection_times[i + 1] = current_time
                    confirmation_times[i + 1] = current_time
                    selection_time = detection_times[i + 1] - start_time
                    confirmation_time = confirmation_times[i + 1] - start_time
                    locked_agents[i + 1] = best_match  # Lock the agent
                elif confirmation_times[i + 1] is None or last_detected_agents[
                    i + 1] != best_match:  # Update confirmation
                    confirmation_times[i + 1] = current_time
                    confirmation_time = confirmation_times[i + 1] - start_time
                    if detection_times[i + 1] is None:  # No selection time, use confirmation time
                        detection_times[i + 1] = current_time
                        selection_time = detection_times[i + 1] - start_time
                    locked_agents[i + 1] = best_match  # Lock the agent
                last_detected_agents[i + 1] = best_match  # Update last detected agent

        agent_results.append((i + 1, display_name, best_score, selection_time, confirmation_time))

    return agent_results
