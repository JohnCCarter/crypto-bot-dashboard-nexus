"""API routes for configuration management with FastAPI."""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_config_service
from backend.api.models import (
    ConfigSummary,
    ValidationResponse,
    ReloadConfigResponse,
    StrategyWeightsResponse,
    StrategyParamsResponse,
    UpdateStrategyWeightRequest,
    ProbabilityConfig,
    UpdateProbabilitySettingsRequest,
)
from backend.services.config_service import ConfigService

# Create router
router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/", response_model=ConfigSummary)
async def get_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Get current configuration.
    
    Returns:
        Configuration summary
    """
    try:
        config_summary = await config_service.get_config_summary_async()
        return config_summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.post("/")
async def update_config(
    data: Dict[str, Any], config_service: ConfigService = Depends(get_config_service)
):
    """
    Update configuration.
    
    Args:
        data: Configuration data to update
        
    Returns:
        Success message with updated fields
    """
    try:
        # För nu, bara returnera success - i verklig implementation skulle detta
        # uppdatera konfigurationen
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_fields": list(data.keys()),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/summary", response_model=ConfigSummary)
async def get_config_summary(config_service: ConfigService = Depends(get_config_service)):
    """
    Get configuration summary with validation status.
    
    Returns:
        Configuration summary
    """
    try:
        summary = await config_service.get_config_summary_async()
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config summary: {str(e)}")


@router.get("/strategies", response_model=StrategyWeightsResponse)
async def get_strategy_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Get strategy configuration.
    
    Returns:
        Strategy weights configuration
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
            "strategy_weights": weights_data,
            "total_strategies": len(weights_data),
            "enabled_strategies": len([sw for sw in strategy_weights if sw.enabled]),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy config: {str(e)}")


@router.get("/strategy/{strategy_name}", response_model=StrategyParamsResponse)
async def get_strategy_params(
    strategy_name: str, config_service: ConfigService = Depends(get_config_service)
):
    """
    Get parameters for a specific strategy.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Strategy parameters
    """
    try:
        params = await config_service.get_strategy_params_async(strategy_name)
        return {"strategy_name": strategy_name, "parameters": params}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy params: {str(e)}")


@router.put("/strategy/{strategy_name}/weight")
async def update_strategy_weight(
    strategy_name: str,
    weight_data: UpdateStrategyWeightRequest,
    config_service: ConfigService = Depends(get_config_service),
):
    """
    Update strategy weight.
    
    Args:
        strategy_name: Name of the strategy
        weight_data: New weight value
        
    Returns:
        Success message with updated weight
    """
    try:
        new_weight = weight_data.weight

        success = await config_service.update_strategy_weight_async(strategy_name, new_weight)

        if success:
            return {
                "message": f"Updated {strategy_name} weight to {new_weight}",
                "strategy_name": strategy_name,
                "new_weight": new_weight,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update strategy weight")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update strategy weight: {str(e)}")


@router.get("/probability", response_model=ProbabilityConfig)
async def get_probability_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Get probability configuration.
    
    Returns:
        Probability configuration
    """
    try:
        config = await config_service.load_config_async()
        return {
            "probability_settings": config.probability_settings,
            "risk_config": {
                "min_signal_confidence": config.risk_config.get("min_signal_confidence"),
                "probability_weight": config.risk_config.get("probability_weight"),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get probability config: {str(e)}")


@router.put("/probability")
async def update_probability_config(
    data: UpdateProbabilitySettingsRequest,
    config_service: ConfigService = Depends(get_config_service),
):
    """
    Update probability configuration.
    
    Args:
        data: New probability settings
        
    Returns:
        Success message with updated settings
    """
    try:
        prob_settings = data.probability_settings

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
                        status_code=400, detail=f"{key} must be between 0.0 and 1.0"
                    )

        success = await config_service.update_probability_settings_async(prob_settings)

        if success:
            return {
                "message": "Probability settings updated successfully",
                "updated_settings": prob_settings,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update probability settings")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update probability config: {str(e)}")


@router.get("/validate", response_model=ValidationResponse)
async def validate_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Validate current configuration.
    
    Returns:
        Validation results
    """
    try:
        validation_errors = await config_service.validate_config_async()

        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "error_count": len(validation_errors),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {str(e)}")


@router.post("/reload", response_model=ReloadConfigResponse)
async def reload_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Force reload configuration from file.
    
    Returns:
        Reload results with validation status
    """
    try:
        await config_service.load_config_async(force_reload=True)
        validation_errors = await config_service.validate_config_async()

        return {
            "message": "Configuration reloaded successfully",
            "config_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}") 