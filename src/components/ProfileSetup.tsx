import { useState, useEffect } from "react";
import { doc, setDoc, getDoc } from "firebase/firestore";
import { db } from "../firebase/config";
import toast from "react-hot-toast";

// You can use any SVG icon or emoji for a gamer vibe
const GamerIcon = () => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="12" fill="#222" />
    <path d="M7 15l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m4-2h.01" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="17" cy="13" r="1.5" fill="#fff"/>
  </svg>
);

const ProfileSetup: React.FC<{ user: any; onComplete: () => void }> = ({ user, onComplete }) => {
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Load profile on mount
  useEffect(() => {
    const fetchProfile = async () => {
      const docSnap = await getDoc(doc(db, "users", user.uid));
      if (docSnap.exists()) {
        const data = docSnap.data();
        setDisplayName(data.displayName || "");
        setPhone(data.phone || "");
      }
    };
    fetchProfile();
  }, [user.uid]);

  const handleSave = async () => {
    if (!displayName.trim() || !phone.trim()) {
      toast.error("Please fill in all fields.");
      return;
    }
    setLoading(true);
    await setDoc(doc(db, "users", user.uid), {
      displayName,
      phone,
      email: user.email,
    }, { merge: true });
    setLoading(false);
    toast.success("Profile updated!");
    setEditMode(false);
    onComplete();
  };

  return (
    <div className="max-w-lg mx-auto mt-12 bg-gradient-to-br from-gray-900 via-blue-900 to-indigo-900 rounded-2xl shadow-2xl p-8 flex flex-col items-center border border-blue-700">
      {/* Gamer Avatar */}
      <div className="relative mb-4">
        <div className="w-28 h-28 rounded-full border-4 border-blue-500 shadow-lg flex items-center justify-center bg-gradient-to-br from-blue-800 to-indigo-800">
          <GamerIcon />
          <span className="absolute bottom-2 right-2 bg-blue-600 text-white rounded-full px-3 py-1 text-lg font-bold shadow-lg border-2 border-white">
            {displayName ? displayName[0].toUpperCase() : user.email[0].toUpperCase()}
          </span>
        </div>
      </div>
      {/* Email (read-only) */}
      <div className="mb-6 text-center">
        <div className="text-2xl font-extrabold text-white drop-shadow">{displayName || "Your Name"}</div>
        <div className="text-blue-200">{user.email}</div>
      </div>
      {/* View or Edit Mode */}
      {!editMode ? (
        <>
          <div className="w-full mb-4">
            <label className="block mb-1 font-medium text-blue-200">Display Name</label>
            <div className="w-full border border-blue-700 rounded px-3 py-2 bg-blue-950 text-white">{displayName}</div>
          </div>
          <div className="w-full mb-6">
            <label className="block mb-1 font-medium text-blue-200">Phone Number</label>
            <div className="w-full border border-blue-700 rounded px-3 py-2 bg-blue-950 text-white">{phone}</div>
          </div>
          <button
            onClick={() => setEditMode(true)}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition mb-2 shadow"
          >
            Edit Profile
          </button>
        </>
      ) : (
        <>
          <div className="w-full mb-4">
            <label className="block mb-1 font-medium text-blue-200">Display Name</label>
            <input
              type="text"
              className="w-full border border-blue-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-blue-950 text-white"
              placeholder="Display Name"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
            />
          </div>
          <div className="w-full mb-6">
            <label className="block mb-1 font-medium text-blue-200">Phone Number</label>
            <input
              type="text"
              className="w-full border border-blue-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-blue-950 text-white"
              placeholder="Phone Number"
              value={phone}
              onChange={e => setPhone(e.target.value)}
            />
          </div>
          <div className="flex w-full gap-2">
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition mb-2 shadow"
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>
            <button
              onClick={() => setEditMode(false)}
              disabled={loading}
              className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg font-semibold hover:bg-gray-400 transition mb-2"
            >
              Cancel
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ProfileSetup;