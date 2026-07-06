import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  setAccessToken: (token) => {
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("sprintflow_access", token);
      else localStorage.removeItem("sprintflow_access");
    }
    set({ accessToken: token });
  }
}));
