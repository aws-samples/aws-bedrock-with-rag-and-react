# USAGE:
# python3 webscraper.py -d 1  <url>
# python3 webscraper.py <url> -d6 -e node-title -p <url>
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import urlunparse
import concurrent.futures
import argparse, base64, json, re, time
from argparse import ArgumentTypeError
from datetime import datetime

OUTPUT_DATA_DIR = './output'
MAX_WORKERS = 3
PAGE_LOAD_TIMEOUT = 10 # seconds
SLEEP_DELAY = 10 # seconds to avoid rate limiting in certain sites
crawled_pg_cnt = 0

# Create the "crawledData" folder in the current directory if it doesn't exist
if not os.path.exists(OUTPUT_DATA_DIR):
    os.makedirs(OUTPUT_DATA_DIR)

# Parse URL to validate it
def parse_url_from_str(arg):
    url = urlparse(arg)
    if all((url.scheme, url.netloc)):  # possibly other sections?
        return arg  # return url in case you need the parsed object
    raise ArgumentTypeError('Invalid URL')

def remove_unwanted_content(driver, pdf_data):
    # Execute JavaScript to hide specific elements before saving as PDF
    # You can add more JavaScript code here to hide different elements as needed
    hide_elements_js = """
        // Hide elements with specific tags
        var tagsToHide = ['img', 'script', 'style', 'video', 'svg', 'iframe', 'code'];
        tagsToHide.forEach(function(tag) {
            var elements = document.getElementsByTagName(tag);
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.display = 'none';
            }
        });
    """

    ex =  '''       // Hide elements with specific class names
        var classNamesToHide = ['advertisement', 'sidebar', 'header'];
        classNamesToHide.forEach(function(className) {
            var elements = document.getElementsByClassName(className);
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.display = 'none';
            }
        });
        '''

    # Execute the JavaScript code in the context of the current page
    driver.execute_script(hide_elements_js)

    # Generate the updated PDF data
    result = send_devtools(driver, "Page.printToPDF", {})
    if (result is not None):
        return base64.b64decode(result['data'])
    else:
        return pdf_data


def send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if (response.get('value') is not None):
        return response.get('value')
    else:
        return None

def save_as_pdf(driver, path, options={}):
    result = send_devtools(driver, "Page.printToPDF", options)
    if (result is not None):
        with open(path, 'wb') as file:
            # Decode the PDF data
            pdf_data = base64.b64decode(result['data'])

            # Remove unwanted content from the PDF data using JavaScript
            pdf_data = remove_unwanted_content(driver, pdf_data)

            file.write(pdf_data)
        return True
    else:
        return False

def delete_files_in_directory(directory_path):
    try:
        # Get a list of all files in the directory
        files = os.listdir(directory_path)

        # Loop through the files and delete each one
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print("All files in the PDF output directory have been deleted.")
    except Exception as e:
        print(f"Error: {e}")

# Helper function for crawling
def crawl(url, max_depth=3, current_depth=1, current_pg_cnt=0, element_id='', prefix=''):
    if url in crawled or current_depth > max_depth:
        return
    crawled.add(url)
    time.sleep(SLEEP_DELAY)
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = True

        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(PAGE_LOAD_TIMEOUT)
        driver.get(url)

        # If an element_id was specified as a cmd line argument, wait for it to appear in the DOM before proceeding
        # else, just look for the <BODY> HTML tag
        try:
            if element_id is None or (not isinstance(element_id, str)) or element_id.strip() == "":
                element_present = EC.presence_of_element_located((By.TAG_NAME, 'body'))
            else:
                element_present = EC.presence_of_element_located((By.ID, element_id))

            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(element_present)
        except TimeoutException:
            print(f"Timed out waiting for page to load - {url}")
            return

        current_pg_cnt += 1
        page_source = driver.page_source
        page_title = get_title_from_page(page_source)
        if page_title is None:
            page_title = ''
        page_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S.%f')[:-3] # millisecond precision
        page_filename = str(current_pg_cnt) + "-" + page_title.strip().replace(" ", "_") + '.' + page_timestamp + '.pdf'
        page_filepath = os.path.join(OUTPUT_DATA_DIR, page_filename)

        save_as_pdf(driver, page_filepath, { 'landscape': False, 'displayHeaderFooter': True })

        if current_depth < max_depth:
            links = collect_links_from_page(url, page_source, prefix)

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_url = {executor.submit(crawl, link, max_depth, current_depth + 1, current_pg_cnt, element_id, prefix): link for link in links}
                for future in concurrent.futures.as_completed(future_to_url):
                    sublink = future_to_url[future]
                    # Do nothing, the crawling is already handled in the function.
        print(f'Crawling page {url} -- COMPLETED')
        driver.quit()
    except Exception as e:
        print(f'Error crawling {url} - {e}')
        return

def get_title_from_page(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    return soup.title.string

def collect_links_from_page(url, page_content, prefix):
    soup = BeautifulSoup(page_content, 'html.parser')
    links_set = set()
    for a in soup.find_all('a', href=True):
        if 'href' in a.attrs:
            link = a['href']
            norm_link = url_normalizer(url, link)
            if norm_link is not None:
                if 'login' not in norm_link:
                    print(f"Found link: {norm_link}")
                    if prefix.strip() == "" or ((len(prefix.strip()) > 0) and norm_link.startswith(prefix.strip())):
                        links_set.add(norm_link)

    return links_set


# Convert relative links to absolute urls
def url_normalizer(parent_url, link):
    # comparator = 

    if link.startswith('#') or link.startswith('../'):
        link = urljoin(parent_url, link)
    elif link.startswith('/'):
        ## TODO: clean up the hack below. It is incorrect.
        link = urljoin(parent_url, link[1:])
        print("new_link: " + link )
    elif link.startswith('./'):
        link = urljoin(parent_url, link[2:])
    else:
        try:
            parse_url_from_str(link)
        except Exception as e:
            link = urljoin(parent_url, link)

    # Validate that link is a valid URL
    try:
        parse_url_from_str(link)
    except Exception as e:
        print(f'Error normalizing {link} - {e}')
        return
    return link 


parser = argparse.ArgumentParser(description='Crawl a webpage and saving pages as PDF files.')
parser.add_argument('-d', '--depth', default=2, type=int, help="max depth to be crawled when following links")
parser.add_argument('-e', '--element_id', default='', type=str, help="webdriver waits until an element containing this ID can be found in the DOM")
parser.add_argument('-p', '--prefix', default='', type=str, help="restrict crawling to URLs matching this prefix")
parser.add_argument('url', type=parse_url_from_str, help="a fully-qualified URL to be crawled; formatted as per RFC 1808")
args = parser.parse_args()

# Ensure URL is terminated by a slash (/)
url=args.url
if re.search("\/$", args.url):
    url=args.url
else:
    url=args.url + "/"

prefix=args.prefix
try:
    if prefix is None or (not isinstance(prefix, str)) or prefix.strip() == "":
        prefix=''
    elif prefix.strip() == '/':
        prefix = url
    else:
        prefix = parse_url_from_str(prefix.strip())
except Exception as e:
        print(f"Error: - Invalid Prefix - {e}")
        parser.print_help()
        exit(-1)

print('PARAMETERS:')
print(f'url: {url}')
print(f'max depth: {args.depth}')
print(f'element_id: {args.element_id}')
print(f'prefix: {prefix}')
delete_files_in_directory(OUTPUT_DATA_DIR)
crawled = set()
crawl(args.url, max_depth=args.depth, element_id=args.element_id, prefix=args.prefix)

print('\n\n\nCRAWLING SUMMARY:')
print(f'URLs crawled: {len(crawled)}')
for page in crawled:
    print(page)

