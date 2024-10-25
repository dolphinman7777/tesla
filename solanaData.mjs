import { Connection, clusterApiUrl, PublicKey, LAMPORTS_PER_SOL } from '@solana/web3.js';
import fetch from 'node-fetch';

async function fetchSolanaData(walletAddress) {
    const connection = new Connection(clusterApiUrl('mainnet-beta'), 'confirmed');

    try {
        // Validate wallet address format
        if (!walletAddress) {
            return { error: 'Wallet address is required' };
        }
        
        if (!isSolanaAddress(walletAddress)) {
            return { error: 'Invalid Solana address format' };
        }

        // Create public key from address
        const publicKey = new PublicKey(walletAddress);
        
        // Get SOL balance
        const balance = await connection.getBalance(publicKey);
        const solBalance = balance / LAMPORTS_PER_SOL;

        // Get current SOL/USD price
        const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd');
        const priceData = await response.json();
        const solToUsd = priceData.solana.usd;
        const usdBalance = solBalance * solToUsd;

        return {
            address: walletAddress,
            solBalance: solBalance.toFixed(4),
            usdBalance: usdBalance.toFixed(2),
            solPrice: solToUsd.toFixed(2)
        };
    } catch (error) {
        console.error('Error fetching Solana wallet data:', error);
        return { error: error.message };
    }
}

// Example usage:
const walletAddress = process.argv[2];

if (walletAddress) {
    fetchSolanaData(walletAddress)
        .then(result => {
            if (result.error) {
                console.log(`Error: ${result.error}`);
            } else {
                console.log(`Wallet: ${result.address}`);
                console.log(`Balance: ${result.solBalance} SOL ($${result.usdBalance})`);
                console.log(`SOL Price: $${result.solPrice}`);
            }
        })
        .catch(err => console.error('Error:', err));
} else {
    console.log('Please provide a wallet address as an argument');
}

function isSolanaAddress(text) {
    // Solana addresses are 44 characters long and Base58 encoded
    const base58Regex = /^[1-9A-HJ-NP-Za-km-z]{44}$/;
    return base58Regex.test(text);
}
