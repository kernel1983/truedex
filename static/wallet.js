import * as ethers from 'https://cdn.jsdelivr.net/npm/ethers@6.15.0/+esm';

const ZEN_ADDR = '0x00000000000000000000000000000000007a656e'; // hex of 'zen'
// const INDEXER_URL = 'https://mainnet.zentra.dev';
const RPC_URL = 'http://127.0.0.1:8545';
// const RPC_URL = 'https://mainnet.base.org';
const INDEXER_URL = RPC_URL; // this should be the indexer address, but in the test it point to rpc url
const CHAIN_ID = 31337n; // Anvil

// --- DOM ELEMENTS ---
const connectButton = document.getElementById('connectButton');
const walletConnectDiv = document.getElementById('walletConnect');
const walletInfoDiv = document.getElementById('walletInfo');
const userAddressSpan = document.getElementById('userAddress');
const networkNameSpan = document.getElementById('networkName');
const networkSwitchPanel = document.getElementById('networkSwitchPanel');
const switchNetworkButton = document.getElementById('switchNetworkButton');

const customJsonButton = document.getElementById('customJsonButton');
const transferResult = document.getElementById('transferResult');
const balanceList = document.getElementById('balance-list');


let provider;
let signer;
let userAddress;


const showMessage = (message, type) => {
  console.log(`[${type}] ${message}`);
  if (transferResult) {
    const color = type === 'error' ? 'text-red-500' : 'text-green-500';
    transferResult.innerHTML = `<span class="${color} font-bold">${message}</span>`;
  }
};

async function fetch_decimal(token) {
  try {
    const prefix = `base-${token}-decimal`;
    const url = `${INDEXER_URL}/api/get_latest_state?prefix=${encodeURIComponent(prefix)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return parseInt(data.result, 10);
  } catch (e) {
    console.error("Error fetching decimal:", e);
    return 18; // Default to 18 if failed
  }
}

async function fetch_token(token, address) {
  try {
    const prefix = `base-${token}-balance:${address.toLowerCase()}`;
    const url = `${INDEXER_URL}/api/get_latest_state?prefix=${encodeURIComponent(prefix)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data_json = await response.text();

    const data = JSON.parse(data_json, (key, value, { source }) =>
      Number.isInteger(value) && !Number.isSafeInteger(value)
        ? BigInt(source)
        : value
    );

    let formatted_balance = '0';
    if (data.result) {
      const balance_big = BigInt(data.result);
      const decimal = await fetch_decimal(token);
      formatted_balance = ethers.formatUnits(balance_big, decimal);
    }

    const div = document.createElement('div');
    div.className = "flex justify-between";
    div.innerHTML = `<span>${token}</span> <span class="font-mono font-bold">${formatted_balance}</span>`;
    balanceList.appendChild(div);
  } catch (err) {
    console.error(`Fetch error for ${token}:`, err);
    // Still show the token with 0 balance on error
    const div = document.createElement('div');
    div.className = "flex justify-between";
    div.innerHTML = `<span>${token}</span> <span class="font-mono font-bold text-gray-400">Error</span>`;
    balanceList.appendChild(div);
  }
}

async function fetch_tx(txhash) {
  try {
    const url = `${INDEXER_URL}/api/events?txhash=${encodeURIComponent(txhash)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const data = await response.json();
    console.log('response data:', data);

    // Check if events were found
    if (!data || (Array.isArray(data) && data.length === 0)) {
      console.log('No events found yet, retrying...');
      setTimeout(() => fetch_tx(txhash), 2000);
      return;
    }

    showMessage(`Transaction successful! <br> <a href="https://basescan.org/tx/0x${txhash}" target="_blank" class="underline">View on Explorer</a>`, 'success');

  } catch (err) {
    console.error('Fetch error:', err);
    showMessage(`Error checking transaction status: ${err.message}`, 'error');
  }
}

const checkNetwork = async () => {
  if (!provider) return false;
  const network = await provider.getNetwork();
  if (network.chainId !== CHAIN_ID) {
    if (networkSwitchPanel) networkSwitchPanel.style.display = 'flex';
    networkNameSpan.textContent = `Unsupported (${network.name})`;
    return false;
  } else {
    if (networkSwitchPanel) networkSwitchPanel.style.display = 'none';
    networkNameSpan.textContent = "Local Zentra Playground";
    return true;
  }
};

const switchNetwork = async () => {
  if (!window.ethereum) return;
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: `0x${CHAIN_ID.toString(16)}` }],
    });
  } catch (switchError) {
    if (switchError.code === 4902) {
      try {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: `0x${CHAIN_ID.toString(16)}`,
            chainName: 'Local Playground',
            nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
            rpcUrls: [RPC_URL],
            // blockExplorerUrls: ['https://basescan.org']
          }]
        });
      } catch (addError) {
        console.error("Could not add network", addError);
      }
    }
  }
};

const connectWallet = async () => {
  if (typeof window.ethereum === 'undefined') {
    return showMessage('MetaMask is not installed!', 'error');
  }

  try {
    provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    signer = await provider.getSigner();
    userAddress = await signer.getAddress();

    walletInfoDiv.style.display = 'block';
    walletConnectDiv.style.display = 'none';
    userAddressSpan.textContent = userAddress;

    if (!await checkNetwork()) return;

    // Fetch balances
    if (balanceList) {
      balanceList.innerHTML = ''; // Clear previous
      // await fetch_token('BTC', userAddress);
      await fetch_token('USDC', userAddress);
      // await fetch_token('ZENT', userAddress);
    }

  } catch (error) {
    console.error(error);
    showMessage(`Error connecting wallet: ${error.message}`, 'error');
  }
};

// const handleTransfer = async () => {
//   const tick = document.getElementById('transfer_tick').value;
//   const to = document.getElementById('transfer_to').value;
//   const amountStr = document.getElementById('transfer_amount').value;

//   if (!tick || !to || !amountStr) {
//     return showMessage('Please fill in all fields', 'error');
//   }

//   try {
//     transferButton.disabled = true;
//     transferButton.innerText = "Processing...";

//     const decimal = await fetch_decimal(tick);
//     const amount = ethers.parseUnits(amountStr, decimal);

//     const calldata = {
//       "p": "zen",
//       "f": "token_transfer",
//       "a": [tick, to, amount.toString()],
//     };

//     const tx = await signer.sendTransaction({
//       to: ZEN_ADDR,
//       data: ethers.hexlify(new TextEncoder().encode(JSON.stringify(calldata)))
//     });

//     showMessage(`Transaction sent: ${tx.hash}`, 'success');
//     fetch_tx(tx.hash.slice(2));

//   } catch (error) {
//     console.error(error);
//     showMessage(`Transfer failed: ${error.message}`, 'error');
//   } finally {
//     transferButton.disabled = false;
//     transferButton.innerText = "Transfer Token";
//   }
// };

const handleCustomJson = async () => {
  const jsonStr = document.getElementById('custom_json').value;
  if (!jsonStr) return showMessage('Please enter JSON', 'error');

  try {
    customJsonButton.disabled = true;
    customJsonButton.innerText = "Processing...";

    // Validate JSON
    JSON.parse(jsonStr);

    const tx = await signer.sendTransaction({
      to: ZEN_ADDR,
      data: ethers.hexlify(new TextEncoder().encode(jsonStr))
    });

    showMessage(`Transaction sent: ${tx.hash}`, 'success');
    fetch_tx(tx.hash.slice(2));

  } catch (error) {
    console.error(error);
    showMessage(`Failed: ${error.message}`, 'error');
  } finally {
    customJsonButton.disabled = false;
    customJsonButton.innerText = "Send Custom Call";
  }
};

const init = async () => {
  if (connectButton) connectButton.addEventListener('click', connectWallet);
  if (switchNetworkButton) switchNetworkButton.addEventListener('click', switchNetwork);

  // if (tabTransfer) tabTransfer.addEventListener('click', () => switchTab('transfer'));
  // if (tabCustom) tabCustom.addEventListener('click', () => switchTab('custom'));
  // if (transferButton) transferButton.addEventListener('click', handleTransfer);
  if (customJsonButton) customJsonButton.addEventListener('click', handleCustomJson);

  if (window.ethereum) {
    window.ethereum.on('chainChanged', () => window.location.reload());
    window.ethereum.on('accountsChanged', () => window.location.reload());
    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
    if (accounts && accounts.length > 0) {
      await connectWallet();
    } else {
      walletConnectDiv.style.display = 'flex';
    }
  } else {
    walletConnectDiv.style.display = 'flex';
  }
};

document.addEventListener('DOMContentLoaded', init);
