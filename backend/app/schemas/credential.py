from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CredentialType(BaseModel):
    """Supported credential types with their descriptions"""
    name: str
    display_name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]


class CredentialBase(BaseModel):
    name: str = Field(..., max_length=255, description="Credential name")
    description: Optional[str] = Field(None, description="Credential description")
    credential_type: str = Field(..., description="Type of credential (api_key, user_pass, oauth, ssh_key, db_connection, custom)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class CredentialCreate(CredentialBase):
    """Schema for creating a new credential"""
    credential_data: Dict[str, Any] = Field(..., description="Credential data to be encrypted")
    user_password: str = Field(..., description="User password for encryption")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "AWS Production API Key",
                "description": "API key for AWS production environment",
                "credential_type": "api_key",
                "tags": ["aws", "production"],
                "expires_at": "2024-12-31T23:59:59Z",
                "credential_data": {
                    "api_key": "AKIAIOSFODNN7EXAMPLE",
                    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                },
                "user_password": "user_login_password"
            }
        }
    )


class CredentialUpdate(BaseModel):
    """Schema for updating a credential"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    credential_data: Optional[Dict[str, Any]] = Field(None, description="New credential data (requires user_password)")
    user_password: Optional[str] = Field(None, description="User password for encryption (required if updating credential_data)")


class CredentialRead(CredentialBase):
    """Schema for reading credential metadata (no sensitive data)"""
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_used_at: Optional[datetime]
    encryption_key_id: str

    model_config = ConfigDict(from_attributes=True)


class CredentialDecryptRequest(BaseModel):
    """Schema for decrypting credential data"""
    user_password: str = Field(..., description="User password for decryption")


class CredentialDecryptResponse(BaseModel):
    """Schema for decrypted credential data"""
    credential_data: Dict[str, Any] = Field(..., description="Decrypted credential data")
    masked_data: Dict[str, Any] = Field(..., description="Masked version for display")


class CredentialTestResponse(BaseModel):
    """Schema for credential test results"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ScriptCredentialBase(BaseModel):
    """Base schema for script-credential associations"""
    variable_name: str = Field(..., max_length=100, description="Environment variable name")
    is_active: bool = Field(default=True)


class ScriptCredentialCreate(ScriptCredentialBase):
    """Schema for creating script-credential association"""
    credential_id: int


class ScriptCredentialRead(ScriptCredentialBase):
    """Schema for reading script-credential association"""
    id: int
    script_id: int
    credential_id: int
    created_at: datetime
    credential: CredentialRead

    model_config = ConfigDict(from_attributes=True)


class ScriptCredentialUpdate(BaseModel):
    """Schema for updating script-credential association"""
    variable_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


# Credential type definitions
SUPPORTED_CREDENTIAL_TYPES = [
    CredentialType(
        name="api_key",
        display_name="API Key",
        description="Single API key with optional headers",
        required_fields=["api_key"],
        optional_fields=["headers", "base_url"]
    ),
    CredentialType(
        name="user_pass",
        display_name="Username/Password",
        description="Basic authentication credentials",
        required_fields=["username", "password"],
        optional_fields=["domain"]
    ),
    CredentialType(
        name="oauth",
        display_name="OAuth Token",
        description="OAuth access/refresh token pairs",
        required_fields=["access_token"],
        optional_fields=["refresh_token", "expires_in", "token_type"]
    ),
    CredentialType(
        name="ssh_key",
        display_name="SSH Key",
        description="Public/private key pairs",
        required_fields=["private_key"],
        optional_fields=["public_key", "passphrase"]
    ),
    CredentialType(
        name="db_connection",
        display_name="Database Connection",
        description="Database connection strings and credentials",
        required_fields=["connection_string"],
        optional_fields=["username", "password", "database"]
    ),
    CredentialType(
        name="custom",
        display_name="Custom",
        description="Flexible JSON structure for any credential type",
        required_fields=[],
        optional_fields=[]
    )
]