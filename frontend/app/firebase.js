import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAyd19VnaSJd6YE1_22OWzQxqM1Ye2-NT8",
  authDomain: "personal-ai-platform.firebaseapp.com",
  projectId: "personal-ai-platform",
  storageBucket: "personal-ai-platform.firebasestorage.app",
  messagingSenderId: "39248169495",
  appId: "1:39248169495:web:a07b597c2b7e25480fea52"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);