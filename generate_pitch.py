# this is the first file to be run, mostly the GUI part
import logging
#FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
#logging.basicConfig(format=FORMAT, handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')])

import os, sys
import docx
import tkinter as tk
from tkinter.ttk import *
from tkinter import filedialog
from ttkthemes import ThemedTk
# import pytesseract
import template
import jf.analyze_jf
from shutil import copyfile
import ntpath



logger = logging.getLogger("pitch_generator")
logger.setLevel(logging.INFO)


fileh = logging.FileHandler('log.txt', 'w', encoding='utf-8')
formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
fileh.setFormatter(formatter)

log = logging.getLogger()  # root logger
for hdlr in log.handlers[:]:  # remove all old handlers
    log.removeHandler(hdlr)

log.addHandler(fileh)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class GUI(object):
    def __init__(self, win):
        self.w = win
        self.w.title("Generate Pitch")
        window.geometry("370x550")
        self.w.resizable(0, 0)

        # with ttk we need to configure styles:
        self.style = Style()
        self.style.configure("TButton", font=("Arial", 12, 'bold'), width=25)
        self.style.configure("TLabel", font=("Arial", 15), anchor=tk.W, width=30, foreground="darkblue")
        self.style.configure("TEntry", font=("Arial", 15), anchor=tk.W)
        self.style.configure("Status.TLabel", font=("Arial", 10), anchor=tk.W, width=50, foreground="darkblue")

        self.title_image = tk.PhotoImage(file=resource_path("pitch-doctor2.gif"))
        self.lb = Label(master=window, image=self.title_image)
        self.lb.grid(row=0, pady=(0,20), columnspan=3)

        self.bt_article = Button(master=self.w, text="Choose Article", command=self.open_article)
        self.bt_article.grid(row=1, column=1, padx=30)

        self.bt_article = Button(master=self.w, text="Debug: Convert All", command=self.open_all_article)
        self.bt_article.grid(row=2, column=1, padx=30)

        self.bt_exit = Button(master=self.w, text="Exit", command=tk.sys.exit)
        self.bt_exit.grid(row=4, column=1, padx=30, pady=20)

        self.lb_status = Label(master=self.w, text="", style="Status.TLabel")
        self.lb_status.grid(row=3, column=0, columnspan=2, pady=30)

        # this is the document we want to create
        self.doc = docx.Document()
        self.table = self.doc.add_table(16, 2, style="Light Grid Accent 1")
        self.article = None
        self.filename = ""

    def open_article(self):
        # text is a list of text pages
        self.filename = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=(("Pdf Files", "*.pdf"), ("All files", "*.*")))
        self.lb_status.config(text="Opened and extracted the text from the file")
        self.article = jf.analyze_jf.get_article_information(self.filename)
        self.generate_doc()

    def open_all_article(self):
        # text is a list of text pages
        self.filename = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=(("Pdf Files", "*.pdf"), ("All files", "*.*")))
        dir_name = ntpath.dirname(self.filename)
        pdfs = []
        for file in os.listdir(dir_name):
            if ".pdf" in file.lower():
                pdfs.append(file)
        print("here are all the files", pdfs)
        for file in pdfs:
            self.filename = dir_name + "/" + file
            self.lb_status.config(text=f"Opened and extracted the text from the file {file}")
            self.article = jf.analyze_jf.get_article_information(self.filename)
            self.generate_doc()

    def generate_doc(self):
        dest = self.filename.lower()
        dest = dest.replace(".pdf", "")
        dest = ntpath.basename(dest)
        template.set_col_widths(self.table)
        template.fill_in(self.table, self.article)
        self.doc.save(f"Pitch-{dest}.docx")
        #rename the log file
        copyfile("log.txt", f"pitch-{dest}.log")

        # delete the logger
        log = logging.getLogger()  # root logger
        for hdlr in log.handlers[:]:  # remove all old handlers
            log.removeHandler(hdlr)

        fileh = logging.FileHandler('log.txt', 'w', encoding='utf-8')
        formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
        fileh.setFormatter(formatter)
        log.addHandler(fileh)




# pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract"
window = ThemedTk(screenName="Contract Generator", theme="radiance")
gui = GUI(window)
# main loop
window.mainloop()