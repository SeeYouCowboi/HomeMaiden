"""
Movie Download Plugin

Plugin for downloading movies via Radarr. Handles commands like:
- download_movie
- add_movie
- search_movie
"""

from typing import Dict, Any
import logging

from core.plugin_base import BasePlugin, PluginMetadata, CommandContext, PluginResult
from .radarr_client import RadarrClient


class MovieDownloadPlugin(BasePlugin):
    """Plugin for downloading movies using Radarr"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize movie download plugin

        Args:
            config: Plugin configuration with keys:
                - radarr_url: Radarr API URL
                - radarr_api_key: Radarr API key
                - root_folder: Root folder for movies
                - quality_profile_id: Quality profile ID
                - auto_search: Whether to auto-search for movie
            logger: Logger instance
        """
        super().__init__(config, logger)
        self.radarr_client = None

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="movie_download",
            version="1.0.0",
            author="HomeCentralMaid",
            description="通过Radarr下载电影",
            commands=["download_movie", "add_movie", "search_movie"],
            config_schema={
                "radarr_url": {"type": "string", "required": True},
                "radarr_api_key": {"type": "string", "required": True},
                "root_folder": {"type": "string", "required": True},
                "quality_profile_id": {"type": "integer", "default": 1},
                "auto_search": {"type": "boolean", "default": True}
            },
            priority=100
        )

    def initialize(self) -> bool:
        """Initialize Radarr client"""
        try:
            # Validate required config
            required_keys = ["radarr_url", "radarr_api_key", "root_folder"]
            for key in required_keys:
                if key not in self.config:
                    self.logger.error(f"Missing required configuration: {key}")
                    return False

            # Initialize Radarr client
            self.radarr_client = RadarrClient(
                url=self.config['radarr_url'],
                api_key=self.config['radarr_api_key'],
                logger=self.logger
            )

            # Test connection
            if not self.radarr_client.test_connection():
                self.logger.error("Failed to connect to Radarr")
                return False

            self.logger.info("MovieDownloadPlugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"MovieDownloadPlugin initialization failed: {e}")
            return False

    def execute(self, context: CommandContext) -> PluginResult:
        """
        Execute movie download command

        Supported commands:
        - download_movie / add_movie: Add movie to Radarr
        - search_movie: Search for movie without adding

        Args:
            context: Command execution context

        Returns:
            PluginResult with execution status
        """
        action = context.parsed_command.get('action')

        if action in ['download_movie', 'add_movie']:
            return self._handle_add_movie(context)
        elif action == 'search_movie':
            return self._handle_search_movie(context)
        else:
            return PluginResult(
                success=False,
                message=f"不支持的命令: {action}",
                data={"action": action}
            )

    def _handle_add_movie(self, context: CommandContext) -> PluginResult:
        """
        Handle add/download movie command

        Args:
            context: Command context

        Returns:
            PluginResult
        """
        try:
            # Extract movie title from command
            title = context.parsed_command.get('title')

            if not title:
                return PluginResult(
                    success=False,
                    message="未指定电影标题",
                    data={"parsed_command": context.parsed_command}
                )

            self.logger.info(f"Adding movie: {title}")

            # Search for movie
            search_results = self.radarr_client.search_movie(title)

            if not search_results:
                return PluginResult(
                    success=False,
                    message=f"未找到电影《{title}》，请检查拼写或尝试使用英文名称",
                    data={"title": title, "search_results": 0}
                )

            # Get best match (first result)
            movie = search_results[0]
            movie_title = movie.get('title', title)
            movie_year = movie.get('year', 'N/A')

            # Check if already in Radarr
            existing_movie = self.radarr_client.get_movie_by_tmdb_id(movie.get('tmdbId'))
            if existing_movie:
                return PluginResult(
                    success=False,
                    message=f"电影《{movie_title}》({movie_year}) 已经在下载队列中了喵~",
                    data={
                        "title": movie_title,
                        "year": movie_year,
                        "status": "already_exists"
                    }
                )

            # Add to Radarr
            success = self.radarr_client.add_movie(
                movie_data=movie,
                root_folder=self.config['root_folder'],
                quality_profile_id=self.config.get('quality_profile_id', 1),
                search_now=self.config.get('auto_search', True)
            )

            if success:
                return PluginResult(
                    success=True,
                    message=f"电影《{movie_title}》({movie_year}) 已添加到下载队列喵~ Catnip会自动为您下载的~",
                    data={
                        "title": movie_title,
                        "year": movie_year,
                        "tmdb_id": movie.get('tmdbId'),
                        "auto_search": self.config.get('auto_search', True)
                    }
                )
            else:
                return PluginResult(
                    success=False,
                    message=f"添加电影《{movie_title}》失败了呢... 可能是Radarr配置有问题 (｡•́︿•̀｡)",
                    data={
                        "title": movie_title,
                        "year": movie_year
                    }
                )

        except Exception as e:
            self.logger.error(f"Error adding movie: {e}", exc_info=True)
            return PluginResult(
                success=False,
                message=f"添加电影时出错: {str(e)}",
                data={"exception": str(e)}
            )

    def _handle_search_movie(self, context: CommandContext) -> PluginResult:
        """
        Handle search movie command (without adding)

        Args:
            context: Command context

        Returns:
            PluginResult
        """
        try:
            title = context.parsed_command.get('title')

            if not title:
                return PluginResult(
                    success=False,
                    message="未指定电影标题",
                    data={"parsed_command": context.parsed_command}
                )

            self.logger.info(f"Searching for movie: {title}")

            # Search for movie
            search_results = self.radarr_client.search_movie(title)

            if not search_results:
                return PluginResult(
                    success=False,
                    message=f"未找到电影《{title}》",
                    data={"title": title, "search_results": 0}
                )

            # Format results
            results_text = []
            for i, movie in enumerate(search_results[:5]):  # Top 5 results
                movie_title = movie.get('title', 'Unknown')
                year = movie.get('year', 'N/A')
                results_text.append(f"{i+1}. {movie_title} ({year})")

            message = f"找到 {len(search_results)} 部电影喵~\n\n" + "\n".join(results_text)

            if len(search_results) > 5:
                message += f"\n\n...还有 {len(search_results) - 5} 部相关电影"

            return PluginResult(
                success=True,
                message=message,
                data={
                    "title": title,
                    "total_results": len(search_results),
                    "results": search_results[:5]
                }
            )

        except Exception as e:
            self.logger.error(f"Error searching movie: {e}", exc_info=True)
            return PluginResult(
                success=False,
                message=f"搜索电影时出错: {str(e)}",
                data={"exception": str(e)}
            )

    def cleanup(self):
        """Cleanup resources"""
        self.radarr_client = None
        self.logger.info("MovieDownloadPlugin cleaned up")

    def health_check(self) -> bool:
        """
        Check if Radarr is accessible

        Returns:
            True if Radarr is accessible
        """
        if not self.radarr_client:
            return False

        try:
            return self.radarr_client.test_connection()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
