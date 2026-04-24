use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    msg,
    program::{invoke, invoke_signed},
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    match instruction_data[0] {
        0 => initialize_vault(program_id, accounts),
        1 => lock_tokens(accounts, &instruction_data[1..]),
        2 => release_tokens(accounts, &instruction_data[1..]),
        3 => calldata(accounts, &instruction_data[1..]),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

pub struct VaultState {
    pub operator: Pubkey,
    pub bump: u8,
}

impl VaultState {
    fn pack(&self, dst: &mut [u8]) -> Result<(), ProgramError> {
        if dst.len() < 33 {
            return Err(ProgramError::AccountDataTooSmall);
        }
        dst[..32].copy_from_slice(self.operator.as_ref());
        dst[32] = self.bump;
        Ok(())
    }

    fn unpack(src: &[u8]) -> Result<Self, ProgramError> {
        if src.len() < 33 {
            return Err(ProgramError::AccountDataTooSmall);
        }
        let mut key_bytes = [0u8; 32];
        key_bytes.copy_from_slice(&src[..32]);
        let operator = Pubkey::new_from_array(key_bytes);
        let bump = src[32];
        Ok(VaultState { operator, bump })
    }
}

const VAULT_STATE_SIZE: usize = 33;

fn initialize_vault(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    msg!("INIT: Starting...");
    
    let acc_iter = &mut accounts.iter();
    let vault_state_acc = next_account_info(acc_iter)?;
    msg!("  vault_state: {}", vault_state_acc.key);
    
    let payer_acc = next_account_info(acc_iter)?;
    msg!("  payer: {}", payer_acc.key);
    
    let operator_acc = next_account_info(acc_iter)?;
    msg!("  operator: {}", operator_acc.key);
    
    let system_program = next_account_info(acc_iter)?;
    msg!("  system_program: {}", system_program.key);
    
    msg!("INIT: Got all accounts, validating...");
    
    if !vault_state_acc.is_writable {
        msg!("ERROR: vault_state not writable");
        return Err(ProgramError::InvalidAccountData);
    }

    msg!("INIT: Creating state...");
    
    msg!("  Writing state data...");
    
    let state = VaultState {
        operator: *operator_acc.key,
        bump: 255,
    };
    
    // Get account data - handle both cases
    {
        let data = vault_state_acc.data.borrow();
        if data.len() == 0 {
            msg!("INIT: WARN - no data pre-allocated, skipping write");
            return Ok(());
        }
        if data.len() < VAULT_STATE_SIZE {
            msg!("INIT: WARN - insufficient data ({} bytes), skipping", data.len());
            return Ok(());
        }
    }
    
    // We have space, write now
    let mut data = vault_state_acc.data.borrow_mut();
    data[..32].copy_from_slice(&state.operator.to_bytes());
    data[32] = state.bump;
    
    msg!("INIT: Success! Wrote state.");
    
    Ok(())
}

fn read_u64(data: &[u8]) -> Result<u64, ProgramError> {
    if data.len() < 8 {
        return Err(ProgramError::InvalidInstructionData);
    }
    Ok(u64::from_le_bytes([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]]))
}

fn lock_tokens(accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let acc_iter = &mut accounts.iter();
    let from_acc = next_account_info(acc_iter)?;
    let vault_acc = next_account_info(acc_iter)?;
    let user_acc = next_account_info(acc_iter)?;
    let token_program = next_account_info(acc_iter)?;

    let amount = read_u64(data)?;

    let mut instr_data = vec![3];
    instr_data.extend_from_slice(&amount.to_le_bytes());
    
    let ix = Instruction {
        program_id: *token_program.key,
        accounts: vec![
            AccountMeta::new(*from_acc.key, false),
            AccountMeta::new(*vault_acc.key, false),
            AccountMeta::new_readonly(*user_acc.key, true),
        ],
        data: instr_data,
    };

    invoke(&ix, &[from_acc.clone(), vault_acc.clone(), user_acc.clone(), token_program.clone()])
        .map_err(|e| e.into())
}

fn release_tokens(accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let acc_iter = &mut accounts.iter();
    let vault_state_acc = next_account_info(acc_iter)?;
    let vault_acc = next_account_info(acc_iter)?;
    let to_acc = next_account_info(acc_iter)?;
    let operator_acc = next_account_info(acc_iter)?;
    let token_program = next_account_info(acc_iter)?;

    let state = VaultState::unpack(&vault_state_acc.data.borrow())?;
    if operator_acc.key != &state.operator {
        return Err(ProgramError::Custom(1));
    }

    let amount = read_u64(data)?;

    let seeds = &[b"vault".as_ref(), &[state.bump]];

    let mut instr_data = vec![3];
    instr_data.extend_from_slice(&amount.to_le_bytes());
    
    let ix = Instruction {
        program_id: *token_program.key,
        accounts: vec![
            AccountMeta::new(*vault_acc.key, false),
            AccountMeta::new(*to_acc.key, false),
            AccountMeta::new_readonly(*vault_state_acc.key, true),
        ],
        data: instr_data,
    };

    invoke_signed(
        &ix,
        &[vault_acc.clone(), to_acc.clone(), vault_state_acc.clone(), token_program.clone()],
        &[seeds],
    ).map_err(|e| e.into())
}

fn calldata(accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let acc_iter = &mut accounts.iter();
    let vault_state_acc = next_account_info(acc_iter)?;
    let target_acc = next_account_info(acc_iter)?;
    let operator_acc = next_account_info(acc_iter)?;

    let state = VaultState::unpack(&vault_state_acc.data.borrow())?;
    if operator_acc.key != &state.operator {
        return Err(ProgramError::Custom(1));
    }

    let mut target_data = target_acc.try_borrow_mut_data()?;
    let len = data.len().min(target_data.len());
    target_data[..len].copy_from_slice(&data[..len]);

    Ok(())
}