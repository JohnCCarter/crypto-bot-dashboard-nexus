"""Tests for probability-based risk management features."""

import pytest
from backend.services.risk_manager import RiskManager, RiskParameters, ProbabilityData


class TestProbabilityData:
    """Test the ProbabilityData class."""
    
    def test_probability_data_creation(self):
        """Test creating ProbabilityData object."""
        prob_data = ProbabilityData(
            probability_buy=0.7,
            probability_sell=0.1,
            probability_hold=0.2,
            confidence=0.8
        )
        
        assert prob_data.probability_buy == 0.7
        assert prob_data.probability_sell == 0.1
        assert prob_data.probability_hold == 0.2
        assert prob_data.confidence == 0.8
    
    def test_get_action_probability(self):
        """Test getting probability for specific actions."""
        prob_data = ProbabilityData(
            probability_buy=0.6,
            probability_sell=0.3,
            probability_hold=0.1,
            confidence=0.8
        )
        
        assert prob_data.get_action_probability("buy") == 0.6
        assert prob_data.get_action_probability("sell") == 0.3
        assert prob_data.get_action_probability("hold") == 0.1
        assert prob_data.get_action_probability("invalid") == 0.0
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        # High confidence + high action probability = low risk
        high_confidence = ProbabilityData(
            probability_buy=0.8,
            probability_sell=0.1,
            probability_hold=0.1,
            confidence=0.9
        )
        assert high_confidence.get_risk_score() < 0.3
        
        # Low confidence + low action probability = high risk
        low_confidence = ProbabilityData(
            probability_buy=0.4,
            probability_sell=0.3,
            probability_hold=0.3,
            confidence=0.2
        )
        assert low_confidence.get_risk_score() > 0.7


class TestRiskManagerProbabilities:
    """Test probability-based risk management features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
            max_daily_loss=0.02,
            max_open_positions=5,
            min_signal_confidence=0.6,
            probability_weight=0.5
        )
        self.risk_manager = RiskManager(self.risk_params)
    
    def test_validate_order_with_probabilities_success(self):
        """Test successful order validation with probabilities."""
        order_data = {
            "amount": 100,
            "price": 50000,
            "side": "buy",
            "leverage": 1.0
        }
        
        prob_data = ProbabilityData(
            probability_buy=0.8,
            probability_sell=0.1,
            probability_hold=0.1,
            confidence=0.7
        )
        
        result = self.risk_manager.validate_order_with_probabilities(
            order_data, 10000000, {}, prob_data
        )
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["confidence"] == 0.7
        assert result["risk_score"] < 0.5
    
    def test_validate_order_low_confidence_rejection(self):
        """Test order rejection for low confidence."""
        order_data = {
            "amount": 100,
            "price": 50000,
            "side": "buy",
            "leverage": 1.0
        }
        
        prob_data = ProbabilityData(
            probability_buy=0.7,
            probability_sell=0.2,
            probability_hold=0.1,
            confidence=0.4  # Below minimum
        )
        
        result = self.risk_manager.validate_order_with_probabilities(
            order_data, 10000000, {}, prob_data
        )
        
        assert result["valid"] is False
        assert any("confidence" in error.lower() for error in result["errors"])
    
    def test_validate_order_low_action_probability(self):
        """Test order rejection for low action probability."""
        order_data = {
            "amount": 100,
            "price": 50000,
            "side": "buy",
            "leverage": 1.0
        }
        
        prob_data = ProbabilityData(
            probability_buy=0.3,  # Low probability for buy
            probability_sell=0.1,
            probability_hold=0.6,
            confidence=0.8
        )
        
        result = self.risk_manager.validate_order_with_probabilities(
            order_data, 10000000, {}, prob_data
        )
        
        assert result["valid"] is False
        assert any("probability" in error.lower() for error in result["errors"])
    
    def test_intelligent_position_sizing(self):
        """Test intelligent position sizing with probabilities."""
        prob_data = ProbabilityData(
            probability_buy=0.8,
            probability_sell=0.1,
            probability_hold=0.1,
            confidence=0.9
        )
        
        position_size, metadata = self.risk_manager.calculate_intelligent_position_size(
            signal_confidence=0.8,
            portfolio_value=100000,
            current_positions={},
            probability_data=prob_data
        )
        
        assert position_size > 0
        assert "probability_factor" in metadata
        assert "risk_adjustment" in metadata
        assert "risk_score" in metadata
        assert metadata["probability_factor"] > 0.8  # Should be high
        assert metadata["risk_adjustment"] > 0.5  # Should reduce risk
    
    def test_position_sizing_without_probabilities(self):
        """Test position sizing fallback without probability data."""
        position_size, metadata = self.risk_manager.calculate_intelligent_position_size(
            signal_confidence=0.7,
            portfolio_value=100000,
            current_positions={}
        )
        
        assert position_size > 0
        assert metadata["probability_factor"] == 0.7
        assert metadata["risk_adjustment"] == 1.0
        assert metadata["risk_score"] is None
    
    def test_dynamic_stop_loss_high_risk(self):
        """Test dynamic stop loss for high risk signals."""
        high_risk_prob = ProbabilityData(
            probability_buy=0.4,
            probability_sell=0.3,
            probability_hold=0.3,
            confidence=0.3
        )
        
        stop_loss, metadata = self.risk_manager.calculate_dynamic_stop_loss(
            entry_price=50000,
            side="buy",
            probability_data=high_risk_prob
        )
        
        base_stop = self.risk_manager.calculate_stop_loss(50000, "buy")
        
        assert stop_loss > base_stop  # Tighter stop loss for high risk
        assert metadata["adjusted_stop_pct"] > self.risk_params.stop_loss_pct
    
    def test_dynamic_take_profit_high_confidence(self):
        """Test dynamic take profit for high confidence signals."""
        high_confidence_prob = ProbabilityData(
            probability_buy=0.9,
            probability_sell=0.05,
            probability_hold=0.05,
            confidence=0.95
        )
        
        take_profit, metadata = self.risk_manager.calculate_dynamic_take_profit(
            entry_price=50000,
            side="buy",
            probability_data=high_confidence_prob
        )
        
        base_take_profit = self.risk_manager.calculate_take_profit(50000, "buy")
        
        assert take_profit > base_take_profit  # More aggressive for high confidence
        assert metadata["adjusted_take_profit_pct"] > self.risk_params.take_profit_pct
    
    def test_portfolio_risk_assessment_empty(self):
        """Test portfolio risk assessment with no positions."""
        assessment = self.risk_manager.assess_portfolio_risk({})
        
        assert assessment["overall_risk_score"] == 0.0
        assert assessment["risk_level"] == "none"
        assert "No open positions" in assessment["recommendations"]
    
    def test_portfolio_risk_assessment_with_positions(self):
        """Test portfolio risk assessment with positions."""
        positions = {
            "BTC/USD": {
                "size": 1.0,
                "entry_price": 50000,
                "probability_data": {
                    "probability_buy": 0.8,
                    "probability_sell": 0.1,
                    "probability_hold": 0.1,
                    "confidence": 0.9
                }
            },
            "ETH/USD": {
                "size": 10.0,
                "entry_price": 3000,
                "probability_data": {
                    "probability_buy": 0.3,
                    "probability_sell": 0.6,
                    "probability_hold": 0.1,
                    "confidence": 0.4
                }
            }
        }
        
        assessment = self.risk_manager.assess_portfolio_risk(positions)
        
        assert assessment["position_count"] == 2
        assert assessment["total_exposure"] == 80000  # 50000 + 30000
        assert "overall_risk_score" in assessment
        assert "risk_level" in assessment
        assert "position_risks" in assessment
        assert len(assessment["position_risks"]) == 2
    
    def test_portfolio_risk_high_risk_warnings(self):
        """Test portfolio risk warnings for high-risk positions."""
        high_risk_positions = {
            "RISKY/USD": {
                "size": 1.0,
                "entry_price": 10000,
                "probability_data": {
                    "probability_buy": 0.2,
                    "probability_sell": 0.2,
                    "probability_hold": 0.6,
                    "confidence": 0.1
                }
            }
        }
        
        assessment = self.risk_manager.assess_portfolio_risk(high_risk_positions)
        
        assert assessment["risk_level"] == "high"
        assert any("high-risk" in rec.lower() for rec in assessment["recommendations"])


class TestIntegrationProbabilityRisk:
    """Integration tests for probability-based risk management."""
    
    def test_end_to_end_order_processing(self):
        """Test complete order processing with probabilities."""
        risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
            max_daily_loss=0.02,
            max_open_positions=5,
            min_signal_confidence=0.7,
            probability_weight=0.6
        )
        risk_manager = RiskManager(risk_params)
        
        # High quality signal
        order_data = {
            "amount": 0.1,
            "price": 50000,
            "side": "buy",
            "leverage": 1.5
        }
        
        prob_data = ProbabilityData(
            probability_buy=0.85,
            probability_sell=0.1,
            probability_hold=0.05,
            confidence=0.9
        )
        
        # Validate order
        validation = risk_manager.validate_order_with_probabilities(
            order_data, 100000, {}, prob_data
        )
        assert validation["valid"] is True
        
        # Calculate intelligent position size
        position_size, size_metadata = risk_manager.calculate_intelligent_position_size(
            signal_confidence=0.9,
            portfolio_value=100000,
            current_positions={},
            probability_data=prob_data
        )
        
        # Calculate dynamic stop loss and take profit
        stop_loss, stop_metadata = risk_manager.calculate_dynamic_stop_loss(
            entry_price=50000,
            side="buy",
            probability_data=prob_data
        )
        
        take_profit, profit_metadata = risk_manager.calculate_dynamic_take_profit(
            entry_price=50000,
            side="buy",
            probability_data=prob_data
        )
        
        # Assertions
        assert position_size > 0
        assert stop_loss < 50000  # Below entry for buy
        assert take_profit > 50000  # Above entry for buy
        assert size_metadata["risk_score"] < 0.3  # Low risk
        assert profit_metadata["adjusted_take_profit_pct"] > risk_params.take_profit_pct