import React, { createContext, useContext, useRef, useState, useCallback, useEffect } from 'react';
import { Balance, OrderHistoryItem, Trade } from '@/types/trading';

/**
 * WebSocket Account Provider för Bitfinex account data
 * 
 * Baserat på Bitfinex WebSocket Account Info dokumentation:
 * https://docs.bitfinex.com/reference/ws-auth-account-info
 * 
 * Hanterar real-time updates för:
 * - Orders (os, on, ou, oc)
 * - Positions (ps, pn, pu, pc) 
 * - Wallets (ws, wu)
 * - Trades (te, tu)
 */

// Account-specific data interfaces enligt Bitfinex WebSocket format
interface BitfinexOrder {
  id: number;
  gid: number | null;
  cid: number;
  symbol: string;
  mtsCreate: number;
  mtsUpdate: number;
  amount: number;
  amountOrig: number;
  type: string;
  typePrev: string | null;
  flags: number;
  status: string;
  price: number;
  priceAvg: number;
  priceTrailing: number;
  priceAuxLimit: number;
  notify: boolean;
  hidden: boolean;
  placedId: number | null;
  routing: string;
  meta: any;
}

interface BitfinexWallet {
  type: string; // 'exchange', 'margin', 'funding'
  currency: string;
  balance: number;
  unsettledInterest: number;
  balanceAvailable: number;
  lastChange: string;
  tradeDetails: any;
}

interface BitfinexPosition {
  symbol: string;
  status: string;
  amount: number;
  basePrice: number;
  marginFunding: number;
  marginFundingType: number;
  pl: number;
  plPerc: number;
  liquidationPrice: number;
  leverage: number;
  flag: number;
  id: number;
  mtsCreate: number;
  mtsUpdate: number;
  type: number;
  collateral: number;
  collateralMin: number;
  meta: any;
}

interface BitfinexTrade {
  id: number;
  pair: string;
  mtsCreate: number;
  orderID: number;
  execAmount: number;
  execPrice: number;
  orderType: string;
  orderPrice: number;
  maker: boolean;
  fee: number;
  feeCurrency: string;
  cid: number;
}

// Margin Info interfaces enligt Bitfinex WebSocket dokumentation
interface BitfinexMarginBase {
  userPL: number;         // User profit and loss
  userSwaps: number;      // Amount of swaps a user has
  marginBalance: number;  // Balance in your margin funding account
  marginNet: number;      // Balance after P&L is accounted for
  marginRequired: number; // Minimum required margin to keep positions open
}

interface BitfinexMarginSym {
  symbol: string;
  tradableBalance: number; // Your buying power (how large a position you can obtain)
  grossBalance: number;    // Your buying power including funds already reserved for open positions
  buy: number | null;      // Maximum amount you can buy at current best ASK
  sell: number | null;     // Maximum amount you can sell at current best BID
}

// Application margin info interface
interface MarginInfo {
  base: BitfinexMarginBase | null;
  symbols: { [symbol: string]: BitfinexMarginSym };
  lastUpdated: number;
}

// Funding interfaces enligt Bitfinex Account Info Events
interface BitfinexFundingOffer {
  id: number;
  symbol: string;
  mtsCreate: number;
  mtsUpdate: number;
  amount: number;
  amountOrig: number;
  type: string;
  flags: number;
  status: string;
  rate: number;
  period: number;
  notify: boolean;
  hidden: boolean;
  renew: boolean;
  rateReal: number;
}

interface BitfinexFundingCredit {
  id: number;
  symbol: string;
  side: number;
  mtsCreate: number;
  mtsUpdate: number;
  amount: number;
  flags: number;
  status: string;
  rate: number;
  period: number;
  mtsOpening: number;
  mtsLastPayout: number;
  notify: boolean;
  hidden: boolean;
  renew: boolean;
  rateReal: number;
  noClose: boolean;
}

interface BitfinexFundingLoan {
  id: number;
  symbol: string;
  side: number;
  mtsCreate: number;
  mtsUpdate: number;
  amount: number;
  flags: number;
  status: string;
  rate: number;
  period: number;
  mtsOpening: number;
  mtsLastPayout: number;
  notify: boolean;
  hidden: boolean;
  renew: boolean;
  rateReal: number;
  noClose: boolean;
}

interface BitfinexFundingTrade {
  id: number;
  symbol: string;
  mtsCreate: number;
  offerId: number;
  amount: number;
  rate: number;
  period: number;
  maker: boolean;
}

// Application funding info interface
interface FundingInfo {
  offers: BitfinexFundingOffer[];
  credits: BitfinexFundingCredit[];
  loans: BitfinexFundingLoan[];
  trades: BitfinexFundingTrade[];
  lastUpdated: number;
}

// WS Input Interfaces baserat på Bitfinex WS Inputs dokumentation
interface NewOrderInput {
  type: string;        // Order type (MARKET, LIMIT, STOP, etc.)
  symbol: string;      // Trading pair (tBTCUSD, etc.)
  amount: number;      // Order amount (positive for buy, negative for sell)
  price?: number;      // Price for limit orders
  priceTrailing?: number; // Trailing price
  priceAuxLimit?: number; // Auxiliary limit price
  priceOcoStop?: number;  // OCO stop price
  flags?: number;      // Order flags
  tif?: string;        // Time in force
  affiliateCode?: string; // Affiliate code
}

interface UpdateOrderInput {
  price?: number;      // New price
  amount?: number;     // New amount
  delta?: number;      // Amount delta
  priceAuxLimit?: number; // New aux limit price
  priceTrailing?: number; // New trailing price
  flags?: number;      // New flags
  tif?: string;        // New time in force
}

interface NewFundingOfferInput {
  type: string;        // Offer type (LIMIT)
  symbol: string;      // Funding currency (fUSD, fBTC, etc.)
  amount: number;      // Offer amount
  rate: number;        // Daily rate
  period: number;      // Period in days (2-120)
  flags?: number;      // Offer flags
}

interface CalcInput {
  // Calc request can trigger margin info calculation
  // according to Bitfinex documentation
}

// State interface för Account WebSocket
interface WebSocketAccountState {
  // Real-time account data
  orders: OrderHistoryItem[];
  balances: Balance[];
  positions: Trade[];
  trades: Trade[];
  marginInfo: MarginInfo;
  fundingInfo: FundingInfo;
  
  // Connection status
  connected: boolean;
  connecting: boolean;
  authenticated: boolean;
  authenticating: boolean;
  error: string | null;
  lastHeartbeat: number | null;
  
  // Control functions
  authenticate: (apiKey: string, apiSecret: string) => void;
  disconnect: () => void;
  
  // WS Input Commands (Trading Operations)
  newOrder: (orderData: NewOrderInput) => Promise<boolean>;
  updateOrder: (orderId: number, updateData: UpdateOrderInput) => Promise<boolean>;
  cancelOrder: (orderId: number) => Promise<boolean>;
  cancelAllOrders: () => Promise<boolean>;
  newFundingOffer: (offerData: NewFundingOfferInput) => Promise<boolean>;
  cancelFundingOffer: (offerId: number) => Promise<boolean>;
  calcRequest: (calcData: CalcInput) => Promise<boolean>;
  
  // Data getters
  getOrderById: (id: string) => OrderHistoryItem | null;
  getBalanceBySymbol: (symbol: string) => Balance | null;
  getActiveOrders: () => OrderHistoryItem[];
  getTotalBalance: () => number;
  getMarginRequirement: () => number;
  getTradableBalance: (symbol?: string) => number;
  getActiveFundingOffers: () => BitfinexFundingOffer[];
  getFundingCredits: () => BitfinexFundingCredit[];
  getFundingLoans: () => BitfinexFundingLoan[];
}

const WebSocketAccountContext = createContext<WebSocketAccountState | null>(null);

export const useWebSocketAccount = (): WebSocketAccountState => {
  const context = useContext(WebSocketAccountContext);
  if (!context) {
    throw new Error('useWebSocketAccount must be used within WebSocketAccountProvider');
  }
  return context;
};

export const WebSocketAccountProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Account data state
  const [orders, setOrders] = useState<OrderHistoryItem[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [positions, setPositions] = useState<Trade[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [marginInfo, setMarginInfo] = useState<MarginInfo>({
    base: null,
    symbols: {},
    lastUpdated: 0
  });
  const [fundingInfo, setFundingInfo] = useState<FundingInfo>({
    offers: [],
    credits: [],
    loans: [],
    trades: [],
    lastUpdated: 0
  });
  
  // Connection state
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [authenticating, setAuthenticating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
  
  // WebSocket connection refs
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeout = useRef<NodeJS.Timeout | null>(null);
  const connectionInitialized = useRef<boolean>(false);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 3;
  
  // Authentication credentials
  const apiCredentials = useRef<{ key: string; secret: string } | null>(null);

  /**
   * Error message mapping baserat på Bitfinex dokumentation
   */
  const getBitfinexErrorMessage = useCallback((code: number, msg: string) => {
    const errorCodes: { [key: number]: string } = {
      10000: 'Okänt fel',
      10001: 'Generellt fel', 
      10008: 'Concurrency fel',
      10020: 'Request parameter fel',
      10050: 'Konfigurationsfel',
      10100: 'Autentisering misslyckades',
      10111: 'Fel i autentiserings-payload',
      10112: 'Fel i autentiserings-signatur',
      10113: 'Fel i autentiserings-kryptering',
      10114: 'Fel i autentiserings-nonce',
      10200: 'Fel vid utloggning',
      10300: 'Prenumeration misslyckades',
      10301: 'Prenumeration misslyckades: redan prenumererad',
      10302: 'Prenumeration misslyckades: okänd kanal',
      10305: 'Prenumeration misslyckades: nått gräns för öppna kanaler',
      10400: 'Avprenumeration misslyckades: kanal hittades inte',
      10401: 'Avprenumeration misslyckades: inte prenumererad',
      11000: 'Inte redo, försök igen senare',
      20051: 'WebSocket server stoppar... återanslut senare',
      20060: 'WebSocket server synkroniserar... återanslut senare',
      20061: 'WebSocket server synkronisering klar. återanslut',
      5000: 'Info meddelande'
    };
    
    const swedishError = errorCodes[code] || 'Okänt fel';
    return `${swedishError}: ${msg} (Kod: ${code})`;
  }, []);

  /**
   * Crypto utility functions för Bitfinex authentication
   */
  const generateAuthPayload = useCallback((apiKey: string, apiSecret: string) => {
    const nonce = Date.now() * 1000; // Microsecond timestamp
    const authPayload = `AUTH${nonce}`;
    
    // I en verklig implementation skulle vi använda crypto-js eller liknande
    // För nu simulerar vi signature generation
    const signature = btoa(`${apiSecret}:${authPayload}`); // Simplified for demo
    
    return {
      apiKey,
      authSig: signature,
      authPayload,
      authNonce: nonce
    };
  }, []);

  /**
   * Data transformation functions från Bitfinex format till vårt format
   */
  const transformBitfinexOrder = useCallback((bitfinexOrder: BitfinexOrder): OrderHistoryItem => {
    return {
      id: bitfinexOrder.id.toString(),
      symbol: bitfinexOrder.symbol,
      order_type: bitfinexOrder.type.includes('LIMIT') ? 'limit' : 'market',
      side: bitfinexOrder.amount > 0 ? 'buy' : 'sell',
      amount: Math.abs(bitfinexOrder.amount),
      price: bitfinexOrder.price,
      timestamp: bitfinexOrder.mtsCreate,
      status: bitfinexOrder.status.toLowerCase() as 'filled' | 'cancelled' | 'pending' | 'open',
      filled: bitfinexOrder.amountOrig - Math.abs(bitfinexOrder.amount),
      remaining: Math.abs(bitfinexOrder.amount)
    };
  }, []);

  const transformBitfinexWallet = useCallback((bitfinexWallet: BitfinexWallet): Balance => {
    return {
      currency: bitfinexWallet.currency,
      total_balance: bitfinexWallet.balance,
      available: bitfinexWallet.balanceAvailable
    };
  }, []);

  const transformBitfinexPosition = useCallback((bitfinexPosition: BitfinexPosition): Trade => {
    return {
      id: bitfinexPosition.id.toString(),
      symbol: bitfinexPosition.symbol,
      amount: Math.abs(bitfinexPosition.amount),
      entry_price: bitfinexPosition.basePrice,
      pnl: bitfinexPosition.pl,
      timestamp: new Date(bitfinexPosition.mtsCreate).toISOString(),
      side: bitfinexPosition.amount > 0 ? 'buy' : 'sell'
    };
  }, []);

  const transformBitfinexTrade = useCallback((bitfinexTrade: BitfinexTrade): Trade => {
    return {
      id: bitfinexTrade.id.toString(),
      symbol: bitfinexTrade.pair,
      amount: Math.abs(bitfinexTrade.execAmount),
      entry_price: bitfinexTrade.execPrice,
      pnl: 0, // PnL beräknas separat
      timestamp: new Date(bitfinexTrade.mtsCreate).toISOString(),
      side: bitfinexTrade.execAmount > 0 ? 'buy' : 'sell'
    };
  }, []);

  /**
   * WebSocket message handlers för olika account events
   */
  const handleOrderSnapshot = useCallback((ordersData: BitfinexOrder[]) => {
    console.log('[WebSocketAccount] 📋 Order snapshot received:', ordersData.length, 'orders');
    const transformedOrders = ordersData.map(transformBitfinexOrder);
    setOrders(transformedOrders);
  }, [transformBitfinexOrder]);

  const handleOrderNew = useCallback((orderData: BitfinexOrder) => {
    console.log('[WebSocketAccount] 🆕 New order:', orderData.id);
    const transformedOrder = transformBitfinexOrder(orderData);
    setOrders(prev => [transformedOrder, ...prev]);
  }, [transformBitfinexOrder]);

  const handleOrderUpdate = useCallback((orderData: BitfinexOrder) => {
    console.log('[WebSocketAccount] 🔄 Order update:', orderData.id);
    const transformedOrder = transformBitfinexOrder(orderData);
    setOrders(prev => prev.map(order => 
      order.id === transformedOrder.id ? transformedOrder : order
    ));
  }, [transformBitfinexOrder]);

  const handleOrderCancel = useCallback((orderData: BitfinexOrder) => {
    console.log('[WebSocketAccount] ❌ Order cancelled:', orderData.id);
    setOrders(prev => prev.filter(order => order.id !== orderData.id.toString()));
  }, []);

  const handleWalletSnapshot = useCallback((walletsData: BitfinexWallet[]) => {
    console.log('[WebSocketAccount] 💰 Wallet snapshot received:', walletsData.length, 'wallets');
    const transformedBalances = walletsData.map(transformBitfinexWallet);
    setBalances(transformedBalances);
  }, [transformBitfinexWallet]);

  const handleWalletUpdate = useCallback((walletData: BitfinexWallet) => {
    console.log('[WebSocketAccount] 💸 Wallet update:', walletData.currency);
    const transformedBalance = transformBitfinexWallet(walletData);
    setBalances(prev => {
      const existingIndex = prev.findIndex(b => b.currency === transformedBalance.currency);
      if (existingIndex !== -1) {
        const updated = [...prev];
        updated[existingIndex] = transformedBalance;
        return updated;
      } else {
        return [...prev, transformedBalance];
      }
    });
  }, [transformBitfinexWallet]);

  const handlePositionSnapshot = useCallback((positionsData: BitfinexPosition[]) => {
    console.log('[WebSocketAccount] 📈 Position snapshot received:', positionsData.length, 'positions');
    const transformedPositions = positionsData.map(transformBitfinexPosition);
    setPositions(transformedPositions);
  }, [transformBitfinexPosition]);

  const handleTradeExecution = useCallback((tradeData: BitfinexTrade) => {
    console.log('[WebSocketAccount] ⚡ Trade execution:', tradeData.id);
    const transformedTrade = transformBitfinexTrade(tradeData);
    setTrades(prev => [transformedTrade, ...prev.slice(0, 99)]); // Keep latest 100 trades
  }, [transformBitfinexTrade]);

  const handlePositionNew = useCallback((positionData: BitfinexPosition) => {
    console.log('[WebSocketAccount] 🆕 New position:', positionData.symbol);
    const transformedPosition = transformBitfinexPosition(positionData);
    setPositions(prev => [transformedPosition, ...prev]);
  }, [transformBitfinexPosition]);

  const handlePositionUpdate = useCallback((positionData: BitfinexPosition) => {
    console.log('[WebSocketAccount] 🔄 Position update:', positionData.symbol);
    const transformedPosition = transformBitfinexPosition(positionData);
    setPositions(prev => prev.map(pos => 
      pos.symbol === transformedPosition.symbol ? transformedPosition : pos
    ));
  }, [transformBitfinexPosition]);

  const handlePositionClose = useCallback((positionData: BitfinexPosition) => {
    console.log('[WebSocketAccount] ❌ Position closed:', positionData.symbol);
    setPositions(prev => prev.filter(pos => pos.symbol !== positionData.symbol));
  }, []);

  const handleNotification = useCallback((notificationData: any) => {
    console.log('[WebSocketAccount] 🔔 Notification received:', notificationData);
    // Kan implementeras för att visa notifikationer i UI
  }, []);

  const handleBalanceUpdate = useCallback((balanceData: BitfinexWallet) => {
    console.log('[WebSocketAccount] 💰 Balance update:', balanceData.currency);
    const transformedBalance = transformBitfinexWallet(balanceData);
    setBalances(prev => {
      const existingIndex = prev.findIndex(b => b.currency === transformedBalance.currency);
      if (existingIndex !== -1) {
        const updated = [...prev];
        updated[existingIndex] = transformedBalance;
        return updated;
      } else {
        return [...prev, transformedBalance];
      }
    });
  }, [transformBitfinexWallet]);

  /**
   * Margin Info Handlers baserat på dokumentation
   * https://docs.bitfinex.com/reference/ws-auth-margin-info
   */
  const handleMarginInfoUpdate = useCallback((updateData: any[]) => {
    const [updateType, ...rest] = updateData;
    
    if (updateType === 'base') {
      // Base margin info update
      const [userPL, userSwaps, marginBalance, marginNet, marginRequired] = rest[0];
      console.log('[WebSocketAccount] 📊 Margin base update - Required:', marginRequired, 'Balance:', marginBalance);
      
      setMarginInfo(prev => ({
        ...prev,
        base: {
          userPL: userPL || 0,
          userSwaps: userSwaps || 0,
          marginBalance: marginBalance || 0,
          marginNet: marginNet || 0,
          marginRequired: marginRequired || 0
        },
        lastUpdated: Date.now()
      }));
      
    } else if (updateType === 'sym') {
      // Symbol-specific margin info update
      const [symbol, symData] = rest;
      const [tradableBalance, grossBalance, buy, sell] = symData;
      console.log('[WebSocketAccount] 📊 Margin symbol update:', symbol, 'Tradable:', tradableBalance);
      
      setMarginInfo(prev => ({
        ...prev,
        symbols: {
          ...prev.symbols,
          [symbol]: {
            symbol,
            tradableBalance: tradableBalance || 0,
            grossBalance: grossBalance || 0,
            buy: buy,
            sell: sell
          }
        },
        lastUpdated: Date.now()
      }));
    }
  }, []);

  /**
   * Funding Event Handlers baserat på Account Info Events dokumentation
   * https://docs.bitfinex.com/docs/ws-auth
   */
  const handleFundingOfferSnapshot = useCallback((offersData: BitfinexFundingOffer[]) => {
    console.log('[WebSocketAccount] 💰 Funding offers snapshot:', offersData.length, 'offers');
    setFundingInfo(prev => ({
      ...prev,
      offers: offersData,
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingOfferNew = useCallback((offerData: BitfinexFundingOffer) => {
    console.log('[WebSocketAccount] 🆕 New funding offer:', offerData.id);
    setFundingInfo(prev => ({
      ...prev,
      offers: [offerData, ...prev.offers],
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingOfferUpdate = useCallback((offerData: BitfinexFundingOffer) => {
    console.log('[WebSocketAccount] 🔄 Funding offer update:', offerData.id);
    setFundingInfo(prev => ({
      ...prev,
      offers: prev.offers.map(offer => 
        offer.id === offerData.id ? offerData : offer
      ),
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingOfferCancel = useCallback((offerData: BitfinexFundingOffer) => {
    console.log('[WebSocketAccount] ❌ Funding offer cancelled:', offerData.id);
    setFundingInfo(prev => ({
      ...prev,
      offers: prev.offers.filter(offer => offer.id !== offerData.id),
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingCreditSnapshot = useCallback((creditsData: BitfinexFundingCredit[]) => {
    console.log('[WebSocketAccount] 💳 Funding credits snapshot:', creditsData.length, 'credits');
    setFundingInfo(prev => ({
      ...prev,
      credits: creditsData,
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingCreditUpdate = useCallback((creditData: BitfinexFundingCredit) => {
    console.log('[WebSocketAccount] 🔄 Funding credit update:', creditData.id);
    setFundingInfo(prev => ({
      ...prev,
      credits: prev.credits.map(credit => 
        credit.id === creditData.id ? creditData : credit
      ),
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingLoanSnapshot = useCallback((loansData: BitfinexFundingLoan[]) => {
    console.log('[WebSocketAccount] 🏦 Funding loans snapshot:', loansData.length, 'loans');
    setFundingInfo(prev => ({
      ...prev,
      loans: loansData,
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingLoanUpdate = useCallback((loanData: BitfinexFundingLoan) => {
    console.log('[WebSocketAccount] 🔄 Funding loan update:', loanData.id);
    setFundingInfo(prev => ({
      ...prev,
      loans: prev.loans.map(loan => 
        loan.id === loanData.id ? loanData : loan
      ),
      lastUpdated: Date.now()
    }));
  }, []);

  const handleFundingTradeExecution = useCallback((tradeData: BitfinexFundingTrade) => {
    console.log('[WebSocketAccount] ⚡ Funding trade execution:', tradeData.id);
    setFundingInfo(prev => ({
      ...prev,
      trades: [tradeData, ...prev.trades.slice(0, 99)], // Keep latest 100 funding trades
      lastUpdated: Date.now()
    }));
  }, []);

  /**
   * WebSocket connection management
   */
  const connect = useCallback(() => {
    if (connectionInitialized.current || ws.current?.readyState === WebSocket.OPEN || connecting) {
      return;
    }

    connectionInitialized.current = true;
    setConnecting(true);
    setError(null);

    try {
      // Connect to Bitfinex private WebSocket endpoint
      ws.current = new WebSocket('wss://api.bitfinex.com/ws/2');

      ws.current.onopen = () => {
        console.log('[WebSocketAccount] 🔗 Connected to Bitfinex account WebSocket');
        setConnected(true);
        setConnecting(false);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle heartbeat
          if (Array.isArray(data) && data[1] === 'hb') {
            setLastHeartbeat(Date.now());
            return;
          }
          
          // Handle authentication response
          if (data.event === 'auth') {
            if (data.status === 'OK') {
              console.log('[WebSocketAccount] ✅ Authentication successful');
              setAuthenticated(true);
              setAuthenticating(false);
            } else {
              console.error('[WebSocketAccount] ❌ Authentication failed:', data);
              setError(`Authentication failed: ${data.msg || 'Unknown error'}`);
              setAuthenticating(false);
            }
            return;
          }
          
          // Handle info messages
          if (data.event === 'info') {
            console.log('[WebSocketAccount] ℹ️ Info:', data);
            return;
          }
          
          // Handle error messages enligt Bitfinex dokumentation
          if (data.event === 'error') {
            console.error('[WebSocketAccount] ❌ Error:', data);
            const errorMessage = getBitfinexErrorMessage(data.code, data.msg);
            setError(errorMessage);
            return;
          }
          
          // Handle account data updates
          if (Array.isArray(data) && data.length >= 2) {
            const [channelId, messageType, messageData] = data;
            
            // Only process channel 0 (account data)
            if (channelId !== 0) return;
            
            switch (messageType) {
              case 'os': // Order snapshot
                if (Array.isArray(messageData)) {
                  handleOrderSnapshot(messageData);
                }
                break;
                
              case 'on': // Order new
                if (Array.isArray(messageData)) {
                  handleOrderNew(messageData);
                }
                break;
                
              case 'ou': // Order update
                if (Array.isArray(messageData)) {
                  handleOrderUpdate(messageData);
                }
                break;
                
              case 'oc': // Order cancel
                if (Array.isArray(messageData)) {
                  handleOrderCancel(messageData);
                }
                break;
                
              case 'ws': // Wallet snapshot
                if (Array.isArray(messageData)) {
                  handleWalletSnapshot(messageData);
                }
                break;
                
              case 'wu': // Wallet update
                if (Array.isArray(messageData)) {
                  handleWalletUpdate(messageData);
                }
                break;
                
              case 'ps': // Position snapshot
                if (Array.isArray(messageData)) {
                  handlePositionSnapshot(messageData);
                }
                break;
                
              case 'te': // Trade execution
                if (Array.isArray(messageData)) {
                  handleTradeExecution(messageData);
                }
                break;
                
              case 'tu': // Trade execution update  
                if (Array.isArray(messageData)) {
                  handleTradeExecution(messageData); // Same handler as te
                }
                break;
                
              case 'pn': // Position new
                if (Array.isArray(messageData)) {
                  handlePositionNew(messageData);
                }
                break;
                
              case 'pu': // Position update
                if (Array.isArray(messageData)) {
                  handlePositionUpdate(messageData);
                }
                break;
                
              case 'pc': // Position close
                if (Array.isArray(messageData)) {
                  handlePositionClose(messageData);
                }
                break;
                
              case 'n': // Notification
                if (Array.isArray(messageData)) {
                  handleNotification(messageData);
                }
                break;
                
              case 'bu': // Balance update
                if (Array.isArray(messageData)) {
                  handleBalanceUpdate(messageData);
                }
                break;
                
              case 'miu': // Margin info update
                if (Array.isArray(messageData)) {
                  handleMarginInfoUpdate(messageData);
                }
                break;
                
              case 'fos': // Funding offer snapshot
                if (Array.isArray(messageData)) {
                  handleFundingOfferSnapshot(messageData);
                }
                break;
                
              case 'fon': // Funding offer new
                if (Array.isArray(messageData)) {
                  handleFundingOfferNew(messageData);
                }
                break;
                
              case 'fou': // Funding offer update
                if (Array.isArray(messageData)) {
                  handleFundingOfferUpdate(messageData);
                }
                break;
                
              case 'foc': // Funding offer cancel
                if (Array.isArray(messageData)) {
                  handleFundingOfferCancel(messageData);
                }
                break;
                
              case 'fcs': // Funding credit snapshot
                if (Array.isArray(messageData)) {
                  handleFundingCreditSnapshot(messageData);
                }
                break;
                
              case 'fcu': // Funding credit update
                if (Array.isArray(messageData)) {
                  handleFundingCreditUpdate(messageData);
                }
                break;
                
              case 'fls': // Funding loan snapshot
                if (Array.isArray(messageData)) {
                  handleFundingLoanSnapshot(messageData);
                }
                break;
                
              case 'flu': // Funding loan update
                if (Array.isArray(messageData)) {
                  handleFundingLoanUpdate(messageData);
                }
                break;
                
              case 'fte': // Funding trade execution
                if (Array.isArray(messageData)) {
                  handleFundingTradeExecution(messageData);
                }
                break;
                
              default:
                console.log('[WebSocketAccount] 📨 Unhandled message type:', messageType, 'data:', messageData);
                break;
            }
          }
        } catch (e) {
          console.error('[WebSocketAccount] ❌ Error parsing message:', e);
        }
      };

      ws.current.onclose = (event) => {
        console.log('[WebSocketAccount] 🔌 Connection closed:', event.code, event.reason);
        setConnected(false);
        setConnecting(false);
        setAuthenticated(false);
        connectionInitialized.current = false;

        // Attempt reconnection if we have credentials and haven't exceeded max attempts
        if (apiCredentials.current && reconnectAttempts.current < maxReconnectAttempts && event.code !== 1000) {
          const delay = Math.min(5000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`[WebSocketAccount] 🔄 Reconnecting in ${delay}ms...`);
          
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      ws.current.onerror = (error) => {
        console.error('[WebSocketAccount] ❌ WebSocket error:', error);
        setError('WebSocket connection failed');
        setConnecting(false);
        connectionInitialized.current = false;
      };

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Failed to create WebSocket connection:', error);
      setError('Failed to create WebSocket connection');
      setConnecting(false);
      connectionInitialized.current = false;
    }
  }, [
    connecting, 
    handleOrderSnapshot, 
    handleOrderNew, 
    handleOrderUpdate, 
    handleOrderCancel,
    handleWalletSnapshot, 
    handleWalletUpdate,
    handlePositionSnapshot,
    handlePositionNew,
    handlePositionUpdate, 
    handlePositionClose,
    handleTradeExecution,
    handleNotification,
    handleBalanceUpdate,
    handleMarginInfoUpdate,
    handleFundingOfferSnapshot,
    handleFundingOfferNew,
    handleFundingOfferUpdate,
    handleFundingOfferCancel,
    handleFundingCreditSnapshot,
    handleFundingCreditUpdate,
    handleFundingLoanSnapshot,
    handleFundingLoanUpdate,
    handleFundingTradeExecution,
    getBitfinexErrorMessage
  ]);

  /**
   * Authentication function
   */
  const authenticate = useCallback((apiKey: string, apiSecret: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket not connected');
      return;
    }

    setAuthenticating(true);
    setError(null);
    
    // Store credentials for reconnection
    apiCredentials.current = { key: apiKey, secret: apiSecret };

    try {
      const authData = generateAuthPayload(apiKey, apiSecret);
      
      const authMessage = {
        event: 'auth',
        apiKey: authData.apiKey,
        authSig: authData.authSig,
        authPayload: authData.authPayload,
        authNonce: authData.authNonce,
        filter: [
          'trading',  // orders, positions, trades
          'funding',  // offers, credits, loans, funding trades  
          'wallet',   // wallet updates
          'balance',  // balance info (tradable balance, ...)
          'notify'    // notifications
        ]
      };

      console.log('[WebSocketAccount] 🔐 Sending authentication request...');
      ws.current.send(JSON.stringify(authMessage));
      
    } catch (error) {
      console.error('[WebSocketAccount] ❌ Authentication error:', error);
      setError('Authentication failed');
      setAuthenticating(false);
    }
  }, [generateAuthPayload]);

  /**
   * Disconnect function
   */
  const disconnect = useCallback(() => {
    console.log('[WebSocketAccount] 🔌 Disconnecting...');
    
    // Clear credentials
    apiCredentials.current = null;
    
    // Clear timeouts
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
      heartbeatTimeout.current = null;
    }
    
    // Close connection
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
    
    // Reset state
    setConnected(false);
    setAuthenticated(false);
    setConnecting(false);
    setAuthenticating(false);
    connectionInitialized.current = false;
  }, []);

  /**
   * Data getter functions
   */
  const getOrderById = useCallback((id: string): OrderHistoryItem | null => {
    return orders.find(order => order.id === id) || null;
  }, [orders]);

  const getBalanceBySymbol = useCallback((symbol: string): Balance | null => {
    return balances.find(balance => balance.currency === symbol) || null;
  }, [balances]);

  const getActiveOrders = useCallback((): OrderHistoryItem[] => {
    return orders.filter(order => order.status === 'open' || order.status === 'pending');
  }, [orders]);

  const getTotalBalance = useCallback((): number => {
    return balances.reduce((total, balance) => total + balance.total_balance, 0);
  }, [balances]);

  const getMarginRequirement = useCallback((): number => {
    return marginInfo.base?.marginRequired || 0;
  }, [marginInfo]);

  const getTradableBalance = useCallback((symbol?: string): number => {
    if (symbol && marginInfo.symbols[symbol]) {
      return marginInfo.symbols[symbol].tradableBalance;
    }
    // Return total tradable balance across all symbols if no specific symbol
    return Object.values(marginInfo.symbols).reduce((total, sym) => total + sym.tradableBalance, 0);
  }, [marginInfo]);

  const getActiveFundingOffers = useCallback((): BitfinexFundingOffer[] => {
    return fundingInfo.offers.filter(offer => offer.status === 'ACTIVE');
  }, [fundingInfo]);

  const getFundingCredits = useCallback((): BitfinexFundingCredit[] => {
    return fundingInfo.credits.filter(credit => credit.status === 'ACTIVE');
  }, [fundingInfo]);

  const getFundingLoans = useCallback((): BitfinexFundingLoan[] => {
    return fundingInfo.loans.filter(loan => loan.status === 'ACTIVE');
  }, [fundingInfo]);

  /**
   * WS Input Commands - Trading Operations
   * Baserat på List of WS Inputs från Bitfinex dokumentation
   */
  const newOrder = useCallback(async (orderData: NewOrderInput): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot send order: not authenticated');
      setError('Inte autentiserad - kan inte skicka order');
      return false;
    }

    try {
      const cid = Date.now(); // Client order ID
      const orderMessage = [
        0,
        'on',
        null,
        {
          type: orderData.type,
          symbol: orderData.symbol,
          amount: orderData.amount.toString(),
          price: orderData.price?.toString() || '0',
          price_trailing: orderData.priceTrailing?.toString(),
          price_aux_limit: orderData.priceAuxLimit?.toString(),
          price_oco_stop: orderData.priceOcoStop?.toString(),
          flags: orderData.flags || 0,
          tif: orderData.tif,
          affiliate_code: orderData.affiliateCode,
          cid: cid
        }
      ];

      console.log('[WebSocketAccount] 📤 Sending new order:', orderData.symbol, orderData.amount);
      ws.current.send(JSON.stringify(orderMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error sending order:', error);
      setError(`Fel vid order: ${error}`);
      return false;
    }
  }, [authenticated]);

  const updateOrder = useCallback(async (orderId: number, updateData: UpdateOrderInput): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot update order: not authenticated');
      setError('Inte autentiserad - kan inte uppdatera order');
      return false;
    }

    try {
      const updateMessage = [
        0,
        'ou',
        null,
        {
          id: orderId,
          price: updateData.price?.toString(),
          amount: updateData.amount?.toString(),
          delta: updateData.delta?.toString(),
          price_aux_limit: updateData.priceAuxLimit?.toString(),
          price_trailing: updateData.priceTrailing?.toString(),
          flags: updateData.flags,
          tif: updateData.tif
        }
      ];

      console.log('[WebSocketAccount] 📤 Updating order:', orderId);
      ws.current.send(JSON.stringify(updateMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error updating order:', error);
      setError(`Fel vid order-uppdatering: ${error}`);
      return false;
    }
  }, [authenticated]);

  const cancelOrder = useCallback(async (orderId: number): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot cancel order: not authenticated');
      setError('Inte autentiserad - kan inte avbryta order');
      return false;
    }

    try {
      const cancelMessage = [
        0,
        'oc',
        null,
        {
          id: orderId
        }
      ];

      console.log('[WebSocketAccount] 📤 Cancelling order:', orderId);
      ws.current.send(JSON.stringify(cancelMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error cancelling order:', error);
      setError(`Fel vid order-avbrytning: ${error}`);
      return false;
    }
  }, [authenticated]);

  const cancelAllOrders = useCallback(async (): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot cancel all orders: not authenticated');
      setError('Inte autentiserad - kan inte avbryta alla ordrar');
      return false;
    }

    try {
      const cancelAllMessage = [
        0,
        'oc_multi',
        null,
        {
          all: 1
        }
      ];

      console.log('[WebSocketAccount] 📤 Cancelling all orders');
      ws.current.send(JSON.stringify(cancelAllMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error cancelling all orders:', error);
      setError(`Fel vid avbrytning av alla ordrar: ${error}`);
      return false;
    }
  }, [authenticated]);

  const newFundingOffer = useCallback(async (offerData: NewFundingOfferInput): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot send funding offer: not authenticated');
      setError('Inte autentiserad - kan inte skicka funding offer');
      return false;
    }

    try {
      const offerMessage = [
        0,
        'fon',
        null,
        {
          type: offerData.type,
          symbol: offerData.symbol,
          amount: offerData.amount.toString(),
          rate: offerData.rate.toString(),
          period: offerData.period,
          flags: offerData.flags || 0
        }
      ];

      console.log('[WebSocketAccount] 📤 Sending funding offer:', offerData.symbol, offerData.amount);
      ws.current.send(JSON.stringify(offerMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error sending funding offer:', error);
      setError(`Fel vid funding offer: ${error}`);
      return false;
    }
  }, [authenticated]);

  const cancelFundingOffer = useCallback(async (offerId: number): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot cancel funding offer: not authenticated');
      setError('Inte autentiserad - kan inte avbryta funding offer');
      return false;
    }

    try {
      const cancelMessage = [
        0,
        'foc',
        null,
        {
          id: offerId
        }
      ];

      console.log('[WebSocketAccount] 📤 Cancelling funding offer:', offerId);
      ws.current.send(JSON.stringify(cancelMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error cancelling funding offer:', error);
      setError(`Fel vid funding offer-avbrytning: ${error}`);
      return false;
    }
  }, [authenticated]);

  const calcRequest = useCallback(async (calcData: CalcInput): Promise<boolean> => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || !authenticated) {
      console.error('[WebSocketAccount] ❌ Cannot send calc request: not authenticated');
      setError('Inte autentiserad - kan inte skicka calc request');
      return false;
    }

    try {
      const calcMessage = [
        0,
        'calc',
        null,
        calcData
      ];

      console.log('[WebSocketAccount] 📤 Sending calc request');
      ws.current.send(JSON.stringify(calcMessage));
      return true;

    } catch (error) {
      console.error('[WebSocketAccount] ❌ Error sending calc request:', error);
      setError(`Fel vid calc request: ${error}`);
      return false;
    }
  }, [authenticated]);

  /**
   * Auto-connect effect
   */
  useEffect(() => {
    // Auto-connect on mount (but don't authenticate until credentials provided)
    const connectTimer = setTimeout(() => {
      connect();
    }, process.env.NODE_ENV === 'development' ? 1000 : 0);

    return () => {
      clearTimeout(connectTimer);
      disconnect();
    };
  }, [connect, disconnect]);

  const value: WebSocketAccountState = {
    orders,
    balances,
    positions,
    trades,
    marginInfo,
    fundingInfo,
    connected,
    connecting,
    authenticated,
    authenticating,
    error,
    lastHeartbeat,
    authenticate,
    disconnect,
    // WS Input Commands (Trading Operations)
    newOrder,
    updateOrder,
    cancelOrder,
    cancelAllOrders,
    newFundingOffer,
    cancelFundingOffer,
    calcRequest,
    // Data getters
    getOrderById,
    getBalanceBySymbol,
    getActiveOrders,
    getTotalBalance,
    getMarginRequirement,
    getTradableBalance,
    getActiveFundingOffers,
    getFundingCredits,
    getFundingLoans
  };

  return (
    <WebSocketAccountContext.Provider value={value}>
      {children}
    </WebSocketAccountContext.Provider>
  );
};