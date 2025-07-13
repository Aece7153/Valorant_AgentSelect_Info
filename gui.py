import customtkinter as ctk
import time
import os
from scanner import scan_and_identify_agents
from PIL import Image
from config import AGENT_ROLES

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

        # Table (as CTkScrollableFrame with CTkLabels inside)
        self.table_frame = ctk.CTkScrollableFrame(main_frame, height=280, corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, pady=5)
        self.tree_rows = [None] * 5  # Pre-allocate 5 rows for 5 areas
        self.row_labels = [[] for _ in range(5)]  # Store labels for each row

        # Table headers
        headers = ["Player", "Agent", "Role", "Confidence", "Selected In", "Confirmed In"]
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

    def update_row_content(self, row_idx, area_num, agent_name, score, sel_time, conf_time):
        """Update the content of a specific row without color flashing."""
        if self.tree_rows[row_idx] is None:
            # Create row if it doesn't exist
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
        values = [f"Player {area_num}", "", AGENT_ROLES.get(agent_name.lower(), "Unknown"), f"{score:.2f}", sel_time_str,
                  conf_time_str]

        # Update labels
        if agent_name in self.agent_images:
            labels[1].configure(image=self.agent_images[agent_name], text="")
        else:
            labels[1].configure(text="Unknown", image=None)
        for i, val in enumerate(values):
            labels[i].configure(text=val)

    def update_results(self):
        if self.start_time is not None:
            try:
                results = scan_and_identify_agents(self.start_time)
            except Exception as e:
                print("Scan error:", e)
                results = []

            # Update existing rows based on results
            for i, (area_num, agent_name, score, sel_time, conf_time) in enumerate(results or []):
                if i < 5:  # Limit to 5 areas
                    self.update_row_content(i, area_num, agent_name, score, sel_time, conf_time)


        self.root.after(150, self.update_results)  # Maintain 150ms interval

    def check_starting_screen(self):
        if self.start_time is None:
            result = scan_and_identify_agents(None)
            start_score = scan_and_identify_agents.start_score
            print(f"Starting screen confidence: {start_score:.2f}")
            if start_score > 0.61:
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