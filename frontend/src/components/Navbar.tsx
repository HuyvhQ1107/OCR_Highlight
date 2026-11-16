import { BookOpen, FileText, LogOut, Search, Sparkles } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  if (!user) return null

  const navLinks = [
    { to: '/dashboard', label: 'Tài liệu', icon: FileText },
    { to: '/search', label: 'Tìm kiếm', icon: Search },
    { to: '/study', label: 'Ôn tập', icon: Sparkles },
  ]

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/dashboard" className="flex items-center gap-2 font-semibold text-indigo-700">
          <BookOpen className="h-5 w-5" />
          <span>Dấu Vết Tri Thức</span>
        </Link>

        <nav className="flex items-center gap-1">
          {navLinks.map(({ to, label, icon: Icon }) => {
            const active = location.pathname.startsWith(to)
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  active
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-slate-500 sm:inline">{user.email}</span>
          <button
            onClick={logout}
            className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
          >
            <LogOut className="h-4 w-4" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </div>
    </header>
  )
}
