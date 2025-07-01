"""
Configuration API endpoints for managing trading bot settings.
"""

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

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
router = APIRouter(
    prefix="/api/config",
    tags=["config"],
)

# Initialize service
config_service = ConfigService()


@router.get("", response_model=ConfigSummary)
async def get_config() -> Dict[str, Any]:
    """
    Get current configuration summary.
    
    Returns:
    --------
    ConfigSummary: Current configuration with validation status
    """
    try:
        config_summary = await config_service.get_config_summary_async()
        return config_summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("", status_code=status.HTTP_200_OK)
async def update_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update configuration.
    
    Note: This is a placeholder implementation.
    
    Parameters:
    -----------
    data: Configuration data to update
    
    Returns:
    --------
    Dict: Result of the update operation
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/summary", response_model=ConfigSummary)
async def get_config_summary() -> Dict[str, Any]:
    """
    Get configuration summary with validation status.
    
    Returns:
    --------
    ConfigSummary: Current configuration summary with validation status
    """
    try:
        summary = await config_service.get_config_summary_async()
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config summary: {str(e)}"
        )


@router.get("/strategies", response_model=StrategyWeightsResponse)
async def get_strategy_config() -> Dict[str, Any]:
    """
    Get strategy configuration.
    
    Returns:
    --------
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy config: {str(e)}"
        )


@router.get("/strategy/{strategy_name}", response_model=StrategyParamsResponse)
async def get_strategy_params(strategy_name: str) -> Dict[str, Any]:
    """
    Get parameters for a specific strategy.
    
    Parameters:
    -----------
    strategy_name: Name of the strategy
    
    Returns:
    --------
    StrategyParamsResponse: Parameters for the specified strategy
    """
    try:
        params = await config_service.get_strategy_params_async(strategy_name)
        return {"strategy_name": strategy_name, "parameters": params}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy params: {str(e)}"
        )


@router.put("/strategy/{strategy_name}/weight")
async def update_strategy_weight(
    strategy_name: str, 
    weight_request: UpdateStrategyWeightRequest
) -> Dict[str, Any]:
    """
    Update strategy weight.
    
    Parameters:
    -----------
    strategy_name: Name of the strategy
    weight_request: Request with new weight value
    
    Returns:
    --------
    Dict: Result of the update operation
    """
    try:
        new_weight = weight_request.weight

        success = await config_service.update_strategy_weight_async(
            strategy_name, new_weight
        )

        if success:
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy weight: {str(e)}"
        )


@router.get("/probability", response_model=ProbabilityConfig)
async def get_probability_config() -> Dict[str, Any]:
    """
    Get probability configuration.
    
    Returns:
    --------
    ProbabilityConfig: Current probability configuration
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get probability config: {str(e)}"
        )


@router.put("/probability")
async def update_probability_config(
    request: UpdateProbabilitySettingsRequest
) -> Dict[str, Any]:
    """
    Update probability configuration.
    
    Parameters:
    -----------
    request: Request with new probability settings
    
    Returns:
    --------
    Dict: Result of the update operation
    """
    try:
        prob_settings = request.probability_settings

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

        success = await config_service.update_probability_settings_async(prob_settings)

        if success:
            return {
                "message": "Probability settings updated successfully",
                "updated_settings": prob_settings,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update probability settings"
            )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update probability config: {str(e)}"
        )


@router.get("/validate", response_model=ValidationResponse)
async def validate_config() -> Dict[str, Any]:
    """
    Validate current configuration.
    
    Returns:
    --------
    ValidationResponse: Validation result with any errors
    """
    try:
        validation_errors = await config_service.validate_config_async()

        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "error_count": len(validation_errors),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.post("/reload", response_model=ReloadConfigResponse)
async def reload_config() -> Dict[str, Any]:
    """
    Force reload configuration from file.
    
    Returns:
    --------
    ReloadConfigResponse: Result of the reload operation with validation status
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration reload failed: {str(e)}"
        ) 