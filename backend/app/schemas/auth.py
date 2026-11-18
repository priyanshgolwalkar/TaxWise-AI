from pydantic import BaseModel, ConfigDict, EmailStr, Field
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class UserLogin(BaseModel):
    email: EmailStr
    password: str
class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
class UserProfile(BaseModel):
    id: int
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
