import logging
logging.root.setLevel(logging.INFO)

from pathlib import Path
import requests
import browser_cookie3
from bs4 import BeautifulSoup

output_folder = 'c:\\temp\\helpdesk'

# The calypso site doesn't like us authenticating, so just grab cookies from the browser.
cj = browser_cookie3.chrome()
search_page_response = requests.get(
    'https://www.calypso.com/case_submit/search_index.php',
    cookies = cj
)

search_soup = BeautifulSoup(
    search_page_response.text,
    'html.parser'
)

links = search_soup.find_all('a',attrs={'target':'_new'})
for link in links:
    # Never understood why the url id is different from the helpdesk ID. Anyway...
    call_id = link.text
    logging.info(f'Grabbing call {call_id}')
    internal_call_id = link.attrs['href'].split('support_client_calls_id=')[1]
    printable_response = requests.get(
        f'https://www.calypso.com/case_submit/hd_history_printable_view.php?support_client_calls_id={internal_call_id}',
        cookies = cj
    )
    # Create a folder for the call info
    Path(output_folder, call_id).mkdir(parents=True, exist_ok=True)

    # Parse the call for attachments
    call_soup = BeautifulSoup(
        printable_response.text,
        'html.parser'
    )
    download_links = call_soup.find_all('a')
    for download_link in (a for a in download_links if a.attrs['href'].startswith('download_file')):
        # Need to build a new url because the download link doesn't work from the 'printable' page
        # Note that the download link uses the 'visible' call id, not the magic internal one
        attachment_id = download_link.attrs['href'].split('support_client_attachment_id=')[1]
        # Make the link in the html file local for ease of opening
        download_link.attrs['href'] = download_link.text
        logging.info(f'Grabbing call {call_id} attachment {download_link.text}')

        f = requests.get(
            f'https://www.calypso.com/case_submit/download_file.php?support_calls_id={call_id}&support_client_attachment_id={attachment_id}',
            cookies=cj
        )
        Path(output_folder,call_id,download_link.text).write_bytes(f.content)


    p = Path(output_folder, call_id, 'call.html')
    logging.info(f'Writing call as a html file to {p}')
    p.write_bytes(call_soup.prettify('utf-8'))
