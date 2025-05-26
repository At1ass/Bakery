from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Annotated
from decimal import Decimal


class Ingredient(BaseModel):
    """Model for ingredients in recipes"""
    ingredient: Annotated[str, Field(min_length=1, max_length=100, description="Ingredient name")]
    quantity: Decimal = Field(..., gt=0, description="Quantity of ingredient")
    unit: Annotated[str, Field(min_length=1, max_length=20, description="Unit of measurement (e.g., g, ml, pcs)")]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient": "flour",
                "quantity": 2.5,
                "unit": "cups"
            }
        }
    )

    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v):
        valid_units = {'g', 'kg', 'ml', 'l', 'pcs', 'tsp', 'tbsp', 'cups', 'oz', 'lbs'}
        if v.lower() not in valid_units:
            raise ValueError(f'Invalid unit. Must be one of: {", ".join(sorted(valid_units))}')
        return v.lower()

    @field_validator('ingredient')
    @classmethod
    def validate_ingredient(cls, v):
        if not v.strip():
            raise ValueError("Ingredient name cannot be empty")
        return v.strip() 