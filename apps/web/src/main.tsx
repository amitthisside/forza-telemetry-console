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

type SessionSummary = {
  session_id: string;
  started_at: string;
  ended_at?: string | null;
};

type TrackPathPoint = {
  frame_index: number;
  lap_id?: string | null;
  x: number;
  y: number;
  z: number;
  color_value: number;
};

type ReplayFrame = {
  frame_index: number;
  lap_id?: string | null;
  speed: number;
  throttle: number;
  brake: number;
  position_x: number;
  position_z: number;
};

type SessionTimeline = {
  frame_start: number | null;
  frame_end: number | null;
  frame_count: number;
};

type SessionAnalysis = {
  coaching_messages: number;
  diagnostics: number;
  lap_count: number;
  best_lap_ms?: number | null;
  consistency_score: number;
};

type DiagnosticsPayload = {
  diagnostics: Array<{ diagnostic_type: string; summary: string; score: number }>;
  zones: Array<{ zone_id: string; x: number; z: number; occurrences: number }>;
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

function useMapReplayData() {
  const sessionApiBase =
    ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8102').replace(
      /\/$/,
      ''
    );

  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [colorBy, setColorBy] = useState<'speed' | 'throttle' | 'brake'>('speed');
  const [pathPoints, setPathPoints] = useState<TrackPathPoint[]>([]);
  const [replayFrames, setReplayFrames] = useState<ReplayFrame[]>([]);
  const [timeline, setTimeline] = useState<SessionTimeline | null>(null);
  const [activeFrame, setActiveFrame] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadSessions() {
      try {
        const response = await fetch(`${sessionApiBase}/api/v1/sessions`);
        if (!response.ok) {
          throw new Error(`sessions request failed: ${response.status}`);
        }
        const payload = (await response.json()) as SessionSummary[];
        if (cancelled) {
          return;
        }
        setSessions(payload);
        if (payload.length > 0) {
          setSessionId(payload[0].session_id);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      }
    }
    void loadSessions();
    return () => {
      cancelled = true;
    };
  }, [sessionApiBase]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }
    let cancelled = false;

    async function loadReplayData() {
      try {
        const [timelineResp, pathResp] = await Promise.all([
          fetch(`${sessionApiBase}/api/v1/sessions/${sessionId}/timeline`),
          fetch(
            `${sessionApiBase}/api/v1/sessions/${sessionId}/track/path?color_by=${colorBy}&limit=4000`
          )
        ]);
        if (!timelineResp.ok || !pathResp.ok) {
          throw new Error('timeline/path request failed');
        }

        const timelinePayload = (await timelineResp.json()) as SessionTimeline;
        const pathPayload = (await pathResp.json()) as { points: TrackPathPoint[] };
        if (cancelled) {
          return;
        }

        setTimeline(timelinePayload);
        setPathPoints(pathPayload.points);

        if (timelinePayload.frame_start === null || timelinePayload.frame_end === null) {
          setReplayFrames([]);
          setActiveFrame(0);
          return;
        }

        const range = timelinePayload.frame_end - timelinePayload.frame_start + 1;
        const step = Math.max(1, Math.ceil(range / 2000));
        const replayResp = await fetch(
          `${sessionApiBase}/api/v1/sessions/${sessionId}/replay?start_frame=${timelinePayload.frame_start}&end_frame=${timelinePayload.frame_end}&step=${step}&limit=2000`
        );
        if (!replayResp.ok) {
          throw new Error('replay request failed');
        }
        const replayPayload = (await replayResp.json()) as { frames: ReplayFrame[] };
        if (cancelled) {
          return;
        }
        setReplayFrames(replayPayload.frames);
        setActiveFrame(timelinePayload.frame_start);
        setError(null);
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      }
    }

    void loadReplayData();
    return () => {
      cancelled = true;
    };
  }, [colorBy, sessionApiBase, sessionId]);

  useEffect(() => {
    if (!isPlaying || replayFrames.length < 2) {
      return;
    }
    const id = window.setInterval(() => {
      setActiveFrame((prev) => {
        const max = replayFrames[replayFrames.length - 1]?.frame_index ?? prev;
        const min = replayFrames[0]?.frame_index ?? prev;
        if (prev >= max) {
          return min;
        }
        return prev + 1;
      });
    }, 120);
    return () => window.clearInterval(id);
  }, [isPlaying, replayFrames]);

  return {
    sessions,
    sessionId,
    setSessionId,
    colorBy,
    setColorBy,
    pathPoints,
    replayFrames,
    timeline,
    activeFrame,
    setActiveFrame,
    isPlaying,
    setIsPlaying,
    error
  };
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
  const {
    sessions,
    sessionId,
    setSessionId,
    colorBy,
    setColorBy,
    pathPoints,
    replayFrames,
    timeline,
    activeFrame,
    setActiveFrame,
    isPlaying,
    setIsPlaying,
    error
  } = useMapReplayData();

  const mappedPoints = useMemo(() => {
    if (pathPoints.length === 0) {
      return [];
    }
    const xs = pathPoints.map((p) => p.x);
    const zs = pathPoints.map((p) => p.z);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minZ = Math.min(...zs);
    const maxZ = Math.max(...zs);
    const spanX = Math.max(1, maxX - minX);
    const spanZ = Math.max(1, maxZ - minZ);

    const values = pathPoints.map((p) => p.color_value);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const spanV = Math.max(0.001, maxV - minV);

    return pathPoints.map((point) => {
      const normalized = (point.color_value - minV) / spanV;
      const hue = 210 - Math.round(180 * normalized);
      return {
        ...point,
        sx: ((point.x - minX) / spanX) * 960 + 20,
        sy: ((point.z - minZ) / spanZ) * 520 + 20,
        color: `hsl(${hue} 82% 48%)`
      };
    });
  }, [pathPoints]);

  const marker = useMemo(() => {
    if (mappedPoints.length === 0) {
      return null;
    }
    let nearest = mappedPoints[0];
    let distance = Math.abs(nearest.frame_index - activeFrame);
    for (const point of mappedPoints) {
      const nextDistance = Math.abs(point.frame_index - activeFrame);
      if (nextDistance < distance) {
        nearest = point;
        distance = nextDistance;
      }
    }
    return nearest;
  }, [activeFrame, mappedPoints]);

  return (
    <section>
      <h1>Track Map</h1>
      <div className="row">
        <Card title="Live Map Preview">
          <div className="map-toolbar">
            <label>
              Session
              <select value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
                {sessions.map((session) => (
                  <option key={session.session_id} value={session.session_id}>
                    {session.session_id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Color By
              <select
                value={colorBy}
                onChange={(e) => setColorBy(e.target.value as 'speed' | 'throttle' | 'brake')}
              >
                <option value="speed">Speed</option>
                <option value="throttle">Throttle</option>
                <option value="brake">Brake</option>
              </select>
            </label>
          </div>
          <svg className="map-canvas" viewBox="0 0 1000 560" role="img" aria-label="track map">
            <rect x="0" y="0" width="1000" height="560" fill="#f7f6f3" stroke="#d9d2c6" />
            {mappedPoints.map((point) => (
              <circle key={point.frame_index} cx={point.sx} cy={point.sy} r="2.8" fill={point.color} />
            ))}
            {marker ? (
              <circle cx={marker.sx} cy={marker.sy} r="7" fill="none" stroke="black" strokeWidth="2.5" />
            ) : null}
          </svg>
          {error ? <p style={{ color: 'var(--danger)' }}>{error}</p> : null}
        </Card>
        <Card title="Replay Controls">
          <p className="label">Current speed</p>
          <div className="value">{frame.speed.toFixed(1)} km/h</div>
          <button className="play-btn" onClick={() => setIsPlaying((p) => !p)}>
            {isPlaying ? 'Pause Replay' : 'Play Replay'}
          </button>
          <input
            type="range"
            min={timeline?.frame_start ?? 0}
            max={timeline?.frame_end ?? 0}
            value={activeFrame}
            onChange={(e) => setActiveFrame(Number(e.target.value))}
            className="replay-slider"
          />
          <ul className="list">
            <li>Frame: {activeFrame}</li>
            <li>Replay samples: {replayFrames.length}</li>
            <li>Total frames: {timeline?.frame_count ?? 0}</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

function AnalysisView() {
  const [analysis, setAnalysis] = useState<SessionAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sessionApiBase =
    ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8102').replace(
      /\/$/,
      ''
    );
  const analyticsApiBase = (
    (import.meta.env.VITE_ANALYTICS_API_BASE_URL as string | undefined) ?? 'http://localhost:8103'
  ).replace(/\/$/, '');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const sessionsResponse = await fetch(`${sessionApiBase}/api/v1/sessions`);
        if (!sessionsResponse.ok) {
          throw new Error('sessions request failed');
        }
        const sessions = (await sessionsResponse.json()) as SessionSummary[];
        if (sessions.length === 0 || cancelled) {
          return;
        }
        const sessionId = sessions[0].session_id;
        const analysisResponse = await fetch(
          `${analyticsApiBase}/api/v1/analysis/sessions/${sessionId}`
        );
        if (!analysisResponse.ok) {
          throw new Error('analysis request failed');
        }
        const payload = (await analysisResponse.json()) as SessionAnalysis;
        if (!cancelled) {
          setAnalysis(payload);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [analyticsApiBase, sessionApiBase]);

  return (
    <section>
      <h1>Analysis</h1>
      <div className="row">
        <Card title="Lap Comparison">
          <ul className="list">
            <li>Lap count: {analysis?.lap_count ?? 0}</li>
            <li>Best lap: {analysis?.best_lap_ms ?? '-'} ms</li>
            <li>Consistency score: {analysis?.consistency_score?.toFixed(3) ?? '0.000'}</li>
          </ul>
        </Card>
        <Card title="Events">
          <ul className="list">
            <li>Coaching messages: {analysis?.coaching_messages ?? 0}</li>
            <li>Diagnostics count: {analysis?.diagnostics ?? 0}</li>
            <li>Trace stats API integration complete</li>
          </ul>
          {error ? <p style={{ color: 'var(--danger)' }}>{error}</p> : null}
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
  const [payload, setPayload] = useState<DiagnosticsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const sessionApiBase =
      ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8102').replace(
        /\/$/,
        ''
      );
    const analyticsApiBase = (
      (import.meta.env.VITE_ANALYTICS_API_BASE_URL as string | undefined) ?? 'http://localhost:8103'
    ).replace(/\/$/, '');

    async function load() {
      try {
        const sessionsResponse = await fetch(`${sessionApiBase}/api/v1/sessions`);
        if (!sessionsResponse.ok) {
          throw new Error('sessions request failed');
        }
        const sessions = (await sessionsResponse.json()) as SessionSummary[];
        if (sessions.length === 0 || cancelled) {
          return;
        }
        const response = await fetch(
          `${analyticsApiBase}/api/v1/diagnostics/sessions/${sessions[0].session_id}`
        );
        if (!response.ok) {
          throw new Error('diagnostics request failed');
        }
        const diagnostics = (await response.json()) as DiagnosticsPayload;
        if (!cancelled) {
          setPayload(diagnostics);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h1>Diagnostics</h1>
      <div className="row">
        <Card title="Traction & Handling">
          <ul className="list">
            {payload?.diagnostics?.map((item) => (
              <li key={item.diagnostic_type}>
                {item.diagnostic_type}: {item.summary} ({item.score.toFixed(2)})
              </li>
            ))}
            {(payload?.diagnostics?.length ?? 0) === 0 ? <li>No diagnostics available.</li> : null}
          </ul>
        </Card>
        <Card title="Instability Zones">
          <ul className="list">
            {payload?.zones?.map((zone) => (
              <li key={zone.zone_id}>
                {zone.zone_id}: x={zone.x}, z={zone.z}, occurrences={zone.occurrences}
              </li>
            ))}
            {(payload?.zones?.length ?? 0) === 0 ? <li>No zones identified yet.</li> : null}
          </ul>
          {error ? <p style={{ color: 'var(--danger)' }}>{error}</p> : null}
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
