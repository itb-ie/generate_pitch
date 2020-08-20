# this is the first file to be run, mostly the GUI part
from template import *
import subprocess
import os
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
import pandas as pd
import tkinter as tk
from tkinter.ttk import *
from tkinter import filedialog
from ttkthemes import ThemedTk
from pdf2image import pdfinfo_from_path, convert_from_path
import pytesseract
import template
import jf.analyze_jf


class GUI(object):
    def __init__(self, win):
        self.w = win
        self.w.title("Generate Pitch")
        # window.geometry("1400x700")
        self.w.resizable(0, 0)

        # with ttk we need to configure styles:
        self.style = Style()
        self.style.configure("TButton", font=("Arial", 12, 'bold'), width=25)
        self.style.configure("TLabel", font=("Arial", 15), anchor=tk.W, width=30, foreground="darkblue")
        self.style.configure("TEntry", font=("Arial", 15), anchor=tk.W)
        self.style.configure("Status.TLabel", font=("Arial", 10), anchor=tk.W, width=70, foreground="darkblue")

        self.title_image = tk.PhotoImage(file="pitch-doctor.gif")
        self.lb = Label(master=window, image=self.title_image)
        self.lb.grid(row=0, pady=(0,20), columnspan=3)

        self.bt_article = Button(master=self.w, text="Choose Article", command=self.open_article)
        self.bt_article.grid(row=1, column=1, padx=30)

        self.bt_exit = Button(master=self.w, text="Exit", command=tk.sys.exit)
        self.bt_exit.grid(row=4, column=1, padx=30, pady=20)

        self.lb_status = Label(master=self.w, text="", style="Status.TLabel")
        self.lb_status.grid(row=3, column=0, columnspan=2, pady=30)

        # this is the document we want to create
        self.doc = docx.Document()
        self.table = self.doc.add_table(16, 2, style="Light Grid Accent 1")
        self.article = None

    def open_article(self):
        # text is a list of text pages
        filename = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=(("Pdf Files", "*.pdf"), ("All files", "*.*")))
        self.lb_status.config(text="Opened and extracted the text from the file")

        #'''
        # the fmt might be important because with JPG I might be losing some accuracy
        info = pdfinfo_from_path(filename, userpw=None, poppler_path=None)

        maxpages = info["Pages"]
        print("maxpages={}".format(maxpages))
        text = []
        for page in range(1, maxpages+1, 5):
            print("Comvertesc intre {} si {}".format(page, min((page + 5 - 1, maxpages))))
            images = convert_from_path(filename, dpi=400, first_page=page, last_page=min(page + 5 - 1, maxpages))

            # images = pdf2image.convert_from_path(filename, dpi=400, fmt='ppm', grayscale=True)
            print("dupa ce am convertit am {} pages".format(len(images)))

            # go page by page (image in images)
            for image in images:
                # convert one page to text using the tesseract OCR:
                print("Inside the for, apelez pe image_to_string")
                text.append(pytesseract.image_to_string(image, config='--psm 4', lang="eng"))

        with open("converted.txt", "w") as fd:
            for idx, page in enumerate(text, 1):
                # save it to text
                fd.write(jf.analyze_jf.start_marker + page)
                # not sure if I need to split by pages at this time
                fd.write(jf.analyze_jf.end_marker)
        #'''

        self.article = jf.analyze_jf.get_article_information("converted.txt")
        self.generate_doc()

    def generate_doc(self):
        template.set_col_widths(self.table)
        template.fill_in(self.table, self.article)
        self.doc.save("Pitch.docx")


pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract"
window = ThemedTk(screenName="Contract Generator", theme="radiance")
gui = GUI(window)
# main loop
window.mainloop()