import { Connection, PublicKey, Transaction, TransactionInstruction } from 'https://esm.sh/@solana/web3.js@1.95.0';

const rc = React.createElement;
const LightweightCharts = window.LightweightCharts;
const TESTNET_INDEXER_URL = 'http://127.0.0.1:3000';

const USE_DEVNET = true; // Set to true for devnet, false for local test validator

const CONFIG = USE_DEVNET ? {
  SOLANA_PROGRAM: '2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih',
  RPC_URL: 'https://api.devnet.solana.com',
} : {
  SOLANA_PROGRAM: '2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih',
  RPC_URL: 'http://127.0.0.1:8899',
};

const SOLANA_PROGRAM = CONFIG.SOLANA_PROGRAM;
const RPC_URL = CONFIG.RPC_URL;

function getConnection() {
  const wallet = getAllWallets();
  if (wallet && wallet.connection) {
    return wallet.connection;
  }
  return new Connection(RPC_URL);
}

const parseJsonWithBigInt = (data_json) => JSON.parse(
  data_json,
  (key, value, { source }) => (
    Number.isInteger(value) && !Number.isSafeInteger(value) ? BigInt(source) : value
  )
);

const getAllWallets = () => window.solana || window.backpack || null;

const logWallets = () => {
  console.log('window.solana:', window.solana);
  console.log('window.backpack:', window.backpack);
  console.log('getAllWallets():', getAllWallets());
};
window.addEventListener('load', logWallets);
setTimeout(logWallets, 1000);

function getWallet() {
  return getAllWallets();
}

const toBigInt = (value) => {
  if (typeof value === 'bigint') return value;
  if (typeof value === 'string') return BigInt(value);
  if (typeof value === 'number') return BigInt(String(Math.trunc(value)));
  return 0n;
}

const toUint8Array = (arr) => {
  return new Uint8Array(arr);
};

class Header extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { solAddress, walletLoading } = this.props.walletState;
    return rc('header', { className: 'header p-4 flex justify-between items-center bg-gray-800 text-white' },
      rc('div', { className: 'logo flex items-center' },
        rc('img', { src: 'logo.svg', alt: 'Logo', className: 'h-8 w-8 mr-2' }),
        rc('span', { className: 'text-xl font-bold' }, 'TrueDEX')
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
          (solAddress ?
            rc('div', { className: 'flex items-center gap-2' },
              rc('span', { className: 'font-mono text-sm' }, `${solAddress.substring(0, 6)}...${solAddress.substring(solAddress.length - 4)}`),
              rc('button', { onClick: this.props.handleWalletLogout, className: 'bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded text-sm' }, 'Logout')
            ) :
            rc('button', { onClick: this.props.handleWalletLogin, className: 'bg-gray-200 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded' }, 'Connect Wallet'))
      )
    );
  }
}

class ChartPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { history: [], interval: '1s', localCandles: [] };
    this.chart = null;
    this.candleSeries = null;
    this.chartRef = React.createRef();
    this.timer = null;
  }

  componentDidMount() {
    this.initChart();
    this.loadHistory();
    this.startAutoRefresh();
  }

  componentWillUnmount() {
    if (this.timer) clearInterval(this.timer);
  }

  startAutoRefresh = () => {
    if (this.timer) clearInterval(this.timer);
    // Check every second for new candle
    this.timer = setInterval(() => {
      const { localCandles, interval } = this.state;
      if (!localCandles.length) return;

      const intervalSec = {
        '1s': 1, '1m': 60, '5m': 300, '15m': 900, '1h': 3600, '1d': 86400
      }[interval] || 3600;

      const now = Math.floor(Date.now() / 1000);
      const bucket = Math.floor(now / intervalSec) * intervalSec;
      const lastCandle = localCandles[localCandles.length - 1];

      if (bucket > lastCandle.time) {
        // Time moved to new bucket, create new candle with previous close
        const newCandle = {
          time: bucket,
          open: lastCandle.close,
          high: lastCandle.close,
          low: lastCandle.close,
          close: lastCandle.close,
          volume: 0
        };
        const newCandles = [...localCandles, newCandle];
        this.setState({ localCandles: newCandles });
        if (this.candleSeries) {
          this.candleSeries.setData(newCandles);
        }
      }
    }, 1000); // Check every second
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
    const { interval } = this.state;
    try {
      const response = await fetch(`${TESTNET_INDEXER_URL}/api/history?base=BTC&quote=USDC&interval=${interval}`);
      const data = await response.json();
      const candles = data.candles || [];

      if (this.candleSeries && candles.length > 0) {
        this.candleSeries.setData(candles);
      }
      this.setState({ history: candles, localCandles: candles });
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  }

  handleIntervalChange = (interval) => {
    this.setState({ interval }, () => {
      this.loadHistory();
    });
  }

  componentDidUpdate(prevProps, prevState) {
    // 切换周期时重新加载
    if (this.state.interval !== prevState.interval) {
      this.loadHistory();
    }
    // 新交易到来时更新蜡烛图
    if (this.props.streamTrades !== prevProps.streamTrades && this.props.streamTrades) {
      console.log('🔄 Updating candles with trades:', this.props.streamTrades);
      this.updateCandlesWithTrades(this.props.streamTrades);
    }
  }

  updateCandlesWithTrades = (trades) => {
    const { interval } = this.state;
    console.log(`updateCandlesWithTrades called, interval=${interval}, trades:`, trades);

    const intervalSec = {
      '1s': 1, '1m': 60, '5m': 300, '15m': 900, '1h': 3600, '1d': 86400
    }[interval] || 3600;

    let { localCandles } = this.state;

    if (!this.candleSeries) {
      console.error('candleSeries is null!');
      return;
    }

    // 滑动窗口大小：1s=300(5分钟), 1m=300(5小时), 1h=200(200小时)
    const MAX_CANDLES = { '1s': 300, '1m': 300, '5m': 300, '15m': 300, '1h': 200, '1d': 100 }[interval] || 300;

    trades.forEach(trade => {
      const tradeTime = trade.timestamp || Math.floor(Date.now() / 1000);
      const bucket = Math.floor(tradeTime / intervalSec) * intervalSec;
      console.log(`trade: price=${trade.price}, bucket=${bucket}`);

      if (!localCandles.length) {
        // 无历史数据：创建第一个蜡烛
        const firstCandle = {
          time: bucket,
          open: trade.price,
          high: trade.price,
          low: trade.price,
          close: trade.price,
          volume: trade.amount || 0
        };
        localCandles = [firstCandle];
        console.log('First candle:', firstCandle);
        return; // 处理下一个 trade
      }

      // 查找对应的 candle（二分查找，因为 localCandles 按 time 排序）
      let idx = -1;
      for (let i = localCandles.length - 1; i >= 0; i--) {
        if (localCandles[i].time === bucket) {
          idx = i;
          break;
        }
        if (localCandles[i].time < bucket) break; // 已排序，可提前退出
      }

      if (idx >= 0) {
        // 找到对应时间桶：更新该蜡烛
        const oldCandle = localCandles[idx];
        const updatedCandle = {
          ...oldCandle,
          high: Math.max(oldCandle.high, trade.price),
          low: Math.min(oldCandle.low, trade.price),
          close: trade.price,
          volume: (oldCandle.volume || 0) + (trade.amount || 0)
        };
        localCandles[idx] = updatedCandle;
        console.log('Updating candle at idx', idx, ':', updatedCandle);
      } else if (bucket > localCandles[localCandles.length - 1].time) {
        // 新时间桶（超过最新）：追加
        const newCandle = {
          time: bucket,
          open: trade.price,
          high: trade.price,
          low: trade.price,
          close: trade.price,
          volume: trade.amount || 0
        };
        localCandles = [...localCandles, newCandle];
        console.log('New candle (append):', newCandle);
      } else if (bucket < localCandles[0].time) {
        // 旧时间桶（早于最早）：在开头插入
        const newCandle = {
          time: bucket,
          open: trade.price,
          high: trade.price,
          low: trade.price,
          close: trade.price,
          volume: trade.amount || 0
        };
        localCandles = [newCandle, ...localCandles];
        console.log('New candle (prepend):', newCandle);
      } else {
        // 中间缺失的时间桶：插入到正确位置
        let insertIdx = localCandles.length;
        for (let i = 0; i < localCandles.length; i++) {
          if (localCandles[i].time > bucket) {
            insertIdx = i;
            break;
          }
        }
        const newCandle = {
          time: bucket,
          open: trade.price,
          high: trade.price,
          low: trade.price,
          close: trade.price,
          volume: trade.amount || 0
        };
        localCandles = [...localCandles.slice(0, insertIdx), newCandle, ...localCandles.slice(insertIdx)];
        console.log('New candle (insert at', insertIdx, '):', newCandle);
      }
    });

    // 滑动窗口：只保留最近 MAX_CANDLES 个
    if (localCandles.length > MAX_CANDLES) {
      localCandles = localCandles.slice(-MAX_CANDLES);
    }

    // 确保 open 承接前一个 close，让 K 线视觉连续
    if (localCandles.length > 1) {
      for (let i = 1; i < localCandles.length; i++) {
        localCandles[i].open = localCandles[i-1].close;
      }
    }

    // 一次性更新图表
    this.candleSeries.setData(localCandles);
    this.setState({ localCandles });
  }

  render() {
    const { history, interval } = this.state;
    const intervals = ['1s', '1m', '5m', '15m', '1h', '1d'];
    return rc('div', { className: 'chart-panel bg-gray-900 p-4 rounded-lg' },
      rc('div', { className: 'flex justify-between items-center mb-2' },
        rc('h2', { className: 'text-lg font-bold text-white' }, `Market Chart (${history.length} trades)`),
        rc('div', { className: 'flex gap-1' },
          intervals.map(iv =>
            rc('button', {
              key: iv,
              onClick: () => this.handleIntervalChange(iv),
              className: `px-2 py-1 text-xs rounded ${interval === iv ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`
            }, iv)
          )
        )
      ),
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
            rc('span', null, Number(ask.price) / 1e6),
            rc('span', null, String(Number(ask.base) / 1e18).substring(0, 8)),
          )
        )
      ),
      rc('div', { className: 'current-price p-2 text-lg font-bold text-center' }, bids.length > 0 ? (Number(bids[0].price) / 1e6).toString() : (asks.length > 0 ? (Number(asks[0].price) / 1e6).toString() : '-')),
      rc('div', { className: 'bids' },
        bids.slice(0, 10).map((bid, index) =>
          rc('div', { key: index, className: 'flex justify-between p-1 text-green-500' },
            rc('span', null, Number(bid.price) / 1e6),
            rc('span', null, String(Number(bid.base) / 1e18).substring(0, 8)),
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
      size: '0.01',
      rangeValue: '0',
      sizeUnit: 'BTC',
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
    // Auto-detect wallet
    const wallet = getAllWallets();
    console.log('Wallet found:', wallet);
    setTimeout(() => {
      const w = getAllWallets();
      console.log('Wallet after timeout:', w, 'publicKey:', w ? w.publicKey : null);
      if (w && w.publicKey) {
        this.setState({
          solAddress: w.publicKey.toString(),
          publicKey: w.publicKey,
          sendTransaction: w.signTransaction,
          walletLoading: false
        });
      }
    }, 500);
  }

  componentWillUnmount() {
    clearInterval(this.balanceInterval);
  }

  componentDidUpdate(prevProps) {
    if (this.props.publicKey !== prevProps.publicKey) {
      this.fetchBalances();
    }
  }

  fetchBalances = async () => {
    const { publicKey } = this.props;
    if (!publicKey) {
      return;
    }
    const address = publicKey.toString();

    const tokens = ['USDC', 'BTC'];
    const decimals = { USDC: 6, BTC: 18 };
    tokens.forEach(async (token) => {
      try {
        const prefix = `${token}-balance:${address}`;
        const response = await fetch(`${TESTNET_INDEXER_URL}/api/get_latest_state?prefix=${prefix}`);
        const data_json = await response.text();
        const data = parseJsonWithBigInt(data_json);
        const formattedBalance = Number(data.result || 0) / Math.pow(10, decimals[token]);
        this.setState(prevState => ({
          balance: {
            ...prevState.balance,
            [token]: formattedBalance
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
    } else {
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
    this.setState({ tradeType: type, size: '0.01', rangeValue: '0' });
  };

  handleSizeUnitChange = () => {
    const for_token = 'BTC';
    this.setState(prevState => ({ sizeUnit: prevState.sizeUnit === for_token ? 'USDC' : for_token, size: '' }));
  }

  placeOrder = async () => {
    // Check both props and direct wallet
    const directWallet = getAllWallets();
    console.log('Direct wallet check:', directWallet);
    console.log('Props:', this.props);
    
    let publicKey = this.props.publicKey;
    let sendTransaction = this.props.sendTransaction;
    
    if (directWallet && directWallet.publicKey) {
      publicKey = directWallet.publicKey;
      if (!sendTransaction && directWallet.signTransaction) {
        sendTransaction = directWallet.signTransaction.bind(directWallet);
      }
      console.log('Using direct wallet:', publicKey.toString());
    }
    
    if (!publicKey || !sendTransaction) {
      console.error('No wallet! publicKey:', publicKey, 'sendTransaction:', sendTransaction);
      alert('Please connect your wallet first.');
      return;
    }

    const { activeTab, tradeType, price, size, sizeUnit } = this.state;
    const for_token = 'BTC';
    const quote_token = 'USDC';
    const prog = new PublicKey(SOLANA_PROGRAM);

    let base_amount;
    let quote_amount;

    if (activeTab === 'Limit') {
      if (!size || isNaN(parseFloat(size)) || parseFloat(price) <= 0) {
        alert('Please enter a valid size and price');
        return;
      }
      if (sizeUnit === for_token) {
        base_amount = BigInt(Math.floor(parseFloat(size) * 1e18)).toString();
        quote_amount = BigInt(Math.floor(parseFloat(size) * parseFloat(price) * 1e6)).toString();
      } else {
        quote_amount = BigInt(Math.floor(parseFloat(size) * 1e6)).toString();
        base_amount = BigInt(Math.floor(parseFloat(size) / parseFloat(price) * 1e18)).toString();
      }

      if (tradeType === 'Buy') {
        quote_amount = '-' + quote_amount;
      } else {
        base_amount = '-' + base_amount;
      }

      const calldata = JSON.stringify({
        f: 'trade_limit_order',
        a: [for_token, base_amount, quote_token, quote_amount]
      });

      const data = new TextEncoder().encode(calldata);
      const instructionData = new Uint8Array([3, ...data]);

      const transaction = new Transaction();
      const keys = [
        { pubkey: publicKey, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: true, isWritable: false },
      ];
      const ix = new TransactionInstruction({
        programId: prog,
        keys: keys,
        data: instructionData,
      });
      transaction.add(ix);

      // try {
        transaction.feePayer = publicKey;
        transaction.recentBlockhash = (await getConnection().getLatestBlockhash()).blockhash;
        const signature = await sendTransaction(transaction, getConnection());
        console.log('Transaction sent:', signature);
      // } catch (error) {
      //   console.error('Order failed:', error);
      //   alert('Order failed.');
      // }
    } else {
      if (!size || isNaN(parseFloat(size)) || parseFloat(size) <= 0) {
        alert('Please enter a valid size');
        return;
      }
      if (tradeType === 'Buy') {
        quote_amount = BigInt(Math.floor(parseFloat(size) * 1e6)).toString();
        base_amount = null;
      } else {
        base_amount = BigInt(Math.floor(parseFloat(size) * 1e18)).toString();
        quote_amount = null;
      }

      const calldata = JSON.stringify({
        f: 'trade_market_order',
        a: [for_token, base_amount ? base_amount.toString() : null, quote_token, quote_amount ? quote_amount.toString() : null]
      });

      const data = new TextEncoder().encode(calldata);
      const instructionData = new Uint8Array([3, ...data]);

      const transaction = new Transaction();
      const keys = [
        { pubkey: publicKey, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: true, isWritable: false },
      ];
      const ix = new TransactionInstruction({
        programId: prog,
        keys: keys,
        data: instructionData,
      });
      transaction.add(ix);

      try {
        transaction.feePayer = publicKey;
        transaction.recentBlockhash = (await getConnection().getLatestBlockhash()).blockhash;
        const signature = await sendTransaction(transaction, getConnection());
        console.log('Transaction sent:', signature);
      } catch (error) {
        console.error('Order failed:', error);
        alert('Order failed.');
      }
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
      rc('div', { className: 'flex mt-4' }),
      rc('button', { className: `flex-1 py-2 ${this.state.tradeType === 'Buy' ? 'bg-green-600' : 'bg-gray-700'}`, onClick: () => this.handleTradeTypeChange('Buy') }, 'Buy'),
      rc('button', { className: `flex-1 py-2 ${this.state.tradeType === 'Sell' ? 'bg-red-600' : 'bg-gray-700'}`, onClick: () => this.handleTradeTypeChange('Sell') }, 'Sell'),
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
          rc('div', { className: 'flex justify-between text-sm' }),
          rc('span', { className: 'text-gray-400' }, 'Total:'),
          rc('span', { className: 'font-mono' }, `${total.toFixed(2)} USDC`)
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
    const addr = this.props.address.toString();
    for (const [tick, dec] of Object.entries(tokens)) {
      try {
        const prefix = `${tick}-balance:${addr}`;
        const response = await fetch(`${TESTNET_INDEXER_URL}/api/get_latest_state?prefix=${prefix}`);
        const data = await response.json();
        const val = data.result;
        newState[tick] = val && val !== '0' ? (Number(val) / Math.pow(10, dec)).toString() : '0';
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
      solAddress: null,
      publicKey: null,
      walletLoading: false,
      sendTransaction: null,
      orderbook: null,
      lastBlock: null,
      trades: [],
      streamTrades: null,
    };
    this.ws = null;
    this.reconnectTimeout = null;
  }

  componentDidMount() {
    this.loadInitialMarketData();
    this.initializeWallet();
  }

  loadInitialMarketData = async () => {
    try {
      const response = await fetch(`${TESTNET_INDEXER_URL}/api/orderbook?base=BTC&quote=USDC`);
      const data = await response.json();
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

initializeWallet = async () => {
  const wallet = getAllWallets();
  console.log('initializeWallet called, wallet:', wallet);
  // alert('initializeWallet: ' + (wallet ? 'found' : 'not found'));
  if (!wallet) {
    this.setState({ walletLoading: false });
    return;
  }

  try {
    // Try different connect methods for different wallets
    let publicKey = null;
    if (wallet.isConnected && wallet.publicKey) {
      publicKey = wallet.publicKey;
    } else if (wallet.connect) {
      await wallet.connect();
      publicKey = wallet.publicKey;
    }
    
    if (publicKey) {
      this.setState({
        solAddress: publicKey.toString(),
        publicKey: publicKey,
        sendTransaction: wallet.signTransaction,
        walletLoading: false
      });
    } else {
      this.setState({ walletLoading: false });
    }
  } catch (error) {
    console.error('Error initializing wallet:', error);
    this.setState({ walletLoading: false });
  }
}

handleWalletLogin = async () => {
  const wallet = getAllWallets();
  console.log('handleWalletLogin called, wallet:', wallet);
  if (!wallet) {
    alert('Solana wallet not installed!');
    return;
  }

  try {
    let publicKey = null;
    if (wallet.isConnected && wallet.publicKey) {
      publicKey = wallet.publicKey;
    } else if (wallet.connect) {
      await wallet.connect();
      publicKey = wallet.publicKey;
    }
    
    if (publicKey) {
      this.setState({
        solAddress: publicKey.toString(),
        publicKey: publicKey,
        sendTransaction: wallet.signTransaction,
        walletLoading: false
      });
    }
  } catch (error) {
    console.error('Error logging in:', error);
  }
}

handleWalletLogout = async () => {
  const wallet = getAllWallets();
  if (wallet && wallet.disconnect) {
    try {
      await wallet.disconnect();
    } catch (e) {
      console.error('Error disconnecting:', e);
    }
  }
  this.setState({
    solAddress: null,
    publicKey: null,
    sendTransaction: null,
    walletLoading: false
  });
}

startStream = () => {
  if (this.ws) return;
  const wsUrl = TESTNET_INDEXER_URL.replace(/^http/, 'ws') + '/ws';
  console.log('🔌 Connecting to WebSocket:', wsUrl);
  this.ws = new WebSocket(wsUrl);

  this.ws.onopen = () => console.log('✅ WebSocket connected');

  this.ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      this.handleStreamOpen(payload);
    } catch (e) {
      console.error('WebSocket message error:', e);
    }
  };

  this.ws.onclose = () => {
    console.log('❌ WebSocket disconnected, reconnecting in 5s...');
    this.ws = null;
    setTimeout(() => this.startStream(), 5000);
  };

  this.ws.onerror = (error) => console.error('WebSocket error:', error);
};

handleStreamOpen = (payload) => {
    if (!payload) return;

    // 处理订单簿更新
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

    // 处理新交易：解析服务端广播的格式
    if (payload.type === 'trade' && payload.price !== undefined) {
      const trade = {
        price: payload.price,
        amount: payload.amount,
        timestamp: payload.timestamp,
        side: payload.side
      };

      this.setState(prev => ({
        trades: [trade, ...prev.trades].slice(0, 200),
        streamTrades: [trade]
      }));
      return;
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
        rc(Header, { walletState: this.state, handleWalletLogin: this.handleWalletLogin, handleWalletLogout: this.handleWalletLogout }),
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

    const orderPanelWithSigner = rc(OrderPanel, { publicKey: this.state.publicKey, sendTransaction: this.state.sendTransaction });
    const marketPanel = rc(MarketPanel, { orderbook: this.state.orderbook, trades: this.state.trades });
    const assetsPanel = rc(AssetsPanel, { address: this.state.publicKey });
    const toolPanel = rc(ToolPanel, null);

    if (this.state.screenWidth < 960) {
      return commonLayout(
        rc('div', { className: 'space-y-4' }, mainContent, orderPanelWithSigner, marketPanel, assetsPanel, toolPanel),
        null,
        null
      );
    }

    if (this.state.screenWidth < 1400) {
      return commonLayout(
        mainContent,
        rc('div', { className: 'space-y-4' }, orderPanelWithSigner, marketPanel),
        rc('div', { className: 'space-y-4' }, assetsPanel, toolPanel)
      );
    }

    return rc('div', { className: 'app' },
      rc(Header, { walletState: this.state, handleWalletLogin: this.handleWalletLogin, handleWalletLogout: this.handleWalletLogout }),
      rc('main', { className: 'p-4' },
        rc('div', { className: 'flex gap-4' },
          rc('div', { className: 'flex-grow space-y-4' },
            rc(InfoPanel, null),
            rc(ChartPanel, {
              streamTrades: this.state.streamTrades,
            }),
            rc(AssetsPanel, { address: this.state.publicKey })
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