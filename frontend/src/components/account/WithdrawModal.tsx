import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { AxiosError } from "axios";

interface WithdrawModalProps {
  onClose: () => void;
}

export default function WithdrawModal({ onClose }: WithdrawModalProps) {
  const { withdraw } = useAuthStore();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError("비밀번호를 입력하세요.");
      return;
    }
    setError("");
    setIsLoading(true);
    try {
      await withdraw(password);
      navigate("/login");
    } catch (err) {
      if (err instanceof AxiosError && err.response?.status === 401) {
        setError("비밀번호가 일치하지 않습니다.");
      } else {
        setError("탈퇴 처리 중 오류가 발생했습니다.");
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-2">회원 탈퇴</h2>
        <p className="text-sm text-gray-500 mb-4">
          탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다.
          <br />
          계속하려면 비밀번호를 입력하세요.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent mb-4"
            autoFocus
          />
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {isLoading ? "처리 중..." : "탈퇴하기"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
