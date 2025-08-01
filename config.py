# config.py
from datetime import datetime

# Define the five areas to scan (x, y, width, height)
AREAS = [
    (578, 815, 142, 125),  # Area 1
    (731, 815, 142, 125),  # Area 2
    (884, 815, 142, 125),  # Area 3
    (1037, 815, 141, 125),  # Area 4
    (1189, 815, 144, 125)  # Area 5
]

# Define the starting screen area to detect (x, y, width, height)
START_AREA = (805, 603, 301, 191)  # Placeholder: Adjust to match your starting screen UI element

# Paths to folders containing reference agent images
DISPLAY_AGENTS_FOLDER = "Agents/"
DEFAULT_IMAGE_FOLDER = "agent_images/"  # Default state (no blue overlay, confirmed)
SELECTED_IMAGE_FOLDER = "agent_images_selected/"  # Selected state (with blue overlay)
START_SCREEN_FOLDER = "start_screen_images/"  # Starting screen reference image

# Comparison threshold
MATCH_THRESHOLD = 0.86  # Adjusted for robustness

# Maximum dimensions for resizing reference images
MAX_WIDTH = 141
MAX_HEIGHT = 125

# Starting screen detection threshold
START_THRESHOLD = 0.74 # Higher threshold for reliable starting screen detection

# Agent roles
AGENT_ROLES = {
    "jett": "duelist",
    "phoenix": "duelist",
    "reyna": "duelist",
    "yoru": "duelist",
    "raze": "duelist",
    "neon": "duelist",
    "iso": "duelist",
    "waylay": "duelist",

    "sage": "sentinel",
    "cypher": "sentinel",
    "killjoy": "sentinel",
    "chamber": "sentinel",
    "deadlock": "sentinel",
    "vyse": "sentinel",

    "brimstone": "smokes",
    "omen": "smokes",
    "astra": "smokes",
    "harbor": "smokes",
    "viper": "smokes",
    "clove": "smokes",

    "skye": "initiator",
    "breach": "initiator",
    "sova": "initiator",
    "fade": "initiator",
    "gekko": "initiator",
    "kayo": "initiator",
    "tejo": "initiator"
}

CSV_FILENAME = f"data/valorant_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
ICON_IMAGE_PATH = f"../../Downloads/Valorant_AgentSelect_Info-main (1)/Valorant_AgentSelect_Info-main/Icon_image/icon.ico"