import React, { useEffect, useState } from "react";
import { db } from "../firebase/config";
import { collection, getDocs, deleteDoc, doc } from "firebase/firestore";
import toast from "react-hot-toast";

const AdminPage: React.FC = () => {
  const [players, setPlayers] = useState<any[]>([]);
  const [games, setGames] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch all data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const usersSnap = await getDocs(collection(db, "users"));
      setPlayers(usersSnap.docs.map((doc) => ({ id: doc.id, ...doc.data() })));

      const gamesSnap = await getDocs(collection(db, "games"));
      setGames(gamesSnap.docs.map((doc) => ({ id: doc.id, ...doc.data() })));

      const txSnap = await getDocs(collection(db, "transactions"));
      setTransactions(txSnap.docs.map((doc) => ({ id: doc.id, ...doc.data() })));

      setLoading(false);
    };
    fetchData();
  }, []);

  // Delete player
  const handleDeletePlayer = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this player?")) {
      await deleteDoc(doc(db, "users", id));
      setPlayers(players.filter((p) => p.id !== id));
      toast.success("Player deleted");
    }
  };

  // Delete game
  const handleDeleteGame = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this game?")) {
      await deleteDoc(doc(db, "games", id));
      setGames(games.filter((g) => g.id !== id));
      toast.success("Game deleted");
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      {loading && <div>Loading...</div>}

      {/* Players */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Players</h2>
        <table className="w-full border mb-4">
          <thead>
            <tr>
              <th className="border px-2">UID</th>
              <th className="border px-2">Name</th>
              <th className="border px-2">Email</th>
              <th className="border px-2">Phone</th>
              <th className="border px-2">Status</th>
              <th className="border px-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {players.map((player) => (
              <tr key={player.id}>
                <td className="border px-2">{player.id}</td>
                <td className="border px-2">{player.displayName || "-"}</td>
                <td className="border px-2">{player.email || "-"}</td>
                <td className="border px-2">{player.phone || "-"}</td>
                <td className="border px-2">{player.status || "active"}</td>
                <td className="border px-2">
                  <button
                    className="bg-red-500 text-white px-2 py-1 rounded"
                    onClick={() => handleDeletePlayer(player.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Games */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Games</h2>
        <table className="w-full border mb-4">
          <thead>
            <tr>
              <th className="border px-2">ID</th>
              <th className="border px-2">Name</th>
              <th className="border px-2">Status</th>
              <th className="border px-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game) => (
              <tr key={game.id}>
                <td className="border px-2">{game.id}</td>
                <td className="border px-2">{game.name || "-"}</td>
                <td className="border px-2">{game.status || "-"}</td>
                <td className="border px-2">
                  <button
                    className="bg-red-500 text-white px-2 py-1 rounded"
                    onClick={() => handleDeleteGame(game.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Transactions */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Payment Transactions</h2>
        <table className="w-full border">
          <thead>
            <tr>
              <th className="border px-2">ID</th>
              <th className="border px-2">User</th>
              <th className="border px-2">Amount</th>
              <th className="border px-2">Status</th>
              <th className="border px-2">Type</th>
              <th className="border px-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr key={txn.id}>
                <td className="border px-2">{txn.id}</td>
                <td className="border px-2">{txn.userId || "-"}</td>
                <td className="border px-2">{txn.amount || "-"}</td>
                <td className="border px-2">{txn.status || "-"}</td>
                <td className="border px-2">{txn.type || "-"}</td>
                <td className="border px-2">{txn.createdAt ? new Date(txn.createdAt.seconds * 1000).toLocaleString() : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default AdminPage;