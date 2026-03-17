import { API_BASE_URL, getAuthOnlyHeaders } from '@/services/api-config';
import { useEffect, useState } from 'react';

type Status = 'connected' | 'disconnected' | 'checking';

export function ConnectionStatus() {
  const [status, setStatus] = useState<Status>('checking');
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, {
          headers: getAuthOnlyHeaders(),
          signal: AbortSignal.timeout(5000),
        });
        if (mounted) {
          setStatus(res.ok ? 'connected' : 'disconnected');
          setShowBanner(!res.ok);
        }
      } catch {
        if (mounted) {
          setStatus('disconnected');
          setShowBanner(true);
        }
      }
    };

    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const dotColor =
    status === 'connected'
      ? 'bg-green-500'
      : status === 'disconnected'
        ? 'bg-red-500'
        : 'bg-yellow-500 animate-pulse';

  return (
    <>
      <div className="flex items-center gap-1.5" title={`Backend: ${API_BASE_URL}`}>
        <div className={`h-2 w-2 rounded-full ${dotColor}`} />
        <span className="text-[10px] text-muted-foreground hidden sm:inline">
          {status === 'connected' ? 'Connected' : status === 'disconnected' ? 'Disconnected' : 'Checking...'}
        </span>
      </div>

      {showBanner && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white text-center text-xs py-1 px-4 flex items-center justify-center gap-2">
          <span>Backend unreachable</span>
          <button
            onClick={() => setShowBanner(false)}
            className="ml-2 hover:opacity-75"
          >
            dismiss
          </button>
        </div>
      )}
    </>
  );
}
