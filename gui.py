import customtkinter as ctk
import time
import os
import csv
from datetime import datetime
import pyautogui
from PIL import Image
import cv2
import numpy as np
from config import AGENT_ROLES, AREAS, CSV_FILENAME, ICON_IMAGE_PATH, START_THRESHOLD, DEFAULT_IMAGE_FOLDER,DISPLAY_AGENTS_FOLDER

from scanner import scan_and_identify_agents, capture_screen_area
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import ImageTk


class ValorantScannerGUI:
    def __init__(self, root):
        # Make app dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        # App Title
        self.root.title("Valorant Agent Scanner")
        self.root.geometry("1250x950")

        try:
            # App icon on top left of App Window
            self.root.iconbitmap(ICON_IMAGE_PATH)
        except Exception:
            pass

        self.start_time = None
        self.last_results = []
        self.area_images = [None] * 5
        self.area_labels = [None] * 5

        self.pages = {}
        self.current_page = None

        # Load agent images
        self.agent_images = {}
        for image_file in os.listdir(DISPLAY_AGENTS_FOLDER):
            if image_file.endswith('.png'):
                agent_name = os.path.splitext(image_file)[0]
                img_path = os.path.join(DISPLAY_AGENTS_FOLDER, image_file)
                img = Image.open(img_path).resize((100, 100), Image.Resampling.LANCZOS)
                self.agent_images[agent_name] = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))

        # Page container
        self.page_container = ctk.CTkFrame(self.root, corner_radius=10)
        self.page_container.pack(fill="both", expand=True, padx=12, pady=12)

        # Build both pages
        self.build_main_page()
        self.build_analytics_page()
        self.show_page('main')

    def build_main_page(self):
        page = ctk.CTkFrame(self.page_container)
        self.pages['main'] = page

        # Header Title
        header = ctk.CTkLabel(page, text="Valorant Agent Scanner",
                              font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(5, 10))

        # Scanning Text
        self.status_label = ctk.CTkLabel(page, text="Status: Waiting for Starting Screen",
                                         text_color="orange", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.pack(anchor="w", pady=(0, 8))

        # Lobby Team Comp Distribution
        self.role_summary_label = ctk.CTkLabel(page, text="Team Composition: None",
                                               font=ctk.CTkFont(size=18), text_color="white")
        self.role_summary_label.pack(anchor="w", pady=(0, 8))

        # Boxes for live agent select updates
        self.area_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.area_frame.pack(fill="x", pady=(0, 8))
        for i in range(5):
            label = ctk.CTkLabel(self.area_frame, text=f"Area {i+1}", width=142, height=125)
            label.pack(side="left", padx=5)
            self.area_labels[i] = label

        # Header column descriptions
        self.table_frame = ctk.CTkScrollableFrame(page, height=280, corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, pady=5)
        self.tree_rows = [None] * 5
        self.row_labels = [[] for _ in range(5)]
        headers = ["Player", "Agent", "Role", "Confidence", "Selected In", "Confirmed In"]
        header_row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 4))
        for col in headers:
            ctk.CTkLabel(header_row, text=col, font=ctk.CTkFont(size=20,weight="bold"),
                         width=150, anchor="center").pack(side="left", padx=5)

        # Export Button
        self.export_button = ctk.CTkButton(page, text="Export to CSV", command=self.export_to_csv)
        self.export_button.pack(anchor="se", padx=10, pady=(5, 10))


        # Toggle View Button
        self.toggle_view_button = ctk.CTkButton(page, text="Go to Analytics View", command=self.show_analytics_page)
        self.toggle_view_button.pack(anchor="se", padx=10, pady=(0, 5))




    def build_analytics_page(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages['analytics'] = page

        # Title For Analytics page
        ctk.CTkLabel(page, text="Analytics View",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        # Frame environment
        self.analytics_image_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.analytics_image_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Ensure the back button is properly configured
        self.back_btn = ctk.CTkButton(page, text="Back to Scanner", command=self.show_main_page)
        self.back_btn.pack(pady=(5, 15))

    # Switch Between Pages
    def show_page(self, name):
        # Hide the current page if it exists
        if self.current_page:
            self.pages[self.current_page].pack_forget()

        # Show the requested page
        self.pages[name].pack(fill="both", expand=True)
        self.current_page = name


    # Switch to Analytics Page
    def show_analytics_page(self):
        print("Switching to analytics page")
        self.show_page('analytics')
    # Switch to Main Page
    def show_main_page(self):
        print("Switching to main page")
        self.show_page('main')

    # Export Agent information and Time information into a csv directory
    def export_to_csv(self):
        # If there is no data, CANCEL: export
        if not self.last_results:
            self.status_label.configure(text="No data to export", text_color="red")
            return

        # Save to file path
        csv_filename = CSV_FILENAME
        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Area', 'Agent', 'Role', 'Confidence', 'Selected In (sec)', 'Confirmed In (sec)'])
                for area_num, agent_name, score, sel_time, conf_time in self.last_results:
                    role = AGENT_ROLES.get(agent_name.lower(), "Unknown")
                    sel_time_str = f"{sel_time:.2f}" if sel_time is not None else "Not selected"
                    conf_time_str = f"{conf_time:.2f}" if conf_time is not None else "Not confirmed"
                    writer.writerow([f"Area {area_num}", agent_name, role, f"{score:.2f}", sel_time_str, conf_time_str])
            self.status_label.configure(text=f"Exported to {csv_filename}", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Export failed: {str(e)}", text_color="red")

    #While scanning this method updates the times and agent information when in lobby
    def update_row_content(self, row_idx, area_num, agent_name, score, sel_time, conf_time):
        if self.tree_rows[row_idx] is None:
            self.tree_rows[row_idx] = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            self.tree_rows[row_idx].pack(fill="x", pady=1)
            self.row_labels[row_idx] = []
            for _ in range(6):
                label = ctk.CTkLabel(self.tree_rows[row_idx], width=150, anchor="center")
                label.pack(side="left", padx=5)
                self.row_labels[row_idx].append(label)

        labels = self.row_labels[row_idx]

        sel_time_str = f"{sel_time:.2f} sec" if sel_time is not None else "Not selected"
        conf_time_str = f"{conf_time:.2f} sec" if conf_time is not None else "Not confirmed"
        values = [f"Area {area_num}", "", AGENT_ROLES.get(agent_name.lower(), "Unknown"),
                  f"{score:.2f}", sel_time_str, conf_time_str]

        if agent_name in self.agent_images:
            labels[1].configure(image=self.agent_images[agent_name], text="")
        else:
            labels[1].configure(text="Unknown", image=None)
        for i, val in enumerate(values):
            if i != 1:
                labels[i].configure(text=val)

    def update_area_images(self, full_screen):
        for i, (x, y, width, height) in enumerate(AREAS):
            screen_area = capture_screen_area(x, y, width, height, full_screen)
            screen_area_rgb = cv2.cvtColor(screen_area, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(screen_area_rgb).resize((142, 125), Image.Resampling.LANCZOS)
            self.area_images[i] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(142, 125))
            self.area_labels[i].configure(image=self.area_images[i], text="")

    def update_results(self):
        if self.start_time is not None:
            try:
                full_screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
                self.last_results = scan_and_identify_agents(self.start_time) or []
                self.update_area_images(full_screen)
            except Exception as e:
                print("Scan error:", e)
                self.last_results = []

            for i, (area_num, agent_name, score, sel_time, conf_time) in enumerate(self.last_results):
                if i < 5:
                    self.update_row_content(i, area_num, agent_name, score, sel_time, conf_time)

            if self.last_results:
                role_counts = {"duelist": 0, "sentinel": 0, "smokes": 0, "initiator": 0}
                for _, agent_name, _, _, _ in self.last_results:
                    role = AGENT_ROLES.get(agent_name.lower(), "Unknown")
                    if role in role_counts:
                        role_counts[role] += 1
                summary = ", ".join(f"{count} {role.capitalize()}" for role, count in role_counts.items() if count > 0)
                self.role_summary_label.configure(text=f"Team Composition: {summary or 'None'}")
            else:
                self.role_summary_label.configure(text="Team Composition: None")

        self.root.after(150, self.update_results)

    # This function checks for the starting screen
    def check_starting_screen(self):
        if self.start_time is None:
            result = scan_and_identify_agents(None)
            start_score = scan_and_identify_agents.start_score
            print(f"Starting screen confidence: {start_score:.2f}")
            if start_score > START_THRESHOLD: #0.74
                # Start timer
                self.start_time = time.perf_counter()
                self.status_label.configure(text="Status: Scanning for agents", text_color="#5D8BF4")

        # Updates every half second
        self.root.after(500, self.check_starting_screen)
