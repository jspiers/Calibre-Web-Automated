import json
import os
import sys
import time
import subprocess

supported_book_formats = ['azw', 'azw3', 'azw4', 'cbz', 'cbr', 'cb7', 'cbc', 'chm', 'djvu', 'docx', 'epub', 'fb2', 'fbz', 'html', 'htmlz', 'lit', 'lrf', 'mobi', 'odt', 'pdf', 'prc', 'pdb', 'pml', 'rb', 'rtf', 'snb', 'tcr', 'txtz']
hierarchy_of_success = ['lit', 'mobi', 'azw', 'epub', 'azw3', 'fb2', 'fbz', 'azw4',  'prc', 'odt', 'lrf', 'pdb',  'cbz', 'pml', 'rb', 'cbr', 'cb7', 'cbc', 'chm', 'djvu', 'snb', 'tcr', 'pdf', 'docx', 'rtf', 'html', 'htmlz', 'txtz']

dirs = {}
with open('/etc/calibre-web-automator/dirs.json', 'r') as f:
    dirs: dict[str, str] = json.load(f)

# Both folders are assigned by user during setup
import_folder = f"{dirs['import_folder']}/"
ingest_folder = f"{dirs['ingest_folder']}/" # Dir where new files are looked for to process and subsequently deleted
arg = sys.argv[1] # path of the book we're targeting

def main(filepath = arg):
    # Check if is a directory. Inotifywait won't detect files inside folders if the folder was moved rather than copied
    if os.path.isdir(filepath):
        print(os.listdir(filepath))
        for filename in os.listdir(filepath):
            f = os.path.join(filepath, filename)
            main(f)
        return

    t_start = time.time()

    is_epub = True if filepath.endswith('.epub') else False

    if not is_epub: # Books require conversion
        print("\n[new-book-processor]: No epub files found in the current directory. Starting conversion process...")
        can_convert, import_format = can_convert_check(filepath)
        print(f"[new-book-processor]: Converting file from to epub format...\n")
        
        if (can_convert):
            time_total_conversion = convert_book(filepath, import_format)
            print(f"\n[new-book-processor]: conversion to .epub format completed succsessfully in {time_total_conversion:.2f} seconds.")
            print("[new-book-processor]: All new epub files have now been moved to the calibre-web import folder.")
        else:
            print(f"Cannot convert {filepath}")
            
    else: # Books only need copying to the import folder
        print(f"\n[new-book-processor]: Found  epub file from the most recent download.")
        print("[new-book-processor]: Moving resulting files to calibre-web import folder...\n")
        move_epub(filepath, is_epub)
        print(f"[new-book-processor]: Copied epub file to calibre-web import folder.")

    t_end = time.time()
    running_time = t_end - t_start

    print(f"[new-book-processor]: Processing of new files completed in {running_time:.2f} seconds.\n\n")
    delete_file(filepath)

def convert_book(filepath, import_format: str) -> float:
    """Uses the following terminal command to convert the books provided using the calibre converter tool:\n\n--- ebook-convert myfile.input_format myfile.output_format\n\nAnd then saves the resulting epubs to the calibre-web import folder."""
    t_convert_total_start = time.time()
    t_convert_book_start = time.time()
    filename = filepath.split('/')[-1]
    print(f"[new-book-processor]: START_CON: Converting {filename}...\n")
    os.system(f'ebook-convert "{filepath}" "{import_folder}{(filename.split(f".{import_format}"))[0]}.epub"')
    t_convert_book_end = time.time()
    time_book_conversion = t_convert_book_end - t_convert_book_start
    print(f"\n[new-book-processor]: END_CON: Conversion of {filename} complete in {time_book_conversion:.2f} seconds.\n")

    t_convert_total_end = time.time()
    time_total_conversion = t_convert_total_end - t_convert_total_start

    return time_total_conversion


def can_convert_check(filepath):
    """When no epubs are detected in the download, this function will go through the list of new files 
    and check for the format the are in that has the highest chance of successful conversion according to the input format hierarchy list 
    provided by calibre"""
    can_convert = False
    import_format = ''
    for format in hierarchy_of_success:
        can_be_converted = True if filepath.endswith(f'.{format}') else False
        if can_be_converted:
            can_convert = True
            import_format = format
            break

    return can_convert, import_format


def move_epub(filepath, is_epub) -> None:
    """Moves the epubs from the download folder to the calibre-web import folder"""
    print(f"[new-book-processor]: Moving {filepath}...")
    filename = filepath.split('/')[-1]
    os.system(f'cp "{filepath}" "{import_folder}{filename}"')

def delete_file(filepath) -> None:
    """Empties the ingest folder"""
    os.remove(filepath)
    subprocess.run(["find", f"{ingest_folder}", "-type", "d", "-empty", "-delete"])

if __name__ == "__main__":
    main()
