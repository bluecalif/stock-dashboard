import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const NAV_ITEMS = [
  { to: "/", label: "홈", icon: "📊" },
  { to: "/prices", label: "가격", icon: "📈" },
  { to: "/correlation", label: "상관", icon: "🔗" },
  { to: "/indicators", label: "지표/시그널", icon: "📐" },
  { to: "/strategy", label: "전략", icon: "🎯" },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col min-h-screen">
      <div className="px-4 py-5 border-b border-gray-700">
        <h1 className="text-lg font-bold tracking-tight">Stock Dashboard</h1>
        <p className="text-xs text-gray-400 mt-1">7 Assets · MVP</p>
      </div>
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? "bg-gray-700 text-white font-medium"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {user && (
        <div className="px-4 py-4 border-t border-gray-700">
          <p className="text-sm font-medium text-gray-200 truncate">
            {user.nickname || user.email}
          </p>
          <p className="text-xs text-gray-400 truncate">{user.email}</p>
          <button
            onClick={logout}
            className="mt-2 w-full text-xs text-gray-400 hover:text-white py-1.5 px-2 rounded hover:bg-gray-800 transition-colors text-left"
          >
            로그아웃
          </button>
        </div>
      )}
    </aside>
  );
}
