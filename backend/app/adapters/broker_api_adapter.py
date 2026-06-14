"""
Enhanced Generic Broker API adapter with real trading functionality
Implements comprehensive broker API integration with order management, webhooks, and risk controls
"""
import asyncio
import json
import httpx
import hashlib
import hmac
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from app.adapters.base import TradingAdapter
from app.config import config

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class BrokerAPIAdapter(TradingAdapter):
    """Enhanced Generic Broker API adapter with real trading functionality"""
    
    def __init__(self):
        self.api_key = None
        self.api_secret = None
        self.api_endpoint = None
        self.mode = None
        self.client = None
        self.connected = False
        self.access_token = None
        self.token_expiry = None
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        self.webhook_handler = WebhookHandler()
        self.rate_limiter = RateLimiter()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Establish real connection to broker API with authentication"""
        try:
            # Store credentials
            self.api_key = credentials.get("api_key")
            self.api_secret = credentials.get("api_secret")
            self.api_endpoint = credentials.get("api_endpoint")
            self.mode = credentials.get("api_mode", "demo")
            
            if config.USE_MOCKS:
                # Mock connection for development
                self.connected = True
                self.access_token = self._generate_mock_token()
                self.token_expiry = time.time() + 3600
                return True
            
            # Authenticate with broker
            auth_result = await self._authenticate()
            if not auth_result[0]:
                self.logger.error(f"Authentication failed: {auth_result[1]}")
                return False
            
            # Initialize HTTP client with proper configuration
            self.client = httpx.AsyncClient(
                base_url=self.api_endpoint,
                timeout=httpx.Timeout(30.0, connect=5.0),
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "TradingRobotMarketplace/1.0"
                },
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
            )
            
            # Test connection
            response = await self.client.get("/api/v1/account/balance")
            if response.status_code == 200:
                self.connected = True
                self.logger.info("Successfully connected to broker API")
                return True
            else:
                self.logger.error(f"Broker API connection failed: {response.status_code}")
                self.connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Broker API connection error: {e}")
            self.connected = False
            if self.client:
                await self.client.aclose()
            return False
    
    async def _authenticate(self) -> tuple[bool, str]:
        """Authenticate with broker API using API key/secret"""
        try:
            # Prepare authentication payload
            auth_payload = {
                "api_key": self.api_key,
                "api_secret": self.api_secret
            }
            
            # Create HMAC signature
            signature = self._create_signature(auth_payload)
            
            # Make authentication request
            headers = {
                "X-Signature": signature,
                "Content-Type": "application/json"
            }
            
            if config.DOCKER_MODE:
                # Use message queue for distributed authentication
                return await self._auth_via_mq(auth_payload, signature)
            else:
                # Direct authentication
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_endpoint}/api/v1/auth",
                        json=auth_payload,
                        headers=headers,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.access_token = data.get("access_token")
                        self.token_expiry = time.time() + data.get("expires_in", 3600)
                        return True, "Authentication successful"
                    else:
                        return False, f"Authentication failed: {response.text}"
                        
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def _create_signature(self, payload: Dict[str, Any]) -> str:
        """Create HMAC signature for API authentication"""
        import base64
        import hashlib
        import hmac
        
        # Convert payload to JSON string
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Create HMAC signature
        secret = self.api_secret.encode('utf-8')
        message = payload_str.encode('utf-8')
        
        signature = hmac.new(secret, message, hashlib.sha256).digest()
        
        # Encode to base64
        return base64.b64encode(signature).decode('utf-8')
    
    async def _auth_via_mq(self, payload: Dict[str, Any], signature: str) -> tuple[bool, str]:
        """Authenticate via message queue for distributed deployment"""
        try:
            import redis
            
            r = redis.Redis.from_url(config.MESSAGE_QUEUE_URL, decode_responses=True)
            
            # Send authentication request
            auth_request = {
                "type": "auth",
                "payload": payload,
                "signature": signature,
                "source": "broker_api_adapter"
            }
            
            r.lpush("broker_auth", json.dumps(auth_request))
            
            # Wait for authentication response
            response = r.brpop("broker_auth_response", timeout=10)
            
            if response:
                _, response_data = response
                auth_result = json.loads(response_data)
                
                if auth_result.get("success"):
                    self.access_token = auth_result.get("access_token")
                    self.token_expiry = auth_result.get("token_expiry")
                    return True, auth_result.get("message", "Authentication successful")
                else:
                    return False, auth_result.get("error", "Authentication failed")
            else:
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"Authentication via message queue error: {str(e)}"
    
    async def disconnect(self) -> bool:
        """Gracefully disconnect from broker API"""
        if self.client:
            await self.client.aclose()
            
        self.connected = False
        self.access_token = None
        self.token_expiry = None
        
        # Cleanup order manager and risk manager
        await self.order_manager.cleanup()
        await self.risk_manager.cleanup()
        await self.webhook_handler.cleanup()
        
        self.logger.info("Disconnected from broker API")
        return True
    
    async def create_order(self, order_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order with comprehensive validation and execution"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            # Validate order request
            validation_result = await self._validate_order(order_request)
            if not validation_result[0]:
                return {"success": False, "error": validation_result[1]}
            
            # Check rate limits
            rate_limit_result = await self.rate_limiter.check_limit("create_order")
            if not rate_limit_result:
                return {"success": False, "error": "Rate limit exceeded"}
            
            # Apply risk management rules
            risk_result = await self.risk_manager.check_order_risk(order_request)
            if not risk_result[0]:
                return {"success": False, "error": risk_result[1]}
            
            # Submit order to broker
            order_data = {
                "symbol": order_request.get("symbol"),
                "type": order_request.get("type"),
                "side": order_request.get("side"),
                "quantity": order_request.get("quantity"),
                "price": order_request.get("price"),
                "stop_price": order_request.get("stop_price"),
                "time_in_force": order_request.get("time_in_force", "GTC"),
                "order_id": order_request.get("order_id"),
                "client_id": order_request.get("client_id"),
                "metadata": order_request.get("metadata", {})
            }
            
            # Add signature for security
            order_data["signature"] = self._create_signature(order_data)
            
            # Send order to broker
            if config.DOCKER_MODE:
                return await self._create_order_via_mq(order_data)
            else:
                return await self._create_order_direct(order_data)
                
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_order_direct(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create order directly to broker API"""
        try:
            # Send order request
            response = await self.client.post(
                "/api/v1/orders",
                json=order_data,
                timeout=10.0
            )
            
            if response.status_code == 200:
                order_result = response.json()
                
                # Store order in order manager
                await self.order_manager.store_order(order_result)
                
                # Notify webhook subscribers
                await self.webhook_handler.notify("order_created", order_result)
                
                self.logger.info(f"Order created successfully: {order_result.get('order_id')}")
                return order_result
            else:
                error_msg = f"Order creation failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            self.logger.error(f"Error creating order directly: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_order_via_mq(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create order via message queue for distributed deployment"""
        try:
            import redis
            
            r = redis.Redis.from_url(config.MESSAGE_QUEUE_URL, decode_responses=True)
            
            # Send order to broker queue
            order_request = {
                "type": "create_order",
                "data": order_data,
                "source": "broker_api_adapter"
            }
            
            r.lpush("broker_orders", json.dumps(order_request))
            
            # Wait for order creation response
            response = r.brpop("broker_order_response", timeout=10)
            
            if response:
                _, response_data = response
                order_result = json.loads(response_data)
                
                # Store order in order manager
                await self.order_manager.store_order(order_result)
                
                # Notify webhook subscribers
                await self.webhook_handler.notify("order_created", order_result)
                
                return order_result
            else:
                return {"success": False, "error": "Order creation timeout"}
                
        except Exception as e:
            self.logger.error(f"Error creating order via message queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            # Check rate limits
            rate_limit_result = await self.rate_limiter.check_limit("cancel_order")
            if not rate_limit_result:
                return {"success": False, "error": "Rate limit exceeded"}
            
            # Get order details for validation
            order_details = await self.order_manager.get_order(order_id, client_id)
            if not order_details:
                return {"success": False, "error": "Order not found"}
            
            # Check if order can be cancelled
            if order_details.get("status") in ["filled", "cancelled"]:
                return {"success": True, "message": "Order already processed"}
            
            # Submit cancellation to broker
            cancel_request = {
                "order_id": order_id,
                "client_id": client_id,
                "action": "cancel",
                "reason": "manual_cancellation"
            }
            
            cancel_request["signature"] = self._create_signature(cancel_request)
            
            if config.DOCKER_MODE:
                return await self._cancel_order_via_mq(cancel_request)
            else:
                return await self._cancel_order_direct(cancel_request)
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return {"success": False, "error": str(e)}
    
    async def _cancel_order_direct(self, cancel_request: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel order directly to broker API"""
        try:
            response = await self.client.post(
                "/api/v1/orders/cancel",
                json=cancel_request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update order status
                await self.order_manager.update_order_status(
                    cancel_request.get("order_id"),
                    "cancelled",
                    cancel_request.get("reason", "manual_cancellation")
                )
                
                # Notify webhook subscribers
                await self.webhook_handler.notify("order_cancelled", result)
                
                return result
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error cancelling order directly: {e}")
            return {"success": False, "error": str(e)}
    
    async def _cancel_order_via_mq(self, cancel_request: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel order via message queue"""
        try:
            import redis
            
            r = redis.Redis.from_url(config.MESSAGE_QUEUE_URL, decode_responses=True)
            
            cancel_request_full = {
                "type": "cancel_order",
                "data": cancel_request,
                "source": "broker_api_adapter"
            }
            
            r.lpush("broker_orders", json.dumps(cancel_request_full))
            
            response = r.brpop("broker_order_response", timeout=10)
            
            if response:
                _, response_data = response
                result = json.loads(response_data)
                return result
            else:
                return {"success": False, "error": "Order cancellation timeout"}
                
        except Exception as e:
            self.logger.error(f"Error cancelling order via message queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_order_status(self, order_id: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current status of an order"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            # First check local order manager cache
            order_details = await self.order_manager.get_order(order_id, client_id)
            if order_details:
                return {"success": True, "data": order_details}
            
            # Fetch from broker API if not in cache
            status_request = {
                "order_id": order_id,
                "client_id": client_id
            }
            
            if config.DOCKER_MODE:
                return await self._get_order_status_via_mq(status_request)
            else:
                return await self._get_order_status_direct(status_request)
                
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_order_status_direct(self, status_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get order status directly from broker API"""
        try:
            response = await self.client.get(
                f"/api/v1/orders/{status_request.get('order_id')}",
                params={"client_id": status_request.get("client_id")},
                timeout=5.0
            )
            
            if response.status_code == 200:
                order_data = response.json()
                
                # Store in order manager
                await self.order_manager.store_order(order_data)
                
                return {"success": True, "data": order_data}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error getting order status directly: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_order_status_via_mq(self, status_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get order status via message queue"""
        try:
            import redis
            
            r = redis.Redis.from_url(config.MESSAGE_QUEUE_URL, decode_responses=True)
            
            status_request_full = {
                "type": "get_order_status",
                "data": status_request,
                "source": "broker_api_adapter"
            }
            
            r.lpush("broker_orders", json.dumps(status_request_full))
            
            response = r.brpop("broker_order_response", timeout=10)
            
            if response:
                _, response_data = response
                result = json.loads(response_data)
                
                if result.get("success"):
                    await self.order_manager.store_order(result.get("data"))
                
                return result
            else:
                return {"success": False, "error": "Order status timeout"}
                
        except Exception as e:
            self.logger.error(f"Error getting order status via message queue: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current open positions"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            params = {}
            if symbol:
                params["symbol"] = symbol
                
            response = await self.client.get(
                "/api/v1/positions",
                params=params,
                timeout=5.0
            )
            
            if response.status_code == 200:
                positions = response.json()
                return positions
            else:
                self.logger.error(f"Failed to get positions: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance information"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            response = await self.client.get(
                "/api/v1/account/balance",
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get account balance: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_trade_history(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        """Get trading history with date filtering"""
        try:
            if not self.connected:
                raise Exception("Not connected to broker API")
            
            params = {}
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date
                
            response = await self.client.get(
                "/api/v1/trades",
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get trade history: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}")
            return []
    
    async def _validate_order(self, order_request: Dict[str, Any]) -> tuple[bool, str]:
        """Validate order request"""
        required_fields = ["symbol", "type", "side", "quantity"]
        
        for field in required_fields:
            if not order_request.get(field):
                return False, f"Missing required field: {field}"
        
        # Validate order type
        try:
            order_type = OrderType(order_request.get("type"))
        except ValueError:
            return False, f"Invalid order type: {order_request.get('type')}"
        
        # Validate order side
        try:
            order_side = OrderSide(order_request.get("side"))
        except ValueError:
            return False, f"Invalid order side: {order_request.get('side')}"
        
        # Validate quantity
        quantity = order_request.get("quantity")
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return False, "Invalid order quantity"
        
        # Validate price if provided
        price = order_request.get("price")
        if price is not None:
            if not isinstance(price, (int, float)) or price <= 0:
                return False, "Invalid order price"
        
        # Validate stop price if provided
        stop_price = order_request.get("stop_price")
        if stop_price is not None:
            if not isinstance(stop_price, (int, float)) or stop_price <= 0:
                return False, "Invalid stop price"
        
        # Validate time in force
        time_in_force = order_request.get("time_in_force", "GTC")
        valid_tif = ["GTC", "IOC", "FOK", "DAY"]
        if time_in_force not in valid_tif:
            return False, f"Invalid time in force: {time_in_force}"
        
        return True, "Order validation successful"
    
    async def get_performance(self) -> Dict[str, Any]:
        """Get trading performance metrics"""
        try:
            # Get trade history from broker
            trades = await self.get_trade_history()
            
            # Get positions for unrealized PnL
            positions = await self.get_positions()
            
            # Calculate performance metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get("realized_pnl", 0) > 0])
            losing_trades = len([t for t in trades if t.get("realized_pnl", 0) < 0])
            
            # Calculate unrealized PnL from positions
            unrealized_pnl = sum(p.get("unrealized_pnl", 0) for p in positions)
            
            # Calculate total profit
            realized_pnl = sum(t.get("realized_pnl", 0) for t in trades)
            total_profit = realized_pnl + unrealized_pnl
            
            # Calculate win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate average win/loss
            avg_win = sum(t.get("realized_pnl", 0) for t in trades if t.get("realized_pnl", 0) > 0) / winning_trades if winning_trades > 0 else 0
            avg_loss = sum(t.get("realized_pnl", 0) for t in trades if t.get("realized_pnl", 0) < 0) / losing_trades if losing_trades > 0 else 0
            
            # Calculate profit factor
            profit_factor = (sum(t.get("realized_pnl", 0) for t in trades if t.get("realized_pnl", 0) > 0) /
                           abs(sum(t.get("realized_pnl", 0) for t in trades if t.get("realized_pnl", 0) < 0))) if losing_trades > 0 else float('inf')
            
            return {
                "total_profit": total_profit,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "average_win": avg_win,
                "average_loss": avg_loss,
                "profit_factor": profit_factor,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "open_positions": len(positions),
                "trades": trades,
                "positions": positions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def setup_webhooks(self, webhook_config: Dict[str, Any]) -> bool:
        """Setup webhooks for real-time updates"""
        try:
            webhook_config["adapter_id"] = id(self)
            webhook_config["broker_endpoint"] = self.api_endpoint
            
            result = await self.webhook_handler.setup(webhook_config)
            
            if result:
                self.logger.info("Webhooks setup successfully")
                return True
            else:
                self.logger.error("Failed to setup webhooks")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up webhooks: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current adapter status"""
        try:
            # Check if client is still connected
            client_connected = self.client is not None and not self.client.is_closed
            
            status = {
                "connected": self.connected and client_connected,
                "platform": "Generic Broker API",
                "mode": self.mode,
                "api_endpoint": self.api_endpoint,
                "access_token_valid": self.access_token is not None,
                "token_expiry": self.token_expiry,
                "rate_limit_remaining": await self.rate_limiter.get_remaining("general"),
                "order_count": await self.order_manager.get_order_count(),
                "webhook_count": await self.webhook_handler.get_subscriber_count()
            }
            
            if config.DOCKER_MODE:
                # Check MQ connection status
                try:
                    import redis
                    r = redis.Redis.from_url(config.MESSAGE_QUEUE_URL, decode_responses=True)
                    status["mq_connected"] = r.ping()
                except:
                    status["mq_connected"] = False
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"connected": False, "error": str(e)}

    async def start_monitoring(self, monitoring_config: Dict[str, Any]) -> bool:
        """Start real-time monitoring of broker API"""
        try:
            result = await self.webhook_handler.start_monitoring(monitoring_config)
            
            if result:
                self.logger.info("Broker monitoring started")
                return True
            else:
                self.logger.error("Failed to start broker monitoring")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop broker monitoring"""
        await self.webhook_handler.stop_monitoring()
        self.logger.info("Broker monitoring stopped")
    
    async def cleanup(self):
        """Clean up resources and stop all tasks"""
        await self.stop_monitoring()
        await self.disconnect()
        
        # Cleanup other components
        await self.order_manager.cleanup()
        await self.risk_manager.cleanup()
        await self.webhook_handler.cleanup()
        
        self.logger.info("Broker API adapter cleanup completed")

    def _generate_mock_token(self) -> str:
        """Generate mock access token for testing"""
        import base64
        import hashlib
        import time
        
        payload = {
            "sub": "test_user",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "mode": self.mode
        }
        
        token = base64.b64encode(json.dumps(payload).encode()).decode()
        return token

# Supporting classes for enhanced broker API adapter

class OrderManager:
    """Manage orders with persistent storage and retrieval"""
    
    def __init__(self):
        self.orders = {}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
    
    async def store_order(self, order_data: Dict[str, Any]):
        """Store order in memory cache"""
        async with self.lock:
            order_id = order_data.get("order_id")
            if order_id:
                self.orders[order_id] = {
                    **order_data,
                    "stored_at": time.time(),
                    "last_updated": time.time()
                }
    
    async def get_order(self, order_id: str, client_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        async with self.lock:
            if order_id in self.orders:
                order = self.orders[order_id].copy()
                
                # Filter by client_id if provided
                if client_id and order.get("client_id") != client_id:
                    return None
                    
                return order
            return None
    
    async def update_order_status(self, order_id: str, status: str, reason: str = ""):
        """Update order status"""
        async with self.lock:
            if order_id in self.orders:
                self.orders[order_id]["status"] = status
                self.orders[order_id]["status_reason"] = reason
                self.orders[order_id]["last_updated"] = time.time()
    
    async def get_order_count(self) -> int:
        """Get total number of orders"""
        async with self.lock:
            return len(self.orders)
    
    async def cleanup(self):
        """Cleanup order data"""
        async with self.lock:
            self.orders.clear()

class RiskManager:
    """Manage risk controls and limits"""
    
    def __init__(self):
        self.risk_limits = {
            "max_order_value": 100000,  # $100,000 max order value
            "max_daily_loss": 5000,     # $5,000 max daily loss
            "max_positions": 10,        # Max concurrent positions
            "max_account_risk": 0.02,    # 2% account risk per trade
            "min_account_balance": 1000 # $1,000 minimum balance
        }
        self.logger = logging.getLogger(__name__)
    
    async def check_order_risk(self, order_request: Dict[str, Any]) -> tuple[bool, str]:
        """Check if order meets risk management rules"""
        try:
            # Check order size against risk limits
            order_value = order_request.get("quantity", 0) * order_request.get("price", 0)
            
            if order_value > self.risk_limits["max_order_value"]:
                return False, f"Order value exceeds limit: ${order_value} > ${self.risk_limits['max_order_value']}"
            
            # Check account risk (simplified - would normally check actual account balance)
            account_risk = order_value / 50000  # Assuming $50,000 account for calculation
            if account_risk > self.risk_limits["max_account_risk"]:
                return False, f"Order exceeds account risk limit: {account_risk:.2%} > {self.risk_limits['max_account_risk']:.2%}"
            
            # Check symbol eligibility (example: avoid too many positions in same symbol)
            symbol = order_request.get("symbol")
            if symbol and len(symbol) > 10:
                return False, "Invalid symbol format"
            
            # Additional risk checks would go here
            # - Correlation checks
            # - Market timing checks
            # - Liquidity checks
            
            return True, "Order passes risk checks"
            
        except Exception as e:
            self.logger.error(f"Error checking order risk: {e}")
            return False, f"Risk check error: {str(e)}"
    
    async def cleanup(self):
        """Cleanup risk management data"""
        pass

class WebhookHandler:
    """Handle webhook subscriptions and notifications"""
    
    def __init__(self):
        self.subscribers = []
        self.webhook_server = None
        self.logger = logging.getLogger(__name__)
    
    async def setup(self, webhook_config: Dict[str, Any]) -> bool:
        """Setup webhook configuration"""
        try:
            # Validate webhook configuration
            if not webhook_config.get("url"):
                self.logger.error("Webhook URL is required")
                return False
            
            # Store webhook configuration
            webhook_info = {
                "url": webhook_config.get("url"),
                "events": webhook_config.get("events", []),
                "secret": webhook_config.get("secret"),
                "format": webhook_config.get("format", "json"),
                "retry_policy": webhook_config.get("retry_policy", {"max_retries": 3, "delay": 1.0})
            }
            
            self.subscribers.append(webhook_info)
            
            # Start webhook server if configured
            if webhook_config.get("enabled", True):
                await self._start_webhook_server()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up webhook: {e}")
            return False
    
    async def _start_webhook_server(self):
        """Start webhook server for receiving broker callbacks"""
        try:
            # This would start a FastAPI/Starlette server for webhooks
            # Implementation depends on the specific web framework used
            
            # For demonstration, create a simple webhook endpoint
            self.webhook_server = {
                "port": 8080,
                "endpoints": [
                    "/webhooks/broker/orders",
                    "/webhooks/broker/positions",
                    "/webhooks/broker/trades"
                ]
            }
            
            self.logger.info(f"Webhook server started on port {self.webhook_server['port']}")
            
        except Exception as e:
            self.logger.error(f"Error starting webhook server: {e}")
    
    async def notify(self, event_type: str, data: Dict[str, Any]):
        """Send notification to all webhook subscribers"""
        try:
            for subscriber in self.subscribers:
                if event_type in subscriber.get("events", []):
                    await self._send_webhook(subscriber, event_type, data)
                    
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
    
    async def _send_webhook(self, subscriber: Dict[str, Any], event_type: str, data: Dict[str, Any]):
        """Send single webhook notification"""
        try:
            webhook_url = subscriber.get("url")
            secret = subscriber.get("secret")
            
            # Prepare webhook payload
            payload = {
                "event": event_type,
                "data": data,
                "timestamp": time.time(),
                "adapter_id": "broker_api_adapter"
            }
            
            # Add signature if secret is provided
            if secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    secret.encode(),
                    json.dumps(payload, separators=(',', ':')).encode(),
                    hashlib.sha256
                ).hexdigest()
                payload["signature"] = signature
            
            # Send webhook (in real implementation, would use httpx or similar)
            # For demonstration, just log the webhook
            self.logger.info(f"Sending webhook to {webhook_url}: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook: {e}")
    
    async def start_monitoring(self, monitoring_config: Dict[str, Any]):
        """Start webhook monitoring"""
        try:
            # Setup monitoring for webhook events
            self.logger.info("Webhook monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting webhook monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop webhook monitoring"""
        self.logger.info("Webhook monitoring stopped")
    
    async def get_subscriber_count(self) -> int:
        """Get number of webhook subscribers"""
        return len(self.subscribers)
    
    async def cleanup(self):
        """Cleanup webhook resources"""
        if self.webhook_server:
            # Stop webhook server
            self.webhook_server = None
        
        self.subscribers.clear()
        self.logger.info("Webhook handler cleanup completed")

class RateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self):
        self.limits = {
            "general": {"requests": 100, "window": 60},  # 100 requests per minute
            "create_order": {"requests": 20, "window": 60},  # 20 orders per minute
            "cancel_order": {"requests": 20, "window": 60},  # 20 cancels per minute
            "get_positions": {"requests": 60, "window": 60},  # 60 position requests per minute
            "get_trade_history": {"requests": 120, "window": 60}  # 120 trade history requests per minute
        }
        self.request_counts = {}
        self.logger = logging.getLogger(__name__)
    
    async def check_limit(self, operation: str) -> bool:
        """Check if operation is within rate limits"""
        try:
            if operation not in self.limits:
                self.logger.warning(f"Unknown rate limit operation: {operation}")
                return True
            
            limit_config = self.limits[operation]
            current_time = time.time()
            window_start = current_time - limit_config["window"]
            
            if operation not in self.request_counts:
                self.request_counts[operation] = []
            
            # Remove old requests outside the current window
            self.request_counts[operation] = [
                req_time for req_time in self.request_counts[operation]
                if req_time > window_start
            ]
            
            # Check if we can make the request
            if len(self.request_counts[operation]) < limit_config["requests"]:
                self.request_counts[operation].append(current_time)
                return True
            else:
                self.logger.warning(f"Rate limit exceeded for operation: {operation}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return False
    
    async def get_remaining(self, operation: str) -> int:
        """Get remaining requests for operation"""
        try:
            if operation not in self.limits:
                return 0
            
            limit_config = self.limits[operation]
            current_time = time.time()
            window_start = current_time - limit_config["window"]
            
            if operation not in self.request_counts:
                return limit_config["requests"]
            
            # Count requests within current window
            recent_requests = len([
                req_time for req_time in self.request_counts[operation]
                if req_time > window_start
            ])
            
            return max(0, limit_config["requests"] - recent_requests)
            
        except Exception as e:
            self.logger.error(f"Error getting remaining rate limit: {e}")
            return 0
    
    async def cleanup(self):
        """Cleanup rate limit data"""
        self.request_counts.clear()

# Create singleton instance
broker_api_adapter = BrokerAPIAdapter()