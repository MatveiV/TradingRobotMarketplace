"""
Enhanced Robot Manager with real trading functionality
Implements real-time trading, risk management, and comprehensive monitoring
"""
import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List
from app.models import Strategy, RobotStatus
from app.adapters.mt4_adapter import EnhancedMT4Adapter

from app.config import config

class OrderManager:
    """Enhanced order management with persistence and tracking"""
    
    def __init__(self):
        self.orders = {}
        self.order_history = {}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
        self.stats = {
            "total_orders": 0,
            "pending_orders": 0,
            "completed_orders": 0,
            "cancelled_orders": 0,
            "rejected_orders": 0
        }
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and track a new order"""
        async with self.lock:
            order_id = order_data.get("order_id") or f"ORD-{int(time.time())}"
            
            order = {
                "order_id": order_id,
                "client_id": order_data.get("client_id"),
                "symbol": order_data.get("symbol"),
                "type": order_data.get("type"),
                "side": order_data.get("side"),
                "quantity": order_data.get("quantity"),
                "price": order_data.get("price"),
                "stop_price": order_data.get("stop_price"),
                "time_in_force": order_data.get("time_in_force", "GTC"),
                "status": "pending",
                "created_at": time.time(),
                "updated_at": time.time(),
                "broker_order_id": None,
                "filled_quantity": 0,
                "average_price": None,
                "commission": 0,
                "fee": 0,
                "metadata": order_data.get("metadata", {}),
                "tags": order_data.get("tags", [])
            }
            
            self.orders[order_id] = order
            self.order_history[order_id] = []
            self.stats["total_orders"] += 1
            self.stats["pending_orders"] += 1
            
            self.logger.info(f"Order created: {order_id} - {order['side']} {order['quantity']} {order['symbol']}")
            
            return order
    
    async def update_order_status(self, order_id: str, status: str, details: Dict[str, Any] = None):
        """Update order status and track changes"""
        async with self.lock:
            if order_id in self.orders:
                old_status = self.orders[order_id]["status"]
                self.orders[order_id]["status"] = status
                self.orders[order_id]["updated_at"] = time.time()
                
                if details:
                    self.orders[order_id].update(details)
                
                # Track status change
                change_record = {
                    "timestamp": time.time(),
                    "old_status": old_status,
                    "new_status": status,
                    "details": details
                }
                
                self.order_history[order_id].append(change_record)
                
                # Update statistics
                if old_status == "pending":
                    self.stats["pending_orders"] -= 1
                
                if status == "filled" or status == "cancelled":
                    self.stats["completed_orders"] += 1
                    self.stats["pending_orders"] -= 1
                elif status == "open":
                    self.stats["pending_orders"] -= 1
                
                self.logger.info(f"Order status updated: {order_id} {old_status} -> {status}")
    
    async def get_order(self, order_id: str, client_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get order by ID with optional client_id filtering"""
        async with self.lock:
            order = self.orders.get(order_id)
            
            if order:
                # Filter by client_id if specified
                if client_id and order.get("client_id") != client_id:
                    return None
                return order.copy()
            return None
    
    async def cancel_order(self, order_id: str, reason: str = "manual_cancellation"):
        """Cancel order and update status"""
        await self.update_order_status(order_id, "cancelled", {"reason": reason})
        self.logger.info(f"Order cancelled: {order_id} - {reason}")
    
    async def fill_order(self, order_id: str, filled_quantity: float, average_price: float, commission: float = 0, fee: float = 0):
        """Record order fill"""
        async with self.lock:
            if order_id in self.orders:
                order = self.orders[order_id]
                
                order["filled_quantity"] = filled_quantity
                order["average_price"] = average_price
                order["commission"] = commission
                order["fee"] = fee
                
                if filled_quantity >= order["quantity"]:
                    await self.update_order_status(order_id, "filled")
                    self.stats["completed_orders"] += 1
                    self.stats["pending_orders"] -= 1
                elif filled_quantity > 0:
                    await self.update_order_status(order_id, "partially_filled")
                
                # Record fill details
                fill_record = {
                    "timestamp": time.time(),
                    "filled_quantity": filled_quantity,
                    "average_price": average_price,
                    "commission": commission,
                    "fee": fee
                }
                
                self.order_history[order_id].append({"type": "fill", **fill_record})
                
                self.logger.info(f"Order filled: {order_id} - {filled_quantity} units @ {average_price}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders, optionally filtered by symbol"""
        async with self.lock:
            open_orders = []
            
            for order_id, order in self.orders.items():
                if order["status"] in ["pending", "open", "partially_filled"]:
                    if not symbol or order["symbol"] == symbol:
                        open_orders.append(order.copy())
            
            return open_orders
    
    async def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get order history and status changes"""
        async with self.lock:
            if order_id in self.order_history:
                return self.order_history[order_id].copy()
            return []
    
    async def cleanup(self):
        """Cleanup order data"""
        async with self.lock:
            self.orders.clear()
            self.order_history.clear()
            self.stats = {
                "total_orders": 0,
                "pending_orders": 0,
                "completed_orders": 0,
                "cancelled_orders": 0,
                "rejected_orders": 0
            }
            self.logger.info("Order manager cleanup completed")
class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, risk_limits: Dict[str, Any] = None):
        self.risk_limits = risk_limits or config.RISK_LIMITS
        self.position_tracker = PositionTracker()
        self.market_data_cache = {}
        self.risk_rules = RiskRules()
        self.logger = logging.getLogger(__name__)
        
        # Initialize risk monitoring
        self.risk_violations = []
        self.risk_alerts = []
    
    async def check_order_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any] = None) -> tuple[bool, str]:
        """Comprehensive risk checking for order"""
        try:
            # Run all risk checks
            risk_checks = [
                self._check_order_size_risk(order_request, account_info),
                self._check_position_limit_risk(order_request, account_info),
                self._check_account_risk_risk(order_request, account_info),
                self._check_market_risk(order_request, account_info),
                self._check_symbol_risk(order_request, account_info),
                self._check_time_risk(order_request, account_info),
                self._check_regulatory_risk(order_request, account_info)
            ]
            
            # Collect all violations
            violations = []
            for check_name, passed, message in risk_checks:
                if not passed:
                    violations.append(message)
                    self.risk_violations.append({
                        "timestamp": time.time(),
                        "order_id": order_request.get("order_id"),
                        "violation_type": check_name,
                        "message": message,
                        "severity": self._get_violation_severity(check_name)
                    })
            
            if violations:
                violation_summary = "; ".join(violations)
                self.risk_alerts.append({
                    "timestamp": time.time(),
                    "type": "risk_violation",
                    "message": f"Order blocked due to risk violations: {violation_summary}"
                })
                
                self.logger.warning(f"Order blocked due to risk violations: {violation_summary}")
                return False, f"Order rejected: {violation_summary}"
            
            return True, "Order passes all risk checks"
            
        except Exception as e:
            self.logger.error(f"Error in risk checking: {e}")
            return False, f"Risk check error: {str(e)}"
    
    async def _check_order_size_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check order size against risk limits"""
        try:
            order_value = order_request.get("quantity", 0) * order_request.get("price", 0)
            max_order_value = self.risk_limits["max_order_value"]
            
            if order_value > max_order_value:
                return "order_size", False, f"Order value ${order_value:.2f} exceeds limit ${max_order_value:.2f}"
            
            # Check if order is within reasonable bounds
            min_order_size = 0.01  # Minimum 0.01 units
            if order_request.get("quantity", 0) < min_order_size:
                return "order_size", False, f"Order size {order_request.get('quantity')} below minimum {min_order_size}"
            
            return "order_size", True, "Order size is within limits"
            
        except Exception as e:
            return "order_size", False, f"Order size risk check error: {str(e)}"
    
    async def _check_position_limit_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check position count against limits"""
        try:
            symbol = order_request.get("symbol")
            order_side = order_request.get("side", "buy").lower()
            quantity = order_request.get("quantity", 0)
            
            # Get current positions for this symbol
            current_positions = await self.position_tracker.get_positions(symbol)
            
            # Calculate new position
            if order_side == "buy":
                new_position = quantity
            else:
                new_position = -quantity
            
            # Check total position limits
            max_positions = self.risk_limits["max_positions"]
            total_positions = len([p for p in current_positions if abs(p.get("quantity", 0)) > 0])
            
            if total_positions >= max_positions:
                return "position_limit", False, f"Maximum positions ({max_positions}) exceeded"
            
            # Check position size limits for specific symbols (if configured)
            # This would require additional configuration
            
            return "position_limit", True, "Position limits within bounds"
            
        except Exception as e:
            return "position_limit", False, f"Position limit risk check error: {str(e)}"
    
    async def _check_account_risk_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check account risk (position size vs account balance)"""
        try:
            # Default account balance if not provided
            account_balance = account_info.get("balance", 50000) if account_info else 50000
            
            order_value = order_request.get("quantity", 0) * order_request.get("price", 0)
            max_account_risk = self.risk_limits["max_account_risk"]
            
            # Calculate risk percentage
            account_risk = order_value / account_balance
            
            if account_risk > max_account_risk:
                return "account_risk", False, f"Order risk {account_risk:.2%} exceeds limit {max_account_risk:.2%}"
            
            # Check minimum account balance
            min_account_balance = self.risk_limits["min_account_balance"]
            if account_balance < min_account_balance:
                return "account_balance", False, f"Account balance ${account_balance:.2f} below minimum ${min_account_balance:.2f}"
            
            return "account_risk", True, "Account risk is within limits"
            
        except Exception as e:
            return "account_risk", False, f"Account risk check error: {str(e)}"
    
    async def _check_market_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check market-specific risks"""
        try:
            symbol = order_request.get("symbol")
            
            # Check for circuit breakers or market halts
            if await self._is_market_halted(symbol):
                return "market_status", False, f"Market for {symbol} is halted or suspended"
            
            # Check for extreme volatility
            if await self._is_extremely_volatile(symbol):
                return "market_volatility", False, f"Extreme volatility detected for {symbol}"
            
            # Check for liquidity issues
            if await self._is_low_liquidity(symbol):
                return "market_liquidity", False, f"Low liquidity detected for {symbol}"
            
            return "market_risk", True, "Market risk is within acceptable limits"
            
        except Exception as e:
            return "market_risk", False, f"Market risk check error: {str(e)}"
    
    async def _is_market_halted(self, symbol: str) -> bool:
        """Check if market is halted or suspended"""
        # This would integrate with real market data APIs
        # For demonstration, return False
        return False
    
    async def _is_extremely_volatile(self, symbol: str) -> bool:
        """Check for extreme volatility"""
        # This would check volatility indices, etc.
        # For demonstration, return False
        return False
    
    async def _is_low_liquidity(self, symbol: str) -> bool:
        """Check for low liquidity"""
        # This would check bid-ask spreads, volume, etc.
        # For demonstration, return False
        return False
    
    async def _check_symbol_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check symbol-specific risk rules"""
        try:
            symbol = order_request.get("symbol")
            
            # Check symbol format (example: must be 3-7 characters)
            if symbol and (len(symbol) < 3 or len(symbol) > 7):
                return "symbol_format", False, f"Invalid symbol format: {symbol}"
            
            # Check if symbol is supported by the broker
            if not await self._is_symbol_supported(symbol):
                return "symbol_support", False, f"Symbol {symbol} is not supported by the broker"
            
            # Check for symbol-specific risk limits
            # This would require symbol-specific configuration
            
            return "symbol_risk", True, "Symbol risk is within limits"
            
        except Exception as e:
            return "symbol_risk", False, f"Symbol risk check error: {str(e)}"
    
    async def _is_symbol_supported(self, symbol: str) -> bool:
        """Check if symbol is supported by the broker"""
        # This would query the broker's symbol list
        # For demonstration, return True for common symbols
        supported_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
        return symbol.upper() in supported_symbols
    
    async def _check_time_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check time-based risk factors"""
        try:
            # Check if trading is allowed at current time
            current_hour = time.localtime().tm_hour
            current_day = time.localtime().tm_wday  # 0-6, Monday is 0
            
            # Check for trading hours (example: no trading on weekends or late night)
            if current_day >= 5:  # Saturday or Sunday
                return "trading_hours", False, "Trading not allowed on weekends"
            
            if current_hour < 0 or current_hour > 23:  # Outside normal trading hours
                return "trading_hours", False, "Outside normal trading hours"
            
            return "time_risk", True, "Time-based risk checks passed"
            
        except Exception as e:
            return "time_risk", False, f"Time risk check error: {str(e)}"
    
    async def _check_regulatory_risk(self, order_request: Dict[str, Any], account_info: Dict[str, Any]) -> tuple[str, bool, str]:
        """Check regulatory compliance"""
        try:
            # Check account type restrictions
            account_type = account_info.get("type", "individual") if account_info else "individual"
            
            if account_type not in ["individual", "institutional", "corporate"]:
                return "account_type", False, f"Unsupported account type: {account_type}"
            
            # Check order size limits for retail accounts
            if account_type == "individual":
                order_value = order_request.get("quantity", 0) * order_request.get("price", 0)
                retail_max_order = 10000  # Example: $10,000 max for retail accounts
                
                if order_value > retail_max_order:
                    return "regulatory_limit", False, f"Order value ${order_value:.2f} exceeds retail account limit ${retail_max_order:.2f}"
            
            # Check for prohibited securities (example)
            prohibited_symbols = ["TEST", "FAKE"]
            symbol = order_request.get("symbol")
            if symbol in prohibited_symbols:
                return "regulatory", False, f"Symbol {symbol} is not tradable"
            
            return "regulatory", True, "Regulatory checks passed"
            
        except Exception as e:
            return "regulatory", False, f"Regulatory check error: {str(e)}"
    
    def _get_violation_severity(self, violation_type: str) -> str:
        """Get severity level for risk violation"""
        severe_violations = ["account_risk", "regulatory_limit", "position_limit"]
        moderate_violations = ["order_size", "market_status"]
        
        if violation_type in severe_violations:
            return "critical"
        elif violation_type in moderate_violations:
            return "warning"
        else:
            return "info"
    
    async def monitor_account_risk(self, account_info: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor ongoing account risk"""
        try:
            violations = []
            alerts = []
            
            # Check position limits
            positions = await self.position_tracker.get_all_positions()
            
            # Calculate current exposure
            total_exposure = sum(abs(p.get("quantity", 0) * p.get("price", 0)) for p in positions)
            account_balance = account_info.get("balance", 50000)
            
            exposure_ratio = total_exposure / account_balance
            
            if exposure_ratio > self.risk_limits["max_account_risk"]:
                violations.append({
                    "type": "excessive_exposure",
                    "current": exposure_ratio,
                    "limit": self.risk_limits["max_account_risk"],
                    "message": f"Account exposure {exposure_ratio:.2%} exceeds risk limit"
                })
            
            # Check daily loss
            daily_loss = await self._calculate_daily_loss()
            if daily_loss > self.risk_limits["max_daily_loss"]:
                violations.append({
                    "type": "excessive_loss",
                    "current": daily_loss,
                    "limit": self.risk_limits["max_daily_loss"],
                    "message": f"Daily loss ${daily_loss:.2f} exceeds limit ${self.risk_limits['max_daily_loss']:.2f}"
                })
            
            # Compile risk report
            risk_report = {
                "timestamp": time.time(),
                "total_positions": len(positions),
                "total_exposure": total_exposure,
                "exposure_ratio": exposure_ratio,
                "daily_loss": daily_loss,
                "violations": violations,
                "alerts": self.risk_alerts,
                "risk_limits": self.risk_limits
            }
            
            return risk_report
            
        except Exception as e:
            self.logger.error(f"Error monitoring account risk: {e}")
            return {"error": str(e)}
    
    async def _calculate_daily_loss(self) -> float:
        """Calculate today's realized loss"""
        # This would query the broker for today's P&L
        # For demonstration, return 0
        return 0
    
    async def cleanup(self):
        """Cleanup risk management resources"""
        self.position_tracker.cleanup()
        self.risk_rules.cleanup()
        self.risk_violations.clear()
        self.risk_alerts.clear()
        self.logger.info("Risk manager cleanup completed")
class PositionTracker:
    """Track and manage open positions"""
    
    def __init__(self):
        self.positions = {}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    async def add_position(self, position_data: Dict[str, Any]):
        """Add or update a position"""
        async with self.lock:
            position_id = position_data.get("position_id")
            
            if position_id:
                self.positions[position_id] = {
                    **position_data,
                    "updated_at": time.time()
                }
                
                self.logger.info(f"Position added/updated: {position_id}")
    
    async def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position by ID"""
        async with self.lock:
            return self.positions.get(position_id)
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all positions, optionally filtered by symbol"""
        async with self.lock:
            positions = list(self.positions.values())
            
            if symbol:
                positions = [p for p in positions if p.get("symbol") == symbol]
            
            return positions
    
    async def update_position(self, position_id: str, updates: Dict[str, Any]):
        """Update position with new data"""
        async with self.lock:
            if position_id in self.positions:
                self.positions[position_id].update(updates)
                self.positions[position_id]["updated_at"] = time.time()
                
                self.logger.info(f"Position updated: {position_id}")
    
    async def remove_position(self, position_id: str):
        """Remove position"""
        async with self.lock:
            if position_id in self.positions:
                del self.positions[position_id]
                self.logger.info(f"Position removed: {position_id}")
    
    async def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        async with self.lock:
            return list(self.positions.values())
    
    async def cleanup(self):
        """Cleanup position data"""
        async with self.lock:
            self.positions.clear()
            self.logger.info("Position tracker cleanup completed")
class RiskRules:
    """Risk rule engine for dynamic risk management"""
    
    def __init__(self):
        self.rules = {}
        self.logger = logging.getLogger(__name__)
    
    async def add_rule(self, rule_name: str, condition: Callable, action: Callable):
        """Add a risk rule"""
        self.rules[rule_name] = {
            "condition": condition,
            "action": action,
            "enabled": True,
            "last_checked": None
        }
    
    async def check_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all risk rules against context"""
        violations = []
        
        for rule_name, rule_config in self.rules.items():
            if rule_config["enabled"]:
                try:
                    rule_config["last_checked"] = time.time()
                    
                    if await rule_config["condition"](context):
                        violation = await rule_config["action"](context)
                        if violation:
                            violations.append(violation)
                            
                except Exception as e:
                    self.logger.error(f"Error in risk rule {rule_name}: {e}")
        
        return violations
    
    async def cleanup(self):
        """Cleanup risk rules"""
        self.rules.clear()
class EnhancedRobotManager:
    """Enhanced robot manager with real trading functionality"""
    
    def __init__(self):
        self.running_robots = {}
        self.adapters = {}
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self.logger = logging.getLogger(__name__)
        
        # Setup monitoring
        self.monitoring_tasks = {}
        self.health_checks = {}
    
    async def connect_robot(self, strategy: Strategy) -> bool:
        """Connect robot to trading system with enhanced validation"""
        try:
            strategy_id = strategy.id
            
            # Check if robot already exists
            if strategy_id in self.running_robots:
                self.logger.warning(f"Robot {strategy_id} already exists")
                return False
            
            if strategy.platform_type in ("mt4", "mt5"):
                adapter = EnhancedMT4Adapter()
            else:
                self.logger.error(f"Unsupported platform type: {strategy.platform_type}")
                return False
            
            # Prepare connection credentials
            credentials = self._prepare_credentials(strategy)
            
            # Connect adapter
            connection_result = await adapter.connect(credentials)
            if not connection_result:
                self.logger.error(f"Failed to connect adapter for strategy {strategy_id}")
                return False
            
            # Store adapter and robot
            self.adapters[strategy_id] = adapter
            self.running_robots[strategy_id] = {
                "strategy": strategy,
                "adapter": adapter,
                "connected_at": time.time(),
                "status": "connected"
            }
            
            self.logger.info(f"Robot {strategy_id} connected successfully via {strategy.platform_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting robot {strategy.id}: {e}")
            return False
    
    def _prepare_credentials(self, strategy: Strategy) -> Dict[str, Any]:
        credentials = {}
        if strategy.platform_type == "mt4":
            if strategy.mt4_login:
                credentials["login"] = strategy.mt4_login
            if strategy.mt4_password:
                credentials["password"] = strategy.mt4_password
            if strategy.mt4_server:
                credentials["server"] = strategy.mt4_server
        elif strategy.platform_type == "mt5":
            if strategy.mt5_login:
                credentials["login"] = strategy.mt5_login
            if strategy.mt5_password:
                credentials["password"] = strategy.mt5_password
            if strategy.mt5_server:
                credentials["server"] = strategy.mt5_server
        return credentials
    
    async def check_robot_running(self, strategy: Strategy) -> Dict[str, Any]:
        """Check if another robot is running on the same account"""
        strategy_id = strategy.id
        
        # Check if any robot is running
        for sid, robot_info in self.running_robots.items():
            if sid != strategy_id and robot_info.get("status") == "running":
                return {
                    "robot_running": True,
                    "robot_id": sid,
                    "robot_name": robot_info.get("strategy", {}).name if hasattr(robot_info.get("strategy"), "name") else f"Robot {sid}",
                    "strategy_id": sid
                }
        
        return {"robot_running": False}
    
    async def replace_robot(self, strategy: Strategy) -> bool:
        """Replace running robot with new one"""
        try:
            # Stop existing robot if running
            for sid in list(self.running_robots.keys()):
                if sid != strategy.id:
                    await self.stop_robot(sid)
            
            # Connect new robot
            return await self.connect_robot(strategy)
        except Exception as e:
            self.logger.error(f"Error replacing robot: {e}")
            return False
    
    async def start_robot(self, strategy: Strategy) -> bool:
        """Start the robot with enhanced functionality"""
        try:
            strategy_id = strategy.id
            
            if strategy_id not in self.running_robots:
                self.logger.error(f"Robot {strategy_id} not connected")
                return False
            
            robot_info = self.running_robots[strategy_id]
            adapter = robot_info["adapter"]
            
            # Start trading based on platform type
            if strategy.platform_type == "mt4":
                # For MT4, attach robot and apply settings
                ex4_path = strategy.robot_file_path
                set_path = strategy.settings_file_path
                
                if ex4_path:
                    attachment_result = await adapter.attach_robot(ex4_path, set_path)
                    if not attachment_result:
                        self.logger.error(f"Failed to attach robot to MT4: {strategy_id}")
                        return False
                
                # Start monitoring
                monitor_result = await adapter.start_monitoring()
                if not monitor_result:
                    self.logger.error(f"Failed to start MT4 monitoring: {strategy_id}")
                    return False
                    
            elif strategy.platform_type == "generic_api":
                # For Generic API, start order monitoring
                monitoring_config = {
                    "check_interval": strategy.sync_interval or 60,
                    "webhook_enabled": True
                }
                
                monitor_result = await adapter.start_monitoring(monitoring_config)
                if not monitor_result:
                    self.logger.error(f"Failed to start API monitoring: {strategy_id}")
                    return False
            
            # Update robot status
            self.running_robots[strategy_id]["status"] = "running"
            self.running_robots[strategy_id]["started_at"] = time.time()
            
            # Setup monitoring tasks
            await self._setup_monitoring(strategy_id)
            
            self.logger.info(f"Robot {strategy_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting robot {strategy.id}: {e}")
            return False
    
    async def _setup_monitoring(self, strategy_id: int):
        """Setup monitoring for robot"""
        try:
            robot_info = self.running_robots[strategy_id]
            adapter = robot_info["adapter"]
            
            # Setup health check task
            health_task = asyncio.create_task(self._health_check(strategy_id))
            self.monitoring_tasks[strategy_id] = health_task
            
            # Setup performance monitoring task
            perf_task = asyncio.create_task(self._performance_monitor(strategy_id))
            self.monitoring_tasks[strategy_id] = perf_task
            
            # Setup risk monitoring task
            risk_task = asyncio.create_task(self._risk_monitor(strategy_id))
            self.monitoring_tasks[strategy_id] = risk_task
            
        except Exception as e:
            self.logger.error(f"Error setting up monitoring for robot {strategy_id}: {e}")
    
    async def _health_check(self, strategy_id: int):
        """Background health check task"""
        try:
            while strategy_id in self.running_robots:
                robot_info = self.running_robots[strategy_id]
                
                if robot_info["status"] != "running":
                    break
                
                # Perform health check
                adapter = robot_info["adapter"]
                status = await adapter.get_status()
                
                # Record health check
                if strategy_id not in self.health_checks:
                    self.health_checks[strategy_id] = []
                
                self.health_checks[strategy_id].append({
                    "timestamp": time.time(),
                    "status": status,
                    "healthy": status.get("connected", False)
                })
                
                # Clean old health checks (keep last 1000)
                if len(self.health_checks[strategy_id]) > 1000:
                    self.health_checks[strategy_id] = self.health_checks[strategy_id][-500:]
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except asyncio.CancelledError:
            self.logger.info(f"Health check cancelled for robot {strategy_id}")
        except Exception as e:
            self.logger.error(f"Error in health check for robot {strategy_id}: {e}")
    
    async def _performance_monitor(self, strategy_id: int):
        """Background performance monitoring task"""
        try:
            while strategy_id in self.running_robots:
                robot_info = self.running_robots[strategy_id]
                
                if robot_info["status"] != "running":
                    break
                
                # Get performance metrics
                adapter = robot_info["adapter"]
                performance = await adapter.get_performance()
                
                # Store performance metrics
                if not hasattr(self, 'performance_metrics'):
                    self.performance_metrics = {}
                
                if strategy_id not in self.performance_metrics:
                    self.performance_metrics[strategy_id] = []
                
                self.performance_metrics[strategy_id].append({
                    "timestamp": time.time(),
                    "performance": performance
                })
                
                # Clean old metrics (keep last 1000)
                if len(self.performance_metrics[strategy_id]) > 1000:
                    self.performance_metrics[strategy_id] = self.performance_metrics[strategy_id][-500:]
                
                # Log performance warnings
                if performance.get("total_profit", 0) < 0:
                    self.logger.warning(f"Robot {strategy_id} has negative profit: ${performance.get('total_profit', 0)}")
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
        except asyncio.CancelledError:
            self.logger.info(f"Performance monitor cancelled for robot {strategy_id}")
        except Exception as e:
            self.logger.error(f"Error in performance monitor for robot {strategy_id}: {e}")
    
    async def _risk_monitor(self, strategy_id: int):
        """Background risk monitoring task"""
        try:
            while strategy_id in self.running_robots:
                robot_info = self.running_robots[strategy_id]
                
                if robot_info["status"] != "running":
                    break
                
                # Get account info from adapter status
                adapter = robot_info["adapter"]
                status = await adapter.get_status()
                
                # Monitor account risk
                account_info = {
                    "balance": status.get("account_balance", 50000),
                    "type": "individual"
                }
                
                risk_report = await self.risk_manager.monitor_account_risk(account_info)
                
                # Process risk violations
                if risk_report.get("violations"):
                    for violation in risk_report["violations"]:
                        self.logger.warning(f"Risk violation for robot {strategy_id}: {violation['message']}")
                        
                        # Auto-action based on violation severity
                        if violation.get("severity") == "critical":
                            await self._handle_critical_risk_violation(strategy_id, violation)
                
                await asyncio.sleep(60)  # Risk monitor every 60 seconds
                
        except asyncio.CancelledError:
            self.logger.info(f"Risk monitor cancelled for robot {strategy_id}")
        except Exception as e:
            self.logger.error(f"Error in risk monitor for robot {strategy_id}: {e}")
    
    async def _handle_critical_risk_violation(self, strategy_id: int, violation: Dict[str, Any]):
        """Handle critical risk violations"""
        try:
            robot_info = self.running_robots.get(strategy_id)
            if not robot_info:
                return
            
            adapter = robot_info["adapter"]
            
            # For critical violations, stop the robot
            self.logger.critical(f"Critical risk violation for robot {strategy_id}. Stopping robot.")
            
            # Close all open positions
            if hasattr(adapter, 'get_positions'):
                positions = await adapter.get_positions()
                for position in positions:
                    await self._close_position(strategy_id, position)
            
            # Cancel all pending orders
            open_orders = await self.order_manager.get_open_orders()
            for order in open_orders:
                await self._cancel_order(strategy_id, order.get("order_id"))
            
            # Stop monitoring
            if strategy_id in self.monitoring_tasks:
                for task in self.monitoring_tasks[strategy_id]:
                    task.cancel()
                
                del self.monitoring_tasks[strategy_id]
            
            # Update robot status
            robot_info["status"] = "stopped"
            robot_info["stopped_at"] = time.time()
            robot_info["stopped_reason"] = f"Risk violation: {violation['message']}"
            
            self.logger.info(f"Robot {strategy_id} stopped due to risk violation")
            
        except Exception as e:
            self.logger.error(f"Error handling risk violation for robot {strategy_id}: {e}")
    
    async def _close_position(self, strategy_id: int, position: Dict[str, Any]):
        """Close a position"""
        try:
            robot_info = self.running_robots.get(strategy_id)
            if not robot_info:
                return
            
            adapter = robot_info["adapter"]
            
            # Close position using adapter
            close_order = {
                "symbol": position.get("symbol"),
                "type": "market",
                "side": "sell" if position.get("quantity", 0) > 0 else "buy",
                "quantity": abs(position.get("quantity", 0)),
                "order_id": f"CLOSE-{strategy_id}-{int(time.time())}",
                "client_id": strategy_id
            }
            
            if strategy_id in self.adapters and hasattr(self.adapters[strategy_id], 'create_order'):
                await self.adapters[strategy_id].create_order(close_order)
                
        except Exception as e:
            self.logger.error(f"Error closing position for robot {strategy_id}: {e}")
    
    async def _cancel_order(self, strategy_id: int, order_id: str):
        """Cancel an order"""
        try:
            if strategy_id in self.adapters and hasattr(self.adapters[strategy_id], 'cancel_order'):
                await self.adapters[strategy_id].cancel_order(order_id, str(strategy_id))
                
        except Exception as e:
            self.logger.error(f"Error cancelling order for robot {strategy_id}: {e}")
    
    async def stop_robot(self, strategy_id: int):
        """Stop the robot and cleanup resources"""
        try:
            if strategy_id not in self.running_robots:
                self.logger.error(f"Robot {strategy_id} not found")
                return
            
            robot_info = self.running_robots[strategy_id]
            adapter = robot_info["adapter"]
            
            # Stop monitoring
            if strategy_id in self.monitoring_tasks:
                for task in self.monitoring_tasks[strategy_id]:
                    task.cancel()
                
                del self.monitoring_tasks[strategy_id]
            
            # Stop monitoring
            if hasattr(adapter, 'stop_monitoring'):
                await adapter.stop_monitoring()
            
            # Disconnect adapter
            if hasattr(adapter, 'disconnect'):
                await adapter.disconnect()
            
            # Remove from tracking
            del self.running_robots[strategy_id]
            del self.adapters[strategy_id]
            
            # Record cleanup
            if not hasattr(self, 'cleanup_log'):
                self.cleanup_log = []
            
            self.cleanup_log.append({
                "timestamp": time.time(),
                "strategy_id": strategy_id,
                "action": "stopped"
            })
            
            self.logger.info(f"Robot {strategy_id} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping robot {strategy_id}: {e}")
    
    async def get_performance(self, strategy_id: int) -> Dict[str, Any]:
        """Get robot performance metrics"""
        try:
            if strategy_id not in self.running_robots:
                return {
                    "total_profit": 0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "trades": []
                }
            
            adapter = self.running_robots[strategy_id]["adapter"]
            
            # Get performance from adapter
            performance = await adapter.get_performance()
            
            # Return flat structure matching PerformanceResponse
            return {
                "total_profit": performance.get("total_profit", 0),
                "total_trades": performance.get("total_trades", 0),
                "winning_trades": performance.get("winning_trades", 0),
                "losing_trades": performance.get("losing_trades", 0),
                "win_rate": performance.get("win_rate", 0),
                "trades": performance.get("trades", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance for robot {strategy_id}: {e}")
            return {
                "total_profit": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "trades": []
            }
    
    async def get_status(self, strategy_id: int) -> Dict[str, Any]:
        """Get comprehensive robot status"""
        try:
            if strategy_id not in self.running_robots:
                return {"error": "Robot not found"}
            
            robot_info = self.running_robots[strategy_id]
            adapter = robot_info["adapter"]
            
            # Get adapter status
            adapter_status = await adapter.get_status()
            
            # Get health check
            health_data = {}
            if strategy_id in self.health_checks:
                recent_health = self.health_checks[strategy_id][-1]
                health_data = {
                    "last_check": recent_health["timestamp"],
                    "healthy": recent_health["healthy"],
                    "consecutive_failures": self._count_consecutive_failures(strategy_id)
                }
            
            # Get performance summary
            perf_summary = {}
            if strategy_id in self.performance_metrics:
                recent_perf = self.performance_metrics[strategy_id][-1]
                perf_summary = {
                    "last_update": recent_perf["timestamp"],
                    "current_profit": recent_perf["performance"].get("total_profit", 0),
                    "total_trades": recent_perf["performance"].get("total_trades", 0),
                    "win_rate": recent_perf["performance"].get("win_rate", 0)
                }
            
            return {
                "strategy_id": strategy_id,
                "status": robot_info["status"],
                "platform_type": robot_info["strategy"].platform_type,
                "adapter_status": adapter_status,
                "health_data": health_data,
                "performance_summary": perf_summary,
                "monitored": strategy_id in self.monitoring_tasks,
                "cleanup_log": self.cleanup_log[-5:] if hasattr(self, 'cleanup_log') else []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status for robot {strategy_id}: {e}")
            return {"error": str(e)}
    
    def _count_consecutive_failures(self, strategy_id: int) -> int:
        """Count consecutive health check failures"""
        if strategy_id not in self.health_checks:
            return 0
        
        health_history = self.health_checks[strategy_id]
        if not health_history:
            return 0
        
        consecutive = 0
        for health in reversed(health_history):
            if not health["healthy"]:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    async def cleanup(self):
        """Clean up all resources and stop all robots"""
        try:
            # Stop all running robots
            robot_ids = list(self.running_robots.keys())
            for strategy_id in robot_ids:
                await self.stop_robot(strategy_id)
            
            # Cleanup adapters
            for strategy_id in self.adapters:
                adapter = self.adapters[strategy_id]
                if hasattr(adapter, 'cleanup'):
                    await adapter.cleanup()
            
            # Cleanup monitoring
            for task in self.monitoring_tasks.values():
                task.cancel()
            
            self.monitoring_tasks.clear()
            self.health_checks.clear()
            self.performance_metrics.clear()
            self.cleanup_log = []
            
            self.logger.info("Robot manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Force cleanup even if there are errors
            self.running_robots.clear()
            self.adapters.clear()
            self.monitoring_tasks.clear()

# Create enhanced robot manager instance
robot_manager = EnhancedRobotManager()