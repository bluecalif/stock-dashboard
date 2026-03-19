import { create } from "zustand";
import { getProfile, submitIceBreaking } from "../api/profile";
import type { IceBreakingRequest, ProfileResponse } from "../types/profile";

interface ProfileState {
  profile: ProfileResponse | null;
  isLoading: boolean;

  loadProfile: () => Promise<void>;
  submitIceBreaking: (answers: IceBreakingRequest) => Promise<void>;
  clear: () => void;
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,

  loadProfile: async () => {
    set({ isLoading: true });
    try {
      const profile = await getProfile();
      set({ profile });
    } catch {
      // 프로필 로드 실패 시 무시 (로그인 안 된 상태 등)
    } finally {
      set({ isLoading: false });
    }
  },

  submitIceBreaking: async (answers: IceBreakingRequest) => {
    const profile = await submitIceBreaking(answers);
    set({ profile });
  },

  clear: () => set({ profile: null }),
}));
