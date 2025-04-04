import os
import json
import time
import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# Define relative paths
BASE_PATH = "CAFB-DATA-DUMP/CAFBrain-Dataset"
TEXT_SAVE_PATH = os.path.join(BASE_PATH, "text", "blog_posts.jsonl")
IMAGE_SAVE_PATH = os.path.join(BASE_PATH, "images")
IMAGE_METADATA_PATH = os.path.join(IMAGE_SAVE_PATH, "image_data.jsonl")

# Base blog URL
BASE_URL = "https://www.capitalareafoodbank.org/blog/"

# Configure Selenium WebDriver (Headless Mode)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

chromedriver_path = "/opt/homebrew/bin/chromedriver"

print(f"Using ChromeDriver at: {chromedriver_path}")  # Debugging info

try:
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("ChromeDriver initialized successfully!")
except WebDriverException as e:
    print(f"Error initializing ChromeDriver: {e}")
    print("Check if chromedriver is installed and accessible.")
    exit(1)

# Ensure directories exist
os.makedirs(os.path.dirname(TEXT_SAVE_PATH), exist_ok=True)
os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)

# Define generic image keywords to exclude
GENERIC_KEYWORDS = [
    "cafb_logo",
    "feeding_america_logo",
    "charity_navigator_badge",
    "favicon",
    "apple-touch-icon",
    "mstile-",
    "logo",
    "icon-facebook",
    "icon-instagram",
    "icon-youtube",
    "analytics",
    "facebook.com/tr?id="
]

def is_generic_image(image_url):
    """Checks if an image URL contains generic elements."""
    return any(keyword in image_url.lower() for keyword in GENERIC_KEYWORDS)

def download_image(image_url, save_directory, index, prefix="blo"):
    """Downloads an image, converts it to PNG, and saves it with the correct filename."""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert("RGBA")  # Ensure transparency support
            filename = f"{prefix}_{index:03d}.png"  # Always save as PNG
            filepath = os.path.join(save_directory, filename)
            
            image.save(filepath, format="PNG")  # Force PNG format

            return {"filename": filename, "source_url": image_url}
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")
    return None

def download_images_from_post(post_soup, post_url, image_index, image_metadata):
    """Scrape all <img> tags and background images from the blog post body, skipping generic images."""
    new_index = image_index  # Keep track of the updated index count

    # Extract all regular <img> tags
    all_imgs = post_soup.find_all("img")
    for img_tag in all_imgs:
        src = img_tag.get("src")
        if not src or is_generic_image(src):
            continue  # Skip if no source or generic image

        saved_image = download_image(src, IMAGE_SAVE_PATH, new_index)
        if saved_image:
            image_metadata.append({
                "filename": saved_image["filename"],
                "source_url": src,
                "blog_post_url": post_url
            })
            print(f"Saved image: {saved_image['filename']}")
            new_index += 1

    # Capture the header background image (if present)
    hero_section = post_soup.find("div", class_="silc-hero__media")
    if hero_section and "style" in hero_section.attrs:
        style_attr = hero_section["style"]
        bg_image_url = None
        if "background-image" in style_attr:
            bg_image_url = style_attr.split("url(")[-1].split(")")[0].strip('"')

        if bg_image_url and not is_generic_image(bg_image_url):
            saved_image = download_image(bg_image_url, IMAGE_SAVE_PATH, new_index)
            if saved_image:
                image_metadata.append({
                    "filename": saved_image["filename"],
                    "source_url": bg_image_url,
                    "blog_post_url": post_url
                })
                print(f"Saved header image: {saved_image['filename']}")
                new_index += 1

    return new_index  # Return updated index


def get_blog_posts():
    print(f"Navigating to {BASE_URL}...")
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)

    blog_posts = []
    image_metadata = []
    image_index = 1
    page_number = 1
    processed_urls = set()  # Track already processed blog URLs

    while True:
        try:
            print(f"\nWaiting for blog posts on page {page_number}...")
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "feed-item__content")))
            print(f"Blog posts detected on page {page_number}.")
        except:
            print("No posts found or error waiting for feed-item__content.")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = soup.find_all("div", class_="feed-item__content")
        print(f"Found {len(articles)} articles on page {page_number}.")

        if not articles:
            print("No articles found; ending.")
            break

        for idx, article in enumerate(articles, 1):
            try:
                print(f"\nProcessing article {idx}/{len(articles)} on page {page_number}...")
                title_div = article.find("h2", class_="feed-item__title")
                if not title_div or not title_div.find("a"):
                    print("Missing title/link. Skipping.")
                    continue

                title_tag = title_div.find("a")
                title = title_tag.get_text(strip=True)
                url = title_tag["href"]

                # **Check if this blog post was already processed**
                if url in processed_urls:
                    print(f"Skipping already processed article: {title} | URL: {url}")
                    continue  # Skip this article if already processed

                processed_urls.add(url)  # Mark as processed

                date_span = article.find("span", class_="feed-item__date")
                date = date_span.get_text(strip=True) if date_span else "Unknown Date"

                print(f"Title: {title} | URL: {url} | Date: {date}")

                # ====== OPEN BLOG POST & SCRAPE ======
                driver.execute_script(f"window.open('{url}', '_blank');")
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(3)

                post_soup = BeautifulSoup(driver.page_source, "html.parser")

                # (Optional) get in-page <h1> override
                h1_tag = post_soup.find("h1", class_="silc-hero__title")
                inpage_title = h1_tag.get_text(strip=True) if h1_tag else ""

                # Main content
                main_body = post_soup.find("div", class_="page-body editor-output")
                if main_body:
                    paragraphs = [p.get_text(strip=True) for p in main_body.find_all("p")]
                else:
                    paragraphs = [p.text.strip() for p in post_soup.find_all("p") if p.text.strip()]

                content = "\n".join(paragraphs)
                print(f"Extracted {len(paragraphs)} paragraphs from the blog page.")

                # ====== DOWNLOAD ALL BLOG IMAGES ======
                image_index = download_images_from_post(post_soup, url, image_index, image_metadata)

                # Close the tab
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                if inpage_title:
                    title = inpage_title

                blog_posts.append({
                    "title": title,
                    "url": url,
                    "date": date,
                    "content": content,
                    "image_filenames": [
                        img["filename"] for img in image_metadata if img["blog_post_url"] == url
                    ],
                    "image_links": [
                        img["source_url"] for img in image_metadata if img["blog_post_url"] == url
                    ]
                })
                print(f"Saved blog: {title}")

                # Save JSONL every 10 blog posts
                if len(blog_posts) % 10 == 0:
                    print(f"Saving after {len(blog_posts)} blog posts...")
                    save_to_jsonl(blog_posts, TEXT_SAVE_PATH)
                    save_to_jsonl(image_metadata, IMAGE_METADATA_PATH)

            except Exception as e:
                print(f"Error processing article {idx}: {e}")
                continue

        # Try to load more
        try:
            load_more_button = driver.find_element(By.CLASS_NAME, "fwp-load-more")
            driver.execute_script("arguments[0].click();", load_more_button)
            print(f"Moving on to page {page_number + 1}...")
            time.sleep(3)
            page_number += 1
        except Exception as e:
            print(f"No more pages to load. Stopping. Error: {e}")
            break

    # FINAL SAVE AFTER EXHAUSTING THE LOOP
    print("No more pages or done scraping. Saving final data.")
    save_to_jsonl(blog_posts, TEXT_SAVE_PATH)
    save_to_jsonl(image_metadata, IMAGE_METADATA_PATH)

    return blog_posts, image_metadata



def save_to_jsonl(data, file_path):
    """Saves data to a JSONL file."""
    with open(file_path, "w", encoding="utf-8") as file:
        for entry in data:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Saved {len(data)} records to {file_path}")

if __name__ == "__main__":
    try:
        blogs, images = get_blog_posts()
        save_to_jsonl(blogs, TEXT_SAVE_PATH)
        save_to_jsonl(images, IMAGE_METADATA_PATH)
    finally:
        driver.quit()  # Close the browser
