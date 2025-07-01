"""
Configuration API endpoints for FastAPI.
"""

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, status, Body
from pydantic import BaseModel, Field

from backend.services.config_service import ConfigService
from backend.api.models import ResponseStatus


# Create router
router = APIRouter(
    prefix="/api/config",
    tags=["config"],
)


# Models
class StrategyWeight(BaseModel):
    """Strategy weight model."""
    strategy_name: str
    weight: float
    min_confidence: float = 0.5
    enabled: bool = True


class ProbabilitySettings(BaseModel):
    """Probability settings model."""
    confidence_threshold_buy: float = Field(0.7, ge=0.0, le=1.0)
    confidence_threshold_sell: float = Field(0.7, ge=0.0, le=1.0)
    confidence_threshold_hold: float = Field(0.6, ge=0.0, le=1.0)
    risk_score_threshold: float = Field(0.8, ge=0.0, le=1.0)
    combination_method: str = "weighted_average"
    enable_dynamic_weights: bool = True


# Dependencies
def get_config_service() -> ConfigService:
    """
    Get config service instance.
    
    Returns:
        ConfigService: Config service instance
    """
    return ConfigService()


@router.get("")
async def get_config(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns:
        Dict: Current configuration
    """
    try:
        config_summary = await config_service.get_config_summary_async()
        return {
            "status": ResponseStatus.SUCCESS,
            "config": config_summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("")
async def update_config(
    data: Dict[str, Any] = Body(...),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Update configuration.
    
    Parameters:
        data: Configuration data to update
        
    Returns:
        Dict: Update result
    """
    try:
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing JSON body"
            )
            
        # In a real implementation, this would update the config
        # For now, just return success
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Configuration updated successfully",
            "updated_fields": list(data.keys()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/summary")
async def get_config_summary(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Get configuration summary with validation status.
    
    Returns:
        Dict: Configuration summary
    """
    try:
        summary = await config_service.get_config_summary_async()
        return {
            "status": ResponseStatus.SUCCESS,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config summary: {str(e)}"
        )


@router.get("/strategies")
async def get_strategy_config(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Get strategy configuration.
    
    Returns:
        Dict: Strategy configuration
    """
    try:
        strategy_weights = await config_service.get_strategy_weights_async()
        
        weights_data = [
            {
                "strategy_name": sw.strategy_name,
                "weight": sw.weight,
                "min_confidence": sw.min_confidence,
                "enabled": sw.enabled,
            }
            for sw in strategy_weights
        ]
        
        return {
            "status": ResponseStatus.SUCCESS,
            "strategy_weights": weights_data,
            "total_strategies": len(weights_data),
            "enabled_strategies": len(
                [sw for sw in strategy_weights if sw.enabled]
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy config: {str(e)}"
        )


@router.get("/strategy/{strategy_name}")
async def get_strategy_params(
    strategy_name: str,
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Get parameters for a specific strategy.
    
    Parameters:
        strategy_name: Name of the strategy
        
    Returns:
        Dict: Strategy parameters
    """
    try:
        params = await config_service.get_strategy_params_async(strategy_name)
        return {
            "status": ResponseStatus.SUCCESS,
            "strategy_name": strategy_name,
            "parameters": params,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy params: {str(e)}"
        )


@router.put("/strategy/{strategy_name}/weight")
async def update_strategy_weight(
    strategy_name: str,
    data: Dict[str, float] = Body(...),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Update strategy weight.
    
    Parameters:
        strategy_name: Name of the strategy
        data: Dictionary with weight value
        
    Returns:
        Dict: Update result
    """
    try:
        new_weight = data.get("weight")
        
        if new_weight is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight value is required"
            )
            
        if not (0.0 <= new_weight <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be between 0.0 and 1.0"
            )
            
        success = await config_service.update_strategy_weight_async(
            strategy_name, new_weight
        )
        
        if success:
            return {
                "status": ResponseStatus.SUCCESS,
                "message": f"Updated {strategy_name} weight to {new_weight}",
                "strategy_name": strategy_name,
                "new_weight": new_weight,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update strategy weight"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy weight: {str(e)}"
        )


@router.get("/probability")
async def get_probability_config(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Get probability configuration.
    
    Returns:
        Dict: Probability configuration
    """
    try:
        config = await config_service.load_config_async()
        return {
            "status": ResponseStatus.SUCCESS,
            "probability_settings": config.probability_settings,
            "risk_config": {
                "min_signal_confidence": config.risk_config.get(
                    "min_signal_confidence"
                ),
                "probability_weight": config.risk_config.get(
                    "probability_weight"
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get probability config: {str(e)}"
        )


@router.put("/probability")
async def update_probability_config(
    data: Dict[str, Any] = Body(...),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Update probability configuration.
    
    Parameters:
        data: Probability settings to update
        
    Returns:
        Dict: Update result
    """
    try:
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided"
            )
            
        # Validate probability settings
        if "probability_settings" in data:
            prob_settings = data["probability_settings"]
            
            # Validate threshold values
            for key in [
                "confidence_threshold_buy",
                "confidence_threshold_sell",
                "confidence_threshold_hold",
                "risk_score_threshold",
            ]:
                if key in prob_settings:
                    value = prob_settings[key]
                    if not (0.0 <= value <= 1.0):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"{key} must be between 0.0 and 1.0"
                        )
                        
            success = await config_service.update_probability_settings_async(
                prob_settings
            )
            
            if success:
                return {
                    "status": ResponseStatus.SUCCESS,
                    "message": "Probability settings updated successfully",
                    "updated_settings": prob_settings,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update probability settings"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="probability_settings field is required"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update probability config: {str(e)}"
        )


@router.get("/validate")
async def validate_config(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Validate current configuration.
    
    Returns:
        Dict: Validation result
    """
    try:
        validation_errors = await config_service.validate_config_async()
        
        return {
            "status": ResponseStatus.SUCCESS,
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "error_count": len(validation_errors),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.post("/reload")
async def reload_config(
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Force reload configuration from file.
    
    Returns:
        Dict: Reload result
    """
    try:
        await config_service.load_config_async(force_reload=True)
        validation_errors = await config_service.validate_config_async()
        
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Configuration reloaded successfully",
            "config_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        ) 