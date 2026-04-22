#!/usr/bin/env python3
"""
Extract all boss pages from Hollow Knight wiki XML dump.
Converts wikitext to clean markdown format.
"""

import argparse
import xml.etree.ElementTree as ET
import re
import os

BOSS_CATEGORY = "Category:Bosses (Hollow Knight)"
NAMESPACE = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}

NON_BOSS_KEYWORDS = [
    "Category:", "File:", "Image:", "Template:", "Talk:", "User:",
    "Hollow Knight (game)", "Hollow Knight: Silksong", "Silksong",
    "Enemies (Hollow Knight)", "Items (Hollow Knight)", "Areas (Hollow Knight)",
    "Areas", "Items", "Charms", "Geo", "SOUL", "Essence", "Shade",
    "Dream Nail", "Dream Realm", "Hallownest", "Steel Soul Mode",
    "Godhome", "Hall of Gods", "Pantheon of the Knight", "Colosseum of Fools",
    "The Knight", "The Hunter", "Hollow Knight Kickstarter",
    "Steel Assassin Sharpe", "Leg Eater", "Iselda", "Tiso",
    "Greenpath", "Forgotten Crossroads", "Fungal Wastes", "City of Tears",
    "Deepnest", "Resting Grounds", "Crystal Peak", "Howling Cliffs",
    "Queen's Gardens", "Fog Canyon", "Kingdom's Edge", "White Palace",
    "Abyss", "Stag Station", "Lore Tablets", "Spirits",
    "Mothwing Cloak", "King's Pass", "Dirtmouth", "Crossroads",
    "Blue Lake", "Waterways", "Nail", "Spell", "Charm",
    "Grub", "Geo Deposit", "Whispering Root", "Lifeblood Cocoon",
    "Wanderer's Journal", "Hunter's Journal", "Hallownest Seal",
]

KNOWN_BOSSES = {
    "False Knight", "Hollow Knight", "Hornet Protector", "Mantis Lords",
    "Soul Master", "Dung Defender", "Watcher Knight", "Vengefly King",
    "Brooding Mawlek", "The Collector", "Flukemarm", "Nosk",
    "Traitor Lord", "Gruz Mother", "Broken Vessel", "Crystal Guardian",
    "Oblobbles", "Massive Moss Charger", "Uumuu", "Zote",
    "Grimm", "Nightmare King Grimm", "Hive Knight", "God Tamer",
    "Radiance", "The Hollow Knight",
    "Elder Hu", "Galien", "Gorb", "Markoth", "Marmu", "No Eyes", "Xero",
    "Soul Warrior", "Paintmaster Sheo", "Brothers Oro & Mato", "Great Nailsage Sly",
    "Failed Champion", "Grey Prince Zote", "Lost Kin", "Hornet Sentinel",
    "Soul Tyrant", "White Defender", "Pure Vessel", "Absolute Radiance",
    "Winged Nosk", "Sisters of Battle", "Enraged Guardian",
}


def is_likely_boss(name):
    """Check if a name is likely a boss based on patterns."""
    name_lower = name.lower()

    if name in KNOWN_BOSSES:
        return True

    for keyword in NON_BOSS_KEYWORDS:
        if keyword.lower() in name_lower:
            return False

    return True


def extract_wikitext(page, ns):
    """Extract wikitext content from a page."""
    text_elem = page.find('mw:revision/mw:text', ns)
    if text_elem is not None and text_elem.text:
        return text_elem.text
    return ""


def discover_bosses(root, ns):
    """Find the Bosses category page and extract boss names from wiki links."""
    bosses = set()

    for page in root.findall('.//mw:page', ns):
        title_elem = page.find('mw:title', ns)
        if title_elem is None or title_elem.text != BOSS_CATEGORY:
            continue

        content = extract_wikitext(page, ns)

        wiki_link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
        for match in wiki_link_pattern.finditer(content):
            name = match.group(1).strip()
            if name and is_likely_boss(name):
                bosses.add(name)

        break

    return sorted(bosses)


def clean_text(text):
    """Clean wikitext markup from a string."""
    if not text:
        return ""

    result = text

    result = re.sub(r'<ref[^>]*>.*?</ref>', '', result, flags=re.DOTALL)
    result = re.sub(r'<ref[^>]*/>', '', result)
    result = re.sub(r'<[^>]+>', '', result)

    result = re.sub(r'<br\s*/?>', ' ', result)
    result = re.sub(r'<i>(.*?)</i>', r'\1', result)
    result = re.sub(r'<b>(.*?)</b>', r'\1', result)

    result = re.sub(r"'''(.+?)'''", r'\1', result)
    result = re.sub(r"''(.+?)''", r'\1', result)

    result = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', result)
    result = re.sub(r'\[\[([^\]]+)\]\]', r'\1', result)

    result = re.sub(r'\[\[File:[^\]]+\]\]', '', result)
    result = re.sub(r'\[\[File:([^\]|]+)\|([^\]]+)\]\]', '', result)

    result = re.sub(r'\{\{G\|(\d+)(?:\|\d+)*\}\}', r'\1 Geo', result)
    result = re.sub(r'\{\{G\|\d+\|(\d+)\}\}', r'\1 Geo', result)
    result = re.sub(r'\{\{G\}\}', 'Geo', result)

    result = re.sub(r'\{\{HK CP Icon Mini\|[^}]+\}\}', '', result)
    result = re.sub(r'\{\{HK CP Header\|[^}]+\}\}', '', result)

    result = re.sub(r'\[https?://[^\s]+\]', '', result)

    result = re.sub(r'\{\{[^}]+\}\}', '', result)
    result = re.sub(r'\}\}', '', result)
    result = re.sub(r'\{\{', '', result)

    result = re.sub(r'\s+', ' ', result)

    return result.strip()


def extract_infobox(text):
    """Extract infobox data from wikitext."""
    infobox_match = re.search(r'\{\{HK Infobox Boss', text)
    if not infobox_match:
        return None

    start = infobox_match.start()
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    infobox_text = text[start:end]
    infobox_text = clean_text(infobox_text)

    data = {}
    fields_to_extract = ['health', 'gender', 'drops', 'theme', 'va', 'backer', 'numbers_required']

    for field in fields_to_extract:
        pattern = rf'{field}\s*=\s*([^\n]+)'
        match = re.search(pattern, infobox_text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value and value != '':
                data[field] = value

    return data if data else None


def extract_quote(text):
    """Extract quote from wikitext."""
    quote_match = re.search(r'\{\{Quote\s*', text)
    if not quote_match:
        return None

    start = quote_match.start()
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    quote_text = text[start:end]
    quote_text = clean_text(quote_text)

    source = None
    if 'Hr' in quote_text:
        parts = re.split(r'\bHr\b', quote_text, maxsplit=1)
        quote = parts[0].strip()
        if len(parts) > 1:
            source = parts[1].strip().strip('=').strip()
    else:
        quote = quote_text.strip()

    if not quote:
        return None

    return {'quote': quote, 'source': source}


def wikitext_to_markdown(text):
    """Convert wikitext to markdown format."""
    if not text:
        return ""

    result = text

    result = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n## \1\n\n', result, flags=re.DOTALL)
    result = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n### \1\n\n', result, flags=re.DOTALL)
    result = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n\n#### \1\n\n', result, flags=re.DOTALL)
    result = re.sub(r'<hr\s*/?>', '\n\n---\n\n', result)

    result = re.sub(r'<ref[^>]*>.*?</ref>', '', result, flags=re.DOTALL)
    result = re.sub(r'<ref[^>]*/>', '', result)
    result = re.sub(r'<[^>]+>', '', result)

    result = re.sub(r"'''(.+?)'''", r'**\1**', result)
    result = re.sub(r"''(.+?)''", r'*\1*', result)

    result = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', result)
    result = re.sub(r'\[\[([^\]]+)\]\]', r'\1', result)

    result = re.sub(r'\[\[File:[^\]]+\]\]', '', result)
    result = re.sub(r'\[\[File:([^\]|]+)\|([^\]]+)\]\]', '', result)

    result = re.sub(r'\{\{Navbar\|[^}]+\}\}', '', result)
    result = re.sub(r'\{\{Clear\}\}', '', result)
    result = re.sub(r'\{\{Disclaimer\|[^}]+\}\}', '', result)
    result = re.sub(r'\{\{HK CP Header\|[^}]+\}\}', '', result)

    result = re.sub(r'\[\[Category:[^\]]+\]\]', '', result)
    result = re.sub(r'\{\{HK CP Icon Mini\|[^}]+\}\}', '', result)

    result = re.sub(r'\{\{Gallery[^}]*\}\}', '', result)
    result = re.sub(r'\|Image\d+', '\n', result)
    result = re.sub(r'\|Title\s*=', '\n## ', result)

    result = re.sub(r'\{\{TabbedPOI[^}]*\}\}', '', result)
    result = re.sub(r'\{\{TabbedDialogue[^}]*\}\}', '', result)
    result = re.sub(r'\{\{Stagger[^}]*\}\}', '', result)
    result = re.sub(r'\{\{Achievement[^}]*\}\}', '', result)
    result = re.sub(r'\{\{Refs[^}]*\}\}', '', result)
    result = re.sub(r'\{\{HK Nav Enemies\}\}', '', result)
    result = re.sub(r'\{\{HK DN[^}]*\}\}', '', result)
    result = re.sub(r'\{\{HK GM Boss[^}]*\}\}', '', result)
    result = re.sub(r'\{\{G\|[^}]+\}\}', '', result)
    result = re.sub(r'\{\{Quote[^}]*\}\}', '', result)
    result = re.sub(r'\{\{HK Infobox Boss[^}]*\}\}', '', result)

    result = re.sub(r'\{\{[^}]+\}\}', '', result)
    result = re.sub(r'\}\}', '', result)
    result = re.sub(r'\{\{', '', result)

    result = re.sub(r'\{\{PAGENAME\}\}', '', result)

    result = re.sub(r'\[\[File:.*?\|([^\]]+)\]\]', '', result)
    result = re.sub(r'\[\[File:.*?\]\]', '', result)

    result = re.sub(r'\[right\|[^\]]+\]', '', result)
    result = re.sub(r'\[thumb\|[^\]]+\]', '', result)
    result = re.sub(r'\[center\|[^\]]+\]', '', result)
    result = re.sub(r'\[left\|[^\]]+\]', '', result)

    result = re.sub(r'^right\|.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^thumb\|.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^center\|.*$', '', result, flags=re.MULTILINE)

    result = re.sub(r'\[[a-z]{2}:[^\]]+\]', '', result)

    result = re.sub(r'\b\w+\.png!', '', result)
    result = re.sub(r'\b\w+\.jpg!', '', result)

    result = re.sub(r'\[right\|[^\]]+\]', '', result)
    result = re.sub(r'\[thumb\|[^\]]+\]', '', result)
    result = re.sub(r'\[center\|[^\]]+\]', '', result)

    result = re.sub(r'^[a-z]{2}:[A-Za-z ]+$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^[a-z]{2}:[А-Яа-я ]+$', '', result, flags=re.MULTILINE)

    result = re.sub(r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', '', result, flags=re.MULTILINE)

    result = re.sub(r'^Screenshot\s+HK\s+.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^Mapshot\s+HK\s+.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^Godhome\s+Arena\s+.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^[A-Z][a-z]+\s+\(Hitless\)\s+Hollow\s+Knight$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^Promotional\s+art$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^Concept\s+sketch$', '', result, flags=re.MULTILINE)

    result = re.sub(r'^Location\s+in\s+.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^Arena\s+in\s+.*$', '', result, flags=re.MULTILINE)
    result = re.sub(r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', '', result, flags=re.MULTILINE)

    result = re.sub(r'\|[A-Za-z]+\d*\s*=', '\n', result)

    result = re.sub(r'Title\d+_[A-Za-z]+\d*', '\n', result)
    result = re.sub(r'Event\d+', '\n', result)
    result = re.sub(r'Dialogue\d+', '', result)

    result = re.sub(r'Achievement\s*\|', '', result)
    result = re.sub(r'columns\s*=\s*\d+', '', result)

    result = re.sub(r'^\s*[-|]+\s*$', '', result, flags=re.MULTILINE)

    result = re.sub(r'={2,}\s*(.+?)\s*={2,}', r'\n\n## \1\n\n', result)

    result = re.sub(r'\n(##[^\n]*)', r'\n\n\1\n', result)
    result = re.sub(r'\n(###[^\n]*)', r'\n\n\1\n', result)
    result = re.sub(r'\n(####[^\n]*)', r'\n\n\1\n', result)

    result = re.sub(r'^\s+', '', result, flags=re.MULTILINE)
    result = re.sub(r'\s+$', '', result)
    result = re.sub(r'\n\n\n+', '\n\n', result)
    result = re.sub(r'\n\s*\n', '\n\n', result)

    return result.strip()


def format_infobox_markdown(infobox):
    """Format infobox data as markdown."""
    if not infobox:
        return ""

    lines = ["### Stats\n"]

    field_map = {
        'health': 'Health',
        'gender': 'Gender',
        'drops': 'Drops',
        'theme': 'Theme',
        'va': 'Voice Actor',
        'backer': 'Backer',
        'numbers_required': 'Numbers Required',
    }

    for key, label in field_map.items():
        if key in infobox and infobox[key]:
            value = infobox[key].strip()
            if value:
                lines.append(f"**{label}:** {value}")

    return '\n'.join(lines) if len(lines) > 1 else ""


def format_quote_markdown(quote):
    """Format quote as markdown blockquote."""
    if not quote:
        return ""

    result = f"> {quote['quote']}"
    if quote.get('source'):
        result += f"\n> \n> *— {quote['source']}*"

    return result


def clean_content(content):
    """Clean up the content after conversion."""
    lines = content.split('\n')
    cleaned = []
    prev_empty = False

    for line in lines:
        line = line.strip()
        if not line:
            if not prev_empty:
                cleaned.append('')
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    result = '\n'.join(cleaned)
    result = re.sub(r'\n(##[^\n]*)\n([^\n])', r'\n\n\1\n\n\2', result)
    result = re.sub(r'\n(###[^\n]*)\n([^\n])', r'\n\n\1\n\n\2', result)
    result = re.sub(r'\n(####[^\n]*)\n([^\n])', r'\n\n\1\n\n\2', result)

    return result


def sanitize_filename(name):
    """Sanitize a filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.replace(' ', '_')
    return name


def extract_boss_pages(xml_path, output_dir=None):
    """Main function to discover and extract all bosses."""
    print(f"Parsing XML file: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    print("Discovering bosses from category page...")
    bosses = discover_bosses(root, NAMESPACE)
    print(f"Found {len(bosses)} bosses")

    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "knowledge_base")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    print("Extracting boss pages...")
    extracted = []

    for page in root.findall('.//mw:page', NAMESPACE):
        title_elem = page.find('mw:title', NAMESPACE)
        if title_elem is None:
            continue

        title = title_elem.text

        if title in bosses:
            content = extract_wikitext(page, NAMESPACE)

            infobox = extract_infobox(content)
            quote = extract_quote(content)

            markdown = wikitext_to_markdown(content)
            markdown = clean_content(markdown)

            extracted.append({
                'title': title,
                'content': markdown,
                'infobox': infobox,
                'quote': quote
            })
            print(f"  - Extracted: {title}")

    print(f"\nWriting {len(extracted)} boss pages to files...")

    for boss in extracted:
        filename = sanitize_filename(boss['title']) + ".md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {boss['title']}\n\n")

            if boss['quote']:
                f.write(format_quote_markdown(boss['quote']) + "\n\n")

            if boss['infobox']:
                info_md = format_infobox_markdown(boss['infobox'])
                if info_md:
                    f.write(info_md + "\n\n")

            f.write(boss['content'])
            f.write("\n")

        print(f"  - Wrote: {filename}")

    print(f"\nDone! Wrote {len(extracted)} boss pages to {output_dir}")
    return extracted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract all boss pages from Hollow Knight wiki XML dump. Converts wikitext to clean markdown format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python extract_bosses.py input.xml output_dir"
    )
    parser.add_argument(
        "xml_file",
        nargs="?",
        default="source/hollowknight_pages_current.xml",
        help="Path to the XML dump file (default: source/hollowknight_pages_current.xml)"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default='knowledge_base',
        help="Output directory for extracted boss markdown files (default: knowledge_base)"
    )

    args = parser.parse_args()

    xml_path = args.xml_file
    if not os.path.exists(xml_path):
        xml_path = os.path.join(os.path.dirname(__file__), args.xml_file)
        if not os.path.exists(xml_path):
            print(f"Error: XML file not found: {args.xml_file}")
            sys.exit(1)

    extract_boss_pages(xml_path, args.output_dir)