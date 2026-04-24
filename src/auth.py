"""认证模块 v0.8：安全优先的用户登录与 RBAC 权限管理。"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


AUTH_ENV_KEY = "LEDGER_USERS_JSON"


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
    """用户认证器 - 处理密码加密解密和用户验证。"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
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
    def _normalize_user_record(username: str, user: Dict[str, object]) -> Dict[str, str]:
        role = str(user.get("role", "viewer")).strip() or "viewer"
        if role not in PermissionManager.ROLES:
            raise ValueError(f"用户 {username} 的角色无效: {role}")

        record: Dict[str, str] = {
            "name": str(user.get("name", username)).strip() or username,
            "role": role,
            "email": str(user.get("email", "")).strip(),
        }

        password_hash = str(user.get("password_hash", "")).strip()
        password_salt = str(user.get("password_salt", "")).strip()
        password_plain = str(user.get("password", "")).strip()

        if password_hash and password_salt:
            record["password_hash"] = password_hash
            record["password_salt"] = password_salt
            return record

        if password_plain:
            hashed, salt = UserAuthenticator.hash_password(password_plain)
            record["password_hash"] = hashed
            record["password_salt"] = salt
            return record

        raise ValueError(f"用户 {username} 缺少密码字段（password 或 password_hash+password_salt）")

    @staticmethod
    def load_users_from_env() -> Tuple[Dict[str, dict], str]:
        """
        从环境变量加载用户配置
        格式：LEDGER_USERS_JSON='{"cupid":{"password":"...","name":"...","role":"admin"},...}'
        """
        users_env = os.getenv(AUTH_ENV_KEY, "").strip()

        if not users_env:
            return {}, f"未检测到 {AUTH_ENV_KEY}，登录已禁用。请先在环境变量或 Streamlit secrets 中配置用户。"

        try:
            raw_users = json.loads(users_env)
        except json.JSONDecodeError as exc:
            return {}, f"{AUTH_ENV_KEY} 不是合法 JSON: {exc.msg}"

        if not isinstance(raw_users, dict) or not raw_users:
            return {}, f"{AUTH_ENV_KEY} 必须是非空对象。"

        normalized: Dict[str, dict] = {}
        try:
            for username, user_data in raw_users.items():
                uname = str(username).strip()
                if not uname:
                    raise ValueError("用户名不能为空")
                if not isinstance(user_data, dict):
                    raise ValueError(f"用户 {uname} 的配置必须是对象")
                normalized[uname] = UserAuthenticator._normalize_user_record(uname, user_data)
        except ValueError as exc:
            return {}, f"{AUTH_ENV_KEY} 配置错误: {exc}"

        return normalized, "认证配置已加载。"


def get_auth_env_template() -> str:
    """返回示例认证配置模板（用于 UI 提示，不包含真实凭证）。"""
    template = {
        "admin_user": {
            "password": "ChangeMe_2026!",
            "name": "管理员",
            "role": "admin",
            "email": "admin@example.com",
        },
        "editor_user": {
            "password": "ChangeMe_2026!",
            "name": "编辑者",
            "role": "editor",
        },
        "viewer_user": {
            "password": "ChangeMe_2026!",
            "name": "访客",
            "role": "viewer",
        },
    }
    return json.dumps(template, ensure_ascii=False, indent=2)


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
USERS_DB, AUTH_STATUS_MESSAGE = UserAuthenticator.load_users_from_env()


def is_auth_configured() -> bool:
    return bool(USERS_DB)


def get_auth_status_message() -> str:
    return AUTH_STATUS_MESSAGE


def authenticate_user(username: str, password: str) -> Tuple[bool, str, str]:
    """
    验证用户账号密码 (改进版)
    
    返回：(是否成功, 用户昵称, 用户角色)
    """
    if not is_auth_configured():
        return False, "", ""

    if username not in USERS_DB:
        AuditLogger.log_event("login_failed", username, details="用户不存在")
        return False, "", ""
    
    user = USERS_DB[username]
    
    if "password_hash" in user and "password_salt" in user:
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
