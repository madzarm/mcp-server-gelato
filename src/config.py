"""Configuration settings for the Gelato MCP server."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the Gelato MCP server."""
    
    # API Configuration
    gelato_api_key: str = Field(
        ..., 
        description="Gelato API key for authentication"
    )
    gelato_base_url: str = Field(
        default="https://order.gelatoapis.com",
        description="Base URL for Gelato Order API"
    )
    gelato_product_url: str = Field(
        default="https://product.gelatoapis.com", 
        description="Base URL for Gelato Product API"
    )
    gelato_ecommerce_url: str = Field(
        default="https://ecommerce.gelatoapis.com",
        description="Base URL for Gelato E-commerce API"
    )
    gelato_shipment_url: str = Field(
        default="https://shipment.gelatoapis.com",
        description="Base URL for Gelato Shipment API"
    )
    
    # HTTP Client Configuration
    timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    
    # Server Configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Environment Configuration
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings instance from environment variables."""
        # Load .env file if it exists
        env_file = ".env"
        if os.path.exists(env_file):
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        return cls()
    
    def validate_api_key(self) -> None:
        """Validate that API key is present and not empty."""
        if not self.gelato_api_key or self.gelato_api_key.strip() == "":
            raise ValueError(
                "GELATO_API_KEY environment variable is required. "
                "Please set it in your environment or .env file."
            )


def get_settings() -> Settings:
    """Get validated settings instance."""
    settings = Settings.from_env()
    settings.validate_api_key()
    return settings