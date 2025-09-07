"""
Configuration and environment validation utilities
"""

import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration and environment variables"""
    
    @staticmethod
    def validate_environment():
        """
        Validate that required environment variables are set.
        
        Raises:
            EnvironmentError: If required variables are missing
        """
        errors = []
        warnings = []
        
        # Check for API key
        if not os.environ.get('ANTHROPIC_API_KEY'):
            warnings.append(
                "ANTHROPIC_API_KEY not set. Claude API operations will fail. "
                "Set it with: export ANTHROPIC_API_KEY=your-key"
            )
        
        # Check for data path
        data_path = os.environ.get('SCIMCP_DATA_PATH')
        if not data_path:
            warnings.append(
                "SCIMCP_DATA_PATH not set. Using default path which may not exist. "
                "Set it with: export SCIMCP_DATA_PATH=/path/to/all_papers.parquet"
            )
        elif not Path(data_path).exists():
            errors.append(
                f"SCIMCP_DATA_PATH points to non-existent file: {data_path}"
            )
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        # Raise errors if critical issues found
        if errors:
            for error in errors:
                logger.error(error)
            raise EnvironmentError(
                "Critical configuration errors found. See logs above."
            )
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate API key format (basic check).
        
        Args:
            api_key: API key to validate
            
        Returns:
            bool: True if key appears valid
        """
        if not api_key:
            return False
        
        # Basic format check for Anthropic keys
        if api_key.startswith('sk-ant-'):
            return True
        
        # Allow any non-empty key for testing
        return len(api_key) > 10
    
    @staticmethod
    def setup_logging(level: str = None):
        """
        Configure logging based on environment.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        if level is None:
            level = os.environ.get('LOG_LEVEL', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @staticmethod
    def get_config() -> dict:
        """
        Get configuration from environment with defaults.
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            'data_path': os.environ.get(
                'SCIMCP_DATA_PATH',
                '/data/yixin/workspace/sciMCP/data/all_papers.parquet'
            ),
            'cache_dir': os.environ.get('CACHE_DIR', 'data/processed'),
            'api_key': os.environ.get('ANTHROPIC_API_KEY'),
            'max_workers': int(os.environ.get('MAX_WORKERS', '4')),
            'rate_limit_delay': float(os.environ.get('API_RATE_LIMIT_DELAY', '3')),
            'log_level': os.environ.get('LOG_LEVEL', 'INFO')
        }


def validate_and_setup():
    """
    Convenience function to validate and setup environment.
    Call this at the start of scripts.
    """
    validator = ConfigValidator()
    validator.setup_logging()
    
    try:
        validator.validate_environment()
    except EnvironmentError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    config = validator.get_config()
    logger.info("Configuration validated successfully")
    return config


if __name__ == "__main__":
    # Test validation
    config = validate_and_setup()
    print("Configuration:")
    for key, value in config.items():
        if key == 'api_key' and value:
            value = value[:10] + '...'  # Hide API key
        print(f"  {key}: {value}")