"""
认证模块 v0.6 - 企业级多用户登录与权限管理系统

支持：
  - 环境变量配置用户凭证
  - 密码加密存储（SHA256 + Salt）
  - 登录审计日志
  - 细粒度权限控制 (RBAC)
  - 会话安全性增强
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from pathlib import Path


class PermissionManager:
    """权限管理器 - 支持细粒度权限"""
    
    PERMISSIONS = {
        "view_dashboard": "查看仪表板",
        "view_analytics": "查看分析",
        "view_details": "查看详细账目",
        "export_data": "导出数据",
        "upload_data": "上传数据",
        "manage_users": "管理用户",
        "system_settings": "系统设置",
    }
    
    ROLES = {
        "admin": [
            "view_dashboard", "view_analytics", "view_details",
            "export_data", "upload_data", "manage_users", "system_settings"
        ],
        "editor": [
            "view_dashboard", "view_analytics", "view_details",
            "export_data", "upload_data"
        ],
        "viewer": [
            "view_dashboard", "view_analytics", "view_details"
        ],
    }
    
    @staticmethod
    def get_permissions(role: str) -> List[str]:
        """获取角色权限列表"""
        return PermissionManager.ROLES.get(role, [])
    
    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """检查是否拥有特定权限"""
        return permission in PermissionManager.get_permissions(role)


class UserAuthenticator:
    """用户认证器 - 处理密码加密解密和用户验证"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """
        使用 SHA256 + Salt 加密密码
        返回：(加密密码, salt)
        """
        if salt is None:
            salt = os.urandom(16).hex()[:8]
        
        hash_obj = hashlib.sha256((password + salt).encode('utf-8'))
        hashed = hash_obj.hexdigest()
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """验证密码是否匹配"""
        computed, _ = UserAuthenticator.hash_password(password, salt)
        return computed == hashed
    
    @staticmethod
    def load_users_from_env() -> Dict[str, dict]:
        """
        从环境变量加载用户配置
        格式：LEDGER_USERS_JSON='{"cupid":{"password":"...","name":"...","role":"admin"},...}'
        """
        users_env = os.getenv("LEDGER_USERS_JSON", "")
        
        if users_env:
            try:
                return json.loads(users_env)
            except json.JSONDecodeError:
                pass
        
        # 回退到默认配置（开发环境）
        return {
            "cupid": {
                "password_hash": hashlib.sha256("demonCupid2026default".encode()).hexdigest(),
                "password_salt": "default",
                "name": "我（Cupid）",
                "role": "admin",
                "email": "cupid@example.com",
            },
            "dad": {
                "password_hash": hashlib.sha256("dad2026default".encode()).hexdigest(),
                "password_salt": "default",
                "name": "爸爸",
                "role": "viewer",
                "email": "dad@example.com",
            },
            "mom": {
                "password_hash": hashlib.sha256("mom2026default".encode()).hexdigest(),
                "password_salt": "default",
                "name": "妈妈",
                "role": "viewer",
                "email": "mom@example.com",
            },
        }


class AuditLogger:
    """审计日志 - 记录用户登录/登出行为"""
    
    AUDIT_FILE = Path(__file__).parent.parent / "logs" / "audit.log"
    
    @staticmethod
    def log_event(event_type: str, username: str, ip: str = "127.0.0.1", details: str = ""):
        """记录审计事件"""
        os.makedirs(AuditLogger.AUDIT_FILE.parent, exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,  # login_success, login_failed, logout
            "username": username,
            "ip": ip,
            "details": details
        }
        
        with open(AuditLogger.AUDIT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    @staticmethod
    def get_recent_events(limit: int = 50) -> List[dict]:
        """获取最近的审计事件"""
        if not AuditLogger.AUDIT_FILE.exists():
            return []
        
        events = []
        with open(AuditLogger.AUDIT_FILE, 'r', encoding='utf-8') as f:
            for line in f.readlines()[-limit:]:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        return events


# ===== 主认证接口 =====
USERS_DB = UserAuthenticator.load_users_from_env()


def authenticate_user(username: str, password: str) -> Tuple[bool, str, str]:
    """
    验证用户账号密码 (改进版)
    
    返回：(是否成功, 用户昵称, 用户角色)
    """
    if username not in USERS_DB:
        AuditLogger.log_event("login_failed", username, details="用户不存在")
        return False, "", ""
    
    user = USERS_DB[username]
    
    # 尝试验证（支持新旧密码格式）
    if "password" in user:
        # 旧格式直接比对
        if user["password"] == password:
            AuditLogger.log_event("login_success", username)
            return True, user["name"], user["role"]
    elif "password_hash" in user and "password_salt" in user:
        # 新格式使用 hash 验证
        if UserAuthenticator.verify_password(password, user["password_hash"], user["password_salt"]):
            AuditLogger.log_event("login_success", username)
            return True, user["name"], user["role"]
    
    AuditLogger.log_event("login_failed", username, details="密码错误")
    return False, "", ""


def get_user_role(username: str) -> Optional[str]:
    """获取用户角色"""
    if username in USERS_DB:
        return USERS_DB[username]["role"]
    return None


def get_user_permissions(username: str) -> List[str]:
    """获取用户权限列表"""
    role = get_user_role(username)
    if role:
        return PermissionManager.get_permissions(role)
    return []


def can_upload(role: str) -> bool:
    """检查是否有上传权限"""
    return PermissionManager.has_permission(role, "upload_data")


def can_export(role: str) -> bool:
    """检查是否有导出权限"""
    return PermissionManager.has_permission(role, "export_data")


def can_manage_users(role: str) -> bool:
    """检查是否能管理用户"""
    return PermissionManager.has_permission(role, "manage_users")


def get_all_users() -> Dict[str, str]:
    """获取所有用户列表（用于开发/演示）"""
    return {k: v["name"] for k, v in USERS_DB.items()}
