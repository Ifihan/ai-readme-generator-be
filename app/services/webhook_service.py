import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for processing GitHub webhook events."""
    
    async def process_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Process a GitHub webhook event."""
        logger.info(f"Processing webhook event: {event_type}")
        
        if event_type == "repository":
            return await self._handle_repository_event(payload)
        elif event_type == "installation":
            return await self._handle_installation_event(payload)
        elif event_type == "installation_repositories":
            return await self._handle_installation_repositories_event(payload)
        elif event_type == "ping":
            return await self._handle_ping_event(payload)
        else:
            logger.info(f"Ignoring webhook event type: {event_type}")
            return False
    
    async def _handle_repository_event(self, payload: Dict[str, Any]) -> bool:
        """Handle repository events (created, deleted, renamed, etc.)."""
        action = payload.get("action")
        repository = payload.get("repository", {})
        installation = payload.get("installation", {})
        
        repo_name = repository.get("full_name")
        installation_id = installation.get("id")
        
        logger.info(f"Repository event: {action} for {repo_name} (installation: {installation_id})")
        
        if action == "created":
            await self._handle_repository_created(repository, installation_id)
        elif action == "deleted":
            await self._handle_repository_deleted(repository, installation_id)
        elif action == "renamed":
            await self._handle_repository_renamed(payload)
        elif action == "transferred":
            await self._handle_repository_transferred(payload)
        elif action in ["privatized", "publicized"]:
            await self._handle_repository_visibility_changed(repository, installation_id, action)
        else:
            logger.info(f"Ignoring repository action: {action}")
            return False
            
        return True
    
    async def _handle_installation_event(self, payload: Dict[str, Any]) -> bool:
        """Handle installation events (created, deleted, suspend, etc.)."""
        action = payload.get("action")
        installation = payload.get("installation", {})
        
        installation_id = installation.get("id")
        account = installation.get("account", {}).get("login")
        
        logger.info(f"Installation event: {action} for installation {installation_id} (account: {account})")
        
        if action == "created":
            await self._handle_installation_created(installation)
        elif action == "deleted":
            await self._handle_installation_deleted(installation)
        elif action in ["suspend", "unsuspend"]:
            await self._handle_installation_status_changed(installation, action)
        else:
            logger.info(f"Ignoring installation action: {action}")
            return False
            
        return True
    
    async def _handle_installation_repositories_event(self, payload: Dict[str, Any]) -> bool:
        """Handle installation repository events (added, removed)."""
        action = payload.get("action")
        installation = payload.get("installation", {})
        repositories_added = payload.get("repositories_added", [])
        repositories_removed = payload.get("repositories_removed", [])
        
        installation_id = installation.get("id")
        
        logger.info(f"Installation repositories event: {action} for installation {installation_id}")
        
        if action == "added":
            for repo in repositories_added:
                logger.info(f"Repository {repo.get('full_name')} added to installation {installation_id}")
                await self._handle_repository_added_to_installation(repo, installation_id)
        elif action == "removed":
            for repo in repositories_removed:
                logger.info(f"Repository {repo.get('full_name')} removed from installation {installation_id}")
                await self._handle_repository_removed_from_installation(repo, installation_id)
        
        return True
    
    async def _handle_ping_event(self, payload: Dict[str, Any]) -> bool:
        """Handle ping events (webhook test)."""
        zen = payload.get("zen", "")
        hook_id = payload.get("hook_id")
        
        logger.info(f"Ping event received (hook_id: {hook_id}): {zen}")
        return True
    
    # Repository event handlers
    async def _handle_repository_created(self, repository: Dict[str, Any], installation_id: Optional[int]):
        """Handle when a new repository is created."""
        repo_name = repository.get("full_name")
        is_private = repository.get("private", False)
        
        logger.info(f"New repository created: {repo_name} (private: {is_private})")
        
        # TODO: You could add logic here to:
        # - Update your local cache of repositories
        # - Send notification to users
        # - Automatically analyze the repository for README generation
        # - Store repository metadata in your database
        
        logger.info(f"New repository {repo_name} is now available for README generation")
    
    async def _handle_repository_deleted(self, repository: Dict[str, Any], installation_id: Optional[int]):
        """Handle when a repository is deleted."""
        repo_name = repository.get("full_name")
        
        logger.info(f"Repository deleted: {repo_name}")
        
        logger.info(f"Repository {repo_name} has been deleted")
    
    async def _handle_repository_renamed(self, payload: Dict[str, Any]):
        """Handle when a repository is renamed."""
        repository = payload.get("repository", {})
        changes = payload.get("changes", {})
        
        old_name = changes.get("repository", {}).get("name", {}).get("from")
        new_name = repository.get("full_name")
        
        logger.info(f"Repository renamed from {old_name} to {new_name}")
        
        logger.info(f"Repository renamed from {old_name} to {new_name}")
    
    async def _handle_repository_transferred(self, payload: Dict[str, Any]):
        """Handle when a repository is transferred to a new owner."""
        repository = payload.get("repository", {})
        changes = payload.get("changes", {})
        
        old_owner = changes.get("owner", {}).get("login", {}).get("from")
        new_owner = repository.get("owner", {}).get("login")
        repo_name = repository.get("name")
        
        logger.info(f"Repository {repo_name} transferred from {old_owner} to {new_owner}")
        
        logger.info(f"Repository {repo_name} transferred from {old_owner} to {new_owner}")
    
    async def _handle_repository_visibility_changed(self, repository: Dict[str, Any], installation_id: Optional[int], action: str):
        """Handle when a repository visibility changes (public/private)."""
        repo_name = repository.get("full_name")
        
        logger.info(f"Repository {repo_name} visibility changed: {action}")
        
        logger.info(f"Repository {repo_name} is now {'private' if action == 'privatized' else 'public'}")
    
    # Installation event handlers
    async def _handle_installation_created(self, installation: Dict[str, Any]):
        """Handle when a new installation is created."""
        installation_id = installation.get("id")
        account = installation.get("account", {}).get("login")
        
        logger.info(f"New installation created: {installation_id} for account {account}")
        
        # TODO: You could:
        # - Welcome the new user
        # - Set up default settings
        # - Send onboarding emails
        
        logger.info(f"New installation {installation_id} created for {account}")
    
    async def _handle_installation_deleted(self, installation: Dict[str, Any]):
        """Handle when an installation is deleted."""
        installation_id = installation.get("id")
        account = installation.get("account", {}).get("login")
        
        logger.info(f"Installation deleted: {installation_id} for account {account}")
        
        logger.info(f"Installation {installation_id} deleted for {account}")
    
    async def _handle_installation_status_changed(self, installation: Dict[str, Any], action: str):
        """Handle when an installation is suspended or unsuspended."""
        installation_id = installation.get("id")
        account = installation.get("account", {}).get("login")
        
        logger.info(f"Installation {installation_id} for {account} is now {action}")
        
        logger.info(f"Installation {installation_id} for {account} is now {action}")
    
    # Installation repository event handlers
    async def _handle_repository_added_to_installation(self, repository: Dict[str, Any], installation_id: int):
        """Handle when a repository is added to an installation."""
        repo_name = repository.get("full_name")
        
        logger.info(f"Repository {repo_name} added to installation {installation_id}")
        
        logger.info(f"Repository {repo_name} is now accessible via installation {installation_id}")
    
    async def _handle_repository_removed_from_installation(self, repository: Dict[str, Any], installation_id: int):
        """Handle when a repository is removed from an installation."""
        repo_name = repository.get("full_name")
        
        logger.info(f"Repository {repo_name} removed from installation {installation_id}")
        
        logger.info(f"Repository {repo_name} is no longer accessible via installation {installation_id}")