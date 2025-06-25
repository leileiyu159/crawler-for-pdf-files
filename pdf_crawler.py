import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import re  # Import the regular expression module for more refined file name cleaning

url_base = "https://www.nice.org.uk" # Replace it with the target url
url_listing = "https://www.nice.org.uk/guidance/conditions-and-diseases/cancer/lung-cancer/products?ProductType=Guidance&Status=Published" # Replace it with the target url

folder_name = 'downloads_pdf'
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

proxies = {}
# If you need an agent, please fill in your agent information here
# proxies = {
#     'http': 'http://your_proxy_ip:your_proxy_port',
#     'https': 'http://your_proxy_ip:your_proxy_port',
# }

print(f"The list page is being accessed: {url_listing}")
try:
    response_listing = requests.get(url_listing, proxies=proxies, verify=True, timeout=10)
    response_listing.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"The request list page failed: {e}")
    exit()

soup_listing = BeautifulSoup(response_listing.text, 'html.parser')

guide_links = []
# Suppose you have found the correct class or are using a broader search
# If you have modified it before, please make sure that the way here is consistent with the actual successful search method you have
# For example, if you determine the class:
product_list = soup_listing.find('ul', class_='nice-product-list')  # Suppose this is the correct class
# Or if you are using the general method of finding all /guidance/ links:
if not product_list:  # If the specific class is not found, go back to the general search
    for link_tag in soup_listing.find_all('a', href=True):
        href = link_tag.get('href')
        if href and href.startswith(
                '/guidance/') and 'products?' not in href and href != '/guidance/' and '.pdf' not in href.lower():
            full_guide_url = urljoin(url_base, href)
            if full_guide_url not in guide_links:
                guide_links.append(full_guide_url)
else:  # If a specific class is found, extract the link from there
    for link_tag in product_list.find_all('a', href=True):
        href = link_tag.get('href')
        if href and href.startswith('/guidance/') and 'products?' not in href and href != '/guidance/':
            full_guide_url = urljoin(url_base, href)
            if full_guide_url not in guide_links:
                guide_links.append(full_guide_url)

if not guide_links:
    print("No links to the guide detail page were found. Please check the HTML structure or URL pattern of the website.")
    exit()

print(f"Fine {len(guide_links)} the guide details pages. Start traversing and searching for the PDF...")

downloaded_count = 0
for i, guide_url in enumerate(guide_links):
    print(f"\n({i + 1}/{len(guide_links)}) The details page of the guide is being visited: {guide_url}")
    try:
        response_guide = requests.get(guide_url, proxies=proxies, verify=True, timeout=15)
        response_guide.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Visit the details page of the guide {guide_url} failure: {e}")
        continue

    soup_guide = BeautifulSoup(response_guide.text, 'html.parser')

    found_pdfs_in_detail_page = False
    for link_tag in soup_guide.find_all('a', href=True):
        href = link_tag.get('href')
        link_text = link_tag.get_text(strip=True).lower()

        if (href and '.pdf' in href.lower() and not any(
                ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif'])) or \
                ('pdf' in link_text and 'download' in link_text):

            pdf_url = urljoin(url_base, href)

            # --- File name generation logic ---
            # 1. Try to obtain a short and clean file name from the URL
            pdf_name_from_url_part = pdf_url.split('/')[-1]
            if '?' in pdf_name_from_url_part:
                pdf_name_from_url_part = pdf_name_from_url_part.split('?')[0]

            # 2. Obtain the unique identification code of the guide (such as ta1072)
            # This part is usually at the end of the guide_url
            guide_code_match = re.search(r'/guidance/([a-zA-Z0-9]+)', guide_url)
            guide_code = guide_code_match.group(1) if guide_code_match else "unknown"

            # 3. Obtain the guide title and clean and truncate it
            guide_title_tag = soup_guide.find('h1')
            raw_guide_title = guide_title_tag.get_text(strip=True) if guide_title_tag else ""
            # Clear the special characters in the title and replace them with Spaces or underscores
            cleaned_title = re.sub(r'[^\w\s-]', '', raw_guide_title).strip()
            cleaned_title = re.sub(r'\s+', '_', cleaned_title)  # Replace the Spaces with underscores

            # 4. Combined file name: Use the guide code first, followed by the truncated title
            if pdf_name_from_url_part.endswith('.pdf') and len(pdf_name_from_url_part) < 50:  # If the file name provided by the URL is good in itself and not long
                final_pdf_filename = pdf_name_from_url_part
            else:
                # Combine it into a new file name: [Guide Code]_[Partial Title].pdf
                # Truncate the title to avoid it being too long
                max_title_len = 80 - len(guide_code) - len(".pdf") - 2  # Leave space for code and underscores
                if max_title_len < 10: max_title_len = 10  # Make sure there are at least 10 characters for the title
                truncated_title = cleaned_title[:max_title_len]

                # Make sure that the file name does not start or end with non-alphanumeric characters
                truncated_title = truncated_title.strip('_')

                if truncated_title:
                    final_pdf_filename = f"{guide_code}_{truncated_title}.pdf"
                else:  # If the title cannot form an effective part either, only the code is used
                    final_pdf_filename = f"{guide_code}.pdf"

            # Finally, clean up the illegal characters in the file name, retaining only alphanumeric characters, dots, underscores and hyphens
            final_pdf_filename = "".join(c for c in final_pdf_filename if c.isalnum() or c in ('.', '_', '-'))
            # Make sure to end with ".pdf"
            if not final_pdf_filename.lower().endswith('.pdf'):
                final_pdf_filename += '.pdf'

            # Make sure the file name is not too short and at least includes the guide code part
            if len(final_pdf_filename) < len(guide_code) + 4:  # 4 for '.pdf'
                final_pdf_filename = f"{guide_code}.pdf"

            # --- End the file name generation logic ---

            pdf_local_path = os.path.join(folder_name, final_pdf_filename)

            print(f'  Try to download PDF: {pdf_url} to {pdf_local_path}')
            try:
                if os.path.exists(pdf_local_path):
                    print(f'    The file already exists. Skip it: {pdf_local_path}')
                    found_pdfs_in_detail_page = True
                    continue

                pdf_response = requests.get(pdf_url, proxies=proxies, verify=True, timeout=30)
                pdf_response.raise_for_status()
                with open(pdf_local_path, 'wb') as f:
                    f.write(pdf_response.content)
                print(f'  >> Downloaded {pdf_local_path}')
                downloaded_count += 1
                found_pdfs_in_detail_page = True
                break
            except requests.exceptions.RequestException as e:
                print(f"  Download {pdf_url} fail: {e}")

    if not found_pdfs_in_detail_page:
        print(f"  In {guide_url} No obvious PDF download link was found on the detail page.")

print(f"\nAll the guidelines have been checked. A total of {downloaded_count} pdf files were downloaded.")
