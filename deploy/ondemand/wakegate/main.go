// wakegate: tiny wake-on-request reverse proxy for one Docker container.
//
// cloudflared -> wakegate -> app container. If the app container is stopped, the first
// request starts it through the Docker API and blocks until it is healthy (or returns a
// "starting up" page after WAKE_TIMEOUT). The container is stopped again after a
// momentum-based idle period: BASE_IDLE after the last request (sliding window), or
// EXTENDED_IDLE when traffic in the last EXTENDED_IDLE was sustained (requests spread
// over >= SUSTAIN_SPAN, or from >= SUSTAIN_CLIENTS distinct clients). Stdlib only.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type config struct {
	listen, adminListen, upstream, label, sock string
	baseIdle, extIdle, span                    time.Duration
	minClients                                 int
	wakeTimeout, checkEvery, stopTimeout       time.Duration
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func envDur(k, d string) time.Duration {
	v, err := time.ParseDuration(env(k, d))
	if err != nil {
		log.Fatalf("bad %s: %v", k, err)
	}
	return v
}

type hit struct {
	t      time.Time
	client string
}

type gate struct {
	cfg    config
	docker *http.Client
	proxy  *httputil.ReverseProxy

	mu        sync.Mutex // guards hits, lastReq
	hits      []hit
	lastReq   time.Time
	started   time.Time
	inflight  atomic.Int64
	readyTill atomic.Int64 // unix nanos until which we trust "running+healthy"

	lifeMu sync.Mutex // serialises start/stop
	state  atomic.Value
}

func (g *gate) dockerReq(ctx context.Context, method, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, method, "http://docker"+path, nil)
	if err != nil {
		return nil, err
	}
	return g.docker.Do(req)
}

type cstate struct {
	ID      string
	Running bool
	Health  string // "", starting, healthy, unhealthy
}

func (g *gate) inspect(ctx context.Context) (*cstate, error) {
	f := url.QueryEscape(fmt.Sprintf(`{"label":["%s"]}`, g.cfg.label))
	resp, err := g.dockerReq(ctx, "GET", "/containers/json?all=1&filters="+f)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var list []struct{ Id string }
	if err := json.NewDecoder(resp.Body).Decode(&list); err != nil {
		return nil, err
	}
	if len(list) == 0 {
		return nil, fmt.Errorf("no container with label %s", g.cfg.label)
	}
	resp2, err := g.dockerReq(ctx, "GET", "/containers/"+list[0].Id+"/json")
	if err != nil {
		return nil, err
	}
	defer resp2.Body.Close()
	var ins struct {
		State struct {
			Running bool
			Health  *struct{ Status string }
		}
	}
	if err := json.NewDecoder(resp2.Body).Decode(&ins); err != nil {
		return nil, err
	}
	cs := &cstate{ID: list[0].Id, Running: ins.State.Running}
	if ins.State.Health != nil {
		cs.Health = ins.State.Health.Status
	}
	return cs, nil
}

func (cs *cstate) ready() bool {
	return cs.Running && (cs.Health == "" || cs.Health == "healthy")
}

func (g *gate) setState(s string) {
	if old, _ := g.state.Load().(string); old != s {
		g.state.Store(s)
		log.Printf("state: %s", s)
	}
}

// ensureReady starts the container if needed and waits until it is healthy.
func (g *gate) ensureReady(ctx context.Context) error {
	if time.Now().UnixNano() < g.readyTill.Load() {
		return nil
	}
	g.lifeMu.Lock()
	defer g.lifeMu.Unlock()
	if time.Now().UnixNano() < g.readyTill.Load() {
		return nil
	}
	cs, err := g.inspect(ctx)
	if err != nil {
		return err
	}
	if cs.ready() {
		g.markReady()
		return nil
	}
	t0 := time.Now()
	if !cs.Running {
		log.Printf("wake: starting container %.12s", cs.ID)
		g.setState("starting")
		resp, err := g.dockerReq(ctx, "POST", "/containers/"+cs.ID+"/start")
		if err != nil {
			return err
		}
		io.Copy(io.Discard, resp.Body)
		resp.Body.Close()
		if resp.StatusCode >= 300 && resp.StatusCode != 304 {
			return fmt.Errorf("docker start: HTTP %d", resp.StatusCode)
		}
	}
	deadline := time.Now().Add(g.cfg.wakeTimeout)
	for time.Now().Before(deadline) {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(300 * time.Millisecond):
		}
		cs, err = g.inspect(ctx)
		if err == nil && cs.ready() {
			log.Printf("wake: ready after %.1fs", time.Since(t0).Seconds())
			g.markReady()
			return nil
		}
	}
	return fmt.Errorf("not ready after %s", g.cfg.wakeTimeout)
}

func (g *gate) markReady() {
	g.readyTill.Store(time.Now().Add(g.cfg.checkEvery).UnixNano())
	g.setState("running")
}

func clientOf(r *http.Request) string {
	if c := r.Header.Get("Cf-Connecting-Ip"); c != "" {
		return c
	}
	h, _, _ := net.SplitHostPort(r.RemoteAddr)
	return h
}

func (g *gate) record(r *http.Request) {
	now := time.Now()
	g.mu.Lock()
	g.lastReq = now
	g.hits = append(g.hits, hit{now, clientOf(r)})
	if len(g.hits) > 200000 {
		g.hits = g.hits[len(g.hits)-100000:]
	}
	g.mu.Unlock()
}

// idleWindow returns the current keep-alive window and its stats.
func (g *gate) idleWindow(now time.Time) (time.Duration, time.Time, bool, float64, int) {
	g.mu.Lock()
	defer g.mu.Unlock()
	// keep 2x the extended window of history; judge momentum over the extended
	// window that ends at the most recent request, so the decision is stable.
	prune := now.Add(-2 * g.cfg.extIdle)
	i := 0
	for i < len(g.hits) && g.hits[i].t.Before(prune) {
		i++
	}
	g.hits = g.hits[i:]
	last := g.lastReq
	if last.IsZero() {
		last = g.started
	}
	cut := last.Add(-g.cfg.extIdle)
	var first time.Time
	clients := map[string]struct{}{}
	for _, h := range g.hits {
		if h.t.Before(cut) {
			continue
		}
		if first.IsZero() {
			first = h.t
		}
		clients[h.client] = struct{}{}
	}
	if len(clients) == 0 {
		return g.cfg.baseIdle, last, false, 0, 0
	}
	span := g.hits[len(g.hits)-1].t.Sub(first)
	sustained := span >= g.cfg.span || len(clients) >= g.cfg.minClients
	if sustained {
		return g.cfg.extIdle, last, true, span.Minutes(), len(clients)
	}
	return g.cfg.baseIdle, last, false, span.Minutes(), len(clients)
}

func (g *gate) idleLoop() {
	lastSustained := false
	for range time.Tick(15 * time.Second) {
		now := time.Now()
		win, last, sustained, span, clients := g.idleWindow(now)
		if sustained != lastSustained {
			log.Printf("momentum: sustained=%v span=%.1fm clients=%d keepalive=%s", sustained, span, clients, win)
			lastSustained = sustained
		}
		if now.Sub(last) < win || g.inflight.Load() > 0 {
			continue
		}
		g.lifeMu.Lock()
		// re-check under the lock: a request may have arrived meanwhile
		win, last, _, _, _ = g.idleWindow(time.Now())
		if time.Since(last) >= win && g.inflight.Load() == 0 {
			ctx, cancel := context.WithTimeout(context.Background(), g.cfg.stopTimeout+30*time.Second)
			cs, err := g.inspect(ctx)
			if err == nil && cs.Running {
				log.Printf("idle: no requests for %s (window %s), stopping %.12s", time.Since(last).Round(time.Second), win, cs.ID)
				g.readyTill.Store(0)
				resp, err := g.dockerReq(ctx, "POST", fmt.Sprintf("/containers/%s/stop?t=%d", cs.ID, int(g.cfg.stopTimeout.Seconds())))
				if err != nil {
					log.Printf("idle: stop failed: %v", err)
				} else {
					io.Copy(io.Discard, resp.Body)
					resp.Body.Close()
					g.setState("stopped")
				}
			} else if err == nil {
				g.setState("stopped")
			}
			cancel()
		}
		g.lifeMu.Unlock()
	}
}

const startingPage = `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<title>Starting up…</title><style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;
justify-content:center;height:100vh;margin:0;color:#333}</style></head><body><div><h1>Starting up…</h1>
<p>Study OS was asleep and is waking up. This page refreshes automatically.</p></div></body></html>`

func (g *gate) unavailable(w http.ResponseWriter, r *http.Request, err error) {
	log.Printf("unavailable: %s %s: %v", r.Method, r.URL.Path, err)
	w.Header().Set("Retry-After", "5")
	w.Header().Set("Cache-Control", "no-store")
	if strings.Contains(r.Header.Get("Accept"), "text/html") {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.WriteHeader(http.StatusServiceUnavailable)
		io.WriteString(w, startingPage)
		return
	}
	http.Error(w, "service is starting up, retry shortly", http.StatusServiceUnavailable)
}

func (g *gate) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	g.record(r)
	g.inflight.Add(1)
	defer func() {
		g.inflight.Add(-1)
		g.mu.Lock()
		g.lastReq = time.Now()
		g.mu.Unlock()
	}()
	if err := g.ensureReady(r.Context()); err != nil {
		g.unavailable(w, r, err)
		return
	}
	g.proxy.ServeHTTP(w, r)
}

func main() {
	log.SetFlags(log.LstdFlags | log.LUTC)
	if len(os.Args) > 1 && os.Args[1] == "healthcheck" {
		c := http.Client{Timeout: 3 * time.Second}
		resp, err := c.Get("http://127.0.0.1" + env("ADMIN_LISTEN", ":8082") + "/healthz")
		if err != nil || resp.StatusCode != 200 {
			os.Exit(1)
		}
		os.Exit(0)
	}
	cfg := config{
		listen:      env("LISTEN", ":8000"),
		adminListen: env("ADMIN_LISTEN", ":8082"),
		upstream:    env("UPSTREAM", "http://study-os-api-upstream:8000"),
		label:       env("TARGET_LABEL", "ondemand.group=study-os"),
		sock:        env("DOCKER_SOCK", "/var/run/docker.sock"),
		baseIdle:    envDur("BASE_IDLE", "30m"),
		extIdle:     envDur("EXTENDED_IDLE", "60m"),
		span:        envDur("SUSTAIN_SPAN", "10m"),
		wakeTimeout: envDur("WAKE_TIMEOUT", "90s"),
		checkEvery:  envDur("READY_CACHE", "5s"),
		stopTimeout: envDur("STOP_TIMEOUT", "20s"),
	}
	cfg.minClients, _ = strconv.Atoi(env("SUSTAIN_CLIENTS", "3"))
	up, err := url.Parse(cfg.upstream)
	if err != nil {
		log.Fatal(err)
	}
	g := &gate{cfg: cfg, started: time.Now()}
	g.docker = &http.Client{
		Transport: &http.Transport{DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			var d net.Dialer
			return d.DialContext(ctx, "unix", cfg.sock)
		}},
		Timeout: 60 * time.Second,
	}
	rp := httputil.NewSingleHostReverseProxy(up)
	rp.FlushInterval = -1 // stream SSE / chunked responses immediately
	rp.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		g.readyTill.Store(0) // re-inspect on next request
		if r.Context().Err() != nil {
			return
		}
		g.unavailable(w, r, err)
	}
	g.proxy = rp

	if cs, err := g.inspect(context.Background()); err == nil {
		if cs.Running {
			g.setState("running")
		} else {
			g.setState("stopped")
		}
	} else {
		log.Printf("initial inspect: %v", err)
	}
	log.Printf("wakegate: listen=%s upstream=%s label=%s base=%s extended=%s span>=%s clients>=%d",
		cfg.listen, cfg.upstream, cfg.label, cfg.baseIdle, cfg.extIdle, cfg.span, cfg.minClients)

	go g.idleLoop()

	admin := http.NewServeMux()
	admin.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) { io.WriteString(w, "ok\n") })
	admin.HandleFunc("/status", func(w http.ResponseWriter, _ *http.Request) {
		win, last, sustained, span, clients := g.idleWindow(time.Now())
		st, _ := g.state.Load().(string)
		json.NewEncoder(w).Encode(map[string]any{
			"state": st, "last_request": last.UTC().Format(time.RFC3339), "keepalive": win.String(),
			"sustained": sustained, "span_minutes": span, "clients": clients,
			"stops_in": (win - time.Since(last)).Round(time.Second).String(), "inflight": g.inflight.Load(),
		})
	})
	go func() { log.Fatal(http.ListenAndServe(cfg.adminListen, admin)) }()
	srv := &http.Server{Addr: cfg.listen, Handler: g, ReadHeaderTimeout: 30 * time.Second}
	log.Fatal(srv.ListenAndServe())
}
