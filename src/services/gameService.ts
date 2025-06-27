import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  getDocs, 
  getDoc,
  onSnapshot,
  query,
  where,
  orderBy,
  Timestamp,
  arrayUnion,
  arrayRemove
} from 'firebase/firestore';
import { db } from '../firebase/config';
import { GameRoom, Player } from '../types/game';

// Helper function to handle Firestore errors
const handleFirestoreError = (error: any, operation: string) => {
  console.error(`Firestore ${operation} error:`, error);

  if (error.code === 'permission-denied') {
    throw new Error('You do not have permission to perform this action');
  } else if (error.code === 'network-request-failed') {
    throw new Error('Network error. Please check your connection and try again');
  } else if (error.code === 'unavailable') {
    throw new Error('Service temporarily unavailable. Please try again later');
  } else {
    throw new Error(`Failed to ${operation}. Please try again`);
  }
};
import { 
  increment,
  serverTimestamp,
} from 'firebase/firestore';
import { GameRoom, Player, BingoCard, Payment } from '../types/game';
import { v4 as uuidv4 } from 'uuid';

const BINGO_RANGES = {
  B: { min: 1, max: 15 },
  I: { min: 16, max: 30 },
  N: { min: 31, max: 45 },
  G: { min: 46, max: 60 },
  O: { min: 61, max: 75 }
};

class GameService {
  // Game Room Management
  async createGameRoom(
    hostId: string, 
    roomName: string, 
    maxPlayers: number, 
    entryFee: number,
    telegramBotEnabled: boolean = false,
    telegramChannelId?: string
  ): Promise<string> {
    try {
      // Validate input
      if (!roomName || !hostId) {
        throw new Error('Game name and host ID are required');
      }

      if (entryFee < 0 || entryFee > 10000) {
        throw new Error('Entry fee must be between 0 and 10,000 ETB');
      }

      if (maxPlayers < 2 || maxPlayers > 100) {
        throw new Error('Max players must be between 2 and 100');
      }

      const gameRoom: Omit<GameRoom, 'id'> = {
        name: roomName,
        hostId,
        players: [],
        maxPlayers,
        entryFee,
        prizePool: 0,
        status: 'waiting',
        calledNumbers: [],
        currentCall: null,
        createdAt: serverTimestamp(),
        telegramBotEnabled,
        ...(telegramBotEnabled && telegramChannelId ? { telegramChannelId } : {})
      };
  
      const docRef = await addDoc(collection(db, 'gameRooms'), {
        ...gameRoom
      });
  
      return docRef.id;
    } catch (error) {
      handleFirestoreError(error, 'create game room');
      throw error;
    }
  }

  async joinGameRoom(gameRoomId: string, player: Player): Promise<void> {
    try {
      const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
      await updateDoc(gameRoomRef, {
        players: arrayUnion(player),
        prizePool: increment(0) 
  
      });
    } catch (error) {
      handleFirestoreError(error, 'join game room');
      throw error;
    }
  }

  async leaveGameRoom(gameRoomId: string, playerId: string): Promise<void> {
    // Proper player removal should be handled server-side or with a transaction.
    // This is a placeholder and may not work as expected.
    // Consider fetching the document, removing the player from the array, and updating.
    try {
        // Fetch the game room document
        const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
        const gameRoomSnap = await getDoc(gameRoomRef);

        if (!gameRoomSnap.exists()) {
            throw new Error('Game room not found');
        }

        const gameRoomData = gameRoomSnap.data() as GameRoom;
        const updatedPlayers = gameRoomData.players.filter(player => player.id !== playerId);

        await updateDoc(gameRoomRef, {
            players: updatedPlayers
        });
    } catch (error) {
        handleFirestoreError(error, 'leave game room');
        throw error;
    }
  }

  async startGame(gameRoomId: string): Promise<void> {
    try {
      const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
      await updateDoc(gameRoomRef, {
        status : 'playing',
      });
  
      // Start auto-calling numbers after a 5 second countdown
      setTimeout(() => {
        this.startAutoCaller(gameRoomId);
      }, 5000);
    } catch (error) {
      handleFirestoreError(error, 'start game');
      throw error;
    }
  }

  private async startAutoCaller(gameRoomId: string): Promise<void> {
    const interval = setInterval(async () => {
      try {
        const result = await this.callNextNumber(gameRoomId);
        if (result === null) {
          clearInterval(interval); // Stop when all numbers are called
        }
      } catch (error) {
        console.error('Auto-caller error:', error);
        clearInterval(interval);
      }
    }, 5000); // Call every 5 seconds
  }

  async callNextNumber(gameRoomId: string): Promise<number | null> {
    try {
      const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
      const gameRoomSnap = await getDoc(gameRoomRef);
      if (!gameRoomSnap.exists()) return null;
  
      const data = gameRoomSnap.data() as GameRoom;
      const calledNumbers = data.calledNumbers || [];
  
      // Only pick from numbers not already called
      const availableNumbers = [];
      for (let i = 1; i <= 75; i++) {
        if (!calledNumbers.includes(i)) {
          availableNumbers.push(i);
        }
      }
  
      if (availableNumbers.length === 0) return null;
  
      const nextNumber = availableNumbers[Math.floor(Math.random() * availableNumbers.length)];
  
      await updateDoc(gameRoomRef, {
        calledNumbers: arrayUnion(nextNumber),
        currentCall: nextNumber
      });
  
      return nextNumber;
    } catch (error) {
      handleFirestoreError(error, 'call next number');
      return null;
    }
  }

  // Bingo Card Generation
  generateBingoCard(playerId: string): BingoCard {
    const card: BingoCard = {
      id: uuidv4(),
      playerId,
      B: [],
      I: [],
      N: [],
      G: [],
      O: []
    };

    Object.entries(BINGO_RANGES).forEach(([letter, range]) => {
      const numbers: number[] = [];
      while (numbers.length < 5) {
        const num = Math.floor(Math.random() * (range.max - range.min + 1)) + range.min;
        if (!numbers.includes(num)) {
          numbers.push(num);
        }
      }

      card[letter as keyof typeof BINGO_RANGES] = numbers.map((num, index) => ({
        number: letter === 'N' && index === 2 ? 0 : num, // Free space
        marked: letter === 'N' && index === 2, // Free space is pre-marked
        called: false
      }));
    });

    return card;
  }

  // Win Detection
  checkWin(card: BingoCard): { hasWon: boolean; pattern?: string; winType?: 'line' | 'fullhouse' | 'corners' | 'center_cross' } {
    const columns = ['B', 'I', 'N', 'G', 'O'] as const;

    // Check columns (vertical lines)
    for (let col of columns) {
      if (card[col].every(cell => cell.marked)) {
        return { hasWon: true, pattern: `${col} Column`, winType: 'line' };
      }
    }

    // Check rows (horizontal lines)
    for (let row = 0; row < 5; row++) {
      if (columns.every(col => card[col][row].marked)) {
        return { hasWon: true, pattern: `Row ${row + 1}`, winType: 'line' };
      }
    }

    // Check diagonals
    if (columns.every((col, index) => card[col][index].marked)) {
      return { hasWon: true, pattern: 'Diagonal (\\)', winType: 'line' };
    }

    if (columns.every((col, index) => card[col][4 - index].marked)) {
      return { hasWon: true, pattern: 'Diagonal (/)', winType: 'line' };
    }

    // Check four corners
    if (card.B[0].marked && card.O[0].marked && card.B[4].marked && card.O[4].marked) {
      return { hasWon: true, pattern: 'Four Corners', winType: 'corners' };
    }

    // Check center cross pattern
    const centerCross = [
      card.N[0].marked, card.N[1].marked, card.N[2].marked, card.N[3].marked, card.N[4].marked, // Middle column
      card.B[2].marked, card.I[2].marked, card.G[2].marked, card.O[2].marked // Middle row (excluding center)
    ].every(marked => marked);

    if (centerCross) {
      return { hasWon: true, pattern: 'Center Cross', winType: 'center_cross' };
    }

    // Check full house (all numbers marked)
    const allMarked = columns.every(col => card[col].every(cell => cell.marked));
    if (allMarked) {
      return { hasWon: true, pattern: 'Full House', winType: 'fullhouse' };
    }

    // Check blackout patterns (various patterns for different game modes)
    const edgePattern = this.checkEdgePattern(card);
    if (edgePattern) {
      return { hasWon: true, pattern: 'Edge Pattern', winType: 'line' };
    }

    return { hasWon: false };
  }

  private checkEdgePattern(card: BingoCard): boolean {
    const columns = ['B', 'I', 'N', 'G', 'O'] as const;
    const edges = [
      // Top row
      ...columns.map(col => card[col][0].marked),
      // Bottom row
      ...columns.map(col => card[col][4].marked),
      // Left column (excluding corners)
      card.B[1].marked, card.B[2].marked, card.B[3].marked,
      // Right column (excluding corners)
      card.O[1].marked, card.O[2].marked, card.O[3].marked
    ];

    return edges.every(marked => marked);
  }

  // Real-time subscriptions
  subscribeToGameRoom(gameRoomId: string, callback: (gameRoom: GameRoom) => void) {
    try {
      const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
      return onSnapshot(gameRoomRef, (doc) => {
        if (doc.exists()) {
          callback({ id: doc.id, ...doc.data() } as GameRoom);
        }
      });
    } catch (error) {
      handleFirestoreError(error, 'subscribe to game room');
      throw error;
    }
  }

  subscribeToGameRooms(callback: (gameRooms: GameRoom[]) => void) {
    try {
      const q = query(
        collection(db, 'gameRooms'),
        where('status', 'in', ['waiting', 'starting', 'playing']),
        orderBy('createdAt', 'desc')
      );
  
      return onSnapshot(q, (snapshot) => {
        const gameRooms = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        })) as GameRoom[];
        callback(gameRooms);
      });
    } catch (error) {
      handleFirestoreError(error, 'subscribe to game rooms');
      throw error;
    }
  }

  // Payment Management
  async recordPayment(payment: Omit<Payment, 'id'>): Promise<string> {
    try {
      const docRef = await addDoc(collection(db, 'payments'), {
        ...payment,
        createdAt: serverTimestamp()
      });
      return docRef.id;
    } catch (error) {
      handleFirestoreError(error, 'record payment');
      throw error;
    }
  }

  async updatePaymentStatus(paymentId: string, status: Payment['status']): Promise<void> {
    try {
      const paymentRef = doc(db, 'payments', paymentId);
      await updateDoc(paymentRef, {
        status,
        completedAt: status === 'completed' ? serverTimestamp() : null
      });
    } catch (error) {
      handleFirestoreError(error, 'update payment status');
      throw error;
    }
  }

  async updatePrizePool(gameRoomId: string, amount: number): Promise<void> {
    try{
      const gameRoomRef = doc(db, 'gameRooms', gameRoomId);
      await updateDoc(gameRoomRef, {
        prizePool: increment(amount)
      });
    } catch (error) {
      handleFirestoreError(error, 'update prize pool');
      throw error;
    }
  }
}

export const gameService = new GameService();