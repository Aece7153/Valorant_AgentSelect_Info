import customtkinter as ctk
from gui import ValorantScannerGUI

def main():
    root = ctk.CTk()
    app = ValorantScannerGUI(root)
    app.check_starting_screen()
    app.update_results()
    root.mainloop()

if __name__ == "__main__":
    main()
