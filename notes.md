# Solana Token Locker - Project Notes

This document provides a guide to the Solana Token Locker project, including its core concepts, architecture, and step-by-step usage instructions.

## 1. Core Concepts

### Mint vs. Token Account (ATA)
*   **Mint Address**: The "Template" or "Identity" of a token (e.g., USDT, SOL-Wrapped). It defines decimals and total supply but doesn't hold balances.
*   **Token Account (ATA)**: The "Wallet" for a specific token. An **Associated Token Account (ATA)** is a deterministic address derived from your Wallet Address + the Mint Address.
    *   *Analogy*: Mint is the currency type (USD), Token Account is your bank account for that currency.

### Vault & PDA (Program Derived Address)
*   **Program ID**: The address of the deployed smart contract (`8ZTKLtRRoji4AwAmYwguNkC1VgJszD1rdASZhxSbRLXA`).
*   **Vault State (PDA)**: A Program Derived Address (`Bg8XQy77nVpZpwFcQuB66TkrP6Nk3tDt2Eoy9PawkEko`). This is a "virtual" account controlled by the program. It has no private key; only the program can sign for it using specific "seeds" (`"vault"`).
*   **Vault Token Account**: A Token Account owned by the **PDA**. This is where tokens are physically stored while locked.

---

## 2. Architecture Flow

1.  **Initialize**: Create the PDA and set up the operator.
2.  **Lock**: User transfers tokens from their **Source ATA** to the **Vault Token Account**.
3.  **Release**: The Program verifies the operator, then uses PDA seeds to sign a transfer from the **Vault Token Account** back to a **Destination ATA**.

---

## 3. Usage Guide

### Step 0: Environment Setup
Ensure a local validator is running:
```bash
solana-test-validator
```

### Step 1: Initialize the Vault
This creates the PDA on-chain and sets the operator (your local keypair).
```bash
python3 init_vault.py
```
**Output**: Note the `Vault PDA` address.

### Step 2: Create a Vault Token Account
The Vault needs a place to hold the specific tokens you want to lock.
```bash
# owner is the Vault PDA from Step 1
spl-token create-account <MINT_ADDRESS> --owner <VAULT_PDA> --url http://localhost:8899 --fee-payer ~/.config/solana/id.json
```
**Output**: This is your `<VAULT_TOKEN_ACCOUNT>`.

### Step 3: Lock Tokens
Transfer tokens from your wallet to the vault.
```bash
python3 lock_tokens.py <SOURCE_ATA> <VAULT_TOKEN_ACCOUNT> <AMOUNT_IN_LAMPORTS>
```

### Step 4: Release Tokens
The operator triggers the program to send tokens back.
```bash
python3 release_tokens.py <VAULT_PDA> <VAULT_TOKEN_ACCOUNT> <DESTINATION_ATA> <AMOUNT_IN_LAMPORTS>
```

---

## 4. Useful Commands

| Action | Command |
| :--- | :--- |
| **Check Token Balance** | `spl-token balance --address <ACCOUNT_ADDR>` |
| **Check All My Tokens** | `spl-token accounts` |
| **Identify Mint from ATA** | `spl-token display <ATA_ADDR>` |
| **Check PDA Info** | `solana account <PDA_ADDR>` |
| **Start Indexer** | `python3 indexer.py` |

---

## 5. Debug History & Fixes
*   **Token Program ID**: Fixed an incorrect 33-byte hardcoded string. Always use `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`.
*   **Account Ordering**: In Solana, the order of accounts in an instruction must exactly match what the Rust program expects.
    *   *Lock*: `[source, vault, user, token_program]`
    *   *Release*: `[vault_state, vault, destination, operator, token_program]`
*   **PDA Logic**: Updated the Rust program to automatically create the PDA account if it doesn't exist during initialization.
