import os
import json
import requests
import base64
from typing import List, Dict
from urllib.parse import urljoin


class SearxSearch:
    """
    SearxNG API Retriever
    """

    def __init__(self, query: str, query_domains=None):
        """
        Initializes the SearxSearch object
        Args:
            query: Search query string
        """
        self.query = query
        self.query_domains = query_domains or None
        self.base_url = self.get_searxng_url()
        self.auth = self.get_searxng_auth()

    def get_searxng_url(self) -> str:
        """
        Gets the SearxNG instance URL from environment variables
        Returns:
            str: Base URL of SearxNG instance
        """
        try:
            base_url = os.environ["SEARX_URL"]
            if not base_url.endswith("/"):
                base_url += "/"
            return base_url
        except KeyError:
            raise Exception(
                "SearxNG URL not found. Please set the SEARX_URL environment variable. "
                "You can find public instances at https://searx.space/"
            )

    def get_searxng_auth(self) -> str | None:
        """
        Gets the SearxNG basic auth credentials from environment variables
        Returns:
            str or None: Base64 encoded user:password for basic auth, or None if not set
        """
        return os.environ.get("SEARX_AUTH")

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Searches the query using SearxNG API
        Args:
            max_results: Maximum number of results to return
        Returns:
            List of dictionaries containing search results
        """
        search_url = urljoin(self.base_url, "search")
        # TODO: Add support for query domains
        params = {
            # The search query.
            "q": self.query,
            # Output format of results. Format needs to be activated in searxng config.
            "format": "json",
        }

        try:
            headers = {"Accept": "application/json"}
            auth_tuple = None

            if self.auth:
                # Decode base64 user:password and create auth tuple
                try:
                    decoded_auth = base64.b64decode(self.auth).decode("utf-8")
                    username, password = decoded_auth.split(":", 1)
                    auth_tuple = (username, password)
                except (ValueError, UnicodeDecodeError):
                    raise Exception(
                        "Invalid SEARX_AUTH format. Must be base64 encoded 'user:password'"
                    )

            # log auth tuple
            print(f"===>>> SearxNG Auth Tuple: {auth_tuple}")
            response = requests.get(
                search_url, params=params, headers=headers, auth=auth_tuple
            )
            response.raise_for_status()
            results = response.json()

            # Normalize results to match the expected format
            search_response = []
            for result in results.get("results", [])[:max_results]:
                search_response.append(
                    {"href": result.get("url", ""), "body": result.get("content", "")}
                )

            return search_response

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying SearxNG: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Error parsing SearxNG response")
