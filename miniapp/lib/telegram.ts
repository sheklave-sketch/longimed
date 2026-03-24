declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
        };
        BackButton: {
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
        };
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
          start_param?: string;
        };
        colorScheme: "light" | "dark";
        themeParams: Record<string, string>;
        openTelegramLink: (url: string) => void;
      };
    };
  }
}

export function getTelegram() {
  if (typeof window === "undefined") return null;
  return window.Telegram?.WebApp ?? null;
}

export function getTelegramUser() {
  return getTelegram()?.initDataUnsafe?.user ?? null;
}

export function initTelegram() {
  const tg = getTelegram();
  if (tg) {
    tg.ready();
    tg.expand();
  }
  return tg;
}

export function openBotLink(path: string) {
  const tg = getTelegram();
  if (tg) {
    tg.openTelegramLink(`https://t.me/longimed_bot?start=${path}`);
  } else {
    window.open(`https://t.me/longimed_bot?start=${path}`, "_blank");
  }
}
