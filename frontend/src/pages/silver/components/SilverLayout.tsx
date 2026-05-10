import { NavLink, Outlet } from "react-router-dom";
import ChatPanel from "../../../components/chat/ChatPanel";
import { useChatStore } from "../../../store/chatStore";
import { useAuthStore } from "../../../store/authStore";

export default function SilverLayout() {
  const togglePanel = useChatStore((s) => s.togglePanel);
  const { user, logout } = useAuthStore();

  return (
    <div className="silver-shell">
      <header className="silver-top-nav">
        <div className="silver-top-nav__brand">Stock Dashboard</div>

        <nav className="silver-top-nav__items">
          <NavLink
            to="/silver/compare"
            className={({ isActive }) =>
              `silver-nav-link${isActive ? " silver-nav-link--active" : ""}`
            }
          >
            적립식 비교
          </NavLink>
          <NavLink
            to="/silver/signals"
            className={({ isActive }) =>
              `silver-nav-link${isActive ? " silver-nav-link--active" : ""}`
            }
          >
            신호
          </NavLink>
          <button
            onClick={togglePanel}
            className="silver-nav-link"
            style={{ background: "none", border: "none", cursor: "pointer" }}
          >
            Chat 💬
          </button>
        </nav>

        <div className="silver-top-nav__right">
          {user && (
            <button className="silver-profile-btn" onClick={logout}>
              {user.nickname ?? user.email} · 로그아웃
            </button>
          )}
        </div>
      </header>

      <main className="silver-main">
        <Outlet />
      </main>

      <ChatPanel />
    </div>
  );
}
