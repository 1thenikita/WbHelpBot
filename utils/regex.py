import re

def extract_product_id(url):
    match = re.search(r'catalog/(\d+)/detail\.aspx', url)
    if match:
        return int(match.group(1))
    return None