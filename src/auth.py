"""
认证模块 - 简单的多用户登录系统
"""

from typing import Dict, Optional, Tuple

# 用户数据库（生产环境应使用真实数据库）
USERS_DB = {
    "cupid": {
        "password": "demonCupid2026",  # 你自己的密码
        "name": "我（Cupid）",
        "role": "admin",  # admin 有上传权限
    },
    "dad": {
        "password": "dad2026",  # 爸爸的密码
        "name": "爸爸",
        "role": "viewer",  # viewer 只能查看
    },
    "mom": {
        "password": "mom2026",  # 妈妈的密码
        "name": "妈妈",
        "role": "viewer",  # viewer 只能查看
    },
}


def authenticate_user(username: str, password: str) -> Tuple[bool, str, str]:
    """
    验证用户账号密码
    
    返回：(是否成功, 用户名, 用户角色)
    """
    if username not in USERS_DB:
        return False, "", ""
    
    user = USERS_DB[username]
    if user["password"] == password:
        return True, user["name"], user["role"]
    
    return False, "", ""


def get_user_role(username: str) -> Optional[str]:
    """获取用户角色"""
    if username in USERS_DB:
        return USERS_DB[username]["role"]
    return None


def can_upload(role: str) -> bool:
    """检查是否有上传权限"""
    return role == "admin"


def get_all_users() -> Dict[str, str]:
    """获取所有用户列表（用于开发/演示）"""
    return {k: v["name"] for k, v in USERS_DB.items()}
