from bs4 import BeautifulSoup
import os
from ..utils import get_relevant_images


class FireCrawl:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        from firecrawl import FirecrawlApp

        self.firecrawl = FirecrawlApp(
            api_key=self.get_api_key(), api_url=self.get_server_url()
        )

    def get_api_key(self) -> str:
        """
        Gets the FireCrawl API key
        Returns:
        Api key (str)
        """
        try:
            api_key = os.environ["FIRECRAWL_API_KEY"]
        except KeyError:
            raise Exception(
                "FireCrawl API key not found. Please set the FIRECRAWL_API_KEY environment variable."
            )
        return api_key

    def get_server_url(self) -> str:
        """
        Gets the FireCrawl server URL.
        Default to official FireCrawl server ('https://api.firecrawl.dev').
        Returns:
        server url (str)
        """
        try:
            server_url = os.environ["FIRECRAWL_SERVER_URL"]
        except KeyError:
            server_url = "https://api.firecrawl.dev"
        return server_url

    def scrape(self) -> tuple:
        """
        This function extracts content and title from a specified link using the FireCrawl Python SDK,
        images from the link are extracted using the functions from `gpt_researcher/scraper/utils.py`.

        Returns:
          The `scrape` method returns a tuple containing the extracted content, a list of image URLs, and
        the title of the webpage specified by the `self.link` attribute. It uses the FireCrawl Python SDK to
        extract and clean content from the webpage. If any exception occurs during the process, an error
        message is printed and an empty result is returned.
        """

        try:
            response = self.firecrawl.scrape(url=self.link, formats=["markdown"])

            # --- Safe metadata access & normalization -------------------------
            # Support both object-style (attrs) and dict-style responses.
            if hasattr(response, "metadata"):
                raw_metadata = response.metadata
            elif isinstance(response, dict):
                raw_metadata = response.get("metadata")
            else:
                raw_metadata = None

            # Normalise to a plain dict for uniform field access.
            if isinstance(raw_metadata, dict):
                meta = raw_metadata
            elif raw_metadata is not None:
                meta = {k: v for k, v in vars(raw_metadata).items()}
            else:
                meta = {}

            # --- Error / status from metadata ---------------------------------
            error = meta.get("error")
            if error:
                print("Scrape failed! : " + str(error))
                return "", [], ""

            status_code = meta.get("status_code") or meta.get("statusCode")
            if status_code and int(status_code) != 200:
                print(f"Scrape failed! Status code: {status_code}")
                return "", [], ""

            # --- Content extraction -------------------------------------------
            # Try object attrs first, then fall back to dict lookups.
            content = getattr(response, "markdown", None) or getattr(response, "content", None)
            if not content and isinstance(response, dict):
                content = response.get("markdown") or response.get("content") or ""

            # --- Title extraction ---------------------------------------------
            # Prefer metadata.title; fall back to response.body/origin.title.
            title = meta.get("title")
            if not title:
                if hasattr(response, "body") and hasattr(response.body, "origin"):
                    title = getattr(response.body.origin, "title", None)
            if not title and isinstance(response, dict):
                title = response.get("title") or response.get("metadata", {}).get("title")
            if not title:
                title = "Unknown Title"

            # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
            response_bs = self.session.get(self.link, timeout=4)
            soup = BeautifulSoup(
                response_bs.content, "lxml", from_encoding=response_bs.encoding
            )

            # Get relevant images using the utility function
            image_urls = get_relevant_images(soup, self.link)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
