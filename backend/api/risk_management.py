"""
Risk management API for FastAPI.

This module provides endpoints for risk management operations.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import (
    get_exchange_service,
    get_order_service,
    get_risk_manager,
)
from backend.api.models import (
    OrderData,
    OrderValidationResponse,
    ProbabilityDataModel,
    ResponseStatus,
    RiskAssessmentResponse,
    RiskScoreResponse,
)
from backend.services.exchange import ExchangeService
from backend.services.exchange_async import fetch_balance_async
from backend.services.order_service_async import OrderServiceAsync
from backend.services.positions_service_async import fetch_positions_async
from backend.services.risk_manager_async import ProbabilityData, RiskManagerAsync

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/risk",
    tags=["risk"],
    responses={404: {"description": "Not found"}},
)


@router.get("/assessment", response_model=RiskAssessmentResponse)
async def assess_portfolio_risk(
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    order_service: OrderServiceAsync = Depends(get_order_service),
):
    """
    Assess the overall portfolio risk based on current positions and orders.

    Returns:
        RiskAssessmentResponse: Risk assessment data
    """
    try:
        # Fetch current positions
        positions = await fetch_positions_async()
        positions_dict = {p["symbol"]: p for p in positions}

        # Fetch pending orders
        open_orders = await order_service.get_open_orders()
        orders_dict = {order["id"]: order for order in open_orders}

        # Assess risk
        risk_assessment = await risk_manager.assess_portfolio_risk(
            current_positions=positions_dict, pending_orders=orders_dict
        )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Risk assessment completed successfully",
            "risk_assessment": risk_assessment,
        }
    except Exception as e:
        logger.error(f"Failed to assess portfolio risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess portfolio risk: {str(e)}",
        )


@router.post("/validate/order", response_model=OrderValidationResponse)
async def validate_order(
    order_data: OrderData,
    probability_data: Optional[ProbabilityDataModel] = None,
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    order_service: OrderServiceAsync = Depends(get_order_service),
    exchange_service: Optional[ExchangeService] = Depends(get_exchange_service),
):
    """
    Validate an order against risk parameters.

    Args:
        order_data: Order data to validate
        probability_data: Optional probability data for enhanced validation

    Returns:
        OrderValidationResponse: Validation result
    """
    try:
        # Get portfolio value
        portfolio_value = 10000.0  # Default fallback value

        if exchange_service:
            try:
                balance_data = await fetch_balance_async(exchange_service)
                if balance_data and "total" in balance_data:
                    # Use USDT or USD value if available
                    portfolio_value = float(
                        balance_data["total"].get("USDT", 0.0)
                        or balance_data["total"].get("USD", 0.0)
                    )

                    # Fallback to BTC value if no USD/USDT
                    if portfolio_value <= 0:
                        btc_value = float(balance_data["total"].get("BTC", 0.0))
                        if btc_value > 0:
                            # Convert to USD (approximate)
                            portfolio_value = btc_value * 30000.0  # Rough estimate
            except Exception as e:
                # Log but continue with default value
                logger.warning(f"Failed to get portfolio value: {e}")

        # Get current positions
        positions = await fetch_positions_async()
        positions_dict = {p["symbol"]: p for p in positions}

        # Prepare order_data in format expected by risk manager
        order_dict = order_data.dict()

        # Convert probability data if provided
        probability_obj = None
        if probability_data:
            probability_obj = ProbabilityData(
                probability_buy=probability_data.probability_buy,
                probability_sell=probability_data.probability_sell,
                probability_hold=probability_data.probability_hold,
                confidence=probability_data.confidence,
            )

        # Validate order
        if probability_obj:
            validation_result = await risk_manager.validate_order_with_probabilities(
                order_data=order_dict,
                portfolio_value=portfolio_value,
                current_positions=positions_dict,
                probability_data=probability_obj,
            )
        else:
            validation_result = await risk_manager.validate_order(
                order_data=order_dict,
                portfolio_value=portfolio_value,
                current_positions=positions_dict,
            )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Order validation completed",
            "valid": validation_result["valid"],
            "errors": validation_result.get("errors", []),
            "risk_assessment": validation_result.get("risk_assessment", {}),
        }
    except Exception as e:
        logger.error(f"Failed to validate order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate order: {str(e)}",
        )


@router.get("/score", response_model=RiskScoreResponse)
async def get_risk_score(
    symbol: str,
    probability_buy: float,
    probability_sell: float,
    probability_hold: float,
    confidence: float,
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
):
    """
    Calculate risk score based on probability data.

    Args:
        symbol: Trading symbol
        probability_buy: Probability of buy action
        probability_sell: Probability of sell action
        probability_hold: Probability of hold action
        confidence: Confidence level

    Returns:
        RiskScoreResponse: Risk score information
    """
    try:
        # Create probability data object
        probability_data = ProbabilityData(
            probability_buy=probability_buy,
            probability_sell=probability_sell,
            probability_hold=probability_hold,
            confidence=confidence,
        )

        # Calculate risk score
        risk_score = probability_data.get_risk_score()

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Risk score calculated successfully",
            "symbol": symbol,
            "risk_score": risk_score,
            "risk_level": _get_risk_level(risk_score),
            "probability_data": {
                "probability_buy": probability_buy,
                "probability_sell": probability_sell,
                "probability_hold": probability_hold,
                "confidence": confidence,
            },
        }
    except Exception as e:
        logger.error(f"Failed to calculate risk score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate risk score: {str(e)}",
        )


def _get_risk_level(risk_score: float) -> str:
    """Convert risk score to risk level description."""
    if risk_score < 0.2:
        return "very_low"
    elif risk_score < 0.4:
        return "low"
    elif risk_score < 0.6:
        return "moderate"
    elif risk_score < 0.8:
        return "high"
    else:
        return "very_high"
