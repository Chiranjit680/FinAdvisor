<<<<<<< HEAD
import re
import requests
from bs4 import BeautifulSoup

def extract_keyword_context(text, keyword, context_size=50):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = pattern.finditer(text)
    results = []
    for match in matches:
        start_index = max(match.start() - context_size, 0)
        end_index = min(match.end() + context_size, len(text))
        context_snippet = text[start_index:end_index]
        results.append(context_snippet)
    return results

def scraping_test_google_news():
    url = "https://news.google.com/rss/search?q=TCS+stock"
    response = requests.get(url)
    keywords = ['TCS', 'Tata Consultancy Services']
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        for item in items:
            title = item.title.get_text()
            description = item.description.get_text() if item.description else ""
            full_text = title + " " + description
            for keyword in keywords:
                if keyword.lower() in full_text.lower():
                    context = extract_keyword_context(full_text, keyword)
                    print(f"Context for '{keyword}':")
                    for snippet in context:
                        print(f" - {snippet}")
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")


def scraping_test_yahoo_finance():
    url = "https://finance.yahoo.com/quote/TCS.NS/news/"
    response = requests.get(url)
    keywords = ['TCS', 'Tata Consultancy Services']
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        for item in items:
            title = item.title.get_text()
            description = item.description.get_text() if item.description else ""
            full_text = title + " " + description
            for keyword in keywords:
                if keyword.lower() in full_text.lower():
                    context = extract_keyword_context(full_text, keyword)
                    print(f"Context for '{keyword}':")
                    for snippet in context:
                        print(f" - {snippet}")
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")

if __name__ == "__main__":
    #scraping_test_google_news()
    scraping_test_yahoo_finance()
=======
import re
import requests
from bs4 import BeautifulSoup

def extract_keyword_context(text, keyword, context_size=50):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = pattern.finditer(text)
    results = []
    for match in matches:
        start_index = max(match.start() - context_size, 0)
        end_index = min(match.end() + context_size, len(text))
        context_snippet = text[start_index:end_index]
        results.append(context_snippet)
    return results

def scraping_test_google_news():
    url = "https://news.google.com/rss/search?q=TCS+stock"
    response = requests.get(url)
    keywords = ['TCS', 'Tata Consultancy Services']
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        for item in items:
            title = item.title.get_text()
            description = item.description.get_text() if item.description else ""
            full_text = title + " " + description
            for keyword in keywords:
                if keyword.lower() in full_text.lower():
                    context = extract_keyword_context(full_text, keyword)
                    print(f"Context for '{keyword}':")
                    for snippet in context:
                        print(f" - {snippet}")
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")


def scraping_test_yahoo_finance():
    url = "https://finance.yahoo.com/quote/TCS.NS/news/"
    response = requests.get(url)
    keywords = ['TCS', 'Tata Consultancy Services']
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        for item in items:
            title = item.title.get_text()
            description = item.description.get_text() if item.description else ""
            full_text = title + " " + description
            for keyword in keywords:
                if keyword.lower() in full_text.lower():
                    context = extract_keyword_context(full_text, keyword)
                    print(f"Context for '{keyword}':")
                    for snippet in context:
                        print(f" - {snippet}")
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")

if __name__ == "__main__":
    #scraping_test_google_news()
    scraping_test_yahoo_finance()
>>>>>>> ecb6f56746ddf60500f7eaea012e7dc21f51ee20
