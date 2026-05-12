import re

from pydantic import BaseModel, Field, field_validator


# ---------- 学生注册 ----------

class StudentRegisterRequest(BaseModel):
    student_id: str = Field(..., pattern=r"^\d{11}$", description="11位学号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    confirm_password: str = Field(..., min_length=8, max_length=32, description="确认密码")
    college_id: int = Field(..., gt=0, description="学院ID")
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: str | None = Field(None, pattern=r"^[\w.-]+@[\w.-]+\.\w+$", description="邮箱")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次密码不一致")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class StudentRegisterData(BaseModel):
    student_id: str
    name: str


# ---------- 活动主体注册 ----------

class OwnerRegisterRequest(BaseModel):
    account: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", description="账号")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    confirm_password: str = Field(..., min_length=8, max_length=32, description="确认密码")
    owner_name: str = Field(..., min_length=1, max_length=100, description="主体名称")
    owner_type: str = Field(..., min_length=1, max_length=20, description="主体类型")
    college_id: int = Field(..., ge=0, description="学院ID，0代表校级")
    contact_name: str = Field(..., min_length=1, max_length=50, description="负责人姓名")
    contact_student_id: str = Field(..., pattern=r"^\d{11}$", description="负责人学号")
    contact_phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="负责人电话")
    advisor_name: str | None = Field(None, max_length=50, description="指导老师姓名")
    advisor_contact: str | None = Field(None, max_length=50, description="指导老师联系方式")
    bio: str | None = Field(None, max_length=500, description="简介")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次密码不一致")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


# ---------- 登录 ----------

class LoginRequest(BaseModel):
    account: str = Field(..., min_length=1, description="学号")
    password: str = Field(..., min_length=1, description="密码")


class LoginUser(BaseModel):
    user_id: int
    account: str
    role: str
    name: str
    avatar_url: str | None
    college_id: int | None
    college_name: str | None
    need_change_password: bool
    status: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: LoginUser


# ---------- 修改密码 ----------

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码")
    confirm_password: str = Field(..., min_length=8, max_length=32, description="确认密码")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次密码不一致")
        return v

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


# ---------- 首次登录强制改密 ----------

class ForceChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码")
    confirm_password: str = Field(..., min_length=8, max_length=32, description="确认密码")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次密码不一致")
        return v

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v
