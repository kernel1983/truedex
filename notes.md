# Solana Token Locker - Project Notes

This document provides a guide to the Solana Token Locker project, including its core concepts, architecture, and step-by-step usage instructions.


---

## 4. Deploy Solana Program

### Build the program
```bash
cargo build-sbf
```

### Deploy to devnet/localnet
```bash
solana program deploy target/deploy/token_locker.so --url localhost
solana program deploy target/deploy/token_locker.so --url devnet
```

### Deploy to mainnet
```bash
solana program deploy target/deploy/token_locker.so --url mainnet
```

### Update program
```bash
solana program deploy target/deploy/token_locker.so --program-id 2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih --url localhost
```

## 1. Core Concepts

### Mint vs. Token Account (ATA)
*   **Mint Address**: The "Identity" of a token (e.g., USDT). Defines decimals and supply.
*   **Token Account (ATA)**: The "Wallet" for a specific token.
    *   *Analogy*: Mint is the currency (USD), Token Account is your wallet.

### Vault Architecture
*   **Program ID**: The address of the smart contract (`2AxT8e7Jq2vgoPNo8uT1Go3Huifdx5XWm4CntKz4aiih`).
*   **Vault (PDA)**: The Program Derived Address. It is the "Manager" of the system. It stores who the operator is and has the power to sign transfers.
*   **Vault Token Account**: A Token Account physically owned by the **Vault (PDA)**. This is where tokens are stored while locked.

---

## 2. Architecture Flow

1.  **Initialize**: Setup the **Vault (PDA)** and set the operator.
2.  **Lock**: User transfers tokens from their **Source ATA** to the **Vault Token Account**.
3.  **Release**: The Program checks operator permissions, then uses the **Vault (PDA)** seeds to sign a transfer from the **Vault Token Account** to a **Destination ATA**.

---

## 3. Usage Guide

### Step 1: Initialize the Vault
```bash
python3 init_vault.py
```
**Output**: Note the `Vault (PDA)` address.

### Step 2: Create the Vault Token Account
```bash
# owner is the Vault (PDA) from Step 1
spl-token create-account <MINT_ADDRESS> --owner <VAULT_PDA_ADDRESS> --url http://localhost:8899
```
**Output**: This is your `<VAULT_TOKEN_ACCOUNT>`.

### Step 3: Lock Tokens
```bash
python3 lock_tokens.py <SOURCE_ATA> <VAULT_TOKEN_ACCOUNT> <AMOUNT>
```

### Step 4: Release Tokens
```bash
python3 release_tokens.py <VAULT_PDA_ADDRESS> <VAULT_TOKEN_ACCOUNT> <DESTINATION_ATA> <AMOUNT>
```


---

## 5. Debugging & Indexer
*   **Indexer**: `python3 indexer.py` monitors the program and parses `lock`/`release` events, showing the sender and mint involved.
*   **Check Balance**: `spl-token balance --address <ATA_ADDRESS>`
