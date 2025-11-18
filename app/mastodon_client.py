import httpx
from typing import Optional
from app.config import settings


class MastodonClient:
    """Mastodon API 客户端"""
    
    def __init__(self, base_url: str, access_token: str):
        """
        初始化 Mastodon 客户端
        
        Args:
            base_url: Mastodon 实例的基础 URL（例如：https://m.somincola.org）
            access_token: 访问令牌
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.api_url = f"{self.base_url}/api/v1"
    
    async def post_status(
        self,
        status: str,
        in_reply_to_id: Optional[int] = None,
        media_ids: Optional[list] = None,
        sensitive: bool = False,
        spoiler_text: Optional[str] = None,
        visibility: str = "public",
        timeout: int = 30
    ) -> dict:
        """
        发布状态（发帖）
        
        Args:
            status: 帖子内容
            in_reply_to_id: 回复的帖子 ID
            media_ids: 媒体文件 ID 列表
            sensitive: 是否标记为敏感内容
            spoiler_text: 内容警告文本
            visibility: 可见性（public, unlisted, private, direct）
            timeout: 请求超时时间（秒）
        
        Returns:
            API 响应数据（包含帖子信息）
        
        Raises:
            httpx.HTTPStatusError: HTTP 错误
            Exception: 其他错误
        """
        url = f"{self.api_url}/statuses"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "status": status,
            "visibility": visibility
        }
        
        if in_reply_to_id:
            data["in_reply_to_id"] = in_reply_to_id
        
        if media_ids:
            data["media_ids[]"] = media_ids
        
        if sensitive:
            data["sensitive"] = "true"
        
        if spoiler_text:
            data["spoiler_text"] = spoiler_text
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise Exception(f"请求超时: {str(e)}")
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 错误 {e.response.status_code}"
            try:
                error_detail = e.response.json()
                if "error" in error_detail:
                    error_msg += f": {error_detail['error']}"
            except:
                error_msg += f": {e.response.text[:200]}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"发布失败: {str(e)}")
    
    async def verify_credentials(self, timeout: int = 30) -> dict:
        """
        验证访问令牌并获取账户信息
        
        Args:
            timeout: 请求超时时间（秒）
        
        Returns:
            账户信息
        
        Raises:
            Exception: 验证失败
        """
        url = f"{self.api_url}/accounts/verify_credentials"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise Exception(f"请求超时: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"验证失败: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"验证失败: {str(e)}")
    
    async def get_status(self, status_id: int, timeout: int = 30) -> dict:
        """
        获取单个帖子信息
        
        Args:
            status_id: 帖子 ID
            timeout: 请求超时时间（秒）
        
        Returns:
            帖子信息
        """
        url = f"{self.api_url}/statuses/{status_id}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise Exception(f"请求超时: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"获取失败: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"获取失败: {str(e)}")


async def post_to_mastodon(base_url: str, access_token: str, status: str) -> dict:
    """
    便捷函数：发布帖子到 Mastodon
    
    Args:
        base_url: Mastodon 实例的基础 URL
        access_token: 访问令牌
        status: 帖子内容
    
    Returns:
        API 响应数据
    """
    client = MastodonClient(base_url, access_token)
    return await client.post_status(status)

