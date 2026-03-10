import os

# Make sure pandoc and xelatex are findable
os.environ["PATH"] = (
    r"C:\\Users\\Marketing\\AppData\\Local\\TinyTeX\\TinyTeX\\bin\\windows" + ";" +
    r"C:\\Users\\Marketing\\AppData\\Local\\Programs\\bin" + ";" +
    os.environ.get("PATH", "")
)

os.chdir(r"C:\\Users\\Marketing\\Desktop\\EIPL\\ENVIRO_DL_DOC")

# Generate DOCX directly from Markdown
os.system('pandoc USER_GUIDE.md -s --toc -o enviro_dl_guide.docx')

# Generate PDF directly from Markdown using xelatex for Unicode support
os.system('pandoc USER_GUIDE.md -s --toc --pdf-engine=xelatex -o enviro_dl_guide.pdf')
