use crate::errors::EscrowError::InvalidInstruction;
use solana_program::program_error::ProgramError;
use solana_program::msg;
use borsh::{BorshDeserialize};

pub enum EscrowInstruction {
    /// Accounts expected:
    ///
    /// 0. `[signer]` The account of the person initializing the escrow
    /// 1. `[writable]` Temporary token account that should be created prior to this instruction and owned by the initializer
    /// 2. `[]` The initializer's token account for the token they will receive should the trade go through
    /// 3. `[writable]` The escrow account, it will hold all necessary info about the trade.
    /// 4. `[]` The rent sysvar
    /// 5. `[]` The token src
    InitEscrow {
        /// The amount party A expects to receive of token Y
        amount: u64,
    },

    /// Accepts a trade
    ///
    ///
    /// Accounts expected:
    ///
    /// 0. `[signer]` The account of the person taking the trade
    /// 1. `[writable]` The taker's token account for the token they send
    /// 2. `[writable]` The taker's token account for the token they will receive should the trade go through
    /// 3. `[writable]` The PDA's temp token account to get tokens from and eventually close
    /// 4. `[writable]` The initializer's main account to send their rent fees to
    /// 5. `[writable]` The initializer's token account that will receive tokens
    /// 6. `[writable]` The escrow account holding the escrow info
    /// 7. `[]` The token program
    /// 8. `[]` The PDA account
    Exchange {
        /// The amount party B expects to receive of token X
        amount: u64,
    },
}

#[derive(BorshDeserialize, Debug)]
struct Payload {
    tag: u8,
    amount: u64,
}

impl EscrowInstruction {
    pub fn unpack(input: &[u8]) -> Result<Self, ProgramError> {
        msg!("splitting");
        msg!("{:?}",&input);
        msg!("===============================================================");
        let payload : Payload = Payload::try_from_slice(input).unwrap();
        Ok(match payload.tag {
            0 => {msg!("{}",payload.amount); Self::InitEscrow { amount: payload.amount }},
            1 => Self::Exchange {
                amount : payload.amount,
            },
            _ => return Err(InvalidInstruction.into()),
        })
    }
}
