<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <title>Aether AI — Telegram Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>

  <!-- Markdown (marked.js) + Подсветка кода (highlight.js) + Формулы (KaTeX) -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link id="hljsThemeLink" rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>

  <style>
    /* =====================================================================
       ТЕМЫ И ПЕРЕМЕННЫЕ (ТЁМНАЯ ПО УМОЛЧАНИЮ + СВЕТЛАЯ)
    ===================================================================== */
    :root {
      --bg-main: #090b10;
      --bg-sidebar: #11141d;
      --bg-sidebar-glass: rgba(17, 20, 29, 0.96);
      --bg-surface: rgba(26, 30, 42, 0.85);
      --bg-surface-hover: rgba(37, 43, 59, 0.96);
      --bg-input: rgba(23, 27, 38, 0.9);
      --border: rgba(255, 255, 255, 0.08);
      --border-strong: rgba(255, 255, 255, 0.14);
      --text-main: #f3f5fa;
      --text-muted: #939bb0;
      --accent: #6366f1;
      --accent-2: #8b5cf6;
      --accent-soft: rgba(99, 102, 241, 0.18);
      --pill-active: rgba(99, 102, 241, 0.18);
      --shadow-modal: 0 24px 60px rgba(0, 0, 0, 0.68);
      --code-bg: #12151f;
      --code-header-bg: #1a1e2c;
      --code-border: rgba(255, 255, 255, 0.08);
      --provider-glow: rgba(139, 92, 246, 0.48);
      --safe-top: env(safe-area-inset-top, 0px);
      --safe-bottom: env(safe-area-inset-bottom, 0px);
      --tg-content-top: var(--tg-content-safe-area-inset-top, 0px);
    }

    body.theme-light {
      --bg-main: #f7f9fe;
      --bg-sidebar: #f0f4fc;
      --bg-sidebar-glass: rgba(240, 244, 252, 0.97);
      --bg-surface: rgba(231, 236, 248, 0.88);
      --bg-surface-hover: rgba(220, 227, 243, 0.98);
      --bg-input: rgba(255, 255, 255, 0.95);
      --border: rgba(15, 23, 42, 0.08);
      --border-strong: rgba(15, 23, 42, 0.15);
      --text-main: #0f172a;
      --text-muted: #5a657a;
      --accent: #4f46e5;
      --accent-2: #7c3aed;
      --accent-soft: rgba(79, 70, 229, 0.11);
      --pill-active: rgba(79, 70, 229, 0.14);
      --shadow-modal: 0 20px 50px rgba(15, 23, 42, 0.14);
      --code-bg: #f4f6fb;
      --code-header-bg: #e8ecf6;
      --code-border: rgba(15, 23, 42, 0.1);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }

    html, body {
      height: 100%;
      width: 100%;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Inter, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      transition: background-color 0.25s ease, color 0.25s ease;
    }

    svg.ico {
      width: 17px;
      height: 17px;
      stroke: currentColor;
      stroke-width: 1.85;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
      flex-shrink: 0;
    }

    /* =====================================================================
       ЗАЩИЩЁННАЯ АВТОРИЗАЦИЯ ДЛЯ БРАУЗЕРА (GOOGLE / CHROME / SAFARI)
    ===================================================================== */
    .web-auth-gate {
      position: fixed;
      inset: 0;
      background: var(--bg-main);
      z-index: 300;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .web-auth-gate.active {
      display: flex;
    }

    .web-auth-card {
      width: 100%;
      max-width: 410px;
      background: var(--bg-sidebar);
      border: 1px solid var(--border-strong);
      border-radius: 28px;
      padding: 28px 24px;
      text-align: center;
      box-shadow: var(--shadow-modal);
      animation: springPop 0.32s cubic-bezier(0.22, 1.25, 0.36, 1);
    }

    .auth-logo-circle {
      width: 60px;
      height: 60px;
      border-radius: 18px;
      margin: 0 auto 16px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: grid;
      place-items: center;
      overflow: hidden;
      box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4);
    }

    .auth-logo-circle img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .auth-title {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }

    .auth-desc {
      font-size: 13.5px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 18px;
    }

    .tg-login-btn {
      width: 100%;
      border: none;
      border-radius: 14px;
      padding: 13px 18px;
      font-size: 14.5px;
      font-weight: 650;
      color: #fff;
      background: linear-gradient(135deg, #24A1DE, #1d8ec4);
      box-shadow: 0 8px 22px rgba(36, 161, 222, 0.35);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 9px;
      text-decoration: none;
      transition: transform 0.15s;
    }

    .tg-login-btn:active {
      transform: scale(0.97);
    }

    .auth-widget-slot {
      display: flex;
      justify-content: center;
      margin: 12px 0 4px;
      min-height: 42px;
    }

    .auth-divider {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 16px 0 12px;
      font-size: 11.5px;
      color: var(--text-muted);
    }

    .auth-divider::before, .auth-divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: var(--border-strong);
    }

    .auth-code-row {
      display: flex;
      gap: 8px;
    }

    /* =====================================================================
       ЖИВОЕ ФОНОВОЕ СВЕЧЕНИЕ (AMBIENT GLOW)
    ===================================================================== */
    .ambient-glow {
      position: fixed;
      top: 48%;
      left: 55%;
      width: 720px;
      height: 720px;
      transform: translate(-50%, -50%);
      background: radial-gradient(circle, rgba(79, 70, 229, 0.24) 0%, rgba(139, 92, 246, 0.14) 32%, rgba(14, 165, 233, 0.08) 54%, transparent 72%);
      filter: blur(58px);
      pointer-events: none;
      z-index: 0;
      animation: ambientBreathe 10s ease-in-out infinite alternate;
    }

    body.theme-light .ambient-glow {
      background: radial-gradient(circle, rgba(99, 102, 241, 0.16) 0%, rgba(168, 85, 247, 0.09) 35%, rgba(56, 189, 248, 0.07) 55%, transparent 72%);
    }

    body.no-gradient .ambient-glow {
      display: none;
    }

    @keyframes ambientBreathe {
      0% { transform: translate(-52%, -50%) scale(0.94); opacity: 0.76; }
      50% { transform: translate(-47%, -46%) scale(1.08); opacity: 1; }
      100% { transform: translate(-50%, -53%) scale(0.98); opacity: 0.84; }
    }

    /* =====================================================================
       ОСНОВНОЙ КАРКАС (ПК + МОБИЛЬНЫЙ)
    ===================================================================== */
    .app-shell {
      display: flex;
      height: 100dvh;
      width: 100vw;
      padding-top: 0px;
      padding-bottom: var(--safe-bottom);
      position: relative;
      z-index: 1;
      overflow: hidden;
    }

    /* ЛЕВАЯ ПАНЕЛЬ (САЙДБАР) */
    .sidebar {
      width: 276px;
      background: var(--bg-sidebar-glass);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      padding: 14px 12px;
      flex-shrink: 0;
      z-index: 50;
      transition: width 0.28s cubic-bezier(0.22, 1, 0.36, 1), transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), background-color 0.25s ease;
    }

    .sidebar-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 4px 14px;
      gap: 6px;
    }

    .brand-box {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      min-width: 0;
      overflow: hidden;
    }

    .brand-logo-img {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      object-fit: cover;
      flex-shrink: 0;
    }

    .brand-logo-fallback {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 800;
      font-size: 14px;
      flex-shrink: 0;
    }

    .brand-name {
      font-size: 17.5px;
      font-weight: 650;
      letter-spacing: -0.02em;
      white-space: nowrap;
    }

    .collapse-pc-btn {
      width: 32px;
      height: 32px;
      border-radius: 9px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      transition: background 0.15s, color 0.15s;
    }

    .collapse-pc-btn:hover {
      background: var(--bg-surface);
      color: var(--text-main);
    }

    .close-sidebar-btn {
      display: none;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 6px;
      border-radius: 8px;
    }

    .new-chat-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 10px 14px;
      border-radius: 999px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      color: var(--text-main);
      font-size: 13.5px;
      font-weight: 550;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s, transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
      margin-bottom: 12px;
      overflow: hidden;
      white-space: nowrap;
    }

    .new-chat-btn:hover {
      background: var(--bg-surface-hover);
      border-color: var(--border-strong);
    }

    .new-chat-btn:active {
      transform: scale(0.97);
    }

    .nav-links {
      display: flex;
      flex-direction: column;
      gap: 3px;
      margin-bottom: 14px;
    }

    .side-nav-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 12px;
      border-radius: 12px;
      color: var(--text-main);
      font-size: 13.5px;
      cursor: pointer;
      transition: background 0.15s;
      overflow: hidden;
      white-space: nowrap;
    }

    .side-nav-item:hover, .side-nav-item.active {
      background: var(--bg-surface-hover);
    }

    .side-nav-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    /* ПЕРЕЛИВАЮЩИЙСЯ БЕЙДЖ PRO */
    .pro-shimmer-badge {
      font-size: 10.5px;
      padding: 2px 8px;
      border-radius: 999px;
      background: linear-gradient(110deg, #f59e0b 15%, #a855f7 45%, #38bdf8 75%, #f59e0b 95%);
      background-size: 220% 100%;
      color: #fff;
      font-weight: 750;
      letter-spacing: 0.04em;
      box-shadow: 0 2px 10px rgba(168, 85, 247, 0.35);
      animation: badgeFlow 3.5s linear infinite;
      flex-shrink: 0;
    }

    @keyframes badgeFlow {
      0% { background-position: 0% 50%; }
      100% { background-position: 220% 50%; }
    }

    .history-label {
      font-size: 11.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      padding: 6px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      white-space: nowrap;
    }

    .history-list {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding-right: 2px;
    }

    .history-list::-webkit-scrollbar { width: 4px; }
    .history-list::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }

    .history-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 10px;
      font-size: 13.5px;
      color: var(--text-main);
      cursor: pointer;
      transition: background 0.15s;
    }

    .history-item:hover { background: var(--bg-surface); }
    .history-item.active { background: var(--pill-active); font-weight: 500; }

    .history-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 195px;
    }

    .history-del {
      opacity: 0.55;
      color: var(--text-muted);
      padding: 2px 4px;
      border-radius: 6px;
      display: grid;
      place-items: center;
    }

    .history-item:hover .history-del { opacity: 1; }

    /* НИЖНИЙ ПРОФИЛЬ */
    .sidebar-footer {
      border-top: 1px solid var(--border);
      padding-top: 10px;
      margin-top: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .user-mini-card {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 8px;
      border-radius: 12px;
      cursor: pointer;
      flex: 1;
      min-width: 0;
      transition: background 0.15s;
    }

    .user-mini-card:hover { background: var(--bg-surface); }

    .user-avatar-wrap {
      width: 35px;
      height: 35px;
      border-radius: 50%;
      position: relative;
      flex-shrink: 0;
      overflow: hidden;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: grid;
      place-items: center;
      border: 1.5px solid var(--border-strong);
    }

    .user-avatar-wrap.pro-ring {
      border: 2px solid transparent;
      background:
        linear-gradient(var(--bg-main), var(--bg-main)) padding-box,
        linear-gradient(135deg, #f59e0b, #8b5cf6, #06b6d4) border-box;
      box-shadow: 0 0 16px rgba(139, 92, 246, 0.5);
    }

    .user-avatar-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: none;
      border-radius: 50%;
    }

    .user-avatar-letter {
      color: #fff;
      font-weight: 700;
      font-size: 14px;
    }

    .user-mini-name {
      font-size: 13.5px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .user-mini-plan {
      font-size: 11px;
      color: var(--text-muted);
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-top: 1px;
    }

    .settings-gear-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      transition: background 0.15s, color 0.15s;
      flex-shrink: 0;
    }

    .settings-gear-btn:hover {
      background: var(--bg-surface);
      color: var(--text-main);
    }

    /* ДЕСКТОП: БОКОВАЯ ПАНЕЛЬ И РАБОЧАЯ ЗОНА СТРОГО РЯДОМ ПО ГОРИЗОНТАЛИ */
    @media (min-width: 769px) {
      body {
        display: flex;
        flex-direction: row;
      }
      .app-shell {
        flex: 1;
        min-width: 0;
        width: auto;
      }
      .sidebar.collapsed {
        width: 68px;
        padding: 14px 10px;
      }
      .sidebar.collapsed .brand-box,
      .sidebar.collapsed .new-chat-btn span,
      .sidebar.collapsed .side-nav-item span,
      .sidebar.collapsed .history-label,
      .sidebar.collapsed .history-list,
      .sidebar.collapsed .user-mini-card > div:last-child {
        display: none;
      }
      .sidebar.collapsed .sidebar-header {
        justify-content: center;
      }
      .sidebar.collapsed .new-chat-btn {
        justify-content: center;
        padding: 10px;
      }
      .sidebar.collapsed .side-nav-item {
        justify-content: center;
        padding: 10px;
      }
      .sidebar.collapsed .sidebar-footer {
        flex-direction: column;
        gap: 10px;
      }
      .sidebar.collapsed .user-mini-card {
        padding: 4px;
        justify-content: center;
      }
    }

    /* =====================================================================
       ПРАВАЯ РАБОЧАЯ ЗОНА
    ===================================================================== */
    .main-stage {
      flex: 1;
      display: flex;
      flex-direction: column;
      position: relative;
      min-width: 0;
      max-width: 100%;
      height: 100%;
      overflow: hidden;
    }

    .stage-topbar {
      height: 56px;
      padding: 0 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 20;
      flex-shrink: 0;
      min-width: 0;
    }

    .topbar-left {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .hamburger-btn {
      display: none;
      background: transparent;
      border: none;
      color: var(--text-main);
      cursor: pointer;
      padding: 7px;
      border-radius: 10px;
    }

    .model-dropdown-trigger {
      display: inline-flex;
      align-items: center;
      gap: 9px;
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-main);
      font-size: 15.5px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 14px;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s, transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
      min-width: 0;
    }

    .model-dropdown-trigger:hover {
      background: var(--bg-surface);
      border-color: var(--border);
    }

    .model-dropdown-trigger:active {
      transform: scale(0.97);
    }

    .model-avatar-slot {
      width: 24px;
      height: 24px;
      border-radius: 7px;
      overflow: hidden;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .model-avatar-slot.lg {
      width: 34px;
      height: 34px;
      border-radius: 10px;
    }

    .model-avatar-slot img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .topbar-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .fullscreen-pc-btn {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--bg-surface);
      color: var(--text-muted);
      cursor: pointer;
      display: grid;
      place-items: center;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
    }

    .fullscreen-pc-btn:hover {
      background: var(--bg-surface-hover);
      color: var(--text-main);
      border-color: var(--border-strong);
    }

    .quota-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 13px;
      border-radius: 999px;
      background: var(--bg-surface);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid var(--border);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      flex-shrink: 0;
      transition: border-color 0.15s;
    }

    .quota-badge:hover { border-color: var(--border-strong); }

    /* =====================================================================
       ЭКРАН ЧАТА, ГРАДИЕНТНЫЙ ЗАГОЛОВОК И БЛИК НА ЛОГОТИПЕ
    ===================================================================== */
    .view-section {
      display: none;
      flex: 1;
      flex-direction: column;
      height: calc(100% - 56px);
      overflow: hidden;
      min-width: 0;
      position: relative;
    }

    .view-section.active { display: flex; }

    .chat-scroll-area {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 12px 20px;
      display: flex;
      flex-direction: column;
      min-width: 0;
      scroll-behavior: smooth;
    }

    .chat-container-inner {
      width: 100%;
      max-width: 780px;
      min-width: 0;
      margin: 0 auto;
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .welcome-hero {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 16px;
      animation: springPop 0.45s cubic-bezier(0.22, 1, 0.36, 1);
    }

    .welcome-logo-wrap {
      position: relative;
      width: 58px;
      height: 58px;
      border-radius: 18px;
      margin-bottom: 18px;
      overflow: hidden;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      box-shadow: 0 12px 34px var(--provider-glow), 0 0 0 1px rgba(255, 255, 255, 0.14);
      transition: box-shadow 0.45s ease;
    }

    .welcome-logo-wrap::after {
      content: "";
      position: absolute;
      top: -50%;
      left: -80%;
      width: 55%;
      height: 200%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.42), transparent);
      transform: rotate(25deg);
      animation: logoSheenSweep 4.2s ease-in-out infinite;
      pointer-events: none;
    }

    @keyframes logoSheenSweep {
      0%, 62% { left: -80%; }
      100% { left: 150%; }
    }

    .welcome-logo-wrap img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .welcome-title {
      font-size: clamp(25px, 4vw, 36px);
      font-weight: 600;
      letter-spacing: -0.025em;
      margin-bottom: 10px;
      line-height: 1.25;
      background: linear-gradient(120deg, #ffffff 10%, #a5b4fc 48%, #7dd3fc 82%, #e0e7ff 100%);
      background-size: 200% auto;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: titleGradientShift 7s ease-in-out infinite alternate;
    }

    body.theme-light .welcome-title {
      background: linear-gradient(120deg, #0f172a 10%, #4338ca 50%, #0284c7 85%, #1e1b4b 100%);
      background-size: 200% auto;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    @keyframes titleGradientShift {
      0% { background-position: 0% 50%; }
      100% { background-position: 100% 50%; }
    }

    .welcome-sub {
      font-size: 14px;
      color: var(--text-muted);
      max-width: 460px;
      margin-bottom: 24px;
    }

    .prompt-chips-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      width: 100%;
      max-width: 580px;
    }

    .prompt-chip-card {
      display: flex;
      align-items: center;
      gap: 11px;
      text-align: left;
      padding: 12px 14px;
      border-radius: 16px;
      background: var(--bg-surface);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid var(--border);
      color: var(--text-main);
      cursor: pointer;
      transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s, background 0.2s, box-shadow 0.2s;
    }

    .prompt-chip-card:hover {
      background: var(--bg-surface-hover);
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 8px 24px rgba(99, 102, 241, 0.14);
      transform: translateY(-2px);
    }

    .prompt-chip-card:active { transform: scale(0.96); }

    .chip-ico-wrap {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      background: var(--accent-soft);
      color: #818cf8;
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .chip-title { font-size: 13px; font-weight: 600; }
    .chip-sub { font-size: 11.5px; color: var(--text-muted); margin-top: 1px; }

    /* =====================================================================
       СООБЩЕНИЯ, ПРУЖИНИСТАЯ АНИМАЦИЯ ВСПЛЫТИЯ, MARKDOWN И БЛОКИ КОДА
    ===================================================================== */
    .messages-stack {
      display: flex;
      flex-direction: column;
      gap: 22px;
      padding-bottom: 24px;
      width: 100%;
      min-width: 0;
    }

    .msg-row {
      display: flex;
      flex-direction: column;
      max-width: 88%;
      min-width: 0;
      animation: springBubble 0.34s cubic-bezier(0.22, 1.25, 0.36, 1);
    }

    @keyframes springBubble {
      0% { opacity: 0; transform: translateY(14px) scale(0.96); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    .msg-row.user {
      align-self: flex-end;
      align-items: flex-end;
    }

    .msg-row.ai {
      align-self: flex-start;
      align-items: flex-start;
      width: 100%;
      max-width: 100%;
      min-width: 0;
    }

    .msg-bubble {
      padding: 13px 17px;
      border-radius: 20px;
      font-size: 15px;
      line-height: 1.62;
      word-wrap: break-word;
      overflow-wrap: break-word;
      min-width: 0;
      max-width: 100%;
    }

    .msg-row.user .msg-bubble {
      background: var(--bg-surface-hover);
      color: var(--text-main);
      border-bottom-right-radius: 6px;
      white-space: pre-wrap;
    }

    .msg-row.ai .msg-bubble {
      background: transparent;
      color: var(--text-main);
      padding: 4px 4px 6px;
      width: 100%;
      min-width: 0;
    }

    .msg-model-tag {
      font-size: 12px;
      font-weight: 500;
      color: var(--text-muted);
      margin-bottom: 5px;
      padding-left: 4px;
      display: flex;
      align-items: center;
      gap: 7px;
    }

    /* СКЕЛЕТОН С ПУЛЬСИРУЮЩИМ ЛОГОТИПОМ AETHER AI */
    .skeleton-thinking-box {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 6px 0;
      max-width: 480px;
    }

    .skeleton-pulse-logo {
      width: 28px;
      height: 28px;
      border-radius: 9px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 800;
      font-size: 13px;
      overflow: hidden;
      flex-shrink: 0;
      animation: logoPulseGlow 1.5s ease-in-out infinite;
    }

    .skeleton-pulse-logo img { width: 100%; height: 100%; object-fit: cover; }

    @keyframes logoPulseGlow {
      0%, 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.5); }
      50% { transform: scale(1.06); box-shadow: 0 0 16px 3px rgba(139, 92, 246, 0.45); }
    }

    .skeleton-bars-col {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-top: 3px;
    }

    .skel-bar {
      height: 10px;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--bg-surface) 20%, rgba(99, 102, 241, 0.34) 50%, var(--bg-surface) 80%);
      background-size: 200% 100%;
      animation: shimmerMove 1.35s infinite linear;
    }

    .skel-bar.w1 { width: 92%; }
    .skel-bar.w2 { width: 74%; }
    .skel-bar.w3 { width: 52%; }

    @keyframes shimmerMove {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* СТИЛИ MARKDOWN */
    .md-content {
      width: 100%;
      min-width: 0;
      max-width: 100%;
    }
    .md-content p { margin-bottom: 10px; }
    .md-content p:last-child { margin-bottom: 0; }
    .md-content h1, .md-content h2, .md-content h3 { margin: 14px 0 8px; font-weight: 700; line-height: 1.3; }
    .md-content h1 { font-size: 1.3em; }
    .md-content h2 { font-size: 1.18em; }
    .md-content h3 { font-size: 1.06em; }
    .md-content ul, .md-content ol { margin: 8px 0 12px 22px; }
    .md-content li { margin-bottom: 5px; }
    .md-content strong { font-weight: 700; }
    .md-content blockquote {
      border-left: 3px solid var(--accent);
      padding-left: 12px;
      color: var(--text-muted);
      margin: 10px 0;
    }
    .md-content table {
      width: 100%;
      max-width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 13.5px;
      display: block;
      overflow-x: auto;
    }
    .md-content th, .md-content td {
      border: 1px solid var(--border-strong);
      padding: 8px 11px;
      text-align: left;
    }
    .md-content th { background: var(--bg-surface); font-weight: 600; }
    .md-content code:not(pre code) {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      padding: 2px 6px;
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.88em;
      word-break: break-all;
    }

    /* БЛОК КОДА */
    .code-block-wrapper {
      margin: 12px 0;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--code-border);
      background: var(--code-bg);
      width: 100%;
      max-width: 100%;
      min-width: 0;
    }

    .code-block-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 7px 14px;
      background: var(--code-header-bg);
      border-bottom: 1px solid var(--code-border);
      font-size: 12px;
      color: var(--text-muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    .copy-code-btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      color: var(--text-main);
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11.5px;
      font-family: inherit;
      cursor: pointer;
      transition: opacity 0.15s;
    }

    .copy-code-btn:hover { opacity: 0.85; }

    .code-block-wrapper pre {
      margin: 0;
      padding: 13px 15px;
      overflow-x: auto;
      max-width: 100%;
      font-size: 13.5px;
      line-height: 1.5;
    }

    .code-block-wrapper pre code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: transparent !important;
      padding: 0 !important;
      white-space: pre;
    }

    .katex-display { overflow-x: auto; overflow-y: hidden; padding: 6px 0; max-width: 100%; }

    .ai-actions-bar {
      display: flex;
      align-items: center;
      margin-top: 4px;
      padding-left: 2px;
    }

    .ai-act-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 6px 10px;
      border-radius: 10px;
      font-size: 12.5px;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }

    .ai-act-btn:hover { background: var(--bg-surface); color: var(--text-main); }

    .msg-attachment-img {
      max-width: 240px;
      border-radius: 14px;
      margin-bottom: 8px;
      border: 1px solid var(--border);
    }

    .msg-attachment-file {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      padding: 6px 11px;
      border-radius: 10px;
      font-size: 12px;
      margin-bottom: 6px;
    }

    /* =====================================================================
       ПАРЯЩАЯ КНОПКА БЫСТРОГО СКРОЛЛА ВНИЗ (↓)
    ===================================================================== */
    .scroll-bottom-fab {
      position: absolute;
      right: 22px;
      bottom: 88px;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: var(--bg-sidebar);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid var(--border-strong);
      color: var(--text-main);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      display: grid;
      place-items: center;
      cursor: pointer;
      z-index: 30;
      opacity: 0;
      transform: translateY(10px) scale(0.9);
      pointer-events: none;
      transition: opacity 0.2s ease, transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .scroll-bottom-fab.visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    .scroll-bottom-fab:hover { background: var(--bg-surface-hover); }

    /* =====================================================================
       НИЖНЯЯ КАПСУЛА ВВОДА + ВИЗУАЛЬНЫЕ КАРТОЧКИ ПРИКРЕПЛЁННЫХ ФАЙЛОВ/ФОТО
    ===================================================================== */
    .composer-wrapper {
      padding: 8px 16px 18px;
      width: 100%;
      max-width: 812px;
      margin: 0 auto;
      position: relative;
      flex-shrink: 0;
    }

    .attachment-preview-tray {
      display: none;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
      padding-left: 6px;
      animation: springBubble 0.25s cubic-bezier(0.22, 1.25, 0.36, 1);
    }

    .att-image-card {
      position: relative;
      width: 68px;
      height: 68px;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--border-strong);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }

    .att-image-card img { width: 100%; height: 100%; object-fit: cover; display: block; }

    .att-file-card {
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 11px;
      background: var(--bg-surface);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-strong);
      border-radius: 14px;
      padding: 9px 34px 9px 11px;
      max-width: 280px;
    }

    .att-file-ext {
      padding: 5px 7px;
      border-radius: 8px;
      background: var(--accent-soft);
      color: #818cf8;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    .att-file-meta { min-width: 0; }
    .att-file-name { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .att-file-size { font-size: 11px; color: var(--text-muted); margin-top: 1px; }

    .att-remove-badge {
      position: absolute;
      top: 5px;
      right: 5px;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: none;
      background: rgba(15, 23, 42, 0.78);
      color: #fff;
      font-size: 12px;
      cursor: pointer;
      display: grid;
      place-items: center;
    }

    .composer-pill {
      background: var(--bg-input);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--border-strong);
      border-radius: 28px;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 10px 32px rgba(0, 0, 0, 0.22);
      transition: border-color 0.2s;
    }

    .composer-pill:focus-within { border-color: var(--accent); }

    .plus-btn {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: var(--text-main);
      cursor: pointer;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      transition: background 0.15s;
    }

    .plus-btn:hover { background: var(--bg-surface-hover); }

    .chat-textarea {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 15px;
      font-family: inherit;
      resize: none;
      max-height: 140px;
      min-height: 24px;
      line-height: 1.45;
      outline: none;
      padding: 6px 4px;
    }

    .chat-textarea::placeholder { color: var(--text-muted); }

    .composer-model-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
      padding: 6px 10px;
      border-radius: 999px;
      cursor: pointer;
      white-space: nowrap;
    }

    .composer-model-pill:hover {
      background: var(--bg-surface-hover);
      color: var(--text-main);
    }

    .send-circle-btn {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      border: none;
      background: var(--text-main);
      color: var(--bg-main);
      cursor: pointer;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .send-circle-btn:active { transform: scale(0.88); }

    .plus-popover {
      position: absolute;
      bottom: 76px;
      left: 18px;
      background: var(--bg-sidebar);
      backdrop-filter: blur(22px);
      -webkit-backdrop-filter: blur(22px);
      border: 1px solid var(--border-strong);
      border-radius: 18px;
      padding: 6px;
      box-shadow: var(--shadow-modal);
      display: none;
      flex-direction: column;
      gap: 2px;
      z-index: 40;
      min-width: 210px;
    }

    .plus-popover.open { display: flex; animation: springPop 0.22s cubic-bezier(0.22, 1.25, 0.36, 1); }

    .popover-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 13px;
      border-radius: 12px;
      font-size: 13.5px;
      cursor: pointer;
      color: var(--text-main);
    }

    .popover-item:hover { background: var(--bg-surface-hover); }

    /* =====================================================================
       ВЫПАДАЮЩЕЕ МЕНЮ ВЫБОРА МОДЕЛИ
    ===================================================================== */
    .model-menu-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.48);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding-top: 64px;
      z-index: 150;
    }

    .model-menu-backdrop.open { display: flex; }

    .model-menu-card {
      width: 92%;
      max-width: 430px;
      max-height: 76vh;
      overflow-y: auto;
      background: var(--bg-sidebar);
      border: 1px solid var(--border-strong);
      border-radius: 24px;
      padding: 12px;
      box-shadow: var(--shadow-modal);
      animation: springPop 0.25s cubic-bezier(0.22, 1.25, 0.36, 1);
    }

    @keyframes springPop {
      0% { opacity: 0; transform: translateY(10px) scale(0.95); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    .model-cat-tabs {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 10px;
      margin-bottom: 6px;
      border-bottom: 1px solid var(--border);
      scrollbar-width: none;
    }
    .model-cat-tabs::-webkit-scrollbar { display: none; }

    .m-cat-btn {
      padding: 5px 11px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--bg-surface);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }

    .m-cat-btn.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }

    .model-option-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 12px;
      border-radius: 14px;
      cursor: pointer;
      transition: background 0.15s, transform 0.15s;
    }

    .model-option-row:hover { background: var(--bg-surface); }
    .model-option-row:active { transform: scale(0.98); }

    .model-opt-left {
      display: flex;
      align-items: center;
      gap: 11px;
      min-width: 0;
    }

    .model-opt-title {
      font-size: 14px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .model-opt-desc {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* =====================================================================
       ВТОРОСТЕПЕННЫЕ РАЗДЕЛЫ (МАГАЗИН, ПРОФИЛЬ, АДМИНКА)
    ===================================================================== */
    .subpage-scroll { flex: 1; overflow-y: auto; padding: 16px 20px 32px; }
    .subpage-inner { max-width: 720px; margin: 0 auto; }
    .bento-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .bento-card {
      background: var(--bg-sidebar);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 16px;
      cursor: pointer;
      transition: border-color 0.2s;
    }
    .bento-card:hover { border-color: var(--border-strong); }
    .bento-card.span-2 { grid-column: span 2; }
    .card-tag {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 999px;
      background: var(--bg-surface);
      color: var(--text-muted);
      margin-bottom: 8px;
    }
    .card-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
    .card-desc { font-size: 13px; color: var(--text-muted); line-height: 1.4; }
    .stat-big { font-size: 24px; font-weight: 800; margin: 4px 0; }

    .btn-primary {
      border: none;
      border-radius: 12px;
      padding: 10px 16px;
      font-size: 13.5px;
      font-weight: 600;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
    }

    .btn-secondary {
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      padding: 10px 16px;
      font-size: 13.5px;
      font-weight: 600;
      background: var(--bg-surface);
      color: var(--text-main);
      cursor: pointer;
    }

    .std-input {
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      padding: 10px 13px;
      color: var(--text-main);
      font-size: 14px;
      outline: none;
    }

    /* =====================================================================
       МОДАЛЬНЫЕ ОКНА (НАСТРОЙКИ ТЕМЫ, ОПЛАТА)
    ===================================================================== */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 200;
    }
    .modal-overlay.open { display: flex; }

    .modal-box {
      width: 100%;
      max-width: 420px;
      background: var(--bg-sidebar);
      border: 1px solid var(--border-strong);
      border-radius: 24px;
      padding: 20px;
      box-shadow: var(--shadow-modal);
      animation: springPop 0.24s cubic-bezier(0.22, 1.25, 0.36, 1);
    }

    .setting-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 13px 0;
      border-bottom: 1px solid var(--border);
    }
    .setting-row:last-child { border-bottom: none; }

    .theme-segment {
      display: flex;
      background: var(--bg-surface);
      padding: 3px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }

    .theme-seg-btn {
      padding: 6px 12px;
      border-radius: 9px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
    }
    .theme-seg-btn.active { background: var(--accent); color: #fff; }

    .toast-box {
      position: fixed;
      top: 56px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--bg-surface-hover);
      border: 1px solid var(--border-strong);
      color: var(--text-main);
      padding: 9px 18px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      z-index: 350;
      display: none;
      box-shadow: var(--shadow-modal);
    }

    /* МОБИЛЬНАЯ ШТОРКА И ПОДЛОЖКА (ВЫНЕСЕНЫ НА ОДИН УРОВЕНЬ С БОДИ, БЕЗ КОНФЛИКТА STACKING CONTEXT) */
    .mobile-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.55);
      z-index: 90;
    }

    /* =====================================================================
       МОБИЛЬНАЯ АДАПТАЦИЯ (< 768px)
    ===================================================================== */
    @media (max-width: 768px) {
      .app-shell {
        padding-top: max(46px, calc(var(--safe-top) + var(--tg-content-top) + 38px));
      }

      .stage-topbar {
        height: 54px;
        padding: 4px 14px 0;
      }

      .view-section {
        height: calc(100% - 54px);
      }

      .model-menu-backdrop {
        padding-top: max(106px, calc(var(--safe-top) + var(--tg-content-top) + 96px));
      }

      .sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        width: 82%;
        max-width: 310px;
        background: var(--bg-sidebar);
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
        z-index: 120;
        transform: translateX(-105%);
        padding-top: max(50px, calc(var(--safe-top) + var(--tg-content-top) + 42px));
        padding-bottom: calc(16px + var(--safe-bottom));
        box-shadow: 12px 0 40px rgba(0, 0, 0, 0.55);
      }

      .sidebar.open { transform: translateX(0); }
      .mobile-backdrop.open { display: block; }
      .close-sidebar-btn, .hamburger-btn { display: inline-flex; }
      .collapse-pc-btn, .fullscreen-pc-btn { display: none; }
      .composer-model-pill { display: none; }
      .msg-row.user { max-width: 90%; }
      .prompt-chips-grid { grid-template-columns: 1fr; }
      .scroll-bottom-fab { right: 16px; bottom: 82px; }
    }
  </style>
</head>
<body>

  <!-- ==================== ЗАЩИЩЁННАЯ АВТОРИЗАЦИЯ ДЛЯ БРАУЗЕРА ==================== -->
  <div id="webAuthGate" class="web-auth-gate">
    <div class="web-auth-card">
      <div class="auth-logo-circle">
        <img id="authLogoImg" src="./logo.png" alt="Aether AI" onerror="this.style.display='none';this.parentNode.innerHTML='<span style=\'color:#fff;font-weight:800;font-size:24px\'>Æ</span>'" />
      </div>
      <div class="auth-title">Вход в Aether AI</div>
      <div class="auth-desc">
        Чтобы защитить твои чаты, подписку PRO и баланс, вход из браузера выполняется только с подтверждением через Telegram.
      </div>

      <!-- Официальный Telegram Login Widget (подгружается автоматически, если указан BOT_USERNAME) -->
      <div id="tgLoginWidgetContainer" class="auth-widget-slot"></div>

      <a id="tgBotLoginLink" href="https://t.me/AetherNeural_bot?start=web_auth" target="_blank" class="tg-login-btn">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
        <span>Получить одноразовый код в Telegram</span>
      </a>

      <div class="auth-divider">или введи одноразовый код из бота</div>

      <div class="auth-code-row">
        <input type="text" id="webAuthCodeInput" class="std-input" placeholder="Код из бота (например: AE-84920)" style="text-transform:uppercase" onkeydown="if(event.key==='Enter') submitWebOneTimeCode()" />
        <button class="btn-primary" id="webAuthCodeBtn" style="white-space:nowrap" onclick="submitWebOneTimeCode()">Войти</button>
      </div>
      <div style="font-size:11.5px;color:var(--text-muted);margin-top:10px">
        Вход по чужому ID без подтверждения в Telegram заблокирован в целях безопасности.
      </div>
    </div>
  </div>

  <div class="ambient-glow"></div>
  <div id="toast" class="toast-box"></div>
  <div id="mobileBackdrop" class="mobile-backdrop" onclick="toggleSidebar(false)"></div>

  <!-- МОБИЛЬНЫЙ САЙДБАР ВЫНЕСЕН НА ВЕРХНИЙ УРОВЕНЬ DOM, ЧТОБЫ НИЧТО ЕГО НЕ ПЕРЕКРЫВАЛО -->
  <aside id="sidebar" class="sidebar">
    <div class="sidebar-header">
      <div class="brand-box" onclick="startNewChat()">
        <img id="sideLogoImg" class="brand-logo-img" alt="Logo" />
        <div id="sideLogoFallback" class="brand-logo-fallback" style="display:none">Æ</div>
        <span class="brand-name" id="brandTitleText">Aether AI</span>
      </div>
      <button class="collapse-pc-btn" title="Свернуть/развернуть меню" onclick="toggleCollapseSidebar()">
        <svg class="ico" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
      </button>
      <button class="close-sidebar-btn" onclick="toggleSidebar(false)">
        <svg class="ico" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>

    <button class="new-chat-btn" onclick="startNewChat()">
      <svg class="ico" viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
      <span>Новый чат</span>
    </button>

    <div class="nav-links">
      <div class="side-nav-item active" id="nav-chat" onclick="switchSection('chat')">
        <div class="side-nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span>Чат с ИИ</span>
        </div>
      </div>
      <div class="side-nav-item" id="nav-shop" onclick="switchSection('shop')">
        <div class="side-nav-left">
          <svg class="ico" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          <span>Подписка и пакеты</span>
        </div>
        <span class="pro-shimmer-badge">PRO</span>
      </div>
      <div class="side-nav-item" id="nav-profile" onclick="switchSection('profile')">
        <div class="side-nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>Профиль и партнёрка</span>
        </div>
      </div>
      <div class="side-nav-item" id="nav-admin" style="display:none" onclick="switchSection('admin')">
        <div class="side-nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
          <span>Админ-панель</span>
        </div>
      </div>
    </div>

    <div class="history-label">
      <span>Недавние чаты</span>
      <span style="cursor:pointer;font-size:11px;text-transform:none" onclick="clearAllSessions()">Очистить</span>
    </div>

    <div id="historyList" class="history-list"></div>

    <!-- НИЖНИЙ БЛОК: АВАТАРКА ПРОФИЛЯ + ИМЯ + НАСТРОЙКИ ТЕМЫ -->
    <div class="sidebar-footer">
      <div class="user-mini-card" onclick="switchSection('profile')">
        <div class="user-avatar-wrap" id="sideAvatarRing">
          <img id="sideUserAvatarImg" class="user-avatar-img" alt="Avatar" />
          <span id="sideUserAvatarLetter" class="user-avatar-letter">Д</span>
        </div>
        <div style="min-width:0">
          <div class="user-mini-name" id="sideUserName">Пользователь</div>
          <div class="user-mini-plan" id="sideUserPlan">Free</div>
        </div>
      </div>
      <button class="settings-gear-btn" title="Настройки" onclick="openModal('settingsModal')">
        <svg class="ico" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l-.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      </button>
    </div>
  </aside>

  <div class="app-shell">
    <!-- ==================== ПРАВАЯ ОСНОВНАЯ ОБЛАСТЬ ==================== -->
    <main class="main-stage">
      <!-- ВЕРХНЯЯ ПАНЕЛЬ -->
      <header class="stage-topbar">
        <div class="topbar-left">
          <button class="hamburger-btn" onclick="toggleSidebar(true)">
            <svg class="ico" viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <button class="model-dropdown-trigger" onclick="openModelSelector()">
            <span class="model-avatar-slot" id="topModelAvatar"></span>
            <span id="topModelName">Gemini 3.1 Pro</span>
            <svg class="ico" style="width:14px;height:14px;opacity:.7" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
        </div>

        <div class="topbar-right">
          <div class="quota-badge" id="topQuotaBadge" onclick="switchSection('shop')">
            <svg class="ico" style="width:14px;height:14px;color:#fbbf24" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <span id="topQuotaText">5 запр.</span>
          </div>
          <!-- Кнопка полного экрана для ПК -->
          <button class="fullscreen-pc-btn" id="pcFullscreenBtn" title="На весь экран" onclick="togglePcFullscreen()">
            <svg class="ico" style="width:15px;height:15px" viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
          </button>
        </div>
      </header>

      <!-- ==================== СЕКЦИЯ 1: ЧАТ ==================== -->
      <section id="sec-chat" class="view-section active">
        <div id="chatScrollArea" class="chat-scroll-area" onscroll="handleChatScroll()">
          <div class="chat-container-inner">
            <!-- ЭКРАН ПРИВЕТСТВИЯ + 4 КАРТОЧКИ-ПОДСКАЗКИ -->
            <div id="welcomeHero" class="welcome-hero">
              <div class="welcome-logo-wrap" id="welcomeLogoBox">
                <img id="heroLogoImg" alt="Logo" />
              </div>
              <h1 class="welcome-title" id="welcomeGreetingText">С чего начнем?</h1>
              <p class="welcome-sub">Выбери любую нейросеть сверху, прикрепи фото или файл через «+» и задай вопрос.</p>

              <div class="prompt-chips-grid">
                <button class="prompt-chip-card" onclick="applyPromptPreset('Напиши чистый и рабочий код на Python для ')">
                  <div class="chip-ico-wrap">
                    <svg class="ico" viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                  </div>
                  <div>
                    <div class="chip-title">Разобрать или написать код</div>
                    <div class="chip-sub">Python, JS, боты и скрипты</div>
                  </div>
                </button>

                <button class="prompt-chip-card" onclick="triggerFileInput('image/*')">
                  <div class="chip-ico-wrap">
                    <svg class="ico" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                  </div>
                  <div>
                    <div class="chip-title">Решить задачу по фото</div>
                    <div class="chip-sub">Физика, алгебра и конспекты</div>
                  </div>
                </button>

                <button class="prompt-chip-card" onclick="applyPromptPreset('Напиши структурированный и живой текст на тему: ')">
                  <div class="chip-ico-wrap">
                    <svg class="ico" viewBox="0 0 24 24"><line x1="21" y1="6" x2="3" y2="6"/><line x1="15" y1="12" x2="3" y2="12"/><line x1="17" y1="18" x2="3" y2="18"/></svg>
                  </div>
                  <div>
                    <div class="chip-title">Написать текст</div>
                    <div class="chip-sub">Посты, конспекты и выжимки</div>
                  </div>
                </button>

                <button class="prompt-chip-card" onclick="applyPromptPreset('Сравни плюсы, минусы и выбери лучший вариант для ')">
                  <div class="chip-ico-wrap">
                    <svg class="ico" viewBox="0 0 24 24"><path d="M9 18h6M10 22h4M12 2a7 7 0 0 1 4 12.7c-.6.5-1 1.3-1 2.3H9c0-1-.4-1.8-1-2.3A7 7 0 0 1 12 2z"/></svg>
                  </div>
                  <div>
                    <div class="chip-title">Сравнить идеи</div>
                    <div class="chip-sub">Анализ вариантов и мозговой штурм</div>
                  </div>
                </button>
              </div>
            </div>

            <!-- СПИСОК СООБЩЕНИЙ -->
            <div id="messagesStack" class="messages-stack" style="display:none"></div>
          </div>
        </div>

        <!-- ПАРЯЩАЯ КНОПКА БЫСТРОГО СКРОЛЛА ВНИЗ -->
        <button id="scrollBottomFab" class="scroll-bottom-fab" title="К последнему сообщению" onclick="scrollChatBottom(true)">
          <svg class="ico" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>
        </button>

        <!-- ПОЛЕ ВВОДА СНИЗУ -->
        <div class="composer-wrapper">
          <div id="plusPopover" class="plus-popover">
            <div class="popover-item" onclick="triggerFileInput('image/*')">
              <svg class="ico" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>Загрузить фото</span>
            </div>
            <div class="popover-item" onclick="triggerFileInput('.txt,.py,.js,.ts,.json,.md,.csv,.html,.css,.sql,.xml,.log')">
              <svg class="ico" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>Прикрепить файл</span>
            </div>
          </div>

          <div id="attachmentPreviewTray" class="attachment-preview-tray"></div>

          <input type="file" id="universalFileInput" style="display:none" onchange="handleFilePicked(event)" />

          <div class="composer-pill">
            <button class="plus-btn" title="Прикрепить фото или файл" onclick="togglePlusPopover(event)">
              <svg class="ico" style="width:20px;height:20px" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
            <textarea id="chatTextarea" class="chat-textarea" rows="1" placeholder="Спросить Aether AI..." oninput="autoResizeTextarea(this)" onkeydown="handleTextareaKey(event)"></textarea>
            <button class="composer-model-pill" onclick="openModelSelector()">
              <span id="pillModelShort">Gemini</span>
              <svg class="ico" style="width:13px;height:13px" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            <button class="send-circle-btn" id="sendOrStopBtn" onclick="handleSendOrStop()">
              <svg class="ico" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </section>

      <!-- ==================== СЕКЦИЯ 2: МАГАЗИН ==================== -->
      <section id="sec-shop" class="view-section">
        <div class="subpage-scroll">
          <div class="subpage-inner">
            <div class="bento-grid">
              <div class="bento-card span-2">
                <div class="card-tag">ПОДПИСКИ PRO</div>
                <div class="card-title">Полный доступ ко всем моделям</div>
                <div class="card-desc">Gemini, Claude, Grok, DeepSeek и ChatGPT без дневных ограничений.</div>
              </div>

              <div class="bento-card" onclick="openCheckout('prod:sub_trial')">
                <div class="card-tag">1 ДЕНЬ</div>
                <div class="card-title">Пробный</div>
                <div class="stat-big" id="price_sub_trial">39 ₽</div>
                <div class="card-desc" id="stars_sub_trial">или 29 Stars</div>
              </div>

              <div class="bento-card" onclick="openCheckout('prod:sub_standard')">
                <div class="card-tag">7 ДНЕЙ • ХИТ</div>
                <div class="card-title">Стандарт</div>
                <div class="stat-big" id="price_sub_standard">149 ₽</div>
                <div class="card-desc" id="stars_sub_standard">или 115 Stars</div>
              </div>

              <div class="bento-card span-2" onclick="openCheckout('prod:sub_premium')">
                <div class="card-tag">30 ДНЕЙ</div>
                <div class="card-title">Премиум подписка — <span id="price_sub_premium">349 ₽</span></div>
                <div class="card-desc" id="stars_sub_premium">или 269 Stars • Максимальная выгода</div>
              </div>

              <div class="bento-card span-2">
                <div class="card-tag">ПАКЕТЫ ЗАПРОСОВ (НЕ СГОРАЮТ)</div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
                  <button class="btn-secondary" onclick="openCheckout('prod:pack_30')">+30 запр. (99 ₽)</button>
                  <button class="btn-secondary" onclick="openCheckout('prod:pack_100')">+100 запр. (259 ₽)</button>
                  <button class="btn-secondary" onclick="openCheckout('prod:pack_300')">+300 запр. (589 ₽)</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== СЕКЦИЯ 3: ПРОФИЛЬ ==================== -->
      <section id="sec-profile" class="view-section">
        <div class="subpage-scroll">
          <div class="subpage-inner">
            <div class="bento-grid">
              <div class="bento-card span-2">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
                  <div>
                    <div class="card-tag" id="profBadge">БЕСПЛАТНЫЙ ПЛАН</div>
                    <div class="card-title" id="profFullName">Пользователь</div>
                    <div class="card-desc" id="profTgId">ID: —</div>
                  </div>
                  <button id="webLogoutBtn" class="btn-secondary" style="display:none;padding:7px 12px;font-size:12px" onclick="logoutWebSession()">Выйти</button>
                </div>
              </div>

              <div class="bento-card">
                <div class="card-tag">СЕГОДНЯ</div>
                <div class="stat-big" id="profDaily">5 / 5</div>
                <div class="card-desc">Дневной лимит</div>
              </div>

              <div class="bento-card">
                <div class="card-tag">ПАКЕТ</div>
                <div class="stat-big" id="profExtra">0</div>
                <div class="card-desc">Доп. запросов</div>
              </div>

              <div class="bento-card span-2">
                <div class="card-tag">ПРОМОКОД</div>
                <div style="display:flex;gap:8px;margin-top:8px">
                  <input type="text" id="promoInput" class="std-input" placeholder="Введи промокод..." style="text-transform:uppercase" />
                  <button class="btn-primary" onclick="applyPromo()">ОК</button>
                </div>
              </div>

              <div class="bento-card span-2">
                <div class="card-tag">ПАРТНЁРКА 25%</div>
                <div class="card-title">Баланс: <span id="profRefBal">0.00 ₽</span> (Приглашено: <span id="profRefCnt">0</span>)</div>
                <div class="card-desc" style="margin-bottom:10px">+2 запроса в день навсегда за друга и 25% с его покупок.</div>
                <button class="btn-secondary" onclick="copyRef()">Скопировать реф. ссылку</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== СЕКЦИЯ 4: АДМИНКА ==================== -->
      <section id="sec-admin" class="view-section">
        <div class="subpage-scroll">
          <div class="subpage-inner">
            <div class="bento-grid">
              <div class="bento-card">
                <div class="card-tag">ПОЛЬЗОВАТЕЛИ</div>
                <div class="stat-big" id="admUsers">0</div>
                <div class="card-desc" id="admPro">PRO: 0</div>
              </div>
              <div class="bento-card">
                <div class="card-tag">КАССА</div>
                <div class="stat-big" id="admRub">0 ₽</div>
                <div class="card-desc" id="admStars">Stars: 0</div>
              </div>
              <div class="bento-card span-2">
                <div class="card-tag">ДВИЖОК ПО УМОЛЧАНИЮ</div>
                <div class="card-title">Текущий: <span id="admEngine">gpt-6-luna</span></div>
                <div style="display:flex;gap:8px;margin-top:8px">
                  <input type="text" id="admEngineInp" class="std-input" placeholder="ID модели..." />
                  <button class="btn-primary" onclick="updateEngine()">Сохранить</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <!-- ==================== ВЫБОР МОДЕЛИ ==================== -->
  <div id="modelMenuBackdrop" class="model-menu-backdrop" onclick="if(event.target===this) closeModelSelector()">
    <div class="model-menu-card">
      <div class="model-cat-tabs" id="modelCatTabs">
        <button class="m-cat-btn active" onclick="setModelFilter('all', this)">Все</button>
        <button class="m-cat-btn" onclick="setModelFilter('gemini', this)">Gemini</button>
        <button class="m-cat-btn" onclick="setModelFilter('claude', this)">Claude</button>
        <button class="m-cat-btn" onclick="setModelFilter('gpt', this)">ChatGPT</button>
        <button class="m-cat-btn" onclick="setModelFilter('deepseek', this)">DeepSeek</button>
        <button class="m-cat-btn" onclick="setModelFilter('grok', this)">Grok</button>
      </div>
      <div id="modelOptionsList"></div>
    </div>
  </div>

  <!-- ==================== МОДАЛКА НАСТРОЕК (ТЕМА + ГРАДИЕНТ) ==================== -->
  <div id="settingsModal" class="modal-overlay" onclick="if(event.target===this) closeModal('settingsModal')">
    <div class="modal-box">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <h3 style="font-size:18px">Настройки интерфейса</h3>
        <button style="background:none;border:none;color:var(--text-muted);cursor:pointer" onclick="closeModal('settingsModal')">
          <svg class="ico" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="setting-row">
        <div>
          <div style="font-size:14px;font-weight:600">Тема оформления</div>
          <div style="font-size:12px;color:var(--text-muted)">Меняет интерфейс и подсветку кода</div>
        </div>
        <div class="theme-segment">
          <button id="btnThemeDark" class="theme-seg-btn active" onclick="setTheme('dark')">Тёмная</button>
          <button id="btnThemeLight" class="theme-seg-btn" onclick="setTheme('light')">Светлая</button>
        </div>
      </div>

      <div class="setting-row">
        <div>
          <div style="font-size:14px;font-weight:600">Фоновое свечение</div>
          <div style="font-size:12px;color:var(--text-muted)">Живой градиент по центру</div>
        </div>
        <div class="theme-segment">
          <button id="btnGradOn" class="theme-seg-btn active" onclick="setGradient(true)">Вкл</button>
          <button id="btnGradOff" class="theme-seg-btn" onclick="setGradient(false)">Выкл</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ==================== МОДАЛКА ОПЛАТЫ ==================== -->
  <div id="checkoutModal" class="modal-overlay" onclick="if(event.target===this) closeModal('checkoutModal')">
    <div class="modal-box">
      <div class="card-tag">ОФОРМЛЕНИЕ</div>
      <div class="card-title" id="chkTitle" style="font-size:18px">Тариф</div>
      <div class="card-desc" id="chkDesc" style="margin-bottom:16px">Описание</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <button class="btn-primary" id="chkSbpBtn">Оплатить через СБП</button>
        <button class="btn-secondary" id="chkStarsBtn">Telegram Stars</button>
        <button class="btn-secondary" onclick="closeModal('checkoutModal')">Отмена</button>
      </div>
    </div>
  </div>

  <script>(function(){var _0x=atob("ZG9jdW1lbnQuYWRkRXZlbnRMaXN0ZW5lcigiY29udGV4dG1lbnUiLCAoZSkgPT4geyBpZiAoIWUudGFyZ2V0LmNsb3Nlc3QoInRleHRhcmVhLCBpbnB1dCwgLm1kLWNvbnRlbnQsIHByZSwgY29kZSIpKSB7IGUucHJldmVudERlZmF1bHQoKTsgfSB9KTsgZG9jdW1lbnQuYWRkRXZlbnRMaXN0ZW5lcigia2V5ZG93biIsIChlKSA9PiB7IGNvbnN0IGsgPSAoZS5rZXkgfHwgIiIpLnRvVXBwZXJDYXNlKCk7IGlmICggayA9PT0gIkYxMiIgfHwgKGUuY3RybEtleSAmJiBlLnNoaWZ0S2V5ICYmIChrID09PSAiSSIgfHwgayA9PT0gIkoiIHx8IGsgPT09ICJDIikpIHx8IChlLmN0cmxLZXkgJiYgayA9PT0gIlUiKSB8fCAoZS5tZXRhS2V5ICYmIGUuYWx0S2V5ICYmIChrID09PSAiSSIgfHwgayA9PT0gIkoiIHx8IGsgPT09ICJVIikpICkgeyBlLnByZXZlbnREZWZhdWx0KCk7IGUuc3RvcFByb3BhZ2F0aW9uKCk7IHJldHVybiBmYWxzZTsgfSB9LCB0cnVlKTsgc2V0SW50ZXJ2YWwoKCkgPT4geyBjb25zdCB0aHJlc2hvbGQgPSAxNzA7IGNvbnN0IG9wZW5lZCA9ICh3aW5kb3cub3V0ZXJXaWR0aCAtIHdpbmRvdy5pbm5lcldpZHRoID4gdGhyZXNob2xkKSB8fCAod2luZG93Lm91dGVySGVpZ2h0IC0gd2luZG93LmlubmVySGVpZ2h0ID4gdGhyZXNob2xkKTsgaWYgKG9wZW5lZCAmJiAhaXNJbnNpZGVUZWxlZ3JhbSkgeyBkb2N1bWVudC5ib2R5LmlubmVySFRNTCA9ICIiOyB9IH0sIDE1MDApOyBjb25zdCBDVVNUT01fTE9HT19VUkwgPSAiLi9sb2dvLnBuZyI7IGNvbnN0IEFQUF9CUkFORF9OQU1FID0gIkFldGhlciBBSSI7IGNvbnN0IEJPVF9VU0VSTkFNRSA9ICJBZXRoZXJOZXVyYWxfYm90IjsgY29uc3QgUFJPVklERVJfQVZBVEFSUyA9IHsgZ2VtaW5pOiB7IGZpbGVzOiBbIi4vZ2VtaW5pLnBuZyJdLCBiZzogImxpbmVhci1ncmFkaWVudCgxMzVkZWcsIzI1NjNlYiwjMzhiZGY4KSIsIGdsb3c6ICJyZ2JhKDEzOSwgOTIsIDI0NiwgMC41NSkiLCBzdmc6IGA8c3ZnIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjE1IiBoZWlnaHQ9IjE1IiBmaWxsPSIjZmZmIj48cGF0aCBkPSJNMTIgMmMuNCA1LjIgNC44IDkuNiAxMCAxMC01LjIuNC05LjYgNC44LTEwIDEwLS40LTUuMi00LjgtOS42LTEwLTEwIDUuMi0uNCA5LjYtNC44IDEwLTEweiIvPjwvc3ZnPmAgfSwgY2xhdWRlOiB7IGZpbGVzOiBbIi4vY2xhdWRlLnBuZyIsICIuL2Nsb3VzZS5wbmciXSwgYmc6ICJsaW5lYXItZ3JhZGllbnQoMTM1ZGVnLCNkOTc3MDYsI2VhNTgwYykiLCBnbG93OiAicmdiYSgyMzQsIDg4LCAxMiwgMC41MikiLCBzdmc6IGA8c3ZnIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjE1IiBoZWlnaHQ9IjE1IiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSI+PHBhdGggZD0iTTEyIDN2MThNNC4yIDcuNWwxNS42IDlNMTkuOCA3LjVMNC4yIDE2LjUiLz48L3N2Zz5gIH0sIGdwdDogeyBmaWxlczogWyIuL2NoYXRncHQucG5nIiwgIi4vZ3B0LnBuZyJdLCBiZzogImxpbmVhci1ncmFkaWVudCgxMzVkZWcsIzA1OTY2OSwjMTBiOTgxKSIsIGdsb3c6ICJyZ2JhKDE2LCAxODUsIDEyOSwgMC41KSIsIHN2ZzogYDxzdmcgdmlld0JveD0iMCAwIDI0IDI0IiB3aWR0aD0iMTUiIGhlaWdodD0iMTUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI4Ii8+PHBhdGggZD0iTTEyIDh2OE04IDEyaDgiLz48L3N2Zz5gIH0sIGRlZXBzZWVrOiB7IGZpbGVzOiBbIi4vZGVlcHNlZWsucG5nIiwgIi4vZGVlcHNla2sucG5nIl0sIGJnOiAibGluZWFyLWdyYWRpZW50KDEzNWRlZywjM2I4MmY2LCM2MzY2ZjEpIiwgZ2xvdzogInJnYmEoNTksIDEzMCwgMjQ2LCAwLjU4KSIsIHN2ZzogYDxzdmcgdmlld0JveD0iMCAwIDI0IDI0IiB3aWR0aD0iMTUiIGhlaWdodD0iMTUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIj48cGF0aCBkPSJNMyAxNWM0LTYgMTQtNiAxOCAwLTQgNC0xNCA0LTE4IDB6Ii8+PGNpcmNsZSBjeD0iMTUiIGN5PSIxMyIgcj0iMSIgZmlsbD0iI2ZmZiIvPjwvc3ZnPmAgfSwgZ3JvazogeyBmaWxlczogWyIuL2dyb2sucG5nIl0sIGJnOiAibGluZWFyLWdyYWRpZW50KDEzNWRlZywjMzM0MTU1LCMwZjE3MmEpIiwgZ2xvdzogInJnYmEoMTQ4LCAxNjMsIDE4NCwgMC40NSkiLCBzdmc6IGA8c3ZnIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjE1IiBoZWlnaHQ9IjE1IiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMi4yIiBmaWxsPSJub25lIj48cGF0aCBkPSJNNSAxOUwxOSA1TTkgNWgxMHYxMCIvPjwvc3ZnPmAgfSB9OyBmdW5jdGlvbiBoYW5kbGVQcm92aWRlckltZ0Vycm9yKGltZ0VsLCBjYXQpIHsgY29uc3QgcCA9IFBST1ZJREVSX0FWQVRBUlNbY2F0XTsgY29uc3QgbmV4dElkeCA9IE51bWJlcihpbWdFbC5kYXRhc2V0LnRyeUlkeCB8fCAiMCIpICsgMTsgaWYgKHAgJiYgcC5maWxlcyAmJiBuZXh0SWR4IDwgcC5maWxlcy5sZW5ndGgpIHsgaW1nRWwuZGF0YXNldC50cnlJZHggPSBTdHJpbmcobmV4dElkeCk7IGltZ0VsLnNyYyA9IHAuZmlsZXNbbmV4dElkeF07IHJldHVybjsgfSBpbWdFbC5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyBpZiAoaW1nRWwubmV4dEVsZW1lbnRTaWJsaW5nKSB7IGltZ0VsLm5leHRFbGVtZW50U2libGluZy5zdHlsZS5kaXNwbGF5ID0gImdyaWQiOyB9IH0gZnVuY3Rpb24gcmVuZGVyTW9kZWxBdmF0YXJIVE1MKGNhdCwgZXh0cmFDbGFzcyA9ICIiLCBleHRyYUlkID0gIiIpIHsgY29uc3QgcCA9IFBST1ZJREVSX0FWQVRBUlNbY2F0XSB8fCBQUk9WSURFUl9BVkFUQVJTLmdwdDsgY29uc3QgaWRBdHRyID0gZXh0cmFJZCA/IGBpZD0iJHtleHRyYUlkfSJgIDogIiI7IHJldHVybiBgIDxzcGFuICR7aWRBdHRyfSBjbGFzcz0ibW9kZWwtYXZhdGFyLXNsb3QgJHtleHRyYUNsYXNzfSIgc3R5bGU9ImJhY2tncm91bmQ6JHtwLmJnfSI+IDxpbWcgc3JjPSIke3AuZmlsZXNbMF19IiBkYXRhLXRyeS1pZHg9IjAiIGFsdD0iJHtjYXR9IiBvbmVycm9yPSJoYW5kbGVQcm92aWRlckltZ0Vycm9yKHRoaXMsICcke2NhdH0nKSIgLz4gPHNwYW4gc3R5bGU9ImRpc3BsYXk6bm9uZTtwbGFjZS1pdGVtczpjZW50ZXI7d2lkdGg6MTAwJTtoZWlnaHQ6MTAwJSI+JHtwLnN2Z308L3NwYW4+IDwvc3Bhbj4gYDsgfSBjb25zdCB1cmxQYXJhbXMgPSBuZXcgVVJMU2VhcmNoUGFyYW1zKHdpbmRvdy5sb2NhdGlvbi5zZWFyY2gpOyBjb25zdCBERUZBVUxUX0ZBTExCQUNLX0FQSSA9ICJodHRwczovL2JvdC0xNzk0NjYzOTc3LTM4NDItZGFuemxlcjExLmJvdGhvc3QudGVjaCI7IGNvbnN0IEFQSV9CQVNFID0gKHVybFBhcmFtcy5nZXQoImFwaSIpIHx8IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfYXBpX2Jhc2UiKSB8fCBERUZBVUxUX0ZBTExCQUNLX0FQSSkucmVwbGFjZSgvXC8kLywgIiIpOyBpZiAodXJsUGFyYW1zLmdldCgiYXBpIikpIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJhZXRoZXJfYXBpX2Jhc2UiLCBBUElfQkFTRSk7IGNvbnN0IHRnID0gd2luZG93LlRlbGVncmFtICYmIHdpbmRvdy5UZWxlZ3JhbS5XZWJBcHAgPyB3aW5kb3cuVGVsZWdyYW0uV2ViQXBwIDogbnVsbDsgY29uc3QgaXNJbnNpZGVUZWxlZ3JhbSA9IEJvb2xlYW4odGcgJiYgdGcuaW5pdERhdGEgJiYgdGcuaW5pdERhdGEubGVuZ3RoID4gMCAmJiB0Zy5pbml0RGF0YVVuc2FmZT8udXNlcj8uaWQpOyBpZiAodGcpIHsgdGcucmVhZHkoKTsgdGcuZXhwYW5kKCk7IGlmIChpc0luc2lkZVRlbGVncmFtICYmIHR5cGVvZiB0Zy5yZXF1ZXN0RnVsbHNjcmVlbiA9PT0gImZ1bmN0aW9uIikgeyB0cnkgeyB0Zy5yZXF1ZXN0RnVsbHNjcmVlbigpOyB9IGNhdGNoIChlKSB7fSB9IH0gZG9jdW1lbnQuYWRkRXZlbnRMaXN0ZW5lcigia2V5ZG93biIsIChldikgPT4geyBpZiAoZXYua2V5ID09PSAiRjExIikgeyBldi5wcmV2ZW50RGVmYXVsdCgpOyB0b2dnbGVQY0Z1bGxzY3JlZW4oKTsgfSB9KTsgZnVuY3Rpb24gdG9nZ2xlUGNGdWxsc2NyZWVuKCkgeyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgaWYgKGlzSW5zaWRlVGVsZWdyYW0gJiYgdGcpIHsgdHJ5IHsgaWYgKHRnLmlzRnVsbHNjcmVlbiAmJiB0eXBlb2YgdGcuZXhpdEZ1bGxzY3JlZW4gPT09ICJmdW5jdGlvbiIpIHsgdGcuZXhpdEZ1bGxzY3JlZW4oKTsgfSBlbHNlIGlmICh0eXBlb2YgdGcucmVxdWVzdEZ1bGxzY3JlZW4gPT09ICJmdW5jdGlvbiIpIHsgdGcucmVxdWVzdEZ1bGxzY3JlZW4oKTsgfSBlbHNlIHsgdGcuZXhwYW5kKCk7IH0gcmV0dXJuOyB9IGNhdGNoIChlKSB7fSB9IGlmICghZG9jdW1lbnQuZnVsbHNjcmVlbkVsZW1lbnQpIHsgZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50LnJlcXVlc3RGdWxsc2NyZWVuPy4oKS5jYXRjaCgoKSA9PiB7fSk7IH0gZWxzZSB7IGRvY3VtZW50LmV4aXRGdWxsc2NyZWVuPy4oKS5jYXRjaCgoKSA9PiB7fSk7IH0gfSB3aW5kb3cub25UZWxlZ3JhbUF1dGggPSBhc3luYyBmdW5jdGlvbih0Z1VzZXIpIHsgaWYgKCF0Z1VzZXIgfHwgIXRnVXNlci5pZCB8fCAhdGdVc2VyLmhhc2gpIHJldHVybjsgdHJ5IHsgY29uc3QgcmVzID0gYXdhaXQgZmV0Y2goQVBJX0JBU0UgKyAiL2FwaS9hdXRoL3RlbGVncmFtLXdpZGdldCIsIHsgbWV0aG9kOiAiUE9TVCIsIGhlYWRlcnM6IHsgIkNvbnRlbnQtVHlwZSI6ICJhcHBsaWNhdGlvbi9qc29uIiB9LCBib2R5OiBKU09OLnN0cmluZ2lmeSh0Z1VzZXIpIH0pOyBjb25zdCBkYXRhID0gYXdhaXQgcmVzLmpzb24oKTsgaWYgKCFyZXMub2sgfHwgIWRhdGEub2sgfHwgIWRhdGEudG9rZW4pIHsgdGhyb3cgbmV3IEVycm9yKGRhdGEuZXJyb3IgfHwgItCe0YjQuNCx0LrQsCDQv9GA0L7QstC10YDQutC4INC/0L7QtNC/0LjRgdC4IFRlbGVncmFtIik7IH0gbG9jYWxTdG9yYWdlLnNldEl0ZW0oImFldGhlcl93ZWJfdG9rZW4iLCBkYXRhLnRva2VuKTsgbG9jYWxTdG9yYWdlLnNldEl0ZW0oImFldGhlcl93ZWJfdWlkIiwgU3RyaW5nKHRnVXNlci5pZCkpOyBsb2NhbFN0b3JhZ2Uuc2V0SXRlbSgiYWV0aGVyX3dlYl9uYW1lIiwgdGdVc2VyLmZpcnN0X25hbWUgfHwgdGdVc2VyLnVzZXJuYW1lIHx8ICLQn9C+0LvRjNC30L7QstCw0YLQtdC70YwiKTsgaWYgKHRnVXNlci5waG90b191cmwpIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJhZXRoZXJfd2ViX3Bob3RvIiwgdGdVc2VyLnBob3RvX3VybCk7IFNUQVRFLnVzZXJfaWQgPSBOdW1iZXIodGdVc2VyLmlkKTsgU1RBVEUud2ViX3Rva2VuID0gZGF0YS50b2tlbjsgU1RBVEUuZnVsbF9uYW1lID0gdGdVc2VyLmZpcnN0X25hbWUgfHwgdGdVc2VyLnVzZXJuYW1lIHx8ICLQn9C+0LvRjNC30L7QstCw0YLQtdC70YwiOyBTVEFURS5waG90b191cmwgPSB0Z1VzZXIucGhvdG9fdXJsIHx8ICIiOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViQXV0aEdhdGUiKS5jbGFzc0xpc3QucmVtb3ZlKCJhY3RpdmUiKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlYkxvZ291dEJ0biIpLnN0eWxlLmRpc3BsYXkgPSAiaW5saW5lLWZsZXgiOyB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBzaG93VG9hc3QoItCS0YXQvtC0INGH0LXRgNC10LcgVGVsZWdyYW0g0LLRi9C/0L7Qu9C90LXQvSIpOyBhd2FpdCBpbml0QXBwKCk7IH0gY2F0Y2ggKGUpIHsgc2hvd1RvYXN0KGUubWVzc2FnZSk7IH0gfTsgZnVuY3Rpb24gbW91bnRUZWxlZ3JhbUxvZ2luV2lkZ2V0KCkgeyBjb25zdCBzbG90ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInRnTG9naW5XaWRnZXRDb250YWluZXIiKTsgaWYgKCFzbG90IHx8IHNsb3QuZGF0YXNldC5tb3VudGVkID09PSAiMSIpIHJldHVybjsgc2xvdC5kYXRhc2V0Lm1vdW50ZWQgPSAiMSI7IGNvbnN0IHMgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCJzY3JpcHQiKTsgcy5hc3luYyA9IHRydWU7IHMuc3JjID0gImh0dHBzOi8vdGVsZWdyYW0ub3JnL2pzL3RlbGVncmFtLXdpZGdldC5qcz8yMiI7IHMuc2V0QXR0cmlidXRlKCJkYXRhLXRlbGVncmFtLWxvZ2luIiwgQk9UX1VTRVJOQU1FKTsgcy5zZXRBdHRyaWJ1dGUoImRhdGEtc2l6ZSIsICJsYXJnZSIpOyBzLnNldEF0dHJpYnV0ZSgiZGF0YS1yYWRpdXMiLCAiMTIiKTsgcy5zZXRBdHRyaWJ1dGUoImRhdGEtb25hdXRoIiwgIm9uVGVsZWdyYW1BdXRoKHVzZXIpIik7IHMuc2V0QXR0cmlidXRlKCJkYXRhLXJlcXVlc3QtYWNjZXNzIiwgIndyaXRlIik7IHNsb3QuYXBwZW5kQ2hpbGQocyk7IH0gZnVuY3Rpb24gY2hlY2tXZWJCcm93c2VyQXV0aCgpIHsgaWYgKGlzSW5zaWRlVGVsZWdyYW0pIHsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlYkF1dGhHYXRlIikuY2xhc3NMaXN0LnJlbW92ZSgiYWN0aXZlIik7IHJldHVybiB0cnVlOyB9IGNvbnN0IHVybFRva2VuID0gdXJsUGFyYW1zLmdldCgidG9rZW4iKSB8fCB1cmxQYXJhbXMuZ2V0KCJhdXRoX3Rva2VuIik7IGNvbnN0IHVybFVpZCA9IHVybFBhcmFtcy5nZXQoInVpZCIpOyBpZiAodXJsVG9rZW4gJiYgdXJsVG9rZW4ubGVuZ3RoID49IDE2KSB7IGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJhZXRoZXJfd2ViX3Rva2VuIiwgdXJsVG9rZW4pOyBpZiAodXJsVWlkKSBsb2NhbFN0b3JhZ2Uuc2V0SXRlbSgiYWV0aGVyX3dlYl91aWQiLCBTdHJpbmcoTnVtYmVyKHVybFVpZCkpKTsgdHJ5IHsgY29uc3QgY2xlYW5VcmwgPSB3aW5kb3cubG9jYXRpb24ub3JpZ2luICsgd2luZG93LmxvY2F0aW9uLnBhdGhuYW1lOyB3aW5kb3cuaGlzdG9yeS5yZXBsYWNlU3RhdGUoe30sIGRvY3VtZW50LnRpdGxlLCBjbGVhblVybCk7IH0gY2F0Y2ggKGUpIHt9IH0gY29uc3Qgc2F2ZWRUb2tlbiA9IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfd2ViX3Rva2VuIikgfHwgIiI7IGNvbnN0IHNhdmVkVWlkID0gTnVtYmVyKGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfd2ViX3VpZCIpIHx8ICIwIik7IGlmIChzYXZlZFRva2VuLmxlbmd0aCA+PSAxNiAmJiBzYXZlZFVpZCA+IDApIHsgU1RBVEUudXNlcl9pZCA9IHNhdmVkVWlkOyBTVEFURS53ZWJfdG9rZW4gPSBzYXZlZFRva2VuOyBTVEFURS5mdWxsX25hbWUgPSBsb2NhbFN0b3JhZ2UuZ2V0SXRlbSgiYWV0aGVyX3dlYl9uYW1lIikgfHwgItCf0L7Qu9GM0LfQvtCy0LDRgtC10LvRjCI7IFNUQVRFLnBob3RvX3VybCA9IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfd2ViX3Bob3RvIikgfHwgIiI7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ3ZWJBdXRoR2F0ZSIpLmNsYXNzTGlzdC5yZW1vdmUoImFjdGl2ZSIpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViTG9nb3V0QnRuIikuc3R5bGUuZGlzcGxheSA9ICJpbmxpbmUtZmxleCI7IHJldHVybiB0cnVlOyB9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ0Z0JvdExvZ2luTGluayIpLmhyZWYgPSBgaHR0cHM6Ly90Lm1lLyR7Qk9UX1VTRVJOQU1FfT9zdGFydD13ZWJfYXV0aGA7IG1vdW50VGVsZWdyYW1Mb2dpbldpZGdldCgpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViQXV0aEdhdGUiKS5jbGFzc0xpc3QuYWRkKCJhY3RpdmUiKTsgcmV0dXJuIGZhbHNlOyB9IGFzeW5jIGZ1bmN0aW9uIHN1Ym1pdFdlYk9uZVRpbWVDb2RlKCkgeyBjb25zdCBpbnAgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViQXV0aENvZGVJbnB1dCIpOyBjb25zdCBidG4gPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViQXV0aENvZGVCdG4iKTsgY29uc3QgY29kZSA9IChpbnAudmFsdWUgfHwgIiIpLnRyaW0oKS50b1VwcGVyQ2FzZSgpOyBpZiAoY29kZS5sZW5ndGggPCA0KSB7IHNob3dUb2FzdCgi0JLQstC10LTQuCDQvtC00L3QvtGA0LDQt9C+0LLRi9C5INC60L7QtCDQuNC3IFRlbGVncmFtLdCx0L7RgtCwIik7IHJldHVybjsgfSBidG4uZGlzYWJsZWQgPSB0cnVlOyBidG4udGV4dENvbnRlbnQgPSAi0J/RgNC+0LLQtdGA0LrQsC4uLiI7IHRyeSB7IGNvbnN0IHJlcyA9IGF3YWl0IGZldGNoKEFQSV9CQVNFICsgIi9hcGkvYXV0aC92ZXJpZnktY29kZSIsIHsgbWV0aG9kOiAiUE9TVCIsIGhlYWRlcnM6IHsgIkNvbnRlbnQtVHlwZSI6ICJhcHBsaWNhdGlvbi9qc29uIiB9LCBib2R5OiBKU09OLnN0cmluZ2lmeSh7IGNvZGUgfSkgfSk7IGNvbnN0IGRhdGEgPSBhd2FpdCByZXMuanNvbigpOyBpZiAoIXJlcy5vayB8fCAhZGF0YS5vayB8fCAhZGF0YS50b2tlbiB8fCAhZGF0YS51c2VyX2lkKSB7IHRocm93IG5ldyBFcnJvcihkYXRhLmVycm9yIHx8ICLQndC10LLQtdGA0L3Ri9C5INC40LvQuCDQv9GA0L7RgdGA0L7Rh9C10L3QvdGL0Lkg0LrQvtC0Iik7IH0gbG9jYWxTdG9yYWdlLnNldEl0ZW0oImFldGhlcl93ZWJfdG9rZW4iLCBkYXRhLnRva2VuKTsgbG9jYWxTdG9yYWdlLnNldEl0ZW0oImFldGhlcl93ZWJfdWlkIiwgU3RyaW5nKGRhdGEudXNlcl9pZCkpOyBpZiAoZGF0YS5mdWxsX25hbWUpIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJhZXRoZXJfd2ViX25hbWUiLCBkYXRhLmZ1bGxfbmFtZSk7IFNUQVRFLnVzZXJfaWQgPSBOdW1iZXIoZGF0YS51c2VyX2lkKTsgU1RBVEUud2ViX3Rva2VuID0gZGF0YS50b2tlbjsgU1RBVEUuZnVsbF9uYW1lID0gZGF0YS5mdWxsX25hbWUgfHwgItCf0L7Qu9GM0LfQvtCy0LDRgtC10LvRjCI7IGlucC52YWx1ZSA9ICIiOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2ViQXV0aEdhdGUiKS5jbGFzc0xpc3QucmVtb3ZlKCJhY3RpdmUiKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlYkxvZ291dEJ0biIpLnN0eWxlLmRpc3BsYXkgPSAiaW5saW5lLWZsZXgiOyB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBzaG93VG9hc3QoItCQ0LLRgtC+0YDQuNC30LDRhtC40Y8g0L/QvtC00YLQstC10YDQttC00LXQvdCwIik7IGF3YWl0IGluaXRBcHAoKTsgfSBjYXRjaCAoZSkgeyBzaG93VG9hc3QoZS5tZXNzYWdlKTsgfSBmaW5hbGx5IHsgYnRuLmRpc2FibGVkID0gZmFsc2U7IGJ0bi50ZXh0Q29udGVudCA9ICLQktC+0LnRgtC4IjsgfSB9IGZ1bmN0aW9uIGxvZ291dFdlYlNlc3Npb24oKSB7IGxvY2FsU3RvcmFnZS5yZW1vdmVJdGVtKCJhZXRoZXJfd2ViX3Rva2VuIik7IGxvY2FsU3RvcmFnZS5yZW1vdmVJdGVtKCJhZXRoZXJfd2ViX3VpZCIpOyBsb2NhbFN0b3JhZ2UucmVtb3ZlSXRlbSgiYWV0aGVyX3dlYl9uYW1lIik7IGxvY2FsU3RvcmFnZS5yZW1vdmVJdGVtKCJhZXRoZXJfd2ViX3Bob3RvIik7IFNUQVRFLnVzZXJfaWQgPSAwOyBTVEFURS53ZWJfdG9rZW4gPSAiIjsgY2hlY2tXZWJCcm93c2VyQXV0aCgpOyB9IGZ1bmN0aW9uIHRyaWdnZXJIYXB0aWNTdWNjZXNzKCkgeyB0cnkgeyB0Zz8uSGFwdGljRmVlZGJhY2s/Lm5vdGlmaWNhdGlvbk9jY3VycmVkKCJzdWNjZXNzIik7IH0gY2F0Y2ggKGUpIHt9IH0gZnVuY3Rpb24gdHJpZ2dlckhhcHRpY0xpZ2h0KCkgeyB0cnkgeyB0Zz8uSGFwdGljRmVlZGJhY2s/LmltcGFjdE9jY3VycmVkKCJsaWdodCIpOyB9IGNhdGNoIChlKSB7fSB9IGlmICh3aW5kb3cubWFya2VkKSB7IG1hcmtlZC5zZXRPcHRpb25zKHsgYnJlYWtzOiB0cnVlLCBnZm06IHRydWUgfSk7IH0gZnVuY3Rpb24gcmVuZGVyUmljaE1hcmtkb3duQW5kTWF0aChjb250YWluZXJFbCwgcmF3VGV4dCkgeyBjb25zdCB0ZXh0ID0gU3RyaW5nKHJhd1RleHQgfHwgIiIpOyBpZiAoIXdpbmRvdy5tYXJrZWQpIHsgY29udGFpbmVyRWwudGV4dENvbnRlbnQgPSB0ZXh0OyByZXR1cm47IH0gY29uc3QgbWF0aEJsb2NrcyA9IFtdOyBsZXQgcHJvdGVjdGVkVGV4dCA9IHRleHQgLnJlcGxhY2UoL1wkXCQoW1xzXFNdKz8pXCRcJC9nLCAoXywgZXEpID0+IHsgY29uc3QgaWQgPSBgQEBNQVRIX0JMT0NLXyR7bWF0aEJsb2Nrcy5sZW5ndGh9QEBgOyBtYXRoQmxvY2tzLnB1c2goeyBpZCwgZGlzcGxheTogdHJ1ZSwgZXEgfSk7IHJldHVybiBpZDsgfSkgLnJlcGxhY2UoL1xcXFsoW1xzXFNdKz8pXFxcXS9nLCAoXywgZXEpID0+IHsgY29uc3QgaWQgPSBgQEBNQVRIX0JMT0NLXyR7bWF0aEJsb2Nrcy5sZW5ndGh9QEBgOyBtYXRoQmxvY2tzLnB1c2goeyBpZCwgZGlzcGxheTogdHJ1ZSwgZXEgfSk7IHJldHVybiBpZDsgfSkgLnJlcGxhY2UoL1xcXCgoW1xzXFNdKz8pXFxcKS9nLCAoXywgZXEpID0+IHsgY29uc3QgaWQgPSBgQEBNQVRIX0JMT0NLXyR7bWF0aEJsb2Nrcy5sZW5ndGh9QEBgOyBtYXRoQmxvY2tzLnB1c2goeyBpZCwgZGlzcGxheTogZmFsc2UsIGVxIH0pOyByZXR1cm4gaWQ7IH0pIC5yZXBsYWNlKC8oXnxbXlxcJF0pXCQoW15ccyRdW14kXG5dKj9bXlxzJF18W15ccyRdKVwkKD8hXCQpL2csIChtLCBwcmVmaXgsIGVxKSA9PiB7IGNvbnN0IGlkID0gYEBATUFUSF9CTE9DS18ke21hdGhCbG9ja3MubGVuZ3RofUBAYDsgbWF0aEJsb2Nrcy5wdXNoKHsgaWQsIGRpc3BsYXk6IGZhbHNlLCBlcSB9KTsgcmV0dXJuIHByZWZpeCArIGlkOyB9KTsgbGV0IGh0bWwgPSBtYXJrZWQucGFyc2UocHJvdGVjdGVkVGV4dCk7IG1hdGhCbG9ja3MuZm9yRWFjaChpdGVtID0+IHsgY29uc3QgZGVsaW0gPSBpdGVtLmRpc3BsYXkgPyBgJCQke2l0ZW0uZXF9JCRgIDogYCQke2l0ZW0uZXF9JGA7IGh0bWwgPSBodG1sLnJlcGxhY2UoaXRlbS5pZCwgZGVsaW0pOyB9KTsgY29udGFpbmVyRWwuaW5uZXJIVE1MID0gaHRtbDsgY29udGFpbmVyRWwucXVlcnlTZWxlY3RvckFsbCgicHJlIikuZm9yRWFjaChwcmVFbCA9PiB7IGNvbnN0IGNvZGVFbCA9IHByZUVsLnF1ZXJ5U2VsZWN0b3IoImNvZGUiKTsgaWYgKCFjb2RlRWwpIHJldHVybjsgaWYgKHdpbmRvdy5obGpzKSB7IGhsanMuaGlnaGxpZ2h0RWxlbWVudChjb2RlRWwpOyB9IGNvbnN0IGxhbmdNYXRjaCA9IChjb2RlRWwuY2xhc3NOYW1lIHx8ICIiKS5tYXRjaCgvbGFuZ3VhZ2UtKFthLXpBLVowLTlfKy1dKykvKTsgY29uc3QgbGFuZ05hbWUgPSBsYW5nTWF0Y2ggPyBsYW5nTWF0Y2hbMV0gOiAiY29kZSI7IGNvbnN0IHdyYXBwZXIgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCJkaXYiKTsgd3JhcHBlci5jbGFzc05hbWUgPSAiY29kZS1ibG9jay13cmFwcGVyIjsgY29uc3QgaGVhZGVyID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgiZGl2Iik7IGhlYWRlci5jbGFzc05hbWUgPSAiY29kZS1ibG9jay1oZWFkZXIiOyBjb25zdCBsYW5nU3BhbiA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoInNwYW4iKTsgbGFuZ1NwYW4udGV4dENvbnRlbnQgPSBsYW5nTmFtZTsgY29uc3QgY29weUJ0biA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoImJ1dHRvbiIpOyBjb3B5QnRuLmNsYXNzTmFtZSA9ICJjb3B5LWNvZGUtYnRuIjsgY29weUJ0bi50ZXh0Q29udGVudCA9ICLQmtC+0L/QuNGA0L7QstCw0YLRjCDQutC+0LQiOyBjb3B5QnRuLm9uY2xpY2sgPSAoKSA9PiB7IG5hdmlnYXRvci5jbGlwYm9hcmQ/LndyaXRlVGV4dChjb2RlRWwuaW5uZXJUZXh0KTsgdHJpZ2dlckhhcHRpY1N1Y2Nlc3MoKTsgY29weUJ0bi50ZXh0Q29udGVudCA9ICLQodC60L7Qv9C40YDQvtCy0LDQvdC+Ijsgc2V0VGltZW91dCgoKSA9PiB7IGNvcHlCdG4udGV4dENvbnRlbnQgPSAi0JrQvtC/0LjRgNC+0LLQsNGC0Ywg0LrQvtC0IjsgfSwgMjAwMCk7IH07IGhlYWRlci5hcHBlbmRDaGlsZChsYW5nU3Bhbik7IGhlYWRlci5hcHBlbmRDaGlsZChjb3B5QnRuKTsgcHJlRWwucGFyZW50Tm9kZS5pbnNlcnRCZWZvcmUod3JhcHBlciwgcHJlRWwpOyB3cmFwcGVyLmFwcGVuZENoaWxkKGhlYWRlcik7IHdyYXBwZXIuYXBwZW5kQ2hpbGQocHJlRWwpOyB9KTsgaWYgKHdpbmRvdy5yZW5kZXJNYXRoSW5FbGVtZW50KSB7IHRyeSB7IHJlbmRlck1hdGhJbkVsZW1lbnQoY29udGFpbmVyRWwsIHsgZGVsaW1pdGVyczogWyB7IGxlZnQ6ICIkJCIsIHJpZ2h0OiAiJCQiLCBkaXNwbGF5OiB0cnVlIH0sIHsgbGVmdDogIiQiLCByaWdodDogIiQiLCBkaXNwbGF5OiBmYWxzZSB9LCB7IGxlZnQ6ICJcXCgiLCByaWdodDogIlxcKSIsIGRpc3BsYXk6IGZhbHNlIH0sIHsgbGVmdDogIlxcWyIsIHJpZ2h0OiAiXFxdIiwgZGlzcGxheTogdHJ1ZSB9IF0sIHRocm93T25FcnJvcjogZmFsc2UgfSk7IH0gY2F0Y2ggKGUpIHt9IH0gfSBmdW5jdGlvbiBnZXRVc2VyRGlzcGxheU5hbWUoKSB7IGNvbnN0IHUgPSB0Zz8uaW5pdERhdGFVbnNhZmU/LnVzZXI7IGlmICh1Py5maXJzdF9uYW1lICYmIHUuZmlyc3RfbmFtZS50cmltKCkpIHJldHVybiB1LmZpcnN0X25hbWUudHJpbSgpOyBpZiAodT8udXNlcm5hbWUgJiYgdS51c2VybmFtZS50cmltKCkpIHJldHVybiAiQCIgKyB1LnVzZXJuYW1lLnRyaW0oKTsgaWYgKFNUQVRFLmZ1bGxfbmFtZSAmJiBTVEFURS5mdWxsX25hbWUgIT09ICLQn9C+0LvRjNC30L7QstCw0YLQtdC70YwiKSByZXR1cm4gU1RBVEUuZnVsbF9uYW1lOyByZXR1cm4gItCU0LDQvdC40LjQuyI7IH0gZnVuY3Rpb24gYXBwbHlVc2VyUHJvZmlsZUF2YXRhcigpIHsgY29uc3QgdSA9IHRnPy5pbml0RGF0YVVuc2FmZT8udXNlcjsgY29uc3QgbmFtZSA9IGdldFVzZXJEaXNwbGF5TmFtZSgpOyBjb25zdCBmaXJzdExldHRlciA9IG5hbWUucmVwbGFjZSgiQCIsICIiKS5jaGFyQXQoMCkudG9VcHBlckNhc2UoKSB8fCAi0JQiOyBjb25zdCBpbWdFbCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzaWRlVXNlckF2YXRhckltZyIpOyBjb25zdCBsZXR0ZXJFbCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzaWRlVXNlckF2YXRhckxldHRlciIpOyBjb25zdCByaW5nRWwgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgic2lkZUF2YXRhclJpbmciKTsgY29uc3QgcGxhbkVsID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNpZGVVc2VyUGxhbiIpOyBsZXR0ZXJFbC50ZXh0Q29udGVudCA9IGZpcnN0TGV0dGVyOyBjb25zdCBpc1BybyA9IEJvb2xlYW4oU1RBVEUuaXNfcHJvIHx8IFNUQVRFLmlzX2FkbWluKTsgcmluZ0VsLmNsYXNzTGlzdC50b2dnbGUoInByby1yaW5nIiwgaXNQcm8pOyBpZiAoaXNQcm8pIHsgcGxhbkVsLmlubmVySFRNTCA9IGA8c3BhbiBjbGFzcz0icHJvLXNoaW1tZXItYmFkZ2UiIHN0eWxlPSJmb250LXNpemU6OS41cHg7cGFkZGluZzoxcHggNnB4Ij5QUk88L3NwYW4+YDsgfSBlbHNlIHsgcGxhbkVsLnRleHRDb250ZW50ID0gIkZyZWUiOyB9IGNvbnN0IGZhbGxiYWNrQXBpQXZhdGFyID0gU1RBVEUudXNlcl9pZCA/IGAke0FQSV9CQVNFfS9hcGkvYXZhdGFyLyR7U1RBVEUudXNlcl9pZH1gIDogIiI7IGNvbnN0IHBob3RvVXJsID0gdT8ucGhvdG9fdXJsIHx8IFNUQVRFLnBob3RvX3VybCB8fCBmYWxsYmFja0FwaUF2YXRhcjsgaWYgKHBob3RvVXJsKSB7IGltZ0VsLnNyYyA9IHBob3RvVXJsOyBpbWdFbC5vbmxvYWQgPSAoKSA9PiB7IGltZ0VsLnN0eWxlLmRpc3BsYXkgPSAiYmxvY2siOyBsZXR0ZXJFbC5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyB9OyBpbWdFbC5vbmVycm9yID0gKCkgPT4geyBpbWdFbC5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyBsZXR0ZXJFbC5zdHlsZS5kaXNwbGF5ID0gImJsb2NrIjsgfTsgfSBlbHNlIHsgaW1nRWwuc3R5bGUuZGlzcGxheSA9ICJub25lIjsgbGV0dGVyRWwuc3R5bGUuZGlzcGxheSA9ICJibG9jayI7IH0gfSBmdW5jdGlvbiBnZXRSYW5kb21HcmVldGluZyhuYW1lKSB7IGNvbnN0IHBocmFzZXMgPSBbIGAke25hbWV9LCDRgSDRh9C10LPQviDQvdCw0YfQvdC10Lw/YCwgYNCf0YDQuNCy0LXRgiwgJHtuYW1lfSEg0JrQsNC60LjQtSDQt9Cw0LTQsNGH0Lgg0YDQsNC30LHQtdGA0ZHQvCDRgdC10LPQvtC00L3Rjz9gLCBgJHtuYW1lfSwg0LPQvtGC0L7QsiDQuiDRgNCw0LHQvtGC0LUuINCeINGH0ZHQvCDQv9C+0LTRg9C80LDQtdC8P2AsIGDQoSDQstC+0LfQstGA0LDRidC10L3QuNC10LwsICR7bmFtZX0hINCn0YLQviDRgdC+0LfQtNCw0LTQuNC8INC40LvQuCDRgNC10YjQuNC8P2AsIGAke25hbWV9LCDQv9GA0LjQstC10YIhINCX0LDQtNCw0Lkg0LLQvtC/0YDQvtGBINC40LvQuCDQt9Cw0LrQuNC90Ywg0YTQsNC50LsuYCwgYNCd0LAg0YHQstGP0LfQuCwgJHtuYW1lfS4g0KEg0YfQtdCz0L4g0YHRgtCw0YDRgtGD0LXQvD9gIF07IHJldHVybiBwaHJhc2VzW01hdGguZmxvb3IoTWF0aC5yYW5kb20oKSAqIHBocmFzZXMubGVuZ3RoKV07IH0gZnVuY3Rpb24gc2V0VGhlbWUodGhlbWUpIHsgbG9jYWxTdG9yYWdlLnNldEl0ZW0oInVpX3RoZW1lIiwgdGhlbWUpOyBjb25zdCBpc0xpZ2h0ID0gdGhlbWUgPT09ICJsaWdodCI7IGRvY3VtZW50LmJvZHkuY2xhc3NMaXN0LnRvZ2dsZSgidGhlbWUtbGlnaHQiLCBpc0xpZ2h0KTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImJ0blRoZW1lRGFyayIpLmNsYXNzTGlzdC50b2dnbGUoImFjdGl2ZSIsICFpc0xpZ2h0KTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImJ0blRoZW1lTGlnaHQiKS5jbGFzc0xpc3QudG9nZ2xlKCJhY3RpdmUiLCBpc0xpZ2h0KTsgY29uc3QgaGxqc0xpbmsgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiaGxqc1RoZW1lTGluayIpOyBpZiAoaGxqc0xpbmspIHsgaGxqc0xpbmsuaHJlZiA9IGlzTGlnaHQgPyAiaHR0cHM6Ly9jZG5qcy5jbG91ZGZsYXJlLmNvbS9hamF4L2xpYnMvaGlnaGxpZ2h0LmpzLzExLjkuMC9zdHlsZXMvYXRvbS1vbmUtbGlnaHQubWluLmNzcyIgOiAiaHR0cHM6Ly9jZG5qcy5jbG91ZGZsYXJlLmNvbS9hamF4L2xpYnMvaGlnaGxpZ2h0LmpzLzExLjkuMC9zdHlsZXMvYXRvbS1vbmUtZGFyay5taW4uY3NzIjsgfSBpZiAodGcgJiYgdGcuc2V0SGVhZGVyQ29sb3IpIHsgdHJ5IHsgY29uc3QgYmcgPSBpc0xpZ2h0ID8gIiNmN2Y5ZmUiIDogIiMwOTBiMTAiOyB0Zy5zZXRIZWFkZXJDb2xvcihiZyk7IHRnLnNldEJhY2tncm91bmRDb2xvcihiZyk7IH0gY2F0Y2ggKGUpIHt9IH0gfSBmdW5jdGlvbiBzZXRHcmFkaWVudChlbmFibGVkKSB7IGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJ1aV9ncmFkaWVudCIsIGVuYWJsZWQgPyAiMSIgOiAiMCIpOyBkb2N1bWVudC5ib2R5LmNsYXNzTGlzdC50b2dnbGUoIm5vLWdyYWRpZW50IiwgIWVuYWJsZWQpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiYnRuR3JhZE9uIikuY2xhc3NMaXN0LnRvZ2dsZSgiYWN0aXZlIiwgZW5hYmxlZCk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJidG5HcmFkT2ZmIikuY2xhc3NMaXN0LnRvZ2dsZSgiYWN0aXZlIiwgIWVuYWJsZWQpOyB9IGZ1bmN0aW9uIHRvZ2dsZUNvbGxhcHNlU2lkZWJhcigpIHsgdHJpZ2dlckhhcHRpY0xpZ2h0KCk7IGNvbnN0IHNiID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNpZGViYXIiKTsgY29uc3QgaXNDb2xsYXBzZWQgPSBzYi5jbGFzc0xpc3QudG9nZ2xlKCJjb2xsYXBzZWQiKTsgbG9jYWxTdG9yYWdlLnNldEl0ZW0oInNpZGViYXJfY29sbGFwc2VkIiwgaXNDb2xsYXBzZWQgPyAiMSIgOiAiMCIpOyB9IGZ1bmN0aW9uIGluaXRTYXZlZEFwcGVhcmFuY2UoKSB7IGNvbnN0IHNhdmVkVGhlbWUgPSBsb2NhbFN0b3JhZ2UuZ2V0SXRlbSgidWlfdGhlbWUiKSB8fCAiZGFyayI7IGNvbnN0IHNhdmVkR3JhZCA9IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJ1aV9ncmFkaWVudCIpICE9PSAiMCI7IGNvbnN0IHNhdmVkQ29sbGFwc2VkID0gbG9jYWxTdG9yYWdlLmdldEl0ZW0oInNpZGViYXJfY29sbGFwc2VkIikgPT09ICIxIjsgc2V0VGhlbWUoc2F2ZWRUaGVtZSk7IHNldEdyYWRpZW50KHNhdmVkR3JhZCk7IGlmIChzYXZlZENvbGxhcHNlZCAmJiB3aW5kb3cuaW5uZXJXaWR0aCA+IDc2OCkgeyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgic2lkZWJhciIpLmNsYXNzTGlzdC5hZGQoImNvbGxhcHNlZCIpOyB9IGNvbnN0IHNpZGVJbWcgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgic2lkZUxvZ29JbWciKTsgY29uc3QgaGVyb0ltZyA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJoZXJvTG9nb0ltZyIpOyBjb25zdCBoZXJvQm94ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlbGNvbWVMb2dvQm94Iik7IGNvbnN0IGZhbGxiYWNrID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNpZGVMb2dvRmFsbGJhY2siKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImJyYW5kVGl0bGVUZXh0IikudGV4dENvbnRlbnQgPSBBUFBfQlJBTkRfTkFNRTsgc2lkZUltZy5zcmMgPSBDVVNUT01fTE9HT19VUkw7IGhlcm9JbWcuc3JjID0gQ1VTVE9NX0xPR09fVVJMOyBzaWRlSW1nLm9uZXJyb3IgPSAoKSA9PiB7IHNpZGVJbWcuc3R5bGUuZGlzcGxheSA9ICJub25lIjsgZmFsbGJhY2suc3R5bGUuZGlzcGxheSA9ICJncmlkIjsgfTsgaGVyb0ltZy5vbmVycm9yID0gKCkgPT4geyBoZXJvSW1nLnN0eWxlLmRpc3BsYXkgPSAibm9uZSI7IGhlcm9Cb3guaW5uZXJIVE1MID0gYDxzcGFuIHN0eWxlPSJjb2xvcjojZmZmO2ZvbnQtd2VpZ2h0OjgwMDtmb250LXNpemU6MjJweCI+w4Y8L3NwYW4+YDsgfTsgfSBjb25zdCBNT0RFTFNfQ0FUQUxPRyA9IFsgeyBpZDogImdlbWluaS0zLjEtcHJvIiwgbmFtZTogIkdlbWluaSAzLjEgUHJvIiwgc2hvcnQ6ICJHZW1pbmkiLCBjYXQ6ICJnZW1pbmkiLCBwcm86IHRydWUsIGRlc2M6ICLQnNC+0YnQvdGL0Lkg0LzRg9C70YzRgtC40LzQvtC00LDQu9GM0L3Ri9C5INCw0L3QsNC70LjQtyIgfSwgeyBpZDogImdlbWluaS0zLjUtZmxhc2gtbGl0ZSIsIG5hbWU6ICJHZW1pbmkgMy41IEZsYXNoIExpdGUiLCBzaG9ydDogIkdlbWluaSBGbGFzaCIsIGNhdDogImdlbWluaSIsIHBybzogZmFsc2UsIGRlc2M6ICLQnNC+0LvQvdC40LXQvdC+0YHQvdGL0LUg0L7RgtCy0LXRgtGLINC4INGA0LDQt9Cx0L7RgCDRhNC+0YLQviIgfSwgeyBpZDogImNsYXVkZS1vcHVzLTUtNSIsIG5hbWU6ICJDbGF1ZGUgT3B1cyA1LjUiLCBzaG9ydDogIkNsYXVkZSBPcHVzIiwgY2F0OiAiY2xhdWRlIiwgcHJvOiB0cnVlLCBkZXNjOiAi0JzQsNC60YHQuNC80LDQu9GM0L3Ri9C5INC40L3RgtC10LvQu9C10LrRgiDQuCDQutC+0LQiIH0sIHsgaWQ6ICJjbGF1ZGUtc29ubmV0LTUiLCBuYW1lOiAiQ2xhdWRlIFNvbm5ldCA1Iiwgc2hvcnQ6ICJDbGF1ZGUgU29ubmV0IiwgY2F0OiAiY2xhdWRlIiwgcHJvOiB0cnVlLCBkZXNjOiAi0JHQsNC70LDQvdGBINGB0LrQvtGA0L7RgdGC0Lgg0Lgg0LPQu9GD0LHQuNC90YsiIH0sIHsgaWQ6ICJjbGF1ZGUtaGFpa3UtNS01IiwgbmFtZTogIkNsYXVkZSBIYWlrdSA1LjUiLCBzaG9ydDogIkNsYXVkZSBIYWlrdSIsIGNhdDogImNsYXVkZSIsIHBybzogZmFsc2UsIGRlc2M6ICLQkdGL0YHRgtGA0YvQuSDQuCDQttC40LLQvtC5INC00LjQsNC70L7QsyIgfSwgeyBpZDogImdwdC02LWx1bmEiLCBuYW1lOiAiQ2hhdEdQVCA2IEx1bmEiLCBzaG9ydDogIkNoYXRHUFQiLCBjYXQ6ICJncHQiLCBwcm86IGZhbHNlLCBkZXNjOiAi0KPQvdC40LLQtdGA0YHQsNC70YzQvdCw0Y8g0LHQsNC30L7QstCw0Y8g0LzQvtC00LXQu9GMIiB9LCB7IGlkOiAiZ3B0LTYuMS10ZXJyYSIsIG5hbWU6ICJDaGF0R1BUIDYuMSBUZXJyYSIsIHNob3J0OiAiR1BULTYuMSIsIGNhdDogImdwdCIsIHBybzogdHJ1ZSwgZGVzYzogItCk0LvQsNCz0LzQsNC9IE9wZW5BSSDQtNC70Y8g0YHQu9C+0LbQvdGL0YUg0LfQsNC00LDRhyIgfSwgeyBpZDogImdwdC01LjMtY29kZXgiLCBuYW1lOiAiQ2hhdEdQVCA1LjMgQ29kZXgiLCBzaG9ydDogIkNvZGV4IiwgY2F0OiAiZ3B0IiwgcHJvOiB0cnVlLCBkZXNjOiAi0KHQv9C10YbQuNCw0LvQuNGB0YIg0L/QviDQv9GA0L7Qs9GA0LDQvNC80LjRgNC+0LLQsNC90LjRjiIgfSwgeyBpZDogImRlZXBzZWVrLXY0LWZsYXNoIiwgbmFtZTogIkRlZXBTZWVrIFY0IEZsYXNoIiwgc2hvcnQ6ICJEZWVwU2VlayIsIGNhdDogImRlZXBzZWVrIiwgcHJvOiBmYWxzZSwgZGVzYzogItCh0LjQu9GM0L3QsNGPINC70L7Qs9C40LrQsCDQuCDQvNCw0YLQtdC80LDRgtC40LrQsCIgfSwgeyBpZDogImRlZXBzZWVrLXY0LXBybyIsIG5hbWU6ICJEZWVwU2VlayBWNCBQcm8iLCBzaG9ydDogIkRlZXBTZWVrIFBybyIsIGNhdDogImRlZXBzZWVrIiwgcHJvOiB0cnVlLCBkZXNjOiAi0JPQu9GD0LHQvtC60LjQtSDRgNCw0YHRgdGD0LbQtNC10L3QuNGPIiB9LCB7IGlkOiAiZ3Jvay00LjYiLCBuYW1lOiAiR3JvayA0LjYiLCBzaG9ydDogIkdyb2siLCBjYXQ6ICJncm9rIiwgcHJvOiB0cnVlLCBkZXNjOiAi0JHRi9GB0YLRgNGL0Lkg0Lgg0LTQtdGA0LfQutC40Lkg0JjQmCDQvtGCIHhBSSIgfSBdOyBjb25zdCBCQVNFX1BST0RVQ1RTID0geyBzdWJfdHJpYWw6IHsgcnViOiAzOSwgc3RhcnM6IDI5LCB0aXRsZTogItCf0YDQvtCx0L3Ri9C5IDEg0LTQtdC90YwiLCBkZXNjOiAi0JHQtdC30LvQuNC80LjRgiDQutC+INCy0YHQtdC8IFBSTy3QvNC+0LTQtdC70Y/QvCDQvdCwIDEg0LTQtdC90YwuIiB9LCBzdWJfc3RhbmRhcmQ6IHsgcnViOiAxNDksIHN0YXJzOiAxMTUsIHRpdGxlOiAi0KHRgtCw0L3QtNCw0YDRgiA3INC00L3QtdC5IiwgZGVzYzogItCR0LXQt9C70LjQvNC40YIg0LrQviDQstGB0LXQvCBQUk8t0LzQvtC00LXQu9GP0Lwg0L3QsCA3INC00L3QtdC5LiIgfSwgc3ViX3ByZW1pdW06IHsgcnViOiAzNDksIHN0YXJzOiAyNjksIHRpdGxlOiAi0J/RgNC10LzQuNGD0LwgMzAg0LTQvdC10LkiLCBkZXNjOiAi0JHQtdC30LvQuNC80LjRgiDQutC+INCy0YHQtdC8IFBSTy3QvNC+0LTQtdC70Y/QvCDQvdCwIDMwINC00L3QtdC5LiIgfSwgcGFja18zMDogeyBydWI6IDk5LCBzdGFyczogNzksIHRpdGxlOiAi0J/QsNC60LXRgiArMzAg0LfQsNC/0YDQvtGB0L7QsiIsIGRlc2M6ICIzMCDQtNC+0L/QvtC70L3QuNGC0LXQu9GM0L3Ri9GFINC30LDQv9GA0L7RgdC+0LIgKNC90LUg0YHQs9C+0YDQsNGO0YIpLiIgfSwgcGFja18xMDA6IHsgcnViOiAyNTksIHN0YXJzOiAxOTksIHRpdGxlOiAi0J/QsNC60LXRgiArMTAwINC30LDQv9GA0L7RgdC+0LIiLCBkZXNjOiAiMTAwINC00L7Qv9C+0LvQvdC40YLQtdC70YzQvdGL0YUg0LfQsNC/0YDQvtGB0L7QsiAo0L3QtSDRgdCz0L7RgNCw0Y7RgikuIiB9LCBwYWNrXzMwMDogeyBydWI6IDU4OSwgc3RhcnM6IDQ0OSwgdGl0bGU6ICLQn9Cw0LrQtdGCICszMDAg0LfQsNC/0YDQvtGB0L7QsiIsIGRlc2M6ICIzMDAg0LTQvtC/0L7Qu9C90LjRgtC10LvRjNC90YvRhSDQt9Cw0L/RgNC+0YHQvtCyICjQvdC1INGB0LPQvtGA0LDRjtGCKS4iIH0gfTsgbGV0IFNUQVRFID0geyB1c2VyX2lkOiB0Zz8uaW5pdERhdGFVbnNhZmU/LnVzZXI/LmlkIHx8IE51bWJlcihsb2NhbFN0b3JhZ2UuZ2V0SXRlbSgiYWV0aGVyX3dlYl91aWQiKSB8fCAiMCIpLCB3ZWJfdG9rZW46IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfd2ViX3Rva2VuIikgfHwgIiIsIGZ1bGxfbmFtZTogbG9jYWxTdG9yYWdlLmdldEl0ZW0oImFldGhlcl93ZWJfbmFtZSIpIHx8ICLQn9C+0LvRjNC30L7QstCw0YLQtdC70YwiLCBwaG90b191cmw6IHRnPy5pbml0RGF0YVVuc2FmZT8udXNlcj8ucGhvdG9fdXJsIHx8IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhZXRoZXJfd2ViX3Bob3RvIikgfHwgIiIsIGlzX2FkbWluOiBmYWxzZSwgaXNfcHJvOiBmYWxzZSwgc2VsZWN0ZWRfbW9kZWw6IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJzZWxlY3RlZF9tb2RlbCIpIHx8ICJncHQtNi1sdW5hIiwgZW5naW5lX21vZGVsOiAiZ3B0LTYtbHVuYSIsIGRhaWx5X2xlZnQ6IDUsIGRhaWx5X3RvdGFsOiA1LCBleHRyYV9yZXF1ZXN0czogMCwgcmVmX2JhbGFuY2U6IDAsIHJlZl9jb3VudDogMCwgcmVmX2xpbms6ICJodHRwczovL3QubWUvQWV0aGVyTmV1cmFsX2JvdCIsIG1vZGVsX2ZpbHRlcjogImFsbCIsIGF0dGFjaG1lbnQ6IG51bGwgfTsgZnVuY3Rpb24gZ2V0U2Vzc2lvbnNTdG9yYWdlS2V5KCkgeyByZXR1cm4gU1RBVEUudXNlcl9pZCA/IGBhaV9jaGF0X3Nlc3Npb25zXyR7U1RBVEUudXNlcl9pZH1gIDogImFpX2NoYXRfc2Vzc2lvbnMiOyB9IGxldCBTRVNTSU9OUyA9IFtdOyBmdW5jdGlvbiBsb2FkU2Vzc2lvbnNGcm9tU3RvcmFnZSgpIHsgdHJ5IHsgU0VTU0lPTlMgPSBKU09OLnBhcnNlKGxvY2FsU3RvcmFnZS5nZXRJdGVtKGdldFNlc3Npb25zU3RvcmFnZUtleSgpKSB8fCAiW10iKTsgaWYgKCFBcnJheS5pc0FycmF5KFNFU1NJT05TKSkgU0VTU0lPTlMgPSBbXTsgfSBjYXRjaCAoZSkgeyBTRVNTSU9OUyA9IFtdOyB9IH0gbGV0IENVUlJFTlRfU0VTU0lPTl9JRCA9IG51bGw7IGxldCBBQ1RJVkVfU1RSRUFNX1RJTUVSID0gbnVsbDsgZnVuY3Rpb24gc2F2ZVNlc3Npb25zKCkgeyBjb25zdCBrZXkgPSBnZXRTZXNzaW9uc1N0b3JhZ2VLZXkoKTsgdHJ5IHsgY29uc3QgbGlnaHR3ZWlnaHQgPSBTRVNTSU9OUy5zbGljZSgwLCAzNSkubWFwKHMgPT4gKHsgaWQ6IHMuaWQsIHRpdGxlOiBzLnRpdGxlLCBtZXNzYWdlczogKHMubWVzc2FnZXMgfHwgW10pLm1hcChtID0+ICh7IHJvbGU6IG0ucm9sZSwgdGV4dDogbS50ZXh0LCBmaWxlTmFtZTogbS5maWxlTmFtZSB8fCAobS5pbWdVcmwgPyAi0KTQvtGC0L4iIDogbnVsbCksIG1vZGVsTmFtZTogbS5tb2RlbE5hbWUsIG1vZGVsQ2F0OiBtLm1vZGVsQ2F0IH0pKSB9KSk7IGxvY2FsU3RvcmFnZS5zZXRJdGVtKGtleSwgSlNPTi5zdHJpbmdpZnkobGlnaHR3ZWlnaHQpKTsgfSBjYXRjaCAoZSkgeyB0cnkgeyBsb2NhbFN0b3JhZ2Uuc2V0SXRlbShrZXksIEpTT04uc3RyaW5naWZ5KFNFU1NJT05TLnNsaWNlKDAsIDEwKSkpOyB9IGNhdGNoIChlMikge30gfSByZW5kZXJIaXN0b3J5U2lkZWJhcigpOyB9IGZ1bmN0aW9uIHN0b3BBY3RpdmVTdHJlYW0oKSB7IGlmIChBQ1RJVkVfU1RSRUFNX1RJTUVSKSB7IGNsZWFySW50ZXJ2YWwoQUNUSVZFX1NUUkVBTV9USU1FUik7IEFDVElWRV9TVFJFQU1fVElNRVIgPSBudWxsOyB9IHNldFNlbmRCdXR0b25Nb2RlKCJzZW5kIik7IH0gZnVuY3Rpb24gaGFuZGxlQ2hhdFNjcm9sbCgpIHsgY29uc3QgYXJlYSA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJjaGF0U2Nyb2xsQXJlYSIpOyBjb25zdCBmYWIgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgic2Nyb2xsQm90dG9tRmFiIik7IGlmICghYXJlYSB8fCAhZmFiKSByZXR1cm47IGNvbnN0IGRpc3RGcm9tQm90dG9tID0gYXJlYS5zY3JvbGxIZWlnaHQgLSBhcmVhLnNjcm9sbFRvcCAtIGFyZWEuY2xpZW50SGVpZ2h0OyBmYWIuY2xhc3NMaXN0LnRvZ2dsZSgidmlzaWJsZSIsIGRpc3RGcm9tQm90dG9tID4gMTQwKTsgfSBmdW5jdGlvbiBzY3JvbGxDaGF0Qm90dG9tKHdpdGhIYXB0aWMgPSBmYWxzZSkgeyBpZiAod2l0aEhhcHRpYykgdHJpZ2dlckhhcHRpY0xpZ2h0KCk7IGNvbnN0IGFyZWEgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiY2hhdFNjcm9sbEFyZWEiKTsgYXJlYS5zY3JvbGxUb3AgPSBhcmVhLnNjcm9sbEhlaWdodDsgaGFuZGxlQ2hhdFNjcm9sbCgpOyB9IGZ1bmN0aW9uIHN0YXJ0TmV3Q2hhdCgpIHsgdHJpZ2dlckhhcHRpY0xpZ2h0KCk7IHN0b3BBY3RpdmVTdHJlYW0oKTsgQ1VSUkVOVF9TRVNTSU9OX0lEID0gbnVsbDsgY2xlYXJBdHRhY2htZW50KCk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtZXNzYWdlc1N0YWNrIikuaW5uZXJIVE1MID0gIiI7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtZXNzYWdlc1N0YWNrIikuc3R5bGUuZGlzcGxheSA9ICJub25lIjsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlbGNvbWVIZXJvIikuc3R5bGUuZGlzcGxheSA9ICJmbGV4IjsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIndlbGNvbWVHcmVldGluZ1RleHQiKS50ZXh0Q29udGVudCA9IGdldFJhbmRvbUdyZWV0aW5nKGdldFVzZXJEaXNwbGF5TmFtZSgpKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNjcm9sbEJvdHRvbUZhYiIpLmNsYXNzTGlzdC5yZW1vdmUoInZpc2libGUiKTsgc3dpdGNoU2VjdGlvbigiY2hhdCIpOyB0b2dnbGVTaWRlYmFyKGZhbHNlKTsgcmVuZGVySGlzdG9yeVNpZGViYXIoKTsgfSBmdW5jdGlvbiBvcGVuU2Vzc2lvbihpZCkgeyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgc3RvcEFjdGl2ZVN0cmVhbSgpOyBjb25zdCBzZXNzID0gU0VTU0lPTlMuZmluZChzID0+IHMuaWQgPT09IGlkKTsgaWYgKCFzZXNzKSByZXR1cm47IENVUlJFTlRfU0VTU0lPTl9JRCA9IGlkOyBzd2l0Y2hTZWN0aW9uKCJjaGF0Iik7IHRvZ2dsZVNpZGViYXIoZmFsc2UpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2VsY29tZUhlcm8iKS5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyBjb25zdCBzdGFjayA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtZXNzYWdlc1N0YWNrIik7IHN0YWNrLnN0eWxlLmRpc3BsYXkgPSAiZmxleCI7IHN0YWNrLmlubmVySFRNTCA9ICIiOyAoc2Vzcy5tZXNzYWdlcyB8fCBbXSkuZm9yRWFjaChtID0+IHsgcmVuZGVyQnViYmxlRE9NKG0ucm9sZSwgbS50ZXh0LCBtLmltZ1VybCwgbS5maWxlTmFtZSwgbS5tb2RlbE5hbWUsIG0ubW9kZWxDYXQpOyB9KTsgc2Nyb2xsQ2hhdEJvdHRvbSgpOyByZW5kZXJIaXN0b3J5U2lkZWJhcigpOyB9IGZ1bmN0aW9uIGRlbGV0ZVNlc3Npb24oZXYsIGlkKSB7IGV2LnN0b3BQcm9wYWdhdGlvbigpOyBTRVNTSU9OUyA9IFNFU1NJT05TLmZpbHRlcihzID0+IHMuaWQgIT09IGlkKTsgc2F2ZVNlc3Npb25zKCk7IGlmIChDVVJSRU5UX1NFU1NJT05fSUQgPT09IGlkKSBzdGFydE5ld0NoYXQoKTsgfSBmdW5jdGlvbiBjbGVhckFsbFNlc3Npb25zKCkgeyBTRVNTSU9OUyA9IFtdOyBzYXZlU2Vzc2lvbnMoKTsgc3RhcnROZXdDaGF0KCk7IHNob3dUb2FzdCgi0JjRgdGC0L7RgNC40Y8g0YfQsNGC0L7QsiDQvtGH0LjRidC10L3QsCIpOyB9IGZ1bmN0aW9uIHJlbmRlckhpc3RvcnlTaWRlYmFyKCkgeyBjb25zdCBib3ggPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiaGlzdG9yeUxpc3QiKTsgaWYgKCFTRVNTSU9OUy5sZW5ndGgpIHsgYm94LmlubmVySFRNTCA9IGA8ZGl2IHN0eWxlPSJwYWRkaW5nOjEwcHggMTJweDtmb250LXNpemU6MTIuNXB4O2NvbG9yOnZhcigtLXRleHQtbXV0ZWQpIj7Qn9C+0LrQsCDQvdC10YIg0YHQvtGF0YDQsNC90ZHQvdC90YvRhSDQtNC40LDQu9C+0LPQvtCyPC9kaXY+YDsgcmV0dXJuOyB9IGJveC5pbm5lckhUTUwgPSBTRVNTSU9OUy5tYXAocyA9PiBgIDxkaXYgY2xhc3M9Imhpc3RvcnktaXRlbSAke3MuaWQgPT09IENVUlJFTlRfU0VTU0lPTl9JRCA/ICJhY3RpdmUiIDogIiJ9IiBvbmNsaWNrPSJvcGVuU2Vzc2lvbignJHtzLmlkfScpIj4gPHNwYW4gY2xhc3M9Imhpc3RvcnktdGl0bGUiPiR7ZXNjYXBlSHRtbChzLnRpdGxlKX08L3NwYW4+IDxzcGFuIGNsYXNzPSJoaXN0b3J5LWRlbCIgdGl0bGU9ItCj0LTQsNC70LjRgtGMIiBvbmNsaWNrPSJkZWxldGVTZXNzaW9uKGV2ZW50LCAnJHtzLmlkfScpIj4gPHN2ZyBjbGFzcz0iaWNvIiBzdHlsZT0id2lkdGg6MTRweDtoZWlnaHQ6MTRweCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNMTggNiA2IDE4TTYgNmwxMiAxMiIvPjwvc3ZnPiA8L3NwYW4+IDwvZGl2PiBgKS5qb2luKCIiKTsgfSBmdW5jdGlvbiBmb3JtYXRCeXRlcyhieXRlcykgeyBpZiAoIWJ5dGVzKSByZXR1cm4gIjAg0JEiOyBpZiAoYnl0ZXMgPCAxMDI0KSByZXR1cm4gYnl0ZXMgKyAiINCRIjsgaWYgKGJ5dGVzIDwgMTAyNCAqIDEwMjQpIHJldHVybiAoYnl0ZXMgLyAxMDI0KS50b0ZpeGVkKDEpICsgIiDQmtCRIjsgcmV0dXJuIChieXRlcyAvICgxMDI0ICogMTAyNCkpLnRvRml4ZWQoMSkgKyAiINCc0JEiOyB9IGZ1bmN0aW9uIGFwcGx5UHJvbXB0UHJlc2V0KHByZWZpeCkgeyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgY29uc3QgdGEgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiY2hhdFRleHRhcmVhIik7IHRhLnZhbHVlID0gcHJlZml4OyB0YS5mb2N1cygpOyBhdXRvUmVzaXplVGV4dGFyZWEodGEpOyB9IGZ1bmN0aW9uIHRvZ2dsZVBsdXNQb3BvdmVyKGV2KSB7IGV2LnN0b3BQcm9wYWdhdGlvbigpOyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInBsdXNQb3BvdmVyIikuY2xhc3NMaXN0LnRvZ2dsZSgib3BlbiIpOyB9IGRvY3VtZW50LmFkZEV2ZW50TGlzdGVuZXIoImNsaWNrIiwgKCkgPT4geyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicGx1c1BvcG92ZXIiKS5jbGFzc0xpc3QucmVtb3ZlKCJvcGVuIik7IH0pOyBmdW5jdGlvbiB0cmlnZ2VyRmlsZUlucHV0KGFjY2VwdFN0cikgeyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicGx1c1BvcG92ZXIiKS5jbGFzc0xpc3QucmVtb3ZlKCJvcGVuIik7IGNvbnN0IGlucCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ1bml2ZXJzYWxGaWxlSW5wdXQiKTsgaW5wLmFjY2VwdCA9IGFjY2VwdFN0cjsgaW5wLnZhbHVlID0gIiI7IGlucC5jbGljaygpOyB9IGZ1bmN0aW9uIGhhbmRsZUZpbGVQaWNrZWQoZXYpIHsgY29uc3QgZmlsZSA9IGV2LnRhcmdldC5maWxlcz8uWzBdOyBpZiAoIWZpbGUpIHJldHVybjsgY29uc3QgaXNJbWFnZSA9IGZpbGUudHlwZS5zdGFydHNXaXRoKCJpbWFnZS8iKTsgY29uc3QgcmVhZGVyID0gbmV3IEZpbGVSZWFkZXIoKTsgaWYgKGlzSW1hZ2UpIHsgcmVhZGVyLm9ubG9hZCA9ICgpID0+IHsgY29uc3QgZGF0YVVybCA9IHJlYWRlci5yZXN1bHQ7IFNUQVRFLmF0dGFjaG1lbnQgPSB7IHR5cGU6ICJpbWFnZSIsIG5hbWU6IGZpbGUubmFtZSwgc2l6ZTogZmlsZS5zaXplLCBiNjQ6IGRhdGFVcmwuc3BsaXQoIiwiKVsxXSwgcHJldmlld1VybDogZGF0YVVybCB9OyByZW5kZXJBdHRhY2htZW50VHJheSgpOyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgfTsgcmVhZGVyLnJlYWRBc0RhdGFVUkwoZmlsZSk7IH0gZWxzZSB7IHJlYWRlci5vbmxvYWQgPSAoKSA9PiB7IFNUQVRFLmF0dGFjaG1lbnQgPSB7IHR5cGU6ICJmaWxlIiwgbmFtZTogZmlsZS5uYW1lLCBzaXplOiBmaWxlLnNpemUsIHRleHRDb250ZW50OiBTdHJpbmcocmVhZGVyLnJlc3VsdCB8fCAiIikuc2xpY2UoMCwgMjUwMDApIH07IHJlbmRlckF0dGFjaG1lbnRUcmF5KCk7IHRyaWdnZXJIYXB0aWNMaWdodCgpOyB9OyByZWFkZXIucmVhZEFzVGV4dChmaWxlKTsgfSB9IGZ1bmN0aW9uIHJlbmRlckF0dGFjaG1lbnRUcmF5KCkgeyBjb25zdCB0cmF5ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImF0dGFjaG1lbnRQcmV2aWV3VHJheSIpOyBjb25zdCBhdHQgPSBTVEFURS5hdHRhY2htZW50OyBpZiAoIWF0dCkgeyB0cmF5LnN0eWxlLmRpc3BsYXkgPSAibm9uZSI7IHRyYXkuaW5uZXJIVE1MID0gIiI7IHJldHVybjsgfSB0cmF5LnN0eWxlLmRpc3BsYXkgPSAiZmxleCI7IGlmIChhdHQudHlwZSA9PT0gImltYWdlIikgeyB0cmF5LmlubmVySFRNTCA9IGAgPGRpdiBjbGFzcz0iYXR0LWltYWdlLWNhcmQiPiA8aW1nIHNyYz0iJHthdHQucHJldmlld1VybH0iIGFsdD0iUHJldmlldyIgLz4gPGJ1dHRvbiBjbGFzcz0iYXR0LXJlbW92ZS1iYWRnZSIgdGl0bGU9ItCj0LHRgNCw0YLRjCIgb25jbGljaz0iY2xlYXJBdHRhY2htZW50KCkiPuKclTwvYnV0dG9uPiA8L2Rpdj4gYDsgfSBlbHNlIHsgY29uc3QgZXh0ID0gKGF0dC5uYW1lLnNwbGl0KCIuIikucG9wKCkgfHwgIkZJTEUiKS5zbGljZSgwLCA1KTsgdHJheS5pbm5lckhUTUwgPSBgIDxkaXYgY2xhc3M9ImF0dC1maWxlLWNhcmQiPiA8c3BhbiBjbGFzcz0iYXR0LWZpbGUtZXh0Ij4ke2VzY2FwZUh0bWwoZXh0KX08L3NwYW4+IDxkaXYgY2xhc3M9ImF0dC1maWxlLW1ldGEiPiA8ZGl2IGNsYXNzPSJhdHQtZmlsZS1uYW1lIj4ke2VzY2FwZUh0bWwoYXR0Lm5hbWUpfTwvZGl2PiA8ZGl2IGNsYXNzPSJhdHQtZmlsZS1zaXplIj4ke2Zvcm1hdEJ5dGVzKGF0dC5zaXplKX08L2Rpdj4gPC9kaXY+IDxidXR0b24gY2xhc3M9ImF0dC1yZW1vdmUtYmFkZ2UiIHRpdGxlPSLQo9Cx0YDQsNGC0YwiIG9uY2xpY2s9ImNsZWFyQXR0YWNobWVudCgpIj7inJU8L2J1dHRvbj4gPC9kaXY+IGA7IH0gfSBmdW5jdGlvbiBjbGVhckF0dGFjaG1lbnQoKSB7IFNUQVRFLmF0dGFjaG1lbnQgPSBudWxsOyByZW5kZXJBdHRhY2htZW50VHJheSgpOyB9IGZ1bmN0aW9uIGF1dG9SZXNpemVUZXh0YXJlYShlbCkgeyBlbC5zdHlsZS5oZWlnaHQgPSAiYXV0byI7IGVsLnN0eWxlLmhlaWdodCA9IE1hdGgubWluKGVsLnNjcm9sbEhlaWdodCwgMTQwKSArICJweCI7IH0gZnVuY3Rpb24gaGFuZGxlVGV4dGFyZWFLZXkoZXYpIHsgaWYgKGV2LmtleSA9PT0gIkVudGVyIiAmJiAhZXYuc2hpZnRLZXkpIHsgZXYucHJldmVudERlZmF1bHQoKTsgc2VuZE1lc3NhZ2UoKTsgfSB9IGZ1bmN0aW9uIHNldFNlbmRCdXR0b25Nb2RlKG1vZGUpIHsgY29uc3QgYnRuID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNlbmRPclN0b3BCdG4iKTsgaWYgKG1vZGUgPT09ICJzdG9wIikgeyBidG4udGl0bGUgPSAi0J7RgdGC0LDQvdC+0LLQuNGC0Ywg0L/QtdGH0LDRgtGMIjsgYnRuLmlubmVySFRNTCA9IGA8c3ZnIGNsYXNzPSJpY28iIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNiIgeT0iNiIgd2lkdGg9IjEyIiBoZWlnaHQ9IjEyIiByeD0iMiIgZmlsbD0iY3VycmVudENvbG9yIi8+PC9zdmc+YDsgfSBlbHNlIHsgYnRuLnRpdGxlID0gItCe0YLQv9GA0LDQstC40YLRjCI7IGJ0bi5pbm5lckhUTUwgPSBgPHN2ZyBjbGFzcz0iaWNvIiB2aWV3Qm94PSIwIDAgMjQgMjQiPjxsaW5lIHgxPSIyMiIgeTE9IjIiIHgyPSIxMSIgeTI9IjEzIi8+PHBvbHlnb24gcG9pbnRzPSIyMiAyIDE1IDIyIDExIDEzIDIgOSAyMiAyIi8+PC9zdmc+YDsgfSB9IGZ1bmN0aW9uIGhhbmRsZVNlbmRPclN0b3AoKSB7IGlmIChBQ1RJVkVfU1RSRUFNX1RJTUVSKSB7IHN0b3BBY3RpdmVTdHJlYW0oKTsgfSBlbHNlIHsgc2VuZE1lc3NhZ2UoKTsgfSB9IGZ1bmN0aW9uIGNyZWF0ZUNvcHlBY3Rpb25CYXIoZ2V0UmF3VGV4dEZuKSB7IGNvbnN0IGJhciA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoImRpdiIpOyBiYXIuY2xhc3NOYW1lID0gImFpLWFjdGlvbnMtYmFyIjsgY29uc3QgY29weUJ0biA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoImJ1dHRvbiIpOyBjb3B5QnRuLmNsYXNzTmFtZSA9ICJhaS1hY3QtYnRuIjsgY29weUJ0bi50aXRsZSA9ICLQodC60L7Qv9C40YDQvtCy0LDRgtGMINC+0YLQstC10YIiOyBjb3B5QnRuLmlubmVySFRNTCA9IGA8c3ZnIGNsYXNzPSJpY28iIHN0eWxlPSJ3aWR0aDoxNXB4O2hlaWdodDoxNXB4IiB2aWV3Qm94PSIwIDAgMjQgMjQiPjxyZWN0IHg9IjkiIHk9IjkiIHdpZHRoPSIxMyIgaGVpZ2h0PSIxMyIgcng9IjIiLz48cGF0aCBkPSJNNSAxNUg0YTIgMiAwIDAgMS0yLTJWNGEyIDIgMCAwIDEgMi0yaDlhMiAyIDAgMCAxIDIgMnYxIi8+PC9zdmc+PHNwYW4+0JrQvtC/0LjRgNC+0LLQsNGC0Yw8L3NwYW4+YDsgY29weUJ0bi5vbmNsaWNrID0gKCkgPT4geyBuYXZpZ2F0b3IuY2xpcGJvYXJkPy53cml0ZVRleHQoZ2V0UmF3VGV4dEZuKCkpOyB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBjb3B5QnRuLmlubmVySFRNTCA9IGA8c3ZnIGNsYXNzPSJpY28iIHN0eWxlPSJ3aWR0aDoxNXB4O2hlaWdodDoxNXB4O2NvbG9yOiMxMGI5ODEiIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiLz48L3N2Zz48c3Bhbj7QodC60L7Qv9C40YDQvtCy0LDQvdC+PC9zcGFuPmA7IHNldFRpbWVvdXQoKCkgPT4geyBjb3B5QnRuLmlubmVySFRNTCA9IGA8c3ZnIGNsYXNzPSJpY28iIHN0eWxlPSJ3aWR0aDoxNXB4O2hlaWdodDoxNXB4IiB2aWV3Qm94PSIwIDAgMjQgMjQiPjxyZWN0IHg9IjkiIHk9IjkiIHdpZHRoPSIxMyIgaGVpZ2h0PSIxMyIgcng9IjIiLz48cGF0aCBkPSJNNSAxNUg0YTIgMiAwIDAgMS0yLTJWNGEyIDIgMCAwIDEgMi0yaDlhMiAyIDAgMCAxIDIgMnYxIi8+PC9zdmc+PHNwYW4+0JrQvtC/0LjRgNC+0LLQsNGC0Yw8L3NwYW4+YDsgfSwgMjAwMCk7IH07IGJhci5hcHBlbmRDaGlsZChjb3B5QnRuKTsgcmV0dXJuIGJhcjsgfSBmdW5jdGlvbiByZW5kZXJCdWJibGVET00ocm9sZSwgdGV4dCwgaW1nVXJsID0gbnVsbCwgZmlsZU5hbWUgPSBudWxsLCBtb2RlbE5hbWUgPSAiIiwgbW9kZWxDYXQgPSAiZ3B0IiwgaXNTa2VsZXRvbiA9IGZhbHNlKSB7IGNvbnN0IHN0YWNrID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoIm1lc3NhZ2VzU3RhY2siKTsgY29uc3Qgcm93ID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgiZGl2Iik7IHJvdy5jbGFzc05hbWUgPSAibXNnLXJvdyAiICsgcm9sZTsgaWYgKHJvbGUgPT09ICJhaSIgJiYgbW9kZWxOYW1lKSB7IGNvbnN0IHRhZyA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoImRpdiIpOyB0YWcuY2xhc3NOYW1lID0gIm1zZy1tb2RlbC10YWciOyB0YWcuaW5uZXJIVE1MID0gYCR7cmVuZGVyTW9kZWxBdmF0YXJIVE1MKG1vZGVsQ2F0KX08c3Bhbj4ke2VzY2FwZUh0bWwobW9kZWxOYW1lKX08L3NwYW4+YDsgcm93LmFwcGVuZENoaWxkKHRhZyk7IH0gY29uc3QgYnViYmxlID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgiZGl2Iik7IGJ1YmJsZS5jbGFzc05hbWUgPSAibXNnLWJ1YmJsZSI7IGlmIChpbWdVcmwpIHsgY29uc3QgaW1nID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgiaW1nIik7IGltZy5zcmMgPSBpbWdVcmw7IGltZy5jbGFzc05hbWUgPSAibXNnLWF0dGFjaG1lbnQtaW1nIjsgYnViYmxlLmFwcGVuZENoaWxkKGltZyk7IH0gaWYgKGZpbGVOYW1lKSB7IGNvbnN0IGZCYWRnZSA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoImRpdiIpOyBmQmFkZ2UuY2xhc3NOYW1lID0gIm1zZy1hdHRhY2htZW50LWZpbGUiOyBmQmFkZ2UudGV4dENvbnRlbnQgPSBmaWxlTmFtZTsgYnViYmxlLmFwcGVuZENoaWxkKGZCYWRnZSk7IH0gY29uc3QgY29udGVudEVsID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgiZGl2Iik7IGlmIChyb2xlID09PSAiYWkiKSB7IGNvbnRlbnRFbC5jbGFzc05hbWUgPSAibWQtY29udGVudCI7IGlmIChpc1NrZWxldG9uKSB7IGNvbnRlbnRFbC5pbm5lckhUTUwgPSBgIDxkaXYgY2xhc3M9InNrZWxldG9uLXRoaW5raW5nLWJveCI+IDxkaXYgY2xhc3M9InNrZWxldG9uLXB1bHNlLWxvZ28iPiA8aW1nIHNyYz0iJHtDVVNUT01fTE9HT19VUkx9IiBhbHQ9IsOGIiBvbmVycm9yPSJ0aGlzLnN0eWxlLmRpc3BsYXk9J25vbmUnO3RoaXMucGFyZW50Tm9kZS50ZXh0Q29udGVudD0nw4YnIiAvPiA8L2Rpdj4gPGRpdiBjbGFzcz0ic2tlbGV0b24tYmFycy1jb2wiPiA8ZGl2IGNsYXNzPSJza2VsLWJhciB3MSI+PC9kaXY+IDxkaXYgY2xhc3M9InNrZWwtYmFyIHcyIj48L2Rpdj4gPGRpdiBjbGFzcz0ic2tlbC1iYXIgdzMiPjwvZGl2PiA8L2Rpdj4gPC9kaXY+IGA7IH0gZWxzZSB7IHJlbmRlclJpY2hNYXJrZG93bkFuZE1hdGgoY29udGVudEVsLCB0ZXh0KTsgfSB9IGVsc2UgeyBjb250ZW50RWwudGV4dENvbnRlbnQgPSB0ZXh0OyB9IGJ1YmJsZS5hcHBlbmRDaGlsZChjb250ZW50RWwpOyByb3cuYXBwZW5kQ2hpbGQoYnViYmxlKTsgbGV0IGN1cnJlbnRSYXdUZXh0ID0gdGV4dDsgaWYgKHJvbGUgPT09ICJhaSIgJiYgIWlzU2tlbGV0b24pIHsgcm93LmFwcGVuZENoaWxkKGNyZWF0ZUNvcHlBY3Rpb25CYXIoKCkgPT4gY3VycmVudFJhd1RleHQpKTsgfSBzdGFjay5hcHBlbmRDaGlsZChyb3cpOyByZXR1cm4geyByb3csIGNvbnRlbnRFbCwgc3RyZWFtQW5kRmluYWxpemUoZnVsbEFuc3dlcikgeyBjdXJyZW50UmF3VGV4dCA9IGZ1bGxBbnN3ZXI7IGNvbnN0IHRva2VucyA9IGZ1bGxBbnN3ZXIuc3BsaXQoLyhccyspLyk7IGxldCBpZHggPSAwOyBsZXQgYWNjID0gIiI7IGNvbnN0IHN0ZXBTaXplID0gTWF0aC5tYXgoMSwgTWF0aC5jZWlsKHRva2Vucy5sZW5ndGggLyA4NSkpOyBzZXRTZW5kQnV0dG9uTW9kZSgic3RvcCIpOyBjb25zdCBmaW5pc2hSZW5kZXIgPSAoKSA9PiB7IHN0b3BBY3RpdmVTdHJlYW0oKTsgcmVuZGVyUmljaE1hcmtkb3duQW5kTWF0aChjb250ZW50RWwsIGZ1bGxBbnN3ZXIpOyBpZiAoIXJvdy5xdWVyeVNlbGVjdG9yKCIuYWktYWN0aW9ucy1iYXIiKSkgeyByb3cuYXBwZW5kQ2hpbGQoY3JlYXRlQ29weUFjdGlvbkJhcigoKSA9PiBjdXJyZW50UmF3VGV4dCkpOyB9IHNjcm9sbENoYXRCb3R0b20oKTsgfTsgQUNUSVZFX1NUUkVBTV9USU1FUiA9IHNldEludGVydmFsKCgpID0+IHsgaWYgKCFBQ1RJVkVfU1RSRUFNX1RJTUVSKSByZXR1cm47IGFjYyArPSB0b2tlbnMuc2xpY2UoaWR4LCBpZHggKyBzdGVwU2l6ZSkuam9pbigiIik7IGlkeCArPSBzdGVwU2l6ZTsgaWYgKGlkeCA+PSB0b2tlbnMubGVuZ3RoKSB7IGZpbmlzaFJlbmRlcigpOyB9IGVsc2UgeyBjb250ZW50RWwudGV4dENvbnRlbnQgPSBhY2MgKyAiIOKWjSI7IHNjcm9sbENoYXRCb3R0b20oKTsgfSB9LCAyMik7IH0gfTsgfSBhc3luYyBmdW5jdGlvbiBzZW5kTWVzc2FnZSgpIHsgY29uc3QgdGEgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiY2hhdFRleHRhcmVhIik7IGNvbnN0IHJhd1RleHQgPSB0YS52YWx1ZS50cmltKCk7IGNvbnN0IGF0dCA9IFNUQVRFLmF0dGFjaG1lbnQ7IGlmICghcmF3VGV4dCAmJiAhYXR0KSByZXR1cm47IHRyaWdnZXJIYXB0aWNMaWdodCgpOyB0YS52YWx1ZSA9ICIiOyB0YS5zdHlsZS5oZWlnaHQgPSAiYXV0byI7IGNsZWFyQXR0YWNobWVudCgpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgid2VsY29tZUhlcm8iKS5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyBjb25zdCBzdGFjayA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtZXNzYWdlc1N0YWNrIik7IHN0YWNrLnN0eWxlLmRpc3BsYXkgPSAiZmxleCI7IGlmICghQ1VSUkVOVF9TRVNTSU9OX0lEKSB7IENVUlJFTlRfU0VTU0lPTl9JRCA9ICJjaGF0XyIgKyBEYXRlLm5vdygpOyBjb25zdCB0aXRsZVByZXZpZXcgPSByYXdUZXh0IHx8IChhdHQgPyBhdHQubmFtZSA6ICLQndC+0LLRi9C5INC00LjQsNC70L7QsyIpOyBTRVNTSU9OUy51bnNoaWZ0KHsgaWQ6IENVUlJFTlRfU0VTU0lPTl9JRCwgdGl0bGU6IHRpdGxlUHJldmlldy5zbGljZSgwLCAzNiksIG1lc3NhZ2VzOiBbXSB9KTsgfSBjb25zdCBhY3RpdmVTZXNzID0gU0VTU0lPTlMuZmluZChzID0+IHMuaWQgPT09IENVUlJFTlRfU0VTU0lPTl9JRCk7IGNvbnN0IHVzZXJJbWcgPSBhdHQ/LnR5cGUgPT09ICJpbWFnZSIgPyBhdHQucHJldmlld1VybCA6IG51bGw7IGNvbnN0IHVzZXJGaWxlID0gYXR0Py50eXBlID09PSAiZmlsZSIgPyBhdHQubmFtZSA6IG51bGw7IGxldCBmaW5hbFByb21wdCA9IHJhd1RleHQ7IGlmIChhdHQ/LnR5cGUgPT09ICJmaWxlIikgeyBmaW5hbFByb21wdCA9IGAke3Jhd1RleHQgfHwgItCf0YDQvtCw0L3QsNC70LjQt9C40YDRg9C5INGB0L7QtNC10YDQttC40LzQvtC1INGE0LDQudC70LA6In1cblxuLS0tINCk0LDQudC7OiAke2F0dC5uYW1lfSAtLS1cbiR7YXR0LnRleHRDb250ZW50fWA7IH0gZWxzZSBpZiAoIWZpbmFsUHJvbXB0ICYmIGF0dD8udHlwZSA9PT0gImltYWdlIikgeyBmaW5hbFByb21wdCA9ICLQn9C+0LTRgNC+0LHQvdC+INGA0LDQt9Cx0LXRgNC4INC4INGA0LXRiNC4INGC0L4sINGH0YLQviDQuNC30L7QsdGA0LDQttC10L3QviDQvdCwINGE0L7RgtC+LiI7IH0gcmVuZGVyQnViYmxlRE9NKCJ1c2VyIiwgcmF3VGV4dCB8fCAodXNlckltZyA/ICLQoNCw0LfQsdC10YDQuCDQuNC30L7QsdGA0LDQttC10L3QuNC1IiA6ICLQn9GA0L7QsNC90LDQu9C40LfQuNGA0YPQuSDRhNCw0LnQuyIpLCB1c2VySW1nLCB1c2VyRmlsZSk7IGFjdGl2ZVNlc3MubWVzc2FnZXMucHVzaCh7IHJvbGU6ICJ1c2VyIiwgdGV4dDogcmF3VGV4dCwgaW1nVXJsOiB1c2VySW1nLCBmaWxlTmFtZTogdXNlckZpbGUgfSk7IHNhdmVTZXNzaW9ucygpOyBzY3JvbGxDaGF0Qm90dG9tKCk7IGNvbnN0IG1vZGVsT2JqID0gTU9ERUxTX0NBVEFMT0cuZmluZChtID0+IG0uaWQgPT09IFNUQVRFLnNlbGVjdGVkX21vZGVsKSB8fCB7IG5hbWU6IFNUQVRFLnNlbGVjdGVkX21vZGVsLCBjYXQ6ICJncHQiIH07IGNvbnN0IHBlbmRpbmdCdWJibGUgPSByZW5kZXJCdWJibGVET00oImFpIiwgIiIsIG51bGwsIG51bGwsIG1vZGVsT2JqLm5hbWUsIG1vZGVsT2JqLmNhdCwgdHJ1ZSk7IHNjcm9sbENoYXRCb3R0b20oKTsgdHJ5IHsgY29uc3QgcmVzID0gYXdhaXQgYXBpUmVxdWVzdCgiL2FwaS9jaGF0IiwgIlBPU1QiLCB7IHRleHQ6IGZpbmFsUHJvbXB0LCBpbWFnZV9iNjQ6IGF0dD8udHlwZSA9PT0gImltYWdlIiA/IGF0dC5iNjQgOiBudWxsLCBtb2RlbF9pZDogU1RBVEUuc2VsZWN0ZWRfbW9kZWwgfSk7IGFjdGl2ZVNlc3MubWVzc2FnZXMucHVzaCh7IHJvbGU6ICJhaSIsIHRleHQ6IHJlcy5hbnN3ZXIsIG1vZGVsTmFtZTogbW9kZWxPYmoubmFtZSwgbW9kZWxDYXQ6IG1vZGVsT2JqLmNhdCB9KTsgc2F2ZVNlc3Npb25zKCk7IHBlbmRpbmdCdWJibGUuc3RyZWFtQW5kRmluYWxpemUocmVzLmFuc3dlcik7IGlmICh0eXBlb2YgcmVzLmRhaWx5X2xlZnQgPT09ICJudW1iZXIiKSBTVEFURS5kYWlseV9sZWZ0ID0gcmVzLmRhaWx5X2xlZnQ7IGlmICh0eXBlb2YgcmVzLmV4dHJhX3JlcXVlc3RzID09PSAibnVtYmVyIikgU1RBVEUuZXh0cmFfcmVxdWVzdHMgPSByZXMuZXh0cmFfcmVxdWVzdHM7IHN5bmNVSSgpOyB9IGNhdGNoIChlcnIpIHsgcGVuZGluZ0J1YmJsZS5jb250ZW50RWwudGV4dENvbnRlbnQgPSAi0J7RiNC40LHQutCwOiAiICsgZXJyLm1lc3NhZ2U7IH0gc2Nyb2xsQ2hhdEJvdHRvbSgpOyB9IGZ1bmN0aW9uIG9wZW5Nb2RlbFNlbGVjdG9yKCkgeyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgcmVuZGVyTW9kZWxPcHRpb25zKCk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtb2RlbE1lbnVCYWNrZHJvcCIpLmNsYXNzTGlzdC5hZGQoIm9wZW4iKTsgfSBmdW5jdGlvbiBjbG9zZU1vZGVsU2VsZWN0b3IoKSB7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtb2RlbE1lbnVCYWNrZHJvcCIpLmNsYXNzTGlzdC5yZW1vdmUoIm9wZW4iKTsgfSBmdW5jdGlvbiBzZXRNb2RlbEZpbHRlcihjYXQsIGJ0bikgeyB0cmlnZ2VySGFwdGljTGlnaHQoKTsgU1RBVEUubW9kZWxfZmlsdGVyID0gY2F0OyBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCIubS1jYXQtYnRuIikuZm9yRWFjaChiID0+IGIuY2xhc3NMaXN0LnJlbW92ZSgiYWN0aXZlIikpOyBidG4uY2xhc3NMaXN0LmFkZCgiYWN0aXZlIik7IHJlbmRlck1vZGVsT3B0aW9ucygpOyB9IGZ1bmN0aW9uIHJlbmRlck1vZGVsT3B0aW9ucygpIHsgY29uc3QgbGlzdCA9IFNUQVRFLm1vZGVsX2ZpbHRlciA9PT0gImFsbCIgPyBNT0RFTFNfQ0FUQUxPRyA6IE1PREVMU19DQVRBTE9HLmZpbHRlcihtID0+IG0uY2F0ID09PSBTVEFURS5tb2RlbF9maWx0ZXIpOyBjb25zdCBoYXNTdWIgPSBTVEFURS5pc19wcm8gfHwgU1RBVEUuaXNfYWRtaW47IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJtb2RlbE9wdGlvbnNMaXN0IikuaW5uZXJIVE1MID0gbGlzdC5tYXAobSA9PiB7IGNvbnN0IHNlbGVjdGVkID0gbS5pZCA9PT0gU1RBVEUuc2VsZWN0ZWRfbW9kZWw7IGNvbnN0IGxvY2tlZCA9IG0ucHJvICYmICFoYXNTdWI7IHJldHVybiBgIDxkaXYgY2xhc3M9Im1vZGVsLW9wdGlvbi1yb3ciIG9uY2xpY2s9ImNob29zZU1vZGVsKCcke20uaWR9JywgJHttLnByb30pIj4gPGRpdiBjbGFzcz0ibW9kZWwtb3B0LWxlZnQiPiAke3JlbmRlck1vZGVsQXZhdGFySFRNTChtLmNhdCwgImxnIil9IDxkaXY+IDxkaXYgY2xhc3M9Im1vZGVsLW9wdC10aXRsZSI+IDxzcGFuPiR7bS5uYW1lfTwvc3Bhbj4gJHtsb2NrZWQgPyBgPHNwYW4gY2xhc3M9InByby1zaGltbWVyLWJhZGdlIiBzdHlsZT0iZm9udC1zaXplOjkuNXB4O3BhZGRpbmc6MXB4IDZweCI+UFJPPC9zcGFuPmAgOiAiIn0gPC9kaXY+IDxkaXYgY2xhc3M9Im1vZGVsLW9wdC1kZXNjIj4ke20uZGVzY308L2Rpdj4gPC9kaXY+IDwvZGl2PiA8ZGl2IHN0eWxlPSJjb2xvcjp2YXIoLS1hY2NlbnQpIj4gJHtzZWxlY3RlZCA/IGA8c3ZnIGNsYXNzPSJpY28iIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiLz48L3N2Zz5gIDogIiJ9IDwvZGl2PiA8L2Rpdj4gYDsgfSkuam9pbigiIik7IH0gYXN5bmMgZnVuY3Rpb24gY2hvb3NlTW9kZWwobW9kZWxJZCwgaXNQcm8pIHsgaWYgKGlzUHJvICYmICFTVEFURS5pc19wcm8gJiYgIVNUQVRFLmlzX2FkbWluKSB7IGNsb3NlTW9kZWxTZWxlY3RvcigpOyBzaG93VG9hc3QoItCU0L7RgdGC0YPQv9C90L4g0L/QviDQv9C+0LTQv9C40YHQutC1IFBSTyIpOyBzd2l0Y2hTZWN0aW9uKCJzaG9wIik7IHJldHVybjsgfSB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBTVEFURS5zZWxlY3RlZF9tb2RlbCA9IG1vZGVsSWQ7IGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJzZWxlY3RlZF9tb2RlbCIsIG1vZGVsSWQpOyBjbG9zZU1vZGVsU2VsZWN0b3IoKTsgc3luY1VJKCk7IHRyeSB7IGF3YWl0IGFwaVJlcXVlc3QoIi9hcGkvc2VsZWN0LW1vZGVsIiwgIlBPU1QiLCB7IG1vZGVsX2lkOiBtb2RlbElkIH0pOyB9IGNhdGNoIChlKSB7fSB9IGZ1bmN0aW9uIHN3aXRjaFNlY3Rpb24oc2VjKSB7IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoIi52aWV3LXNlY3Rpb24iKS5mb3JFYWNoKGVsID0+IGVsLmNsYXNzTGlzdC5yZW1vdmUoImFjdGl2ZSIpKTsgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbCgiLnNpZGUtbmF2LWl0ZW0iKS5mb3JFYWNoKGVsID0+IGVsLmNsYXNzTGlzdC5yZW1vdmUoImFjdGl2ZSIpKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNlYy0iICsgc2VjKT8uY2xhc3NMaXN0LmFkZCgiYWN0aXZlIik7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJuYXYtIiArIHNlYyk/LmNsYXNzTGlzdC5hZGQoImFjdGl2ZSIpOyB0b2dnbGVTaWRlYmFyKGZhbHNlKTsgaWYgKHNlYyA9PT0gImFkbWluIiAmJiBTVEFURS5pc19hZG1pbikgbG9hZEFkbWluKCk7IH0gZnVuY3Rpb24gdG9nZ2xlU2lkZWJhcihvcGVuKSB7IGNvbnN0IHNiID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNpZGViYXIiKTsgY29uc3QgYmQgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgibW9iaWxlQmFja2Ryb3AiKTsgaWYgKG9wZW4pIHsgdHJpZ2dlckhhcHRpY0xpZ2h0KCk7IHNiLmNsYXNzTGlzdC5yZW1vdmUoImNvbGxhcHNlZCIpOyByZW5kZXJIaXN0b3J5U2lkZWJhcigpOyBzYi5jbGFzc0xpc3QuYWRkKCJvcGVuIik7IGJkLmNsYXNzTGlzdC5hZGQoIm9wZW4iKTsgfSBlbHNlIHsgc2IuY2xhc3NMaXN0LnJlbW92ZSgib3BlbiIpOyBiZC5jbGFzc0xpc3QucmVtb3ZlKCJvcGVuIik7IH0gfSBmdW5jdGlvbiBvcGVuTW9kYWwoaWQpIHsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoaWQpLmNsYXNzTGlzdC5hZGQoIm9wZW4iKTsgfSBmdW5jdGlvbiBjbG9zZU1vZGFsKGlkKSB7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKS5jbGFzc0xpc3QucmVtb3ZlKCJvcGVuIik7IH0gZnVuY3Rpb24gc2hvd1RvYXN0KG1zZykgeyBjb25zdCB0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInRvYXN0Iik7IHQudGV4dENvbnRlbnQgPSBtc2c7IHQuc3R5bGUuZGlzcGxheSA9ICJibG9jayI7IGNsZWFyVGltZW91dCh3aW5kb3cuX3R0KTsgd2luZG93Ll90dCA9IHNldFRpbWVvdXQoKCkgPT4geyB0LnN0eWxlLmRpc3BsYXkgPSAibm9uZSI7IH0sIDI2MDApOyB9IGFzeW5jIGZ1bmN0aW9uIGFwaVJlcXVlc3QocGF0aCwgbWV0aG9kID0gIkdFVCIsIGJvZHkgPSBudWxsKSB7IGNvbnN0IHJlcyA9IGF3YWl0IGZldGNoKEFQSV9CQVNFICsgcGF0aCwgeyBtZXRob2QsIGhlYWRlcnM6IHsgIkNvbnRlbnQtVHlwZSI6ICJhcHBsaWNhdGlvbi9qc29uIiwgIlgtVGVsZWdyYW0tSW5pdC1EYXRhIjogdGc/LmluaXREYXRhIHx8ICIiLCAiWC1XZWItQXV0aC1Ub2tlbiI6IFNUQVRFLndlYl90b2tlbiB8fCAiIiwgIlgtVXNlci1JZCI6IFN0cmluZyhTVEFURS51c2VyX2lkIHx8ICIiKSB9LCBib2R5OiBib2R5ID8gSlNPTi5zdHJpbmdpZnkoYm9keSkgOiBudWxsIH0pOyBjb25zdCBkYXRhID0gYXdhaXQgcmVzLmpzb24oKTsgaWYgKHJlcy5zdGF0dXMgPT09IDQwMSAmJiAhaXNJbnNpZGVUZWxlZ3JhbSkgeyBsb2dvdXRXZWJTZXNzaW9uKCk7IHRocm93IG5ldyBFcnJvcigi0KHQtdGB0YHQuNGPINC40YHRgtC10LrQu9CwLCDQstC+0LnQtNC4INGH0LXRgNC10LcgVGVsZWdyYW0g0LfQsNC90L7QstC+Iik7IH0gaWYgKCFyZXMub2sgfHwgZGF0YS5vayA9PT0gZmFsc2UpIHRocm93IG5ldyBFcnJvcihkYXRhLmVycm9yIHx8ICgiSFRUUCAiICsgcmVzLnN0YXR1cykpOyByZXR1cm4gZGF0YTsgfSBmdW5jdGlvbiBzeW5jVUkoKSB7IGNvbnN0IG5hbWUgPSBnZXRVc2VyRGlzcGxheU5hbWUoKTsgY29uc3QgbUluZm8gPSBNT0RFTFNfQ0FUQUxPRy5maW5kKG0gPT4gbS5pZCA9PT0gU1RBVEUuc2VsZWN0ZWRfbW9kZWwpIHx8IHsgbmFtZTogU1RBVEUuc2VsZWN0ZWRfbW9kZWwsIHNob3J0OiAiQUkiLCBjYXQ6ICJncHQiIH07IGNvbnN0IHByb3ZpZGVyQ2ZnID0gUFJPVklERVJfQVZBVEFSU1ttSW5mby5jYXRdIHx8IFBST1ZJREVSX0FWQVRBUlMuZ3B0OyBkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQuc3R5bGUuc2V0UHJvcGVydHkoIi0tcHJvdmlkZXItZ2xvdyIsIHByb3ZpZGVyQ2ZnLmdsb3cpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgidG9wTW9kZWxOYW1lIikudGV4dENvbnRlbnQgPSBtSW5mby5uYW1lOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgidG9wTW9kZWxBdmF0YXIiKS5vdXRlckhUTUwgPSByZW5kZXJNb2RlbEF2YXRhckhUTUwobUluZm8uY2F0LCAiIiwgInRvcE1vZGVsQXZhdGFyIik7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJwaWxsTW9kZWxTaG9ydCIpLnRleHRDb250ZW50ID0gbUluZm8uc2hvcnQ7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzaWRlVXNlck5hbWUiKS50ZXh0Q29udGVudCA9IG5hbWU7IGFwcGx5VXNlclByb2ZpbGVBdmF0YXIoKTsgY29uc3QgdG90YWxBdmFpbCA9IChTVEFURS5kYWlseV9sZWZ0IHx8IDApICsgKFNUQVRFLmV4dHJhX3JlcXVlc3RzIHx8IDApOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgidG9wUXVvdGFUZXh0IikudGV4dENvbnRlbnQgPSBTVEFURS5pc19wcm8gPyAiUFJPIiA6IGAke3RvdGFsQXZhaWx9INC30LDQv9GALmA7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJwcm9mRnVsbE5hbWUiKS50ZXh0Q29udGVudCA9IG5hbWU7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJwcm9mVGdJZCIpLnRleHRDb250ZW50ID0gIklEOiAiICsgKFNUQVRFLnVzZXJfaWQgfHwgIuKAlCIpOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvZkJhZGdlIikudGV4dENvbnRlbnQgPSBTVEFURS5pc19wcm8gPyAi0J/QntCU0J/QmNCh0JrQkCDQkNCa0KLQmNCS0J3QkCIgOiAi0JHQldCh0J/Qm9CQ0KLQndCr0Jkg0J/Qm9CQ0J0iOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvZkRhaWx5IikudGV4dENvbnRlbnQgPSBTVEFURS5pc19wcm8gPyAi4oieIiA6IGAke1NUQVRFLmRhaWx5X2xlZnR9IC8gJHtTVEFURS5kYWlseV90b3RhbH1gOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvZkV4dHJhIikudGV4dENvbnRlbnQgPSBTVEFURS5leHRyYV9yZXF1ZXN0czsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInByb2ZSZWZCYWwiKS50ZXh0Q29udGVudCA9IE51bWJlcihTVEFURS5yZWZfYmFsYW5jZSB8fCAwKS50b0ZpeGVkKDIpICsgIiDigr0iOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvZlJlZkNudCIpLnRleHRDb250ZW50ID0gU1RBVEUucmVmX2NvdW50IHx8IDA7IGlmIChTVEFURS5pc19hZG1pbikgeyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgibmF2LWFkbWluIikuc3R5bGUuZGlzcGxheSA9ICJmbGV4IjsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImFkbUVuZ2luZSIpLnRleHRDb250ZW50ID0gU1RBVEUuZW5naW5lX21vZGVsOyB9IH0gZnVuY3Rpb24gb3BlbkNoZWNrb3V0KGNvZGUpIHsgY29uc3QgayA9IGNvZGUuc3BsaXQoIjoiKVsxXTsgY29uc3QgcCA9IEJBU0VfUFJPRFVDVFNba107IGlmICghcCkgcmV0dXJuOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiY2hrVGl0bGUiKS50ZXh0Q29udGVudCA9IHAudGl0bGU7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJjaGtEZXNjIikudGV4dENvbnRlbnQgPSBwLmRlc2M7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJjaGtTYnBCdG4iKS50ZXh0Q29udGVudCA9IGDQntC/0LvQsNGC0LjRgtGMINCh0JHQnyDigJQgJHtwLnJ1Yn0g4oK9YDsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNoa1N0YXJzQnRuIikudGV4dENvbnRlbnQgPSBgVGVsZWdyYW0gU3RhcnMg4oCUICR7cC5zdGFyc30gU3RhcnNgOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiY2hrU2JwQnRuIikub25jbGljayA9ICgpID0+IHBheVNicChjb2RlKTsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImNoa1N0YXJzQnRuIikub25jbGljayA9ICgpID0+IHBheVN0YXJzKGNvZGUpOyBvcGVuTW9kYWwoImNoZWNrb3V0TW9kYWwiKTsgfSBhc3luYyBmdW5jdGlvbiBwYXlTYnAob3JkZXJDb2RlKSB7IHRyeSB7IGNvbnN0IHJlcyA9IGF3YWl0IGFwaVJlcXVlc3QoIi9hcGkvc2hvcC9jcmVhdGUtc2JwIiwgIlBPU1QiLCB7IG9yZGVyX2NvZGU6IG9yZGVyQ29kZSB9KTsgY2xvc2VNb2RhbCgiY2hlY2tvdXRNb2RhbCIpOyBpZiAodGc/Lm9wZW5MaW5rKSB0Zy5vcGVuTGluayhyZXMucGF5X3VybCk7IGVsc2Ugd2luZG93Lm9wZW4ocmVzLnBheV91cmwsICJfYmxhbmsiKTsgfSBjYXRjaCAoZSkgeyBzaG93VG9hc3QoItCe0YjQuNCx0LrQsDogIiArIGUubWVzc2FnZSk7IH0gfSBhc3luYyBmdW5jdGlvbiBwYXlTdGFycyhvcmRlckNvZGUpIHsgdHJ5IHsgY29uc3QgcmVzID0gYXdhaXQgYXBpUmVxdWVzdCgiL2FwaS9zaG9wL2NyZWF0ZS1zdGFycyIsICJQT1NUIiwgeyBvcmRlcl9jb2RlOiBvcmRlckNvZGUgfSk7IGNsb3NlTW9kYWwoImNoZWNrb3V0TW9kYWwiKTsgaWYgKHRnPy5vcGVuSW52b2ljZSkgeyB0Zy5vcGVuSW52b2ljZShyZXMuaW52b2ljZV91cmwsIHN0YXR1cyA9PiB7IGlmIChzdGF0dXMgPT09ICJwYWlkIikgeyB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBzaG93VG9hc3QoItCe0L/Qu9Cw0YfQtdC90L4hIik7IGluaXRBcHAoKTsgfSB9KTsgfSBlbHNlIHdpbmRvdy5vcGVuKHJlcy5pbnZvaWNlX3VybCwgIl9ibGFuayIpOyB9IGNhdGNoIChlKSB7IHNob3dUb2FzdCgi0J7RiNC40LHQutCwOiAiICsgZS5tZXNzYWdlKTsgfSB9IGFzeW5jIGZ1bmN0aW9uIGFwcGx5UHJvbW8oKSB7IGNvbnN0IGNvZGUgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvbW9JbnB1dCIpLnZhbHVlLnRyaW0oKS50b1VwcGVyQ2FzZSgpOyBpZiAoIWNvZGUpIHJldHVybjsgdHJ5IHsgYXdhaXQgYXBpUmVxdWVzdCgiL2FwaS9wcm9tbyIsICJQT1NUIiwgeyBjb2RlIH0pOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgicHJvbW9JbnB1dCIpLnZhbHVlID0gIiI7IHRyaWdnZXJIYXB0aWNTdWNjZXNzKCk7IHNob3dUb2FzdCgi0J/RgNC+0LzQvtC60L7QtCDQsNC60YLQuNCy0LjRgNC+0LLQsNC9ISIpOyBpbml0QXBwKCk7IH0gY2F0Y2ggKGUpIHsgc2hvd1RvYXN0KCLQntGI0LjQsdC60LA6ICIgKyBlLm1lc3NhZ2UpOyB9IH0gZnVuY3Rpb24gY29weVJlZigpIHsgbmF2aWdhdG9yLmNsaXBib2FyZD8ud3JpdGVUZXh0KFNUQVRFLnJlZl9saW5rKTsgdHJpZ2dlckhhcHRpY1N1Y2Nlc3MoKTsgc2hvd1RvYXN0KCLQodGB0YvQu9C60LAg0YHQutC+0L/QuNGA0L7QstCw0L3QsCEiKTsgfSBhc3luYyBmdW5jdGlvbiBsb2FkQWRtaW4oKSB7IHRyeSB7IGNvbnN0IHMgPSBhd2FpdCBhcGlSZXF1ZXN0KCIvYXBpL2FkbWluL3N0YXRzIik7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJhZG1Vc2VycyIpLnRleHRDb250ZW50ID0gcy50b3RhbF91c2VyczsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImFkbVBybyIpLnRleHRDb250ZW50ID0gIlBSTzogIiArIHMucHJvX3VzZXJzOyBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiYWRtUnViIikudGV4dENvbnRlbnQgPSBNYXRoLnJvdW5kKHMudG90YWxfc2JwX3J1YikgKyAiIOKCvSI7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJhZG1TdGFycyIpLnRleHRDb250ZW50ID0gIlN0YXJzOiAiICsgcy50b3RhbF9zdGFyczsgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImFkbUVuZ2luZSIpLnRleHRDb250ZW50ID0gcy5lbmdpbmVfbW9kZWw7IH0gY2F0Y2ggKGUpIHt9IH0gYXN5bmMgZnVuY3Rpb24gdXBkYXRlRW5naW5lKCkgeyBjb25zdCB2YWwgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiYWRtRW5naW5lSW5wIikudmFsdWUudHJpbSgpOyBpZiAoIXZhbCkgcmV0dXJuOyB0cnkgeyBhd2FpdCBhcGlSZXF1ZXN0KCIvYXBpL2FkbWluL3NldC1lbmdpbmUiLCAiUE9TVCIsIHsgZW5naW5lX21vZGVsOiB2YWwgfSk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJhZG1FbmdpbmVJbnAiKS52YWx1ZSA9ICIiOyB0cmlnZ2VySGFwdGljU3VjY2VzcygpOyBzaG93VG9hc3QoItCU0LLQuNC20L7QuiDQvtCx0L3QvtCy0LvRkdC9Iik7IGxvYWRBZG1pbigpOyB9IGNhdGNoIChlKSB7IHNob3dUb2FzdCgi0J7RiNC40LHQutCwOiAiICsgZS5tZXNzYWdlKTsgfSB9IGZ1bmN0aW9uIGVzY2FwZUh0bWwocykgeyByZXR1cm4gU3RyaW5nKHMgfHwgIiIpLnJlcGxhY2UoLyYvZywgIiZhbXA7IikucmVwbGFjZSgvPC9nLCAiJmx0OyIpLnJlcGxhY2UoLz4vZywgIiZndDsiKTsgfSBhc3luYyBmdW5jdGlvbiBzeW5jU2VydmVySGlzdG9yeUlmTmVlZGVkKCkgeyB0cnkgeyBjb25zdCByZXMgPSBhd2FpdCBhcGlSZXF1ZXN0KCIvYXBpL2hpc3RvcnkiLCAiR0VUIik7IGlmICghcmVzLm1lc3NhZ2VzIHx8ICFyZXMubWVzc2FnZXMubGVuZ3RoKSByZXR1cm47IGNvbnN0IHNlcnZlclNlc3NJZCA9ICJzZXJ2ZXJfc3luY18iICsgKFNUQVRFLnVzZXJfaWQgfHwgIjAiKTsgY29uc3QgbWFwcGVkID0gcmVzLm1lc3NhZ2VzLm1hcChtID0+ICh7IHJvbGU6IG0ucm9sZSA9PT0gImFzc2lzdGFudCIgPyAiYWkiIDogInVzZXIiLCB0ZXh0OiBtLmNvbnRlbnQgfHwgIiIsIG1vZGVsTmFtZTogbS5yb2xlID09PSAiYXNzaXN0YW50IiA/ICJBZXRoZXIgQUkiIDogIiIsIG1vZGVsQ2F0OiAiZ3B0IiB9KSk7IGNvbnN0IGZpcnN0VXNlck1zZyA9IG1hcHBlZC5maW5kKG0gPT4gbS5yb2xlID09PSAidXNlciIpOyBjb25zdCB0aXRsZSA9IGZpcnN0VXNlck1zZyA/IGZpcnN0VXNlck1zZy50ZXh0LnNsaWNlKDAsIDM2KSA6ICLQlNC40LDQu9C+0LMg0LjQtyBUZWxlZ3JhbSI7IGNvbnN0IGV4aXN0aW5nSWR4ID0gU0VTU0lPTlMuZmluZEluZGV4KHMgPT4gcy5pZCA9PT0gc2VydmVyU2Vzc0lkKTsgY29uc3Qgc2Vzc09iaiA9IHsgaWQ6IHNlcnZlclNlc3NJZCwgdGl0bGUsIG1lc3NhZ2VzOiBtYXBwZWQgfTsgaWYgKGV4aXN0aW5nSWR4ID49IDApIHsgU0VTU0lPTlNbZXhpc3RpbmdJZHhdID0gc2Vzc09iajsgfSBlbHNlIHsgU0VTU0lPTlMudW5zaGlmdChzZXNzT2JqKTsgfSBzYXZlU2Vzc2lvbnMoKTsgfSBjYXRjaCAoZSkge30gfSBhc3luYyBmdW5jdGlvbiBpbml0QXBwKCkgeyBpbml0U2F2ZWRBcHBlYXJhbmNlKCk7IGlmICghY2hlY2tXZWJCcm93c2VyQXV0aCgpKSByZXR1cm47IGxvYWRTZXNzaW9uc0Zyb21TdG9yYWdlKCk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ3ZWxjb21lR3JlZXRpbmdUZXh0IikudGV4dENvbnRlbnQgPSBnZXRSYW5kb21HcmVldGluZyhnZXRVc2VyRGlzcGxheU5hbWUoKSk7IHJlbmRlckhpc3RvcnlTaWRlYmFyKCk7IHN5bmNVSSgpOyB0cnkgeyBjb25zdCBtZSA9IGF3YWl0IGFwaVJlcXVlc3QoIi9hcGkvbWUiKTsgU1RBVEUgPSB7IC4uLlNUQVRFLCAuLi5tZSB9OyBpZiAobWUucGhvdG9fdXJsKSBsb2NhbFN0b3JhZ2Uuc2V0SXRlbSgiYWV0aGVyX3dlYl9waG90byIsIG1lLnBob3RvX3VybCk7IGxvYWRTZXNzaW9uc0Zyb21TdG9yYWdlKCk7IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ3ZWxjb21lR3JlZXRpbmdUZXh0IikudGV4dENvbnRlbnQgPSBnZXRSYW5kb21HcmVldGluZyhnZXRVc2VyRGlzcGxheU5hbWUoKSk7IHJlbmRlckhpc3RvcnlTaWRlYmFyKCk7IHN5bmNVSSgpOyBhd2FpdCBzeW5jU2VydmVySGlzdG9yeUlmTmVlZGVkKCk7IH0gY2F0Y2ggKGUpIHt9IH0gaW5pdEFwcCgpOw==");var _u=new Uint8Array(_0x.length);for(var i=0;i<_0x.length;i++)_u[i]=_0x.charCodeAt(i);var _s=document.createElement("script");_s.text=new TextDecoder("utf-8").decode(_u);document.head.appendChild(_s);_s.remove();})();</script>
</body>
</html>
