#!/bin/bash

cd /mnt/c/Repositories/solana_indexer

tmux new-window -d
tmux new-window -d
tmux new-window -d
tmux new-window -d
tmux rename-window -t :1 "cmd"
tmux rename-window -t :2 "server"
tmux rename-window -t :3 "indexer"
tmux rename-window -t :4 "validator"

# Tab 4: validator
tmux send-keys -t :4 "cd ~ && rm -rf test-ledger/ && solana-test-validator" Enter

# Tab 3: indexer
tmux send-keys -t :3 "cd /mnt/c/Repositories/solana_indexer && sleep 10 && python indexer.py" Enter

# Tab 2: server
tmux send-keys -t :2 "cd /mnt/c/Repositories/solana_indexer && python server.py" Enter


# Tab 1
tmux select-window -t :1

# tmux send-keys -t :1 "cd /mnt/c/Repositories/solana_indexer && sleep 3 && cargo build-sbf && solana program deploy target/deploy/token_locker.so --url localhost && python test_rpc_init.py && python test_rpc_mint.py && python test_rpc_transfer.py" Enter
tmux send-keys -t :1 "cd /mnt/c/Repositories/solana_indexer && sleep 3 && solana program deploy target/deploy/token_locker.so --url localhost && sleep 15 && python test_rpc_init.py && python test_rpc_mint.py && python test_rpc_transfer.py && python test_rpc_orders.py" Enter
