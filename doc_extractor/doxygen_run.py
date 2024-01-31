import os, subprocess
from bs4 import BeautifulSoup

PATH_DIR = "C:/Users/claud/OneDrive/Desktop/Montreal_DIRO_work/validations-libs-1.9.0/validations-libs-1.9.0"
OUT_DIR = 'C:/Users/claud/OneDrive/Desktop/Montreal_DIRO_work/generated_doc/'
OUT_HTML = 'C:/Users/claud/OneDrive/Desktop/Montreal_DIRO_work/generated_doc/html/'


# def clean_tag(node):
#     return str(node).replace('{http://docbook.org/ns/docbook}', '').strip()


def filter_class_paths(file_paths):
    filter_list = []

    for file in file_paths:
        if 'class' in file:
            filter_list.append(file)

    return filter_list




def generate_doxygen_config(config_file, input_dir, out_dir):
    with open(config_file, 'r', encoding='utf-8', errors='ignore') as config:
        lines = config.readlines()

    with open(config_file, 'w', encoding='utf-8', errors='ignore') as config:
        for line in lines:
            if line.strip().startswith("INPUT "):
                config.write(f"INPUT = {input_dir}\n")
            if line.strip().startswith("OUTPUT_DIRECTORY "):
                config.write(f"OUTPUT_DIRECTORY = {out_dir}\n")
            else:
                config.write(line)



# class DocBookParser:
#     def __init__(self, file_paths, root):
#         """
#         Initializes the parser with a list of file paths to DocBook XML files.
#         """
#         self.file_paths = file_paths
#         self.trees = [self._parse_xml(file, root) for file in self.file_paths]
#
#     def _parse_xml(self, file_path, root):
#         """
#         Parses an XML file and returns the ElementTree object.
#         """
#         file_full_path = os.path.join(root, file_path)
#         if not os.path.exists(file_full_path):
#             raise FileNotFoundError(f"The file {file_full_path} does not exist.")
#         try:
#             tree = ET.parse(file_full_path)
#             return tree
#         except ET.ParseError as e:
#             raise Exception(f"Error parsing {file_full_path}: {e}")
#
#     def get_titles(self):
#         """
#         Example method to get titles from the DocBook files.
#         """
#         titles = {}
#         for tree in self.trees:
#             root = tree.getroot()
#             #print(root)
#             for elem in root:
#                 if clean_tag(elem.tag) == 'section':
#                     for sub_elem in elem:
#                         if clean_tag(sub_elem.tag) == 'title':
#                             print("title", sub_elem.text)
#                         if clean_tag(sub_elem.tag) == 'para':
#                             print(sub_elem)
#                             for literal in sub_elem:
#                                 print(literal.tag)
#                                 for out in literal:
#                                     print("doc ", out)
#
#
#                             #titles.append(clean_tag(section.text))
#         return titles

    # You can add more methods here to extract different types of data

# Example usage











def parse_documentation(html_folder):

    for file in os.listdir(html_folder):
        path = os.path.join(html_folder,file)
        parse_html_doc(path)


def parse_html_doc(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'lxml')

        memitems = soup.find_all("div", class_="memitem")
        results = {}

        for memitem in memitems:

            # Extracting the memtitle
            contents = memitem.contents
            if contents:
                for c in contents:
                    print(c)


                    # Extracting the fragment from memdoc
                    # memdoc = memitem.find("div", class_="memdoc")
                    # if memdoc:
                    #     fragment = memdoc.find("pre", class_="fragment")
                    #     if fragment:
                    #         doc = fragment.get_text(strip=True)
                    #         results[title] = doc

        # Printing or returning the results
        for title, doc in results.items():
            print(f"{title}: {doc}")

    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")



def run_doxygen():

    generate_doxygen_config('config_file', PATH_DIR, OUT_DIR)#
#
    subprocess.run(["C:/Program Files/doxygen/bin/doxygen.exe", 'config_file'])
    parse_html_doc("C:\\Users\\claud\\OneDrive\\Desktop\\Montreal_DIRO_work\\generated_doc\\html\\classvalidations__libs_1_1validation__logs_1_1_validation_logs.html")


run_doxygen()




