from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class PermissionBase(BaseModel):
    name: str
    resource: str

class PermissionCreate(PermissionBase):
    pass

class PermissionOut(PermissionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int
    permissions: list[PermissionOut] = []
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    roles: list[RoleOut] = []
    model_config = ConfigDict(from_attributes=True)


class AccessLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    timestamp: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)


class UserPermissionsOut(BaseModel):
    user_id: int
    username: str
    permissions: list[PermissionOut]


class PermissionCheckOut(BaseModel):
    user_id: int
    username: str
    permission: str
    has_permission: bool


class PasswordChange(BaseModel):
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
