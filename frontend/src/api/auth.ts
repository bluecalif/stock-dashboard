import apiClient from "./client";
import type {
  SignupRequest,
  LoginRequest,
  TokenResponse,
  User,
} from "../types/auth";

export async function signup(data: SignupRequest): Promise<User> {
  const res = await apiClient.post<User>("/v1/auth/signup", data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/v1/auth/login", data);
  return res.data;
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/v1/auth/refresh", {
    refresh_token: refreshToken,
  });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await apiClient.get<User>("/v1/auth/me");
  return res.data;
}

export async function withdraw(password: string): Promise<void> {
  await apiClient.delete("/v1/auth/me", { data: { password } });
}
