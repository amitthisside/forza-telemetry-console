import React, { useEffect, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation
} from 'react-router-dom';

import './styles.css';

type TelemetryFrame = {
  speed: number;
  rpm: number;
  gear: number;
  throttle: number;
  brake: number;
  steering: number;
  lap_number?: number;
};

const emptyFrame: TelemetryFrame = {
  speed: 0,
  rpm: 0,
  gear: 0,
  throttle: 0,
  brake: 0,
  steering: 0,
  lap_number: 0
};

function useTelemetryStream() {
  const [connected, setConnected] = useState(false);
  const [frame, setFrame] = useState<TelemetryFrame>(emptyFrame);

  useEffect(() => {
    const wsUrl =
      (import.meta.env.VITE_STREAM_WS_URL as string | undefined) ??
      'ws://localhost:8101/ws/telemetry';

    let interval: number | undefined;
    let ws: WebSocket | undefined;

    const applyMockData = () => {
      interval = window.setInterval(() => {
        setFrame((prev) => ({
          speed: Math.max(0, prev.speed + (Math.random() * 10 - 5)),
          rpm: Math.max(1000, prev.rpm + (Math.random() * 700 - 350)),
          gear: Math.max(1, Math.min(8, prev.gear + (Math.random() > 0.8 ? 1 : 0))),
          throttle: Math.min(1, Math.max(0, Math.random())),
          brake: Math.min(1, Math.max(0, Math.random() * 0.7)),
          steering: Math.max(-1, Math.min(1, Math.random() * 2 - 1)),
          lap_number: (prev.lap_number ?? 1) + (Math.random() > 0.98 ? 1 : 0)
        }));
      }, 800);
    };

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        applyMockData();
      };
      ws.onerror = () => {
        setConnected(false);
        ws?.close();
      };
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as {
            type?: string;
            data?: Partial<TelemetryFrame>;
          };
          if (payload.type === 'frame' && payload.data) {
            setFrame((prev) => ({ ...prev, ...payload.data }));
          }
        } catch {
          // Ignore malformed frame payloads.
        }
      };
    } catch {
      applyMockData();
    }

    return () => {
      if (interval !== undefined) {
        window.clearInterval(interval);
      }
      ws?.close();
    };
  }, []);

  return { connected, frame };
}

function Sidebar() {
  const location = useLocation();
  const overlayMode = location.pathname.startsWith('/overlay');

  const links = [
    ['/', 'Live'],
    ['/map', 'Map'],
    ['/analysis', 'Analysis'],
    ['/coaching', 'Coaching'],
    ['/diagnostics', 'Diagnostics'],
    ['/history', 'History'],
    ['/devices', 'Devices'],
    ['/overlay/config', 'Overlay Config'],
    ['/overlay', 'Overlay Route']
  ];

  return (
    <aside className="sidebar">
      <div className="brand">Forza Telemetry Console</div>
      <div className="badge">{overlayMode ? 'Overlay Mode' : 'Operator Mode'}</div>
      <nav className="nav" style={{ marginTop: 12 }}>
        {links.map(([path, label]) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) => (isActive ? 'active' : '')}
            end={path === '/'}
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

function LiveView({ frame, connected }: { frame: TelemetryFrame; connected: boolean }) {
  return (
    <section>
      <h1>Live Dashboard</h1>
      <p>
        Stream status: <strong>{connected ? 'Connected' : 'Simulated'}</strong>
      </p>
      <div className="card-grid">
        <Metric label="Speed" value={`${frame.speed.toFixed(1)} km/h`} />
        <Metric label="RPM" value={frame.rpm.toFixed(0)} />
        <Metric label="Gear" value={`${frame.gear}`} />
        <Metric label="Lap" value={`${frame.lap_number ?? 0}`} />
      </div>
      <div className="row">
        <Card title="Inputs">
          <ul className="list">
            <li>Throttle: {(frame.throttle * 100).toFixed(0)}%</li>
            <li>Brake: {(frame.brake * 100).toFixed(0)}%</li>
            <li>Steering: {(frame.steering * 100).toFixed(0)}%</li>
          </ul>
        </Card>
        <Card title="Session State">
          <ul className="list">
            <li>Tire slip warnings: pending analytics integration</li>
            <li>Delta indicator: pending session baseline</li>
            <li>Traction summary: from diagnostics endpoint (next hookup)</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function MapView({ frame }: { frame: TelemetryFrame }) {
  return (
    <section>
      <h1>Track Map</h1>
      <div className="row">
        <Card title="Live Map Preview">
          <p className="label">Current speed</p>
          <div className="value">{frame.speed.toFixed(1)} km/h</div>
          <p style={{ color: 'var(--muted)' }}>
            Path reconstruction and color overlays are scaffolded for stream/session integration.
          </p>
        </Card>
        <Card title="Replay Controls">
          <ul className="list">
            <li>Frame scrubbing (planned)</li>
            <li>Color by speed/throttle/brake (planned)</li>
            <li>Lap segment bookmarks (planned)</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function AnalysisView() {
  return (
    <section>
      <h1>Analysis</h1>
      <div className="row">
        <Card title="Lap Comparison">
          <ul className="list">
            <li>Best lap vs current lap trace</li>
            <li>Corner entry/exit trend markers</li>
            <li>Brake and throttle traces</li>
          </ul>
        </Card>
        <Card title="Events">
          <ul className="list">
            <li>Wheelspin events</li>
            <li>Heavy braking markers</li>
            <li>Instability zones</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function CoachingView() {
  return (
    <section>
      <h1>Coaching</h1>
      <div className="row">
        <Card title="Top Issues (Current Session)">
          <ul className="list">
            <li>Early throttle causing rear slip</li>
            <li>Inconsistent brake release</li>
            <li>Reduced corner exit speed</li>
          </ul>
        </Card>
        <Card title="Severity Ranking">
          <p style={{ color: 'var(--muted)' }}>
            Wired to `/api/v1/coaching/sessions/:id` in next integration pass.
          </p>
        </Card>
      </div>
    </section>
  );
}

function DiagnosticsView() {
  return (
    <section>
      <h1>Diagnostics</h1>
      <div className="row">
        <Card title="Traction & Handling">
          <ul className="list">
            <li>Oversteer trend: monitored</li>
            <li>Understeer trend: monitored</li>
            <li>Instability zones: monitored</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function HistoryView() {
  return (
    <section>
      <h1>History</h1>
      <div className="row">
        <Card title="Session History">
          <ul className="list">
            <li>Best laps</li>
            <li>Average lap times</li>
            <li>Consistency score trend</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function DevicesView() {
  return (
    <section>
      <h1>Devices</h1>
      <div className="row">
        <Card title="Adapter Status">
          <ul className="list">
            <li>Serial adapter: not configured</li>
            <li>UDP adapter: available</li>
            <li>Simulated mode: available</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function OverlayConfigView() {
  return (
    <section>
      <h1>Overlay Config</h1>
      <div className="row">
        <Card title="Widget Presets">
          <ul className="list">
            <li>Speed + gear compact</li>
            <li>Input bars HUD</li>
            <li>Delta + warning strip</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function OverlayLiveView({ frame }: { frame: TelemetryFrame }) {
  return (
    <section>
      <h1>Overlay Route</h1>
      <div className="overlay-preview">
        <div style={{ fontSize: 12, opacity: 0.7 }}>OBS Overlay Preview</div>
        <div style={{ fontSize: 40, fontWeight: 700 }}>{frame.speed.toFixed(0)} km/h</div>
        <div>Gear {frame.gear} · RPM {frame.rpm.toFixed(0)}</div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </article>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="card">
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {children}
    </article>
  );
}

function App() {
  const { connected, frame } = useTelemetryStream();
  const frameMemo = useMemo(() => frame, [frame]);

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <main className="content">
          <Routes>
            <Route path="/" element={<LiveView frame={frameMemo} connected={connected} />} />
            <Route path="/map" element={<MapView frame={frameMemo} />} />
            <Route path="/analysis" element={<AnalysisView />} />
            <Route path="/coaching" element={<CoachingView />} />
            <Route path="/diagnostics" element={<DiagnosticsView />} />
            <Route path="/history" element={<HistoryView />} />
            <Route path="/devices" element={<DevicesView />} />
            <Route path="/overlay/config" element={<OverlayConfigView />} />
            <Route path="/overlay" element={<OverlayLiveView frame={frameMemo} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
