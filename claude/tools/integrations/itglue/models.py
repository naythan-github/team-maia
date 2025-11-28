"""
Pydantic models for ITGlue entities

These models provide type validation and serialization for all ITGlue API entities.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Organization(BaseModel):
    """ITGlue Organization (client/company)"""
    id: str
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    organization_type_name: Optional[str] = None
    quick_notes: Optional[str] = None

    class Config:
        # Allow datetime as ISO string
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Configuration(BaseModel):
    """ITGlue Configuration (server, workstation, network device)"""
    id: str
    name: str
    configuration_type: str = Field(alias='configuration_type_name')
    organization_id: str
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Password(BaseModel):
    """ITGlue Password entry"""
    id: str
    name: str
    username: Optional[str] = None
    # Note: password field is encrypted in API, we don't store it
    organization_id: str
    password_category_name: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FlexibleAsset(BaseModel):
    """ITGlue Flexible Asset (custom documentation)"""
    id: str
    name: str
    flexible_asset_type_id: str
    organization_id: str
    traits: Optional[Dict[str, Any]] = None  # Custom fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Document(BaseModel):
    """ITGlue Document (file attachment)"""
    id: str
    name: str
    size: int  # Bytes
    organization_id: str
    upload_date: datetime = Field(alias='created_at')
    content_type: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Contact(BaseModel):
    """ITGlue Contact (person)"""
    id: str
    name: str
    organization_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Relationship(BaseModel):
    """ITGlue Relationship between entities"""
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
