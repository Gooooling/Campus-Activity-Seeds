from pydantic import BaseModel


# -------- 8.1 GET /v1/users/me --------

class StudentProfile(BaseModel):
    user_id: int
    account: str
    role: str  # "student"
    name: str
    avatar_url: str | None
    college_id: int
    college_name: str | None
    phone: str | None
    email: str | None
    status: str

class OwnerProfile(BaseModel):
    user_id: int
    account: str
    role: str  # "activity_owner"
    owner_name: str
    owner_type: str
    avatar_url: str | None
    college_id: int
    college_name: str | None
    bio: str | None
    contact_name: str
    contact_student_id: str
    contact_phone: str
    advisor_name: str | None
    advisor_contact: str | None
    status: str


# -------- 8.2 PUT /v1/users/me --------

class StudentProfileUpdate(BaseModel):
    name: str | None = None
    college_id: int | None = None
    phone: str | None = None
    email: str | None = None
    avatar_url: str | None = None

class OwnerProfileUpdate(BaseModel):
    owner_name: str | None = None
    owner_type: str | None = None
    college_id: int | None = None
    bio: str | None = None
    avatar_url: str | None = None


# -------- 8.3 --------

class PendingContact(BaseModel):
    old: dict
    new: dict

class ContactInfo(BaseModel):
    contact_name: str
    contact_student_id: str
    contact_phone: str
    pending_change: PendingContact | None

class ContactUpdate(BaseModel):
    contact_name: str
    contact_student_id: str
    contact_phone: str


# -------- 8.4 --------

class AdvisorUpdate(BaseModel):
    advisor_name: str
    advisor_contact: str
