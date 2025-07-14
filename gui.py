import customtkinter as ctk
import time
import os
import csv
from datetime import datetime
import pyautogui  # For screenshot capture
from scanner import scan_and_identify_agents, capture_screen_area
from PIL import Image
import cv2
import numpy as np
from config import AGENT_ROLES, AREAS

class ValorantScannerGUI:
    def __init__(self, root):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("Valorant Agent Scanner")
        self.root.geometry("1000x600")
        self.root.attributes('-topmost', True)

        try:
            self.root.iconbitmap('icon.ico')
        except Exception:
            pass

        self.start_time = None
        self.last_results = []  # Store the latest scan results for export and role composition
        self.area_images = [None] * 5  # Store CTkImage for each area
        self.area_labels = [None] * 5  # Store CTkLabel for each area

        # Layout
        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # Header
        header = ctk.CTkLabel(main_frame, text="Valorant Agent Scanner",
                              font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(pady=(5, 10))

        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="Status: Waiting for Starting Screen",
                                         text_color="orange", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.pack(anchor="w", pady=(0, 8))

        # Role Composition Display
        self.role_summary_label = ctk.CTkLabel(main_frame, text="Team Composition: None",
                                              font=ctk.CTkFont(size=12), text_color="white")
        self.role_summary_label.pack(anchor="w", pady=(0, 8))

        # Area Images Display
        self.area_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.area_frame.pack(fill="x", pady=(0, 8))
        for i in range(5):
            label = ctk.CTkLabel(self.area_frame, text=f"Area {i+1}", width=142, height=125)
            label.pack(side="left", padx=5)
            self.area_labels[i] = label

        # Table (as CTkScrollableFrame with CTkLabels inside)
        self.table_frame = ctk.CTkScrollableFrame(main_frame, height=280, corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, pady=5)
        self.tree_rows = [None] * 5  # Pre-allocate 5 rows for 5 areas
        self.row_labels = [[] for _ in range(5)]  # Store labels for each row

        # Table headers
        headers = ["PLayer", "Agent", "Role", "Confidence", "Selected In", "Confirmed In"]
        header_row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 4))
        for col in headers:
            ctk.CTkLabel(header_row, text=col, font=ctk.CTkFont(weight="bold"),
                         width=150, anchor="center").pack(side="left", padx=5)

        # Load agent images
        self.agent_images = {}
        agent_image_dir = "agent_images"
        for image_file in os.listdir(agent_image_dir):
            if image_file.endswith(('.png', '.jpg', '.jpeg')):
                agent_name = os.path.splitext(image_file)[0]  # Remove .png
                img_path = os.path.join(agent_image_dir, image_file)
                img = Image.open(img_path).resize((100, 100), Image.Resampling.LANCZOS)  # Resize for table
                self.agent_images[agent_name] = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))

        # Export button
        self.export_button = ctk.CTkButton(main_frame, text="Export to CSV", command=self.export_to_csv)
        self.export_button.pack(anchor="se", padx=10, pady=10)  # Bottom-right corner

    def export_to_csv(self):
        """Export the latest scan results to a CSV file."""
        if not self.last_results:
            self.status_label.configure(text="No data to export", text_color="red")
            return
        csv_filename = f"valorant_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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

    def update_row_content(self, row_idx, area_num, agent_name, score, sel_time, conf_time):
        """Update the content of a specific row without color flashing."""
        if self.tree_rows[row_idx] is None:
            self.tree_rows[row_idx] = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            self.tree_rows[row_idx].pack(fill="x", pady=1)
            self.row_labels[row_idx] = []
            for _ in range(6):  # Now 6 columns (including Role)
                label = ctk.CTkLabel(self.tree_rows[row_idx], width=150, anchor="center")
                label.pack(side="left", padx=5)
                self.row_labels[row_idx].append(label)

        row = self.tree_rows[row_idx].pack(fill="x", pady=5)
        labels = self.row_labels[row_idx]

        # Prepare values
        sel_time_str = f"{sel_time:.2f} sec" if sel_time is not None else "Not selected"
        conf_time_str = f"{conf_time:.2f} sec" if conf_time is not None else "Not confirmed"
        values = [f"Area {area_num}", "", AGENT_ROLES.get(agent_name.lower(), "Unknown"), f"{score:.2f}", sel_time_str,
                  conf_time_str]

        # Update labels
        if agent_name in self.agent_images:
            labels[1].configure(image=self.agent_images[agent_name], text="")
        else:
            labels[1].configure(text="Unknown", image=None)
        for i, val in enumerate(values):
            labels[i].configure(text=val)

    def update_area_images(self, full_screen):
        """Update the displayed images for the five areas."""
        for i, (x, y, width, height) in enumerate(AREAS):
            # Capture area from full screenshot
            screen_area = capture_screen_area(x, y, width, height, full_screen)
            # Convert BGR (OpenCV) to RGB (PIL)
            screen_area_rgb = cv2.cvtColor(screen_area, cv2.COLOR_BGR2RGB)
            # Create PIL Image and resize to match area dimensions
            pil_img = Image.fromarray(screen_area_rgb).resize((142, 125), Image.Resampling.LANCZOS)
            # Create CTkImage
            self.area_images[i] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(142, 125))
            # Update label
            self.area_labels[i].configure(image=self.area_images[i], text="")

    def update_results(self):
        if self.start_time is not None:
            try:
                # Capture full screen once for efficiency
                full_screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
                self.last_results = scan_and_identify_agents(self.start_time) or []
                # Update area images
                self.update_area_images(full_screen)
            except Exception as e:
                print("Scan error:", e)
                self.last_results = []

            # Update existing rows based on results
            for i, (area_num, agent_name, score, sel_time, conf_time) in enumerate(self.last_results):
                if i < 5:  # Limit to 5 areas
                    self.update_row_content(i, area_num, agent_name, score, sel_time, conf_time)

            # Update role composition display
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

        self.root.after(150, self.update_results)  # Maintain 150ms interval

    def check_starting_screen(self):
        if self.start_time is None:
            result = scan_and_identify_agents(None)
            start_score = scan_and_identify_agents.start_score
            print(f"Starting screen confidence: {start_score:.2f}")
            if start_score > 0.58:
                self.start_time = time.perf_counter()
                self.status_label.configure(text="Status: Scanning", text_color="#5D8BF4")
        self.root.after(1000, self.check_starting_screen)

def main():
    root = ctk.CTk()
    app = ValorantScannerGUI(root)
    app.check_starting_screen()
    app.update_results()
    root.mainloop()

if __name__ == "__main__":
    main()
