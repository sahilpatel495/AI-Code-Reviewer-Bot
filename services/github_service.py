"""
GitHub API Service

This module handles all interactions with the GitHub API, including
authentication, fetching pull request data, and posting review comments.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

import httpx
import structlog
from jose import jwt
from cryptography.hazmat.primitives import serialization

from config.settings import settings

logger = structlog.get_logger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.app_id = settings.github_app_id
        self.private_key = self._load_private_key()
        self._installation_tokens = {}  # Cache for installation tokens
        
    def _load_private_key(self) -> str:
        """Load and parse the GitHub App private key."""
        try:
            # Handle both file path and direct key content
            if settings.github_app_private_key.startswith("-----BEGIN"):
                key_content = settings.github_app_private_key
            else:
                # Assume it's a file path
                with open(settings.github_app_private_key, 'r') as f:
                    key_content = f.read()
            
            # Validate the key format
            serialization.load_pem_private_key(
                key_content.encode(),
                password=None
            )
            
            return key_content
        except Exception as e:
            logger.error("Failed to load GitHub App private key", error=str(e))
            raise ValueError("Invalid GitHub App private key")
    
    def _generate_jwt_token(self) -> str:
        """Generate a JWT token for GitHub App authentication."""
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp()) - 60,  # Issued at (1 minute ago)
            "exp": int(now.timestamp()) + 600,  # Expires in 10 minutes
            "iss": self.app_id  # Issuer (GitHub App ID)
        }
        
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    async def _get_installation_token(self, installation_id: str) -> str:
        """Get or refresh installation access token."""
        # Check cache first
        if installation_id in self._installation_tokens:
            token_data = self._installation_tokens[installation_id]
            if token_data["expires_at"] > datetime.now(timezone.utc):
                return token_data["token"]
        
        # Generate new token
        jwt_token = self._generate_jwt_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code != 201:
                logger.error(
                    "Failed to get installation token",
                    status_code=response.status_code,
                    response=response.text,
                    installation_id=installation_id
                )
                raise Exception(f"Failed to get installation token: {response.status_code}")
            
            token_data = response.json()
            
            # Cache the token
            self._installation_tokens[installation_id] = {
                "token": token_data["token"],
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"] - 60)
            }
            
            logger.info("Installation token obtained", installation_id=installation_id)
            return token_data["token"]
    
    async def get_installation_id(self, owner: str, repo: str) -> Optional[str]:
        """Get the installation ID for a repository."""
        jwt_token = self._generate_jwt_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/installation",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code == 404:
                return None
            elif response.status_code != 200:
                logger.error(
                    "Failed to get installation ID",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo
                )
                raise Exception(f"Failed to get installation ID: {response.status_code}")
            
            return response.json()["id"]
    
    async def get_pull_request(self, owner: str, repo: str, pull_number: int, installation_id: str) -> Dict[str, Any]:
        """Get pull request details."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get pull request",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number
                )
                raise Exception(f"Failed to get pull request: {response.status_code}")
            
            return response.json()
    
    async def get_pull_request_diff(self, owner: str, repo: str, pull_number: int, installation_id: str) -> str:
        """Get pull request diff."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3.diff",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=60.0  # Diffs can be large
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get pull request diff",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number
                )
                raise Exception(f"Failed to get pull request diff: {response.status_code}")
            
            return response.text
    
    async def get_pull_request_files(self, owner: str, repo: str, pull_number: int, installation_id: str) -> List[Dict[str, Any]]:
        """Get list of files changed in the pull request."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get pull request files",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number
                )
                raise Exception(f"Failed to get pull request files: {response.status_code}")
            
            return response.json()
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str, installation_id: str) -> str:
        """Get file content from repository."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                params={"ref": ref},
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get file content",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    path=path,
                    ref=ref
                )
                raise Exception(f"Failed to get file content: {response.status_code}")
            
            file_data = response.json()
            
            # Decode base64 content
            import base64
            return base64.b64decode(file_data["content"]).decode("utf-8")
    
    async def post_review_comment(self, owner: str, repo: str, pull_number: int, comment: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Post a review comment on a pull request."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                json=comment,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                logger.error(
                    "Failed to post review comment",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    comment=comment
                )
                raise Exception(f"Failed to post review comment: {response.status_code}")
            
            return response.json()
    
    async def post_inline_comment(self, owner: str, repo: str, pull_number: int, comment: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Post an inline comment on a pull request."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/comments",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                json=comment,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                logger.error(
                    "Failed to post inline comment",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    comment=comment
                )
                raise Exception(f"Failed to post inline comment: {response.status_code}")
            
            return response.json()
    
    async def create_check_run(self, owner: str, repo: str, check_data: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Create a check run for the pull request."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/check-runs",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                json=check_data,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                logger.error(
                    "Failed to create check run",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    check_data=check_data
                )
                raise Exception(f"Failed to create check run: {response.status_code}")
            
            return response.json()
    
    async def update_check_run(self, owner: str, repo: str, check_run_id: int, check_data: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Update an existing check run."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/repos/{owner}/{repo}/check-runs/{check_run_id}",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                json=check_data,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                logger.error(
                    "Failed to update check run",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    check_run_id=check_run_id,
                    check_data=check_data
                )
                raise Exception(f"Failed to update check run: {response.status_code}")
            
            return response.json()
    
    async def get_repository_languages(self, owner: str, repo: str, installation_id: str) -> Dict[str, int]:
        """Get repository language statistics."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/languages",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get repository languages",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo
                )
                raise Exception(f"Failed to get repository languages: {response.status_code}")
            
            return response.json()
    
    async def get_commit_details(self, owner: str, repo: str, commit_sha: str, installation_id: str) -> Dict[str, Any]:
        """Get commit details including diff."""
        token = await self._get_installation_token(installation_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{settings.app_name}/{settings.app_version}"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get commit details",
                    status_code=response.status_code,
                    response=response.text,
                    owner=owner,
                    repo=repo,
                    commit_sha=commit_sha
                )
                raise Exception(f"Failed to get commit details: {response.status_code}")
            
            return response.json()
