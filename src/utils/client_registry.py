"""Client registry for sharing the Gelato client across resources."""

from typing import Optional

from ..client.gelato_client import GelatoClient


class ClientRegistry:
    """Registry to share the Gelato client across resources without Context injection."""
    
    _instance: Optional['ClientRegistry'] = None
    _client: Optional[GelatoClient] = None
    
    def __new__(cls) -> 'ClientRegistry':
        """Singleton pattern to ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_client(self, client: GelatoClient) -> None:
        """Set the active Gelato client."""
        self._client = client
    
    def get_client(self) -> GelatoClient:
        """Get the active Gelato client."""
        if self._client is None:
            raise RuntimeError(
                "❌ Server not configured. Please set your GELATO_API_KEY environment variable.\n"
                "💡 For Claude Desktop: claude mcp add gelato -v GELATO_API_KEY=your_key_here -- uvx --from git+https://github.com/madzarmaksim/mcp-server-gelato mcp-server-gelato\n"
                "💡 Or use the 'configure_gelato' tool to set up your API key."
            )
        return self._client

    def is_configured(self) -> bool:
        """Check if a client is registered (API key configured)."""
        return self._client is not None
    
    def clear_client(self) -> None:
        """Clear the client reference (for cleanup)."""
        self._client = None


# Global instance
client_registry = ClientRegistry()