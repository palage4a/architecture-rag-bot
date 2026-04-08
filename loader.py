import argparse
from langchain_community.document_loaders import MWDumpLoader

parser = argparse.ArgumentParser(description="Load documents from MediaWiki XML dump")
parser.add_argument("file", help="Path to the source XML file")
args = parser.parse_args()

loader = MWDumpLoader(
    file_path=args.file,
    encoding="utf8",
    # namespaces = [0,2,3] Optional list to load only specific namespaces. Loads all namespaces by default.
    skip_redirects=True,  # will skip over pages that just redirect to other pages (or not if False)
    stop_on_error=False,  # will skip over pages that cause parsing errors (or not if False)
)
documents = loader.load()
print(f"You have {len(documents)} document(s) in your data ")