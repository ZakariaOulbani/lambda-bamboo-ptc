"""
Modèles de données basés sur le fichier OpenAPI
Utilisés pour valider les requêtes et réponses
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Modèles de base (Measures)
# ============================================================================

class MeasureModel(BaseModel):
    """Modèle pour une mesure numérique"""
    value: float
    timestamp: str
    quality: str = Field(description="0=BAD, 1=GOOD")


class MeasureTextModel(BaseModel):
    """Modèle pour une mesure textuelle (ex: operation_mode)"""
    value: str
    timestamp: str
    quality: str


# ============================================================================
# Modèles de hiérarchie (GET /locations)
# ============================================================================

class CircuitHierarchyModel(BaseModel):
    """Circuit dans la hiérarchie"""
    id: str
    name: str


class AssetHierarchyModel(BaseModel):
    """Asset dans la hiérarchie"""
    id: str
    name: str
    circuits: List[CircuitHierarchyModel]


class LocationHierarchyModel(BaseModel):
    """Location dans la hiérarchie"""
    id: str
    name: str
    assets: List[AssetHierarchyModel]


class LocationsListModel(BaseModel):
    """Liste de toutes les locations"""
    locations: List[LocationHierarchyModel]


# ============================================================================
# Modèles de données temps réel (GET /locations/{id})
# ============================================================================

class CircuitModel(BaseModel):
    """Données temps réel d'un circuit"""
    id: str
    tempsp: Optional[MeasureModel] = None
    deltatempsp: Optional[MeasureModel] = None
    temp: Optional[MeasureModel] = None
    power: Optional[MeasureModel] = None
    humidity: Optional[MeasureModel] = None
    quality: Optional[MeasureModel] = None
    availability: Optional[MeasureModel] = None
    operation_mode: Optional[MeasureTextModel] = None
    status: Optional[MeasureModel] = None


class AssetModel(BaseModel):
    """Données temps réel d'un asset"""
    id: str
    tempsp: Optional[MeasureModel] = None
    deltatempsp: Optional[MeasureModel] = None
    temp: Optional[MeasureModel] = None
    power: Optional[MeasureModel] = None
    humidity: Optional[MeasureModel] = None
    quality: Optional[MeasureModel] = None
    availability: Optional[MeasureModel] = None
    operation_mode: Optional[MeasureTextModel] = None
    status: Optional[MeasureModel] = None
    circuits: List[CircuitModel]


class LocationModel(BaseModel):
    """Données temps réel d'une location"""
    id: str
    grid_power: Optional[MeasureModel] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    aggregated_power: Optional[MeasureModel] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    local_generated_power: Optional[MeasureModel] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    assets: List[AssetModel]


# ============================================================================
# Modèles de données historiques (GET /locations/{id}/measures)
# ============================================================================

class CircuitHistoryModel(BaseModel):
    """Données historiques d'un circuit"""
    id: str
    tempsp: Optional[List[MeasureModel]] = None
    deltatempsp: Optional[List[MeasureModel]] = None
    temp: Optional[List[MeasureModel]] = None
    power: Optional[List[MeasureModel]] = None
    humidity: Optional[List[MeasureModel]] = None
    quality: Optional[List[MeasureModel]] = None
    availability: Optional[List[MeasureModel]] = None
    operation_mode: Optional[List[MeasureTextModel]] = None
    status: Optional[List[MeasureModel]] = None


class AssetHistoryModel(BaseModel):
    """Données historiques d'un asset"""
    id: str
    tempsp: Optional[List[MeasureModel]] = None
    deltatempsp: Optional[List[MeasureModel]] = None
    temp: Optional[List[MeasureModel]] = None
    power: Optional[List[MeasureModel]] = None
    humidity: Optional[List[MeasureModel]] = None
    quality: Optional[List[MeasureModel]] = None
    availability: Optional[List[MeasureModel]] = None
    operation_mode: Optional[List[MeasureTextModel]] = None
    status: Optional[List[MeasureModel]] = None
    circuits: List[CircuitHistoryModel]


class LocationHistoryModel(BaseModel):
    """Données historiques d'une location"""
    id: str
    grid_power: Optional[List[MeasureModel]] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    aggregated_power: Optional[List[MeasureModel]] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    local_generated_power: Optional[List[MeasureModel]] = Field(None, description="A positive number for consumption, a negative value for injection. In kW")
    assets: List[AssetHistoryModel]


# ============================================================================
# Modèles d'activation (POST /activations)
# ============================================================================

class ActivationModel(BaseModel):
    """Une activation à envoyer"""
    id: str
    requested_start_time: str = Field(description="ISO date string")
    requested_end_time: str = Field(description="ISO date string")
    setpoint: Optional[float] = None
    delta_setpoint: float


class CircuitActivationModel(BaseModel):
    """Activations pour un circuit"""
    id: str
    activations: List[ActivationModel]


class AssetsActivationModel(BaseModel):
    """Activations pour un asset"""
    id: str
    activations: List[ActivationModel]
    circuits: List[CircuitActivationModel]


class LocationsActivationModel(BaseModel):
    """Activations pour une location"""
    id: str
    activations: List[ActivationModel]
    assets: List[AssetsActivationModel]


class HierarchicalActivationModel(BaseModel):
    """Request body pour POST /activations"""
    locations: List[LocationsActivationModel]


class ActivationResponseModel(BaseModel):
    """Réponse pour une activation"""
    id: str
    response: int = Field(description="HTTP status code")
    error: Optional[str] = None


# ============================================================================
# Modèles de listing des activations (GET /activations)
# ============================================================================

class ActivationsListModel(BaseModel):
    """Une activation dans la liste"""
    id: str
    target_id: str
    target_type: str = Field(description="location, asset, or circuit")
    requested_start_time: str
    requested_end_time: str
    actual_start_time: Optional[str] = None
    actual_end_time: Optional[str] = None
    setpoint: Optional[float] = None
    delta_setpoint: float
    activation_status: str = Field(description="idle, waiting, active, cancelled, completed")


# ============================================================================
# Modèles d'erreur
# ============================================================================

class ErrorDetail(BaseModel):
    """Détail d'une erreur"""
    field: str
    error: str


class ErrorInfo(BaseModel):
    """Information d'erreur"""
    code: int
    message: str
    details: List[ErrorDetail]


class ErrorModel(BaseModel):
    """Modèle d'erreur standard"""
    error: ErrorInfo
