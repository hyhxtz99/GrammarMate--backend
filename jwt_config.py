"""
JWT认证配置模块
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTHandler:
    """JWT处理类"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict):
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access"):
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        """验证密码"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            # If passlib fails, try alternative verification methods
            print(f"Passlib verification failed: {e}")
            
            # Check if it's a plain text password (legacy support)
            if hashed_password == plain_password:
                print("Plain text password match detected")
                return True
            
            # Check if it's a corrupted hash (try to identify the issue)
            if not hashed_password.startswith('$2b$') and not hashed_password.startswith('$2a$') and not hashed_password.startswith('$2y$'):
                print("Invalid hash format detected")
                return False
            
            # If it's a valid bcrypt format but passlib can't handle it, 
            # try using bcrypt directly
            try:
                import bcrypt
                # Convert the hash back to bytes for bcrypt
                if isinstance(hashed_password, str):
                    hashed_password_bytes = hashed_password.encode('utf-8')
                else:
                    hashed_password_bytes = hashed_password
                
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password_bytes)
            except Exception as bcrypt_error:
                print(f"Bcrypt direct verification failed: {bcrypt_error}")
                return False
    
    @staticmethod
    def get_password_hash(password: str):
        """获取密码哈希"""
        return pwd_context.hash(password)

# 创建全局JWT处理器实例
jwt_handler = JWTHandler()
