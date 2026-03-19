import { useState } from "react";
import { useProfileStore } from "../../store/profileStore";
import type { IceBreakingRequest } from "../../types/profile";

const EXPERIENCE_OPTIONS = [
  { value: "beginner", label: "초보", desc: "투자를 막 시작했어요" },
  { value: "intermediate", label: "중급", desc: "기본 개념은 알고 있어요" },
  { value: "expert", label: "전문가", desc: "투자 경험이 풍부해요" },
] as const;

const STYLE_OPTIONS = [
  { value: "feeling", label: "직감형", desc: "느낌과 트렌드를 중시해요" },
  { value: "logic", label: "분석형", desc: "데이터와 지표를 중시해요" },
  { value: "balanced", label: "균형형", desc: "둘 다 적절히 활용해요" },
] as const;

export default function IceBreakingModal() {
  const submitIceBreaking = useProfileStore((s) => s.submitIceBreaking);
  const [step, setStep] = useState<1 | 2>(1);
  const [experience, setExperience] =
    useState<IceBreakingRequest["experience_level"] | null>(null);
  const [style, setStyle] =
    useState<IceBreakingRequest["decision_style"] | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!experience || !style) return;
    setSubmitting(true);
    try {
      await submitIceBreaking({
        experience_level: experience,
        decision_style: style,
      });
    } catch {
      // 실패해도 모달 닫힘 — 다음 접속 시 재시도
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-1">
          반갑습니다!
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          맞춤형 분석을 위해 두 가지만 알려주세요.
        </p>

        {step === 1 && (
          <>
            <p className="text-sm font-medium text-gray-700 mb-3">
              투자 경험 수준이 어떻게 되시나요?
            </p>
            <div className="space-y-2 mb-6">
              {EXPERIENCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setExperience(opt.value)}
                  className={`w-full text-left p-3 rounded-lg border-2 transition ${
                    experience === opt.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <span className="font-medium text-gray-900">
                    {opt.label}
                  </span>
                  <span className="text-sm text-gray-500 ml-2">
                    {opt.desc}
                  </span>
                </button>
              ))}
            </div>
            <button
              disabled={!experience}
              onClick={() => setStep(2)}
              className="w-full py-2.5 rounded-lg bg-blue-500 text-white font-medium disabled:opacity-40 hover:bg-blue-600 transition"
            >
              다음
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <p className="text-sm font-medium text-gray-700 mb-3">
              투자 의사결정 스타일은 어떤가요?
            </p>
            <div className="space-y-2 mb-6">
              {STYLE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setStyle(opt.value)}
                  className={`w-full text-left p-3 rounded-lg border-2 transition ${
                    style === opt.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <span className="font-medium text-gray-900">
                    {opt.label}
                  </span>
                  <span className="text-sm text-gray-500 ml-2">
                    {opt.desc}
                  </span>
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition"
              >
                이전
              </button>
              <button
                disabled={!style || submitting}
                onClick={handleSubmit}
                className="flex-1 py-2.5 rounded-lg bg-blue-500 text-white font-medium disabled:opacity-40 hover:bg-blue-600 transition"
              >
                {submitting ? "저장 중..." : "시작하기"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
