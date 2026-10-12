import banner from './assets/banner.png'
import LanguageSelector from './LanguageSelector'

// Single shared top bar: logo on the left, a compact right-hand cluster
// (language switcher + whatever page-specific actions are passed in).
// Used by every page instead of each one hand-rolling its own header.
export default function Header({ children }) {
  return (
    <header className="app-header">
      <img src={banner} alt="iTransfer" className="app-logo" />
      <div className="app-header__actions">
        <LanguageSelector />
        {children}
      </div>
    </header>
  )
}
