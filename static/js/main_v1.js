import { ethers } from "https://cdnjs.cloudflare.com/ajax/libs/ethers/6.13.2/ethers.min.js";

let rc = React.createElement;
const LightweightCharts = window.LightweightCharts;
// const TESTNET_INDEXER_URL = 'https://testnet3.zentra.dev';
// const TESTNET_INDEXER_URL = 'http://127.0.0.1:8090';
const TESTNET_INDEXER_URL = 'http://127.0.0.1:8545';
const CHAIN = 'base';
// const CHAIN = 'cto';
const BASE_TOKEN = 'BTC';
const QUOTE_TOKEN = 'USDC';

const parseJsonWithBigInt = (data_json) => JSON.parse(
  data_json,
  (key, value, { source }) => (
    Number.isInteger(value) && !Number.isSafeInteger(value) ? BigInt(source) : value
  )
);

const toBigInt = (value) => {
  if (typeof value === 'bigint') return value;
  if (typeof value === 'string') return BigInt(value);
  if (typeof value === 'number') return BigInt(String(Math.trunc(value)));
  return 0n;
};

class Header extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { ethAddress, walletLoading } = this.props.walletState;
    return rc('header', { className: 'header p-4 flex justify-between items-center bg-gray-800 text-white' },
      rc('div', { className: 'logo flex items-center' },
        rc('img', { src: 'logo.svg', alt: 'Logo', className: 'h-8 w-8 mr-2' }),
        rc('span', { className: 'text-xl font-bold' }, 'OrderBook')
      ),
      rc('nav', { className: 'menu' },
        rc('ul', { className: 'flex space-x-4' },
          rc('li', null, rc('a', { href: '#', className: 'hover:text-gray-400' }, 'Home')),
          rc('li', null, rc('a', { href: '#', className: 'hover:text-gray-400' }, 'About')),
          rc('li', null, rc('a', { href: '#', className: 'hover:text-gray-400' }, 'Contact'))
        )
      ),
      rc('div', { className: 'login' },
        walletLoading ?
          null :
          (ethAddress ?
            rc('span', { className: 'font-mono' }, `${ethAddress.substring(0, 6)}...${ethAddress.substring(ethAddress.length - 4)}`) :
            rc('button', { onClick: this.props.handleWalletLogin, className: 'bg-gray-200 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded' }, 'Connect Wallet'))
      )
    );
  }
}

class ChartPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { history: [] };
    this.chart = null;
    this.candleSeries = null;
    this.chartRef = React.createRef();
  }

  componentDidMount() {
    this.initChart();
    this.loadHistory();
  }

initChart() {
    if (!this.chartRef.current) return;
    this.chart = LightweightCharts.createChart(this.chartRef.current, {
      width: this.chartRef.current.offsetWidth || 600,
      height: 300,
      layout: { background: { color: 'transparent' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#2d3748' }, horzLines: { color: '#2d3748' } },
      timeScale: {
        tickMarkFormatter: (time) => {
          return `b${time}`;
        },
      },
    });
    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444', borderDownColor: '#ef4444', borderUpColor: '#22c55e',
      wickDownColor: '#ef4444', wickUpColor: '#22c55e',
    });
  }


  loadHistory = async () => {
    try {
      const response = await fetch(`${TESTNET_INDEXER_URL}/api/history?base=BTC&quote=USDC`);
      const data = await response.json();
      const candles = data.candles || [];
      
      if (this.candleSeries && candles.length > 0) {
        this.candleSeries.setData(candles);
      }
      this.setState({ history: candles });
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  } 

  render() {
    const { history } = this.state;
    return rc('div', { className: 'chart-panel bg-gray-900 p-4 rounded-lg' },
      rc('h2', { className: 'text-lg font-bold text-white mb-2' }, `Market Chart (${history.length} trades)`),
      rc('div', { ref: this.chartRef, className: 'w-full' })
    );
  }
}

class MarketPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      activeTab: 'Order Book',
      orderBook: {
        bids: [],
        asks: []
      },
    };
  }

  componentDidMount() {
    this.applyOrderbookFromProps(this.props.orderbook);
  }

  componentWillUnmount() {
  }

  componentDidUpdate(prevProps) {
    if (this.props.orderbook !== prevProps.orderbook) {
      this.applyOrderbookFromProps(this.props.orderbook);
    }
  }

  applyOrderbookFromProps = (orderbook) => {
    if (!orderbook) return;
    this.setState({
      orderBook: {
        bids: orderbook.buys || orderbook.bids || [],
        asks: orderbook.sells || orderbook.asks || []
      }
    });
  }

  handleTabChange = (tab) => {
    this.setState({ activeTab: tab });
  };

  renderOrderBook() {
    const { bids, asks } = this.state.orderBook;
    return rc('div', { className: 'order-book text-white' },
      rc('div', { className: 'flex justify-between text-xs text-gray-400 p-2' },
        rc('span', null, 'Price (USDC)'),
        rc('span', null, `Size (BTC)`),
      ),
      rc('div', { className: 'asks' },
        asks.slice(0, 10).reverse().map((ask, index) =>
          rc('div', { key: index, className: 'flex justify-between p-1 text-red-500' },
            rc('span', null, ethers.formatUnits(toBigInt(ask.price), 6)),
            rc('span', null, ethers.formatUnits(-toBigInt(ask.base), 18).substring(0, 8)),
          )
        )
      ),
      rc('div', { className: 'current-price p-2 text-lg font-bold text-center' }, bids.length > 0 ? ethers.formatUnits(toBigInt(bids[0].price), 6) : (asks.length > 0 ? ethers.formatUnits(toBigInt(asks[0].price), 6) : '-')),
      rc('div', { className: 'bids' },
        bids.slice(0, 10).map((bid, index) =>
          rc('div', { key: index, className: 'flex justify-between p-1 text-green-500' },
            rc('span', null, ethers.formatUnits(toBigInt(bid.price), 6)),
            rc('span', null, ethers.formatUnits(toBigInt(bid.base), 18).substring(0, 8)),
          )
        )
      )
    );
  }

  renderTrades() {
    const { trades } = this.props;
    if (!trades || trades.length === 0) {
      return rc('div', { className: 'trades text-white text-center p-4' }, 'No recent trades.');
    }

    return rc('div', { className: 'trades text-white', style: { maxHeight: '400px', overflowY: 'auto' } },
      rc('div', { className: 'flex justify-between text-xs text-gray-400 p-2 sticky top-0 bg-gray-900' },
        rc('span', { className: 'w-1/3' }, 'Time'),
        rc('span', { className: 'w-1/3 text-right' }, 'Price (USDC)'),
        rc('span', { className: 'w-1/3 text-right' }, 'Size (BTC)'),
      ),
      rc('div', { className: 'trade-list' },
        trades.map((trade, index) =>
          rc('div', { key: index, className: `flex justify-between p-1 ${trade.side === 'buy' ? 'text-green-500' : 'text-red-500'}` },
            rc('span', { className: 'w-1/3 font-mono' }, new Date(trade.timestamp * 1000).toLocaleTimeString()),
            rc('span', { className: 'w-1/3 text-right font-mono' }, trade.price.toFixed(2)),
            rc('span', { className: 'w-1/3 text-right font-mono' }, trade.base_amount.toFixed(6)),
          )
        )
      )
    );
  }

  render() {
    return rc('div', { className: 'market-panel bg-gray-900 p-4 rounded-lg text-white', style: { minWidth: '300px', height: '100%' } },
      rc('div', { className: 'flex border-b border-gray-700' },
        rc('button', { className: `px-4 py-2 ${this.state.activeTab === 'Order Book' ? 'border-b-2 border-blue-500' : ''}`, onClick: () => this.handleTabChange('Order Book') }, 'Order Book'),
        rc('button', { className: `px-4 py-2 ${this.state.activeTab === 'Trades' ? 'border-b-2 border-blue-500' : ''}`, onClick: () => this.handleTabChange('Trades') }, 'Trades')
      ),
      rc('div', { className: 'mt-4' },
        this.state.activeTab === 'Order Book' ? this.renderOrderBook() : this.renderTrades()
      )
    );
  }
}

class OrderPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      activeTab: 'Limit',
      tradeType: 'Buy',
      price: '68000',
      size: '',
      rangeValue: '0',
      sizeUnit: 'BTC', // BTC or USDC
      balance: {
        BTC: 0,
        USDC: 0
      }
    };
    this.balanceInterval = null;
  }

  componentDidMount() {
    this.fetchBalances();
    this.balanceInterval = setInterval(this.fetchBalances, 2000);
  }

  componentWillUnmount() {
    clearInterval(this.balanceInterval);
  }

  componentDidUpdate(prevProps) {
    if (this.props.signer !== prevProps.signer) {
      this.fetchBalances();
    }
  }

  fetchBalances = async () => {
    const { signer } = this.props;
    if (!signer) {
      return;
    }
    const address = await signer.getAddress();

    const tokens = ['USDC', 'BTC'];
    const decimals = {
      'USDC': 6,
      'BTC': 18
    }

    tokens.forEach(async (token) => {
      if (!token || !decimals[token]) return;
      try {
        const prefix = `${token}-balance:${address.toLowerCase()}`;
        const response = await fetch(`${TESTNET_INDEXER_URL}/api/get_latest_state?prefix=${prefix}`);
        const data_json = await response.text();
        const data = parseJsonWithBigInt(data_json);
        const formattedBalance = ethers.formatUnits(BigInt(data.result || 0), decimals[token] || 18);
        this.setState(prevState => ({
          balance: {
            ...prevState.balance,
            [token]: parseFloat(formattedBalance)
          }
        }));
      } catch (error) {
        console.error(`Failed to fetch ${token} balance:`, error);
      }
    });
  }

  handleInputChange = (e) => {
    const { name, value } = e.target;
    this.setState({ [name]: value });
  }

  handleRangeChange = (e) => {
    const percentage = e.target.value;
    const { tradeType, balance, price, sizeUnit } = this.state;
    const for_token = 'BTC';
    let newSize = '';

    if (tradeType === 'Buy') {
      const budget = balance.USDC * (percentage / 100);
      if (price > 0) {
        newSize = sizeUnit === for_token ? (budget / price).toFixed(6) : budget.toFixed(2);
      }
    } else { // Sell
      const amount = balance[for_token] * (percentage / 100);
      if (price > 0) {
        newSize = sizeUnit === for_token ? amount.toFixed(6) : (amount * price).toFixed(2);
      }
    }

    this.setState({ rangeValue: percentage, size: newSize });
  }

  handleTabChange = (tab) => {
    this.setState({ activeTab: tab });
  };

  handleTradeTypeChange = (type) => {
    this.setState({ tradeType: type, size: '', rangeValue: '0' });
  };

  handleSizeUnitChange = () => {
    const for_token = 'BTC';
    this.setState(prevState => ({ sizeUnit: prevState.sizeUnit === for_token ? 'USDC' : for_token, size: '' }));
  }

  placeOrder = async () => {
    const { signer } = this.props;
    if (!signer) {
      alert('Please connect your wallet first.');
      return;
    }

    const { activeTab, tradeType, price, size, sizeUnit } = this.state;
    const for_token = 'BTC';
    const quote_token = 'USDC';
    const ZEN_ADDR = '0x00000000000000000000000000000000007a656e';
    const base_decimals = 18;
    const quote_decimals = 6;

    let calldata;
    let base_amount;
    let quote_amount;

    if (activeTab === 'Limit') {
      if (!size || isNaN(parseFloat(size)) || parseFloat(price) <= 0) {
        alert('Please enter a valid size and price');
        return;
      }
      if (sizeUnit === for_token) { // size is in base token
        base_amount = ethers.parseUnits(size, base_decimals);
        quote_amount = ethers.parseUnits((parseFloat(size) * parseFloat(price)).toString(), quote_decimals);
      } else { // size is in USDC
        quote_amount = ethers.parseUnits(size, quote_decimals);
        base_amount = ethers.parseUnits((parseFloat(size) / parseFloat(price)).toString(), base_decimals);
      }

      if (tradeType === 'Buy') {
        quote_amount = -quote_amount;
      } else { // Sell
        base_amount = -base_amount;
      }

      calldata = {
        'p': 'zentest3',
        'f': 'trade_limit_order',
        'a': [for_token, base_amount.toString(), quote_token, quote_amount.toString()]
      };

    } else { // Market
      if (!size || isNaN(parseFloat(size)) || parseFloat(size) <= 0) {
        alert('Please enter a valid size');
        return;
      }
      if (tradeType === 'Buy') {
        // Market buy is specified by quote amount to spend
        quote_amount = -ethers.parseUnits(size, quote_decimals);
        base_amount = null;
      } else { // Market sell is specified by base amount to sell
        base_amount = -ethers.parseUnits(size, base_decimals);
        quote_amount = null;
      }

      calldata = {
        'p': 'zentest3',
        'f': 'trade_market_order',
        'a': [for_token, base_amount ? base_amount.toString() : null, quote_token, quote_amount ? quote_amount.toString() : null]
      };
    }

    try {
      console.log('calldata', calldata);
      const tx = await signer.sendTransaction({
        to: ZEN_ADDR,
        value: 0,
        data: ethers.hexlify(new TextEncoder().encode(JSON.stringify(calldata)))
      });
      alert(`Transaction sent: ${tx.hash}`);
    } catch (error) {
      console.error('Order failed:', error);
      alert('Order failed.');
    }
  };

  render() {
    const tradeTypeClass = this.state.tradeType === 'Buy' ? 'bg-green-500 hover:bg-green-700' : 'bg-red-500 hover:bg-red-700';
    const balanceToShow = this.state.tradeType === 'Buy' ? `${this.state.balance.USDC.toFixed(2)} USDC` : `${(this.state.balance.BTC || 0).toFixed(4)} BTC`;
    let total = 0;
    if (this.state.price > 0 && this.state.size > 0) {
      if (this.state.sizeUnit === 'BTC') {
        total = this.state.price * this.state.size;
      } else {
        total = parseFloat(this.state.size);
      }
    }

    return rc('div', { className: 'order-panel bg-gray-900 p-4 rounded-lg text-white', style: { minWidth: '300px', height: '100%' } },
      rc('div', { className: 'flex border-b border-gray-700' },
        rc('button', { className: `px-4 py-2 ${this.state.activeTab === 'Market' ? 'border-b-2 border-blue-500' : ''}`, onClick: () => this.handleTabChange('Market') }, 'Market'),
        rc('button', { className: `px-4 py-2 ${this.state.activeTab === 'Limit' ? 'border-b-2 border-blue-500' : ''}`, onClick: () => this.handleTabChange('Limit') }, 'Limit')
      ),
      rc('div', { className: 'flex mt-4' },
        rc('button', { className: `flex-1 py-2 ${this.state.tradeType === 'Buy' ? 'bg-green-600' : 'bg-gray-700'}`, onClick: () => this.handleTradeTypeChange('Buy') }, 'Buy'),
        rc('button', { className: `flex-1 py-2 ${this.state.tradeType === 'Sell' ? 'bg-red-600' : 'bg-gray-700'}`, onClick: () => this.handleTradeTypeChange('Sell') }, 'Sell')
      ),
      rc('div', { className: 'mt-4 space-y-4' },
        rc('div', { className: 'flex justify-between text-sm' },
          rc('span', { className: 'text-gray-400' }, 'Available:'),
          rc('span', { className: 'font-mono' }, balanceToShow)
        ),
        this.state.activeTab === 'Market' && rc('div', { className: 'market-tab space-y-4' },
          rc('div', null,
            rc('label', { className: 'block text-sm text-gray-400' }, 'Size'),
            rc('input', { type: 'text', name: 'size', value: this.state.size, onChange: this.handleInputChange, placeholder: 'Enter size', className: 'w-full p-2 bg-gray-800 border border-gray-700 rounded' })
          )
        ),
        this.state.activeTab === 'Limit' && rc('div', { className: 'limit-tab space-y-4' },
          rc('div', null,
            rc('label', { className: 'block text-sm text-gray-400' }, 'Price'),
            rc('input', { type: 'text', name: 'price', value: this.state.price, onChange: this.handleInputChange, className: 'w-full p-2 bg-gray-800 border border-gray-700 rounded' })
          ),
          rc('div', null,
            rc('div', { className: 'flex justify-between' },
              rc('label', { className: 'block text-sm text-gray-400' }, 'Size'),
              rc('button', { onClick: this.handleSizeUnitChange, className: 'text-sm text-blue-400 hover:text-blue-300' }, `in ${this.state.sizeUnit}`)
            ),
            rc('input', { type: 'text', name: 'size', value: this.state.size, onChange: this.handleInputChange, placeholder: `Enter size in ${this.state.sizeUnit}`, className: 'w-full p-2 bg-gray-800 border border-gray-700 rounded' })
          ),
          rc('div', { className: 'range' },
            rc('input', {
              type: 'range', min: '0', max: '100', value: this.state.rangeValue,
              onChange: this.handleRangeChange,
              className: 'w-full'
            }),
            rc('div', { className: 'flex justify-between text-xs text-gray-400' },
              rc('span', null, '0%'),
              rc('span', null, '25%'),
              rc('span', null, '50%'),
              rc('span', null, '75%'),
              rc('span', null, '100%')
            )
          ),
          rc('div', { className: 'flex justify-between text-sm' },
            rc('span', { className: 'text-gray-400' }, 'Total:'),
            rc('span', { className: 'font-mono' }, `${total.toFixed(2)} USDC`)
          )
        ),
        rc('button', { className: `w-full mt-4 py-2 rounded text-white font-bold ${tradeTypeClass}`, onClick: this.placeOrder }, `Place ${this.state.tradeType} Order`)
      )
    );
  }
}

class InfoPanel extends React.Component {
  render() {
    return rc('div', { className: 'info-panel bg-gray-900 p-4 rounded-lg text-white' },
      rc('h2', { className: 'text-lg font-bold mb-4' }, 'Market Info'),
      rc('div', { className: 'grid grid-cols-2 gap-4 text-sm' },
        rc('div', null,
          rc('div', { className: 'text-gray-400' }, '24h High'),
          rc('div', { className: 'font-bold' }, '69,420.00')
        ),
        rc('div', null,
          rc('div', { className: 'text-gray-400' }, '24h Low'),
          rc('div', { className: 'font-bold' }, '67,123.00')
        ),
        rc('div', null,
          rc('div', { className: 'text-gray-400' }, '24h Volume (BTC)'),
          rc('div', { className: 'font-bold' }, '1,234.56')
        ),
        rc('div', null,
          rc('div', { className: 'text-gray-400' }, '24h Volume (USD)'),
          rc('div', { className: 'font-bold' }, '84,567,890.12')
        )
      )
    );
  }
}

class AssetsPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      BTC: null,
      USDC: null
    };
  }

  componentDidMount() {
    this.fetchAssets();
  }

  componentDidUpdate(prevProps) {
    if (this.props.address !== prevProps.address && this.props.address) {
      this.fetchAssets();
    }
  }

  fetchAssets = async () => {
    if (!this.props.address) return;
    const tokens = { BTC: 18, USDC: 6 };
    const newState = {};
    const addr = this.props.address.toLowerCase();
    for (const [tick, dec] of Object.entries(tokens)) {
      try {
        const prefix = `${tick}-balance:${addr}`;
        const response = await fetch(`${TESTNET_INDEXER_URL}/api/get_latest_state?prefix=${prefix}`);
        const data = await response.json();
        const val = data.result;
        newState[tick] = val && val !== '0' ? ethers.formatUnits(toBigInt(val), dec) : '0';
      } catch (e) {
        newState[tick] = '0';
      }
    }
    this.setState(newState);
  }

  render() {
    const assets = [
      { tick: 'BTC', amount: this.state.BTC || '0' },
      { tick: 'USDC', amount: this.state.USDC || '0' }
    ];

    return rc('div', { className: 'assets-panel bg-gray-900 p-4 rounded-lg text-white h-full' },
      rc('h2', { className: 'text-lg font-bold mb-4' }, 'My Assets'),
      rc('div', { className: 'space-y-4' },
        assets.map(asset =>
          rc('div', { key: asset.tick, className: 'flex justify-between items-center' },
            rc('div', null,
              rc('div', { className: 'font-bold' }, asset.tick)
            ),
            rc('div', { className: 'text-right font-mono' }, asset.amount)
          )
        )
      )
    );
  }
}

class ToolPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isDarkTheme: true
    };
  }

  toggleTheme = () => {
    this.setState(prevState => ({ isDarkTheme: !prevState.isDarkTheme }));
  }

  render() {
    return rc('div', { className: 'tool-panel bg-gray-900 p-4 rounded-lg text-white' },
      rc('h2', { className: 'text-lg font-bold mb-4' }, 'Tools & Settings'),
      rc('div', { className: 'flex justify-between items-center' },
        rc('span', null, 'Dark Theme'),
        rc('label', { className: 'switch' },
          rc('input', { type: 'checkbox', checked: this.state.isDarkTheme, onChange: this.toggleTheme }),
          rc('span', { className: 'slider round' })
        )
      )
    );
  }
}


class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      screenWidth: window.innerWidth,
      ethAddress: null,
      provider: null,
      signer: null,
      walletLoading: true,
      orderbook: null,
      lastBlock: null,
      trades: [],
      streamTrades: null,
    };
    this.ws = null;
    this.reconnectTimeout = null;
  }

  loadInitialMarketData = async () => {
    try {
      const response = await fetch(`${TESTNET_INDEXER_URL}/api/orderbook?base=${BASE_TOKEN}&quote=${QUOTE_TOKEN}`);
      const data = await response.json();
      // console.log('Orderbook data:', data);
      this.setState(
        {
          orderbook: { buys: data.buys, sells: data.sells },
          lastBlock: null
        },
        () => this.startStream()
      );
    } catch (error) {
      console.error('Failed to load market data:', error);
    }
  }

  // Function for the initial silent check and for handling account changes
  initializeWallet = async () => {
    if (typeof window.ethereum === 'undefined') {
      this.setState({ walletLoading: false });
      return;
    }

    try {
      const accounts = await window.ethereum.request({ method: 'eth_accounts' });

      if (accounts.length > 0) {
        const ethAddress = accounts[0];
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        this.setState({ ethAddress, provider, signer });

        try {
          const chainId = await window.ethereum.request({ method: 'eth_chainId' });
          if (chainId !== '0x7a69') {
            try {
              await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x7a69' }],
              });
            } catch (switchError) {
              if (switchError.code === 4902) {
                await window.ethereum.request({
                  method: 'wallet_addEthereumChain',
                  params: [{
                    chainId: '0x7a69',
                    chainName: 'Local Testnet',
                    rpcUrls: ['http://127.0.0.1:8545'],
                    nativeCurrency: { name: 'Ethereum', symbol: 'ETH', decimals: 18 },
                  }],
                });
              }
            }
          }
        } catch (e) {
          console.error('Failed to switch chain:', e);
        }
      } else {
        this.setState({ ethAddress: null, provider: null, signer: null });
      }
    } catch (error) {
      console.error('Error initializing wallet:', error);
    } finally {
      this.setState({ walletLoading: false });
    }
  }

  // Function for the user explicitly clicking the "Connect Wallet" button
  handleWalletLogin = async () => {
    if (typeof window.ethereum === 'undefined') {
      alert('Wallet not installed!');
      return;
    }

    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const ethAddress = accounts[0];

      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();

      this.setState({ ethAddress, provider, signer, walletLoading: false });

      try {
        await window.ethereum.request({
          method: 'wallet_switchEthereumChain',
          params: [{ chainId: '0x7a69' }],
        });
      } catch (switchError) {
        if (switchError.code === 4902) {
          try {
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: '0x7a69',
                chainName: 'Local Testnet',
                rpcUrls: ['http://127.0.0.1:8545'],
                nativeCurrency: {
                  name: 'Ethereum',
                  symbol: 'ETH',
                  decimals: 18,
                },
              }],
            });
          } catch (addError) {
            console.error('Failed to add Base Sepolia Testnet:', addError);
            alert('Failed to add Base Sepolia Testnet.');
          }
        } else {
          console.error('Failed to switch to Base Sepolia Testnet:', switchError);
          alert('Failed to switch to Base Sepolia Testnet.');
        }
      }
    } catch (error) {
      console.error('Error logging in:', error);
      this.setState({ walletLoading: false });
    }
  }

  componentDidMount() {
    window.addEventListener('resize', this.handleResize);
    this.initializeWallet();
    this.loadInitialMarketData();

    this.orderbookInterval = setInterval(() => {
      this.loadInitialMarketData();
    }, 3000);

    if (window.ethereum) {
      window.ethereum.on('accountsChanged', (accounts) => {
        this.initializeWallet();
      });
    }
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.handleResize);
    this.teardownStream();
    if (this.orderbookInterval) {
      clearInterval(this.orderbookInterval);
    }
    if (window.ethereum && window.ethereum.removeListener) {
      window.ethereum.removeListener('accountsChanged', this.initializeWallet);
    }
  }

  handleResize = () => {
    this.setState({
      screenWidth: window.innerWidth
    });
  }

  handleIntervalChange = () => {
    this.loadInitialMarketData();
  }

  startStream = () => {
    if (this.ws) return;
    const lastBlockHeight = this.state.lastBlock ? this.state.lastBlock.height : null;
    if (lastBlockHeight === null || lastBlockHeight === undefined) return;
    const wsUrl = `${TESTNET_INDEXER_URL.replace(/^http/, 'ws')}/api/stream?base=${BASE_TOKEN}&quote=${QUOTE_TOKEN}` +
      (lastBlockHeight ? `&start_block=${lastBlockHeight}` : '');

    try {
      this.ws = new WebSocket(wsUrl);
    } catch (err) {
      console.error('Failed to open websocket:', err);
      return;
    }

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        this.handleStreamMessage(payload);
      } catch (err) {
        console.error('Failed to parse stream message:', err);
      }
    };

    this.ws.onerror = (err) => {
      console.error('Websocket error:', err);
    };

    this.ws.onclose = () => {
      this.scheduleReconnect();
    };
  }

  teardownStream = () => {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (!this.ws) return;
    this.ws.onopen = null;
    this.ws.onclose = null;
    this.ws.onmessage = null;
    this.ws.onerror = null;
    try {
      this.ws.close();
    } catch (_) { }
    this.ws = null;
  }

  scheduleReconnect = () => {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.teardownStream();
      this.startStream();
    }, 2000);
  }

  handleStreamMessage = (payload) => {
    if (!payload) return;

    if (payload.type === 'orderbook' || payload.orderbook || payload.bids || payload.asks || payload.buys || payload.sells) {
      const bids = payload.bids || payload.buys || (payload.orderbook && payload.orderbook.bids) || [];
      const asks = payload.asks || payload.sells || (payload.orderbook && payload.orderbook.asks) || [];
      if (Array.isArray(bids) || Array.isArray(asks)) {
        this.setState({
          orderbook: {
            bids,
            asks,
            buys: bids,
            sells: asks
          }
        });
      }
    }

    if (payload.type === 'trade' || payload.trades) {
      const incomingTrades = payload.trades || (payload.trade ? [payload.trade] : []);
      if (incomingTrades && incomingTrades.length > 0) {
        this.setState(prev => ({
          trades: [...incomingTrades, ...prev.trades].slice(0, 200),
          streamTrades: incomingTrades
        }));
      }
      if (payload.last_block) {
        this.setState({ lastBlock: payload.last_block });
      }
    }
  }

  render() {
    const commonLayout = (mainPanel, sidePanel1, sidePanel2) => {
      return rc('div', { className: 'app' },
        rc(Header, { walletState: this.state, handleWalletLogin: this.handleWalletLogin }),
        rc('main', { className: 'p-4' },
          rc('div', { className: 'flex flex-col lg:flex-row gap-4' },
            rc('div', { className: 'flex-grow' },
              mainPanel
            ),
            rc('div', { className: 'w-full lg:w-80 space-y-4' },
              sidePanel1,
              sidePanel2
            )
          )
        )
      );
    };

    const mainContent = rc('div', { className: 'space-y-4' },
      rc(ChartPanel, {
        streamTrades: this.state.streamTrades,
      }),
      rc(InfoPanel, null)
    );

    const orderPanelWithSigner = rc(OrderPanel, { signer: this.state.signer });
    const marketPanel = rc(MarketPanel, { orderbook: this.state.orderbook, trades: this.state.trades });
    const assetsPanel = rc(AssetsPanel, { address: this.state.ethAddress });
    const toolPanel = rc(ToolPanel, null);

    if (this.state.screenWidth < 960) { // Mobile layout
      return commonLayout(
        rc('div', { className: 'space-y-4' }, mainContent, orderPanelWithSigner, marketPanel, assetsPanel, toolPanel),
        null,
        null
      );
    }

    if (this.state.screenWidth < 1400) { // Tablet layout
      return commonLayout(
        mainContent,
        rc('div', { className: 'space-y-4' }, orderPanelWithSigner, marketPanel),
        rc('div', { className: 'space-y-4' }, assetsPanel, toolPanel)
      );
    }

    // Desktop layout
    return rc('div', { className: 'app' },
      rc(Header, { walletState: this.state, handleWalletLogin: this.handleWalletLogin }),
      rc('main', { className: 'p-4' },
        rc('div', { className: 'flex gap-4' },
          rc('div', { className: 'flex-grow space-y-4' },
            rc(InfoPanel, null),
            rc(ChartPanel, {
              streamTrades: this.state.streamTrades,
            }),
            rc(AssetsPanel, { address: this.state.ethAddress })
          ),
          rc('div', { className: 'w-80 space-y-4' },
            marketPanel,
            rc(ToolPanel, null)
          ),
          rc('div', { className: 'w-80 space-y-4' },
            orderPanelWithSigner
          )
        )
      )
    );
  }
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(rc(App, null));
