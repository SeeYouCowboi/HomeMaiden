"""
Radarr API Client

Client for interacting with Radarr API to manage movie downloads.
Radarr is a movie collection manager and downloader.
"""

import requests
from typing import Dict, Any, List, Optional
import logging


class RadarrClient:
    """Client for Radarr API"""

    def __init__(self, url: str, api_key: str, logger: logging.Logger):
        """
        Initialize Radarr client

        Args:
            url: Radarr API base URL (e.g., "http://localhost:7878/api/v3")
            api_key: Radarr API key
            logger: Logger instance
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.headers = {"X-Api-Key": api_key}

        self.logger.debug(f"Radarr client initialized: {self.url}")

    def test_connection(self) -> bool:
        """
        Test if Radarr is accessible

        Returns:
            True if connection successful
        """
        try:
            response = requests.get(
                f"{self.url}/system/status",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                status = response.json()
                version = status.get('version', 'unknown')
                self.logger.info(f"Radarr connection successful (version: {version})")
                return True
            else:
                self.logger.error(f"Radarr connection failed: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            self.logger.error("Radarr connection timeout")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Cannot connect to Radarr: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Radarr connection test failed: {e}")
            return False

    def search_movie(self, title: str) -> List[Dict[str, Any]]:
        """
        Search for movie by title using TMDb lookup

        Args:
            title: Movie title to search

        Returns:
            List of movie dictionaries from TMDb
        """
        try:
            self.logger.info(f"Searching for movie: {title}")

            response = requests.get(
                f"{self.url}/movie/lookup",
                params={"term": title},
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                results = response.json()
                self.logger.info(f"Found {len(results)} result(s) for '{title}'")

                # Log first few results for debugging
                for i, movie in enumerate(results[:3]):
                    self.logger.debug(
                        f"  Result {i+1}: {movie.get('title')} "
                        f"({movie.get('year', 'N/A')}) - "
                        f"TMDb ID: {movie.get('tmdbId')}"
                    )

                return results
            else:
                self.logger.error(
                    f"Movie search failed: HTTP {response.status_code} - {response.text}"
                )
                return []

        except requests.exceptions.Timeout:
            self.logger.error("Movie search timeout")
            return []
        except Exception as e:
            self.logger.error(f"Error searching movie: {e}")
            return []

    def add_movie(
        self,
        movie_data: Dict[str, Any],
        root_folder: str,
        quality_profile_id: int,
        search_now: bool = True
    ) -> bool:
        """
        Add movie to Radarr

        Args:
            movie_data: Movie data from search results (must include tmdbId)
            root_folder: Root folder path for movie storage
            quality_profile_id: Quality profile ID
            search_now: Whether to immediately search for the movie

        Returns:
            True if movie added successfully
        """
        try:
            title = movie_data.get("title", "Unknown")
            tmdb_id = movie_data.get("tmdbId")

            if not tmdb_id:
                self.logger.error("Movie data missing tmdbId")
                return False

            self.logger.info(f"Adding movie to Radarr: {title} (TMDb ID: {tmdb_id})")

            # Check if movie already exists
            if self._movie_exists(tmdb_id):
                self.logger.warning(f"Movie already exists in Radarr: {title}")
                return False

            # Prepare payload
            payload = {
                "title": movie_data.get("title"),
                "qualityProfileId": quality_profile_id,
                "tmdbId": tmdb_id,
                "titleSlug": movie_data.get("titleSlug"),
                "images": movie_data.get("images", []),
                "year": movie_data.get("year"),
                "rootFolderPath": root_folder,
                "monitored": True,
                "addOptions": {
                    "searchForMovie": search_now
                }
            }

            response = requests.post(
                f"{self.url}/movie",
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 201:
                added_movie = response.json()
                self.logger.info(
                    f"Movie added successfully: {title} "
                    f"(ID: {added_movie.get('id')})"
                )
                return True
            elif response.status_code == 400:
                error_msg = response.json().get('message', 'Unknown error')
                self.logger.error(f"Failed to add movie: {error_msg}")
                return False
            else:
                self.logger.error(
                    f"Failed to add movie: HTTP {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            self.logger.error("Add movie request timeout")
            return False
        except Exception as e:
            self.logger.error(f"Error adding movie: {e}")
            return False

    def _movie_exists(self, tmdb_id: int) -> bool:
        """
        Check if movie already exists in Radarr

        Args:
            tmdb_id: TMDb ID of movie

        Returns:
            True if movie exists
        """
        try:
            response = requests.get(
                f"{self.url}/movie",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                movies = response.json()
                return any(movie.get('tmdbId') == tmdb_id for movie in movies)
            else:
                return False

        except Exception as e:
            self.logger.warning(f"Error checking if movie exists: {e}")
            return False

    def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Get movie details by TMDb ID

        Args:
            tmdb_id: TMDb ID

        Returns:
            Movie dictionary or None
        """
        try:
            response = requests.get(
                f"{self.url}/movie",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                movies = response.json()
                for movie in movies:
                    if movie.get('tmdbId') == tmdb_id:
                        return movie
                return None
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error getting movie by TMDb ID: {e}")
            return None

    def get_all_movies(self) -> List[Dict[str, Any]]:
        """
        Get all movies in Radarr

        Returns:
            List of movie dictionaries
        """
        try:
            response = requests.get(
                f"{self.url}/movie",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                movies = response.json()
                self.logger.info(f"Retrieved {len(movies)} movies from Radarr")
                return movies
            else:
                self.logger.error(f"Failed to get movies: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error getting all movies: {e}")
            return []

    def get_quality_profiles(self) -> List[Dict[str, Any]]:
        """
        Get available quality profiles

        Returns:
            List of quality profile dictionaries
        """
        try:
            response = requests.get(
                f"{self.url}/qualityprofile",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                profiles = response.json()
                self.logger.debug(f"Found {len(profiles)} quality profiles")
                for profile in profiles:
                    self.logger.debug(
                        f"  - {profile.get('name')} (ID: {profile.get('id')})"
                    )
                return profiles
            else:
                self.logger.error(f"Failed to get quality profiles: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error getting quality profiles: {e}")
            return []

    def get_root_folders(self) -> List[Dict[str, Any]]:
        """
        Get available root folders

        Returns:
            List of root folder dictionaries
        """
        try:
            response = requests.get(
                f"{self.url}/rootfolder",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                folders = response.json()
                self.logger.debug(f"Found {len(folders)} root folders")
                for folder in folders:
                    self.logger.debug(
                        f"  - {folder.get('path')} "
                        f"(Free: {folder.get('freeSpace', 0) / (1024**3):.1f} GB)"
                    )
                return folders
            else:
                self.logger.error(f"Failed to get root folders: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error getting root folders: {e}")
            return []
