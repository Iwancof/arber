"""Common schema types and mixins."""


from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    """Base schema with ORM mode enabled."""
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    limit: int = 50
    offset: int = 0


class PaginatedResponse(OrmBase):
    """Wrapper for paginated list responses."""
    total: int
    limit: int
    offset: int
