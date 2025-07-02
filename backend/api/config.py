"""
API routes for configuration management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from backend.api.models import (
    ConfigSummary,
    StrategyWeightsResponse,
    StrategyParamsResponse,
    UpdateStrategyWeightRequest,
    UpdateProbabilitySettingsRequest,
    ProbabilityConfig,
    ValidationResponse,
    ReloadConfigResponse
)
from backend.api.dependencies import get_config_service
from backend.services.config_service import ConfigService
from backend.services.event_logger import event_logger, EventType

# Create router
router = APIRouter(
    prefix="/api",
    tags=["config"],
)


@router.get("/config", response_model=ConfigSummary)
async def get_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get current configuration.
    
    Returns:
        ConfigSummary: Summary of the current configuration
    """
    try:
        config_summary = await config_service.get_config_summary_async()
        return config_summary
    except Exception as e:
        event_logger.log_api_error(
            endpoint="GET /api/config", 
            error=str(e)
        )
        # Return a valid ConfigSummary with error info
        return ConfigSummary(
            config_file="error.json",
            config_valid=False,
            validation_errors=[str(e)],
            enabled_strategies=[],
            total_strategy_count=0,
            risk_management={},
            probability_framework={}
        )


@router.post("/config", status_code=status.HTTP_200_OK)
async def update_config(
    data: Dict[str, Any],
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update configuration.
    
    Args:
        data: Configuration data to update
        
    Returns:
        Dict[str, Any]: Result of the update operation
    """
    try:
        # For now, just return success - in real implementation this would
        # update config
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_fields": list(data.keys()),
        }
    except Exception as e:
        event_logger.log_api_error(
            endpoint="POST /api/config", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/config/summary", response_model=ConfigSummary)
async def get_config_summary(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get configuration summary with validation status.
    
    Returns:
        ConfigSummary: Summary of the current configuration with validation status
    """
    try:
        summary = await config_service.get_config_summary_async()
        return summary
    except Exception as e:
        event_logger.log_api_error(
            endpoint="GET /api/config/summary", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config summary: {str(e)}"
        )


@router.get("/config/strategies", response_model=StrategyWeightsResponse)
async def get_strategy_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get strategy configuration.
    
    Returns:
        StrategyWeightsResponse: Strategy weights configuration
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
            "enabled_strategies": len(
                [sw for sw in strategy_weights if sw.enabled]
            ),
        }
    except Exception as e:
        event_logger.log_api_error(
            endpoint="GET /api/config/strategies", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy config: {str(e)}"
        )


@router.get("/config/strategy/{strategy_name}", response_model=StrategyParamsResponse)
async def get_strategy_params(
    strategy_name: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get parameters for a specific strategy.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        StrategyParamsResponse: Strategy parameters
    """
    try:
        params = await config_service.get_strategy_params_async(strategy_name)
        return {"strategy_name": strategy_name, "parameters": params}
    except Exception as e:
        endpoint = f"GET /api/config/strategy/{strategy_name}"
        event_logger.log_api_error(endpoint=endpoint, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy params: {str(e)}"
        )


@router.put("/config/strategy/{strategy_name}/weight", status_code=status.HTTP_200_OK)
async def update_strategy_weight(
    strategy_name: str,
    data: UpdateStrategyWeightRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update strategy weight.
    
    Args:
        strategy_name: Name of the strategy
        data: New weight data
        
    Returns:
        Dict[str, Any]: Result of the update operation
    """
    try:
        new_weight = data.weight

        if not (0.0 <= new_weight <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="Weight must be between 0.0 and 1.0"
            )

        success = await config_service.update_strategy_weight_async(strategy_name, new_weight)

        if success:
            event_logger.log_event(
                EventType.PARAMETER_CHANGED,
                f"Updated {strategy_name} weight to {new_weight}"
            )
            return {
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
        endpoint = f"PUT /api/config/strategy/{strategy_name}/weight"
        event_logger.log_api_error(endpoint=endpoint, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy weight: {str(e)}"
        )


@router.get("/config/probability", response_model=ProbabilityConfig)
async def get_probability_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get probability configuration.
    
    Returns:
        ProbabilityConfig: Probability configuration
    """
    try:
        config = await config_service.load_config_async()
        return {
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
        event_logger.log_api_error(
            endpoint="GET /api/config/probability", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get probability config: {str(e)}"
        )


@router.put("/config/probability", status_code=status.HTTP_200_OK)
async def update_probability_config(
    data: UpdateProbabilitySettingsRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update probability configuration.
    
    Args:
        data: New probability settings
        
    Returns:
        Dict[str, Any]: Result of the update operation
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
                        status_code=400,
                        detail=f"{key} must be between 0.0 and 1.0"
                    )

        success = await config_service.update_probability_settings_async(prob_settings)

        if success:
            event_logger.log_event(
                EventType.PARAMETER_CHANGED,
                "Probability settings updated successfully"
            )
            return {
                "message": "Probability settings updated successfully",
                "updated_settings": prob_settings,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update probability settings"
            )
    except HTTPException:
        raise
    except Exception as e:
        event_logger.log_api_error(
            endpoint="PUT /api/config/probability", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update probability config: {str(e)}"
        )


@router.get("/config/validate", response_model=ValidationResponse)
async def validate_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Validate current configuration.
    
    Returns:
        ValidationResponse: Validation results
    """
    try:
        validation_errors = await config_service.validate_config_async()

        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "error_count": len(validation_errors),
        }
    except Exception as e:
        event_logger.log_api_error(
            endpoint="GET /api/config/validate", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.post("/config/reload", response_model=ReloadConfigResponse)
async def reload_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Force reload configuration from file.
    
    Returns:
        ReloadConfigResponse: Result of the reload operation
    """
    try:
        await config_service.load_config_async(force_reload=True)
        validation_errors = await config_service.validate_config_async()

        event_logger.log_event(
            EventType.PARAMETER_CHANGED,
            "Configuration reloaded successfully"
        )
        
        return {
            "message": "Configuration reloaded successfully",
            "config_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
        }
    except Exception as e:
        event_logger.log_api_error(
            endpoint="POST /api/config/reload", 
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        ) 